"""Conector de feeds RSS fijos (Fase 1, tercer conector).

A diferencia de Google News / GDELT (que buscan por empresa en una API), aquí
se traen feeds RSS de sitios completos y se filtran las entradas que MENCIONAN
la empresa como PALABRA COMPLETA (mismo criterio de `_ocurrencias_org` de
`clasificacion_epistemologica.py`, reutilizado tal cual, no reimplementado).
Ese filtro es extracción determinista (¿contiene el texto el nombre de la
empresa?), NO interpretación: no se lee ni se juzga el contenido.

Corrección 2026-09-20 (ver CLAUDE.md, "Errores recurrentes" #6): antes el
filtro era `subcadena in texto`, sin límite de palabra, y admitía falsos
positivos reales de producción ("mundi" dentro de "mundial", "clara" dentro
de "declaración"/"aclara"). Ahora reutiliza `_ocurrencias_org` (que ya
combina `\b...\b` con la Guardia 1, `_es_parte_de_nombre_mas_largo`, para
nombres de una sola palabra — el mismo caso real "Clara"/"Clara Brugada" que
ya protege `_construir_expedientes`), en vez de una segunda implementación
de la guardia.

Fuentes fijas de Fase 1: Startupeable, Contxto, LAVCA, LatamList,
Bloomberg Línea, Forbes México, El CEO, Xataka México, DPL News, Expansión,
El Financiero.

Sobre la invariante "no interpreta":
  - ``tipo_evento`` viaja en la ``QuerySpec`` (lo declara el operador).
  - ``origen_declaracion`` es ``prensa`` por estructura (son medios).
  - ``nombre_medio`` es el nombre fijo de la fuente (autoritativo), no lo que
    diga el feed.

Salud: cada feed es una sub-fuente independiente. El conector emite un evento
de salud por feed (``rss_fijos:<Medio>``); el pipeline lo persiste. Así, si un
feed puntual cae 2 corridas seguidas, se marca su alerta sin afectar a los otros.

Cuerpo del artículo vía JSON-LD (2026-09-20, resuelve el techo confirmado
empíricamente contra 25 URLs reales de Google News: su enlace envoltorio
nunca entrega cuerpo sin JavaScript; el RSS directo del medio sí trae una URL
real navegable). Para cada entrada que YA pasó el filtro de mención literal
(no se profundiza en URLs que no son candidatas), se hace UN fetch adicional
de esa URL y se lee el bloque `<script type="application/ld+json">`
Article/NewsArticle/BlogPosting que el propio medio ya declara — nunca se
parsea HTML a mano para extraer el cuerpo. `articleBody` si está presente,
si no `description` (ambos declarados por el medio, nunca inventados). Si el
fetch falla o no hay JSON-LD reconocible, la entrada degrada exactamente al
comportamiento anterior (solo titular) sin tumbar las demás — mismo criterio
de resiliencia que ya aplica a un feed caído. `cita_textual` pasa a ser
titular + cuerpo (titular siempre primero, para no alterar el comportamiento
de todo lector existente que asume que el nombre de la organización aparece
al inicio, p. ej. `relevance.detectar_empresa`); nunca se sobrescribe el
titular con el cuerpo. `persona_citada`/`cargo` NUNCA se rellenan desde el
autor de la nota (el autor es quien ESCRIBE, no a quien se cita): decidir
quién habla dentro del cuerpo sigue siendo, exclusivamente, trabajo de
`clasificacion_epistemologica.py`, que no se toca aquí.

Medios evaluados y NO agregados, documentados para no reintentar a ciegas
(ver CLAUDE.md, "Errores recurrentes"): El Economista bloquea con 403 incluso
la URL de su propio `<link rel="alternate">` (protección anti-bot del CDN,
no una ruta equivocada); Bloomberg Línea ya está en la lista pero su feed
puede degradar igual si el proveedor cambia su protección — se deja tal cual,
gestionado por la salud existente. Forbes México YA estaba en `FEEDS_DEFAULT`
antes de esta ampliación; su feed hoy responde 403 "invalid or missing feed
token" (antes abierto, ahora cerrado con token) — no se retira de la lista:
la salud por feed ya existente lo reporta como caído sin intervención nueva.
"""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Iterable, Optional

import feedparser

from ..clasificacion_epistemologica import _ocurrencias_org
from ..db.models import (
    EvidenceRecord,
    QuerySpec,
    RawItem,
    ahora_iso,
    calcular_hash_dedup,
)
from .base import Connector
from .google_news import _struct_time_a_iso

