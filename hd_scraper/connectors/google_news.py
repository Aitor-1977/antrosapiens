"""Conector Google News RSS (Fase 1, primer conector de punta a punta).

Descubre notas de prensa que mencionan a una empresa a través del feed RSS de
búsqueda de Google News.

Sobre la invariante "no interpreta":
  - ``tipo_evento`` NO se infiere leyendo la nota. Viaja en la ``QuerySpec``:
    lo declara el operador al lanzar la corrida (p. ej. "buscar señales de
    'ronda' de la empresa X"). Es una propiedad estructural de la consulta.
  - ``origen_declaracion`` es ``prensa`` por estructura: la fuente es un feed
    de noticias, no el operador ni el usuario.
El conector solo extrae y reordena campos ya presentes en el RSS.
"""
from __future__ import annotations

import html
import json
import re
import time
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import quote_plus

import feedparser

from ..config import settings
from ..db.models import (
    EvidenceRecord,
    QuerySpec,
    RawItem,
    ahora_iso,
    calcular_hash_dedup,
)
from ..filtros import REGIONES
from .base import Connector

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

# El <link> de un ítem de Google News RSS nunca es la URL del medio: es un
# wrapper que solo un navegador real resuelve (ejecuta JS). Verificado en
# producción (auditoría 2026-09-14): 100% de una muestra de 1060 evidencias
# reales tenía este wrapper sin resolver. Los tres patrones de abajo permiten
# decodificarlo con dos peticiones HTTP planas (sin navegador headless),
# técnica pública y documentada (p. ej. proyecto "google-news-url-decoder"):
# 1) GET al wrapper trae una página con atributos data-n-a-{id,ts,sg} (firma
#    de Google para esa URL concreta).
# 2) POST a `_/DotsSplashUi/data/batchexecute` con esos tres valores devuelve
#    la URL real del artículo.
_WRAPPER_PREFIX = "https://news.google.com/rss/articles/"
_ATTR_ID = re.compile(r'data-n-a-id="([^"]+)"')
_ATTR_TS = re.compile(r'data-n-a-ts="(\d+)"')
_ATTR_SG = re.compile(r'data-n-a-sg="([^"]+)"')
_BATCHEXECUTE_URL = "https://news.google.com/_/DotsSplashUi/data/batchexecute"

_TAG_HTML = re.compile(r"<[^>]+>")
_ESPACIOS = re.compile(r"\s+")
_NO_ALFANUM = re.compile(r"[^\w]+", re.UNICODE)


def _normalizar_para_comparar(texto: str) -> str:
    """Reduce a solo caracteres alfanuméricos en minúscula, para comparar
    'mismo contenido' sin que separadores distintos (" - " en el título del
    RSS vs espacio/&nbsp; en la descripción) generen un falso "es distinto"."""
    return _NO_ALFANUM.sub("", texto).lower()


def _resumen_util(resumen_crudo: str, titulo: str) -> str | None:
    """Limpia el ``<summary>`` del feed y descarta el que no aporta nada.

    Verificado contra el feed real (auditoría 2026-09-14, y contra una
    corrida en vivo real hoy): Google News NO entrega un extracto del cuerpo
    del artículo en ``<description>`` — envía marcado HTML
    (``<a href="...">titular</a>&nbsp;&nbsp;<font>medio</font>``) que, sin
    las etiquetas, es el mismo titular + nombre del medio, solo que el
    título del RSS los separa con " - " y la descripción con espacio/&nbsp;
    (por eso la comparación se hace normalizando separadores, no con
    igualdad literal). Guardar eso como ``resumen_fuente`` presentaría el
    titular disfrazado de contenido nuevo: se descarta (``None``), nunca se
    inventa ni se rellena con el titular."""
    if not resumen_crudo:
        return None
    texto = html.unescape(_TAG_HTML.sub(" ", resumen_crudo))
    texto = _ESPACIOS.sub(" ", texto).strip()
    if not texto:
        return None
    titulo_norm = titulo.strip()
    if not titulo_norm:
        return None
    # startswith (no ==): la descripción real suele ser "titular + medio"
    # concatenado (con o sin el sufijo "- medio" que ya trae el título), así
    # que basta con que el titular sea el prefijo normalizado del resumen.
    if _normalizar_para_comparar(texto).startswith(_normalizar_para_comparar(titulo_norm)):
        return None
    return texto


def _struct_time_a_iso(parsed: time.struct_time | None) -> str | None:
    """Convierte el ``published_parsed`` de feedparser (UTC) a ISO 8601."""
    if not parsed:
        return None
    try:
        dt = datetime(*parsed[:6], tzinfo=timezone.utc)
        return dt.isoformat()
    except (ValueError, TypeError):
        return None