# Feeds fijos de Fase 1. Configurables por si una URL cambia. El nombre (clave)
# es el ``nombre_medio`` autoritativo que se persiste. Agregar un medio nuevo
# es sumar una entrada aquí: el fetch de cuerpo vía JSON-LD es genérico
# (schema.org Article/NewsArticle/BlogPosting), no hay lógica por medio.
FEEDS_DEFAULT: dict[str, str] = {
    "Startupeable": "https://startupeable.com/feed/",
    # Contxto migró su feed a rutas con prefijo de idioma (auditoría
    # 2026-09-10, P0): la URL anterior devuelve 404 verificado en vivo; esta
    # SÍ responde 200 con entradas válidas. Recuperación de una fuente ya
    # declarada, no una fuente nueva.
    "Contxto": "https://contxto.com/es/feed/",
    "LAVCA": "https://www.lavca.org/feed/",
    "LatamList": "https://latamlist.com/feed/",
    "Bloomberg Línea": "https://www.bloomberglinea.com/arc/outboundfeeds/rss/?outputType=xml",
    # Forbes México: feed verificado en vivo 2026-09-20, responde 403
    # "invalid or missing feed token" (antes abierto). Se conserva en la
    # lista: la salud por feed ya reporta el fallo sin código nuevo.
    "Forbes México": "https://www.forbes.com.mx/feed/",
    "El CEO": "https://elceo.com/feed/",
    "Xataka México": "https://www.xataka.com.mx/tag/feeds/rss2.xml",
    # Ampliación 2026-09-20 (RSS directo como fuente de contenido primario,
    # ver CLAUDE.md): los 3 medios confirmados accesibles ese día, además de
    # El CEO y Forbes México (ya en la lista).
    "DPL News": "https://dplnews.com/feed/",
    "Expansión": "https://expansion.mx/rss",
    "El Financiero": "https://www.elfinanciero.com.mx/rss/",
}

# Tope de caracteres del cuerpo recuperado vía JSON-LD, para no dejar crecer
# cita_textual sin límite con artículos largos. El titular nunca se recorta.
MAX_CUERPO_CHARS = 4000

_TIPOS_ARTICULO = {"Article", "NewsArticle", "BlogPosting"}
_RE_JSON_LD = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.S | re.I,
)


def _extraer_json_ld_articulo(html: str) -> Optional[dict]:
    """Cuerpo/fecha del primer bloque JSON-LD Article/NewsArticle/BlogPosting.

    Estructural, no interpretación: solo lee el JSON que el propio medio ya
    declara en su página (schema.org), sin parsear HTML a mano. Devuelve
    ``None`` si no hay ningún bloque reconocible — nunca inventa contenido.
    """
    for bloque in _RE_JSON_LD.findall(html):
        try:
            data = json.loads(bloque.strip())
        except (ValueError, TypeError):
            continue
        candidatos = data if isinstance(data, list) else [data]
        for item in candidatos:
            if not isinstance(item, dict):
                continue
            tipo = item.get("@type")
            tipos = tipo if isinstance(tipo, list) else [tipo]
            if not any(t in _TIPOS_ARTICULO for t in tipos):
                continue
            cuerpo = (item.get("articleBody") or item.get("description") or "").strip()
            return {
                "cuerpo": cuerpo[:MAX_CUERPO_CHARS],
                "fecha_publicacion": item.get("datePublished"),
            }
    return None


def _normalizar_texto(texto: str) -> str:
    """Minúsculas + sin acentos, para una coincidencia literal robusta."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    sin_acentos = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sin_acentos.lower()


class RssFijosConnector(Connector):
    name = "rss_fijos"
    origen_declaracion_default = "prensa"

    def __init__(self, feeds: dict[str, str] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.feeds = dict(feeds) if feeds is not None else dict(FEEDS_DEFAULT)

    # -- search ---------------------------------------------------------
    def search(self, query: QuerySpec) -> Iterable[RawItem]:
        objetivo = _normalizar_texto(query.empresa)
        items: list[RawItem] = []
        for medio, url in self.feeds.items():
            try:
                texto = self.rate_limiter.run(lambda u=url: self._get(u))
                feed = feedparser.parse(texto)
            except Exception as exc:  # un feed caído no tumba a los demás
                self.emit_health(f"{self.name}:{medio}", ok=False, detalle=str(exc)[:200])
                continue

            self.emit_health(f"{self.name}:{medio}", ok=True,
                             detalle=f"{len(feed.entries)} entradas")

            for entry in feed.entries:
                titulo = entry.get("title", "")
                resumen = entry.get("summary", "")
                # Filtro estructural: ¿el texto menciona literalmente la
                # empresa? Reutiliza la Guardia 1 ya validada
                # (`_ocurrencias_org`, que internamente usa
                # `_es_parte_de_nombre_mas_largo`) de
                # `clasificacion_epistemologica.py`, en vez de un `in` por
                # subcadena sin límite de palabra. Corrige el falso positivo
                # real de producción 2026-09-20: "mundi" coincidía dentro de
                # "mundial" y "clara" dentro de "declaración"/"aclara" (sin
                # límite de palabra, cualquier subcadena bastaba). Para
                # nombres de una sola palabra, además descarta el caso ya
                # conocido ("Clara" pegada a "Brugada", un tercero).
                texto_filtro = f"{titulo} {resumen}"
                plano_filtro = _normalizar_texto(texto_filtro)
                if objetivo and not _ocurrencias_org(texto_filtro, plano_filtro, objetivo):
                    continue
                link = entry.get("link", "")
                # Cuerpo vía JSON-LD (2026-09-20): solo se profundiza en URLs
                # que YA pasaron el filtro de mención literal (candidatas), un
                # fetch adicional por entrada, nunca scraping indiscriminado.
                # Cualquier fallo (red, sin JSON-LD reconocible) degrada al
                # comportamiento anterior — solo titular — sin tumbar el resto.
                cuerpo, fecha_jsonld = "", None
                if link:
                    try:
                        html_articulo = self.rate_limiter.run(lambda u=link: self._get(u))
                        info = _extraer_json_ld_articulo(html_articulo)
                        if info:
                            cuerpo = info["cuerpo"]
                            fecha_jsonld = info["fecha_publicacion"]
                    except Exception:
                        pass
                meta = {
                    "titulo": titulo,
                    "link": link,
                    "medio": medio,
                    "cuerpo": cuerpo,
                    "fecha_publicacion": (
                        fecha_jsonld or _struct_time_a_iso(entry.get("published_parsed"))
                    ),
                    # Resumen/descripción del feed. Ya se leía para el filtro
                    # de mención literal (línea arriba); antes se descartaba
                    # al normalizar (auditoría 2026-09-10, P0). Se conserva
                    # aparte de ``cita_textual``: no es una cita literal.
                    "resumen": resumen,
                    "empresa": query.empresa,
                    "tipo_evento": query.tipo_evento,
                }
                crudo = "\n".join(filter(None, [titulo, resumen, cuerpo, link]))
                items.append(RawItem(url=link, contenido=crudo, formato="xml", meta=meta))
        return items

    # -- fetch ----------------------------------------------------------
    def fetch(self, url: str) -> RawItem:
        """Trae el HTML de una URL puntual (crudo, sin parsear)."""
        html = self.rate_limiter.run(lambda: self._get(url))
        return RawItem(url=url, contenido=html, formato="html", meta={})

    def _get(self, url: str) -> str:
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp.text

    # -- normalize ------------------------------------------------------
    def normalize(self, raw: RawItem) -> EvidenceRecord:
        m = raw.meta
        empresa = m.get("empresa", "")
        url_fuente = m.get("link") or raw.url
        titulo = (m.get("titulo") or "").strip()
        cuerpo = (m.get("cuerpo") or "").strip()
        # Titular SIEMPRE primero: preserva el comportamiento de todo lector
        # existente que asume que el nombre de la organización aparece al
        # inicio del texto (p. ej. relevance.detectar_empresa). El cuerpo se
        # agrega, nunca sustituye al titular.
        cita_textual = f"{titulo}. {cuerpo}" if cuerpo else titulo
        return EvidenceRecord(
            cita_textual=cita_textual,
            fecha_extraccion=ahora_iso(),
            url_fuente=url_fuente,
            nombre_medio=m.get("medio", "").strip(),
            empresa_mencionada=empresa,
            tipo_evento=m.get("tipo_evento", ""),
            origen_declaracion=self.origen_declaracion_default,
            hash_dedup=calcular_hash_dedup(empresa, url_fuente),
            fecha_publicacion=m.get("fecha_publicacion"),
            persona_citada=None,
            cargo=None,
            resumen_fuente=(m.get("resumen") or "").strip() or None,
            connector=self.name,
        )