class GoogleNewsConnector(Connector):
    name = "google_news"
    origen_declaracion_default = "prensa"

    def __init__(self, hl: str = "es-419", gl: str = "MX", ceid: str = "MX:es",
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.hl = hl
        self.gl = gl
        self.ceid = ceid

    # -- search ---------------------------------------------------------
    def _build_url(self, query: QuerySpec) -> str:
        # Modo exacto (nombre de empresa): entre comillas para precisión.
        # Modo amplio (descubrimiento por categoría): frase temática sin comillas.
        q = f'"{query.empresa}"' if query.exact else query.empresa
        if query.terminos:
            q += f" {query.terminos}"
        # La región del radar sobreescribe los parámetros por defecto de clase.
        region = REGIONES.get(query.region) if query.region else None
        hl = region["hl"] if region else self.hl
        gl = region["gl"] if region else self.gl
        ceid = region["ceid"] if region else self.ceid
        return (
            f"{GOOGLE_NEWS_RSS}?q={quote_plus(q)}"
            f"&hl={hl}&gl={gl}&ceid={quote_plus(ceid)}"
        )

    def search(self, query: QuerySpec) -> Iterable[RawItem]:
        url = self._build_url(query)
        resp = self.rate_limiter.run(lambda: self._get(url))
        feed = feedparser.parse(resp)
        items: list[RawItem] = []
        resueltas = 0
        for entry in feed.entries:
            fuente = None
            src = entry.get("source")
            if isinstance(src, dict):
                fuente = src.get("title")
            elif src is not None:
                fuente = getattr(src, "title", None) or str(src)

            link = entry.get("link", "")
            if link.startswith(_WRAPPER_PREFIX) and resueltas < settings.google_news_resolver_max:
                resueltas += 1
                resuelto = self._resolver_url_real(link)
                if resuelto:
                    link = resuelto

            meta = {
                "titulo": entry.get("title", ""),
                "link": link,
                "fuente": fuente,
                "fecha_publicacion": _struct_time_a_iso(entry.get("published_parsed")),
                # Resumen/descripción que el feed adjunta a la entrada. Antes
                # se retenía solo en el crudo comprimido y se descartaba al
                # normalizar (auditoría 2026-09-10, P0): se conserva aquí
                # para persistirlo en ``resumen_fuente``, SIN convertirlo en
                # ``cita_textual`` (no es una cita literal).
                "resumen": entry.get("summary", ""),
                # Contexto estructural de la consulta (no del contenido):
                "empresa": query.empresa,
                "tipo_evento": query.tipo_evento,
            }
            # El crudo retenido es la entry serializada (JSON), vinculada por hash.
            crudo = json.dumps(
                {k: entry.get(k) for k in ("title", "link", "published", "summary")},
                ensure_ascii=False,
            )
            items.append(RawItem(url=meta["link"], contenido=crudo, formato="json", meta=meta))
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

    def _resolver_url_real(self, wrapper_url: str) -> str | None:
        """Decodifica un wrapper de Google News a la URL real del medio.

        Best-effort puro: CUALQUIER fallo (red, formato inesperado, JSON
        inválido, atributos ausentes) devuelve ``None`` y el llamador
        conserva el wrapper original — nunca rompe la ingesta. No usa
        navegador headless: son dos peticiones HTTP planas, con timeout
        corto propio (no el de reintentos con backoff del rate limiter
        principal, pensado para el feed, no para esta resolución opcional).
        """
        timeout = settings.google_news_resolver_timeout_s
        try:
            html = self.rate_limiter.run(lambda: self._get_con_timeout(wrapper_url, timeout))
            m_id = _ATTR_ID.search(html)
            m_ts = _ATTR_TS.search(html)
            m_sg = _ATTR_SG.search(html)
            if not (m_id and m_ts and m_sg):
                return None

            payload = {"f.req": self._payload_decode(m_id.group(1), m_ts.group(1), m_sg.group(1))}
            texto = self.rate_limiter.run(
                lambda: self._post_con_timeout(_BATCHEXECUTE_URL, payload, timeout)
            )
            return self._extraer_url_decodificada(texto)
        except Exception:
            # Best-effort: cualquier excepción (red, parseo, formato de
            # Google cambiado) degrada al wrapper original, nunca propaga.
            return None

    def _get_con_timeout(self, url: str, timeout: float) -> str:
        resp = self.client.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text

    def _post_con_timeout(self, url: str, data: dict, timeout: float) -> str:
        resp = self.client.post(
            url, data=data, timeout=timeout,
            headers={"content-type": "application/x-www-form-urlencoded;charset=UTF-8"},
        )
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _payload_decode(article_id: str, ts: str, sg: str) -> str:
        """Payload RPC de Google (formato público, técnica documentada de
        decodificación de wrappers de Google News). No interpreta ni
        modifica contenido: solo reconstruye la petición para obtener la
        URL que Google ya codificó en el propio wrapper."""
        inner = json.dumps([
            "garturlreq",
            [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1,
              None, None, None, None, None, 0, 1],
             "X", "X", 1, [1, 2, 3, 4], 1, 1, None, 0, 0, None, 0],
            article_id, ts, sg,
        ])
        return json.dumps([[["Fbv4je", inner, None, "generic"]]])

    @staticmethod
    def _extraer_url_decodificada(texto: str) -> str | None:
        # La respuesta trae un prefijo anti-XSSI ")]}'" antes del JSON real.
        cuerpo = texto.split("\n", 1)[-1] if texto.startswith(")]}'") else texto
        datos = json.loads(cuerpo)
        # datos[0] = ["wrb.fr", "Fbv4je", "<json-string>", ...]
        interior = json.loads(datos[0][2])
        # interior = ["garturlres", "<url real>", 1]
        url = interior[1] if len(interior) > 1 else None
        return url if isinstance(url, str) and url.startswith("http") else None

    # -- normalize ------------------------------------------------------
    def normalize(self, raw: RawItem) -> EvidenceRecord:
        m = raw.meta
        empresa = m.get("empresa", "")
        url_fuente = m.get("link") or raw.url
        return EvidenceRecord(
            cita_textual=(m.get("titulo") or "").strip(),
            fecha_extraccion=ahora_iso(),
            url_fuente=url_fuente,
            nombre_medio=(m.get("fuente") or "Google News").strip(),
            empresa_mencionada=empresa,
            tipo_evento=m.get("tipo_evento", ""),
            origen_declaracion=self.origen_declaracion_default,
            hash_dedup=calcular_hash_dedup(empresa, url_fuente),
            fecha_publicacion=m.get("fecha_publicacion"),
            persona_citada=None,   # el RSS no la provee de forma estructural
            cargo=None,
            resumen_fuente=_resumen_util(m.get("resumen") or "", m.get("titulo") or ""),
            connector=self.name,
        )
