"""Conector de búsqueda dinámica de auto-declaraciones de founders.

A diferencia de los conectores de Fase 1 (que buscan por EMPRESA en una fuente
fija), este conector ejecuta un LÉXICO de frases en primera persona contra un
motor de búsqueda web general (Google Custom Search JSON API) y trae
resultados nuevos en cada corrida, sin depender de una lista fija de sitios ni
de autores. El objetivo no es una empresa: es la POSTURA de quien habla (un
founder narrando en primera persona un error, un cierre o un pivote), que es
justo la señal que hoy falta en el corpus de prensa (ver
``clasificacion_epistemologica.py``: un titular de agencia rara vez trae una
autodeclaración identificable).

Aislado del resto del sistema a propósito: valor de ``connector`` propio
('busqueda_dinamica_founder'), no toca `clasificacion_epistemologica.py`,
`promocion_candidatos.py` ni `android_v2`.

Sobre la invariante "no interpreta":
  - ``tipo_evento`` NO se infiere leyendo el resultado. Cada FRASE del léxico
    trae su ``tipo_evento`` fijo en ``FRASES_FOUNDER``, declarado en este
    módulo — mismo patrón que ``TIPO_KEYWORDS`` en ``discovery.py``.
  - ``origen_declaracion`` es ``'usuario'`` por estructura: el léxico completo
    busca explícitamente publicaciones en primera persona de un individuo, no
    comunicados de la organización (`operador`) ni notas de prensa (`prensa`).
  - ``empresa_mencionada`` es la FRASE de búsqueda (término de la consulta), NO
    una empresa detectada leyendo el contenido. Mismo patrón que el
    descubrimiento por categoría (ver el comentario sobre
    ``calcular_hash_dedup`` en ``db/models.py``: "en descubrimiento por
    categoría la 'empresa' es el TÉRMINO de la consulta, no una compañía
    real"). Por eso ``QuerySpec.exact`` se deja en ``True`` al invocar este
    conector: así el pipeline NO reescribe ``empresa_mencionada`` intentando
    detectar un nombre propio (`pipeline.py`) ni aplica el filtro de
    relevancia de descubrimiento por ecosistema (`relevance.py`), que está
    calibrado para eventos de negocio de prensa y descartaría por diseño el
    propio tono de "reflexión/opinión" que este léxico busca a propósito.
  - ``nombre_medio`` es el DOMINIO (host) de la URL del resultado —
    extracción estructural de la URL, no lectura del contenido.
  - ``persona_citada``/``cargo`` se rellenan SOLO si la propia página lo
    declaró como metadata estructural (``schema.org/Person`` o metatags de
    autoría: ``author``, ``article:author``, ``twitter:creator``…) que la API
    ya trae en ``pagemap``. Es el mismo dato que ya expone
    ``clasificacion_epistemologica.py`` como columna del contrato con
    prioridad sobre el texto (ver su docstring); este conector solo lo
    traslada cuando la fuente lo publicó, nunca lo infiere leyendo el cuerpo.
    Sin ese metadato (el caso más común), ambas quedan en ``None``, igual que
    en los cuatro conectores de Fase 1.
  - Sin restricción de país ni categoría en la búsqueda: ese filtro ya existe
    en la app (curaduría/relevancia) y se aplica después, no aquí.

Requiere ``GOOGLE_CSE_API_KEY`` y ``GOOGLE_CSE_CX`` (ver ``config.py``). Sin
ambas, ``search`` no ejecuta ninguna llamada de red y devuelve vacío (nunca
lanza): el resto del sistema sigue funcionando sin este conector configurado.
"""
from __future__ import annotations

import json
from typing import Iterable, Optional
from urllib.parse import quote_plus, urlsplit

from ..config import settings
from ..db.models import (
    EvidenceRecord,
    QuerySpec,
    RawItem,
    ahora_iso,
    calcular_hash_dedup,
)
from .base import Connector

GOOGLE_CSE_API = "https://www.googleapis.com/customsearch/v1"

# Léxico de partida (ajustable, no definitivo — ver discusión con el
# operador). Cada frase declara su propio tipo_evento estructural: lo fija
# quien mantiene este módulo, nunca se infiere leyendo el resultado.
#   - "pivotar" -> cambio_sitio (mismo bucket que usa discovery.py para pivote).
#   - "renuncié como CEO porque" -> despido (salida de la máxima autoridad;
#     es la aproximación más cercana dentro del vocabulario cerrado del
#     contrato, que no tiene un tipo_evento propio para renuncia ejecutiva).
#   - el resto son variantes del bucket de fricción/crisis -> queja.
FRASES_FOUNDER: tuple[tuple[str, str], ...] = (
    ('"cometí el error de" startup', "queja"),
    ('"el error que casi" mi empresa', "queja"),
    ('"lo que aprendí cuando cerré" startup', "queja"),
    ('"por qué decidimos pivotar" startup', "cambio_sitio"),
    ('"el problema que no vi venir en mi startup"', "queja"),
    ('"casi quiebro mi empresa cuando"', "queja"),
    ('"renuncié como CEO porque"', "despido"),
    ('"la decisión que casi hunde a mi startup"', "queja"),
)

RESULTADOS_POR_FRASE_DEFAULT = 10  # tope de resultados por página de la API


def _host(url: str) -> str:
    """Dominio de una URL, o 'desconocido' si no se puede extraer. Estructural."""
    try:
        host = urlsplit(url).netloc
    except ValueError:
        return "desconocido"
    return host or "desconocido"


def _fecha_de_pagemap(pagemap: Optional[dict]) -> Optional[str]:
    """Fecha de publicación de los metatags que la API puede devolver.

    Estructural: solo lee campos ya presentes en la respuesta (metatags
    Open Graph / article que el propio sitio publicó), no interpreta el
    contenido de la página.
    """
    if not pagemap:
        return None
    metatags = pagemap.get("metatags") or []
    if not metatags:
        return None
    tags = metatags[0] or {}
    for campo in ("article:published_time", "og:updated_time", "date", "datepublished"):
        valor = tags.get(campo)
        if valor:
            return valor
    return None


def _persona_y_cargo_de_pagemap(pagemap: Optional[dict]) -> tuple[Optional[str], Optional[str]]:
    """(persona_citada, cargo) desde metadata estructural de la página, si existe.

    Algunos sitios (Medium, LinkedIn, blogs corporativos) publican marcado
    ``schema.org/Person`` (autor + ``jobtitle``) o metatags de autoría
    (``author``, ``article:author``, ``twitter:creator``, ``parsely-author``).
    Cuando ese dato existe, es la ORGANIZACIÓN/PLATAFORMA FUENTE la que declaró
    quién escribe y con qué cargo — no algo que este conector infiera leyendo
    el cuerpo del texto. Por eso ``clasificacion_epistemologica.py`` da
    prioridad a estas dos columnas por encima del texto (ver su docstring).
    Sin ese dato estructural (lo más frecuente), ambas quedan en ``None`` y la
    fila cae al mismo camino que hoy siguen los cuatro conectores de Fase 1
    (persona_citada/cargo NULL, atribución leída del propio texto si la hay).
    """
    if not pagemap:
        return None, None
    personas = pagemap.get("person") or []
    if personas:
        p = personas[0] or {}
        nombre = (p.get("name") or "").strip() or None
        cargo = (p.get("jobtitle") or p.get("jobtitile") or "").strip() or None
        if nombre or cargo:
            return nombre, cargo

    metatags = pagemap.get("metatags") or []
    if not metatags:
        return None, None
    tags = metatags[0] or {}
    nombre = None
    for campo in ("author", "article:author", "twitter:creator", "parsely-author",
                  "sailthru.author", "citation_author"):
        valor = (tags.get(campo) or "").strip()
        if valor:
            nombre = valor
            break
    cargo = None
    for campo in ("profile:job_title", "job_title", "jobtitle"):
        valor = (tags.get(campo) or "").strip()
        if valor:
            cargo = valor
            break
    return nombre, cargo


class BusquedaDinamicaConnector(Connector):
    name = "busqueda_dinamica_founder"
    origen_declaracion_default = "usuario"

    def __init__(self, frases: Optional[tuple[tuple[str, str], ...]] = None,
                 resultados_por_frase: int = RESULTADOS_POR_FRASE_DEFAULT,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.frases = frases if frases is not None else FRASES_FOUNDER
        self.resultados_por_frase = max(1, min(resultados_por_frase, 10))

    def _disponible(self) -> bool:
        return bool(settings.google_cse_api_key and settings.google_cse_cx)

    def _build_url(self, frase: str) -> str:
        return (
            f"{GOOGLE_CSE_API}?key={quote_plus(settings.google_cse_api_key)}"
            f"&cx={quote_plus(settings.google_cse_cx)}"
            f"&q={quote_plus(frase)}&num={self.resultados_por_frase}"
        )

    # -- search ---------------------------------------------------------
    def search(self, query: QuerySpec) -> Iterable[RawItem]:
        if not self._disponible():
            self.emit_health(self.name, ok=False,
                              detalle="sin GOOGLE_CSE_API_KEY/GOOGLE_CSE_CX")
            return []

        items: list[RawItem] = []
        for frase, tipo_evento in self.frases:
            url = self._build_url(frase)
            try:
                texto = self.rate_limiter.run(lambda u=url: self._get(u))
                data = self._parse_json(texto)
            except Exception as exc:  # una frase caída no tumba a las demás
                self.emit_health(f"{self.name}:{frase}", ok=False, detalle=str(exc)[:200])
                continue

            resultados = data.get("items", [])
            self.emit_health(f"{self.name}:{frase}", ok=True,
                              detalle=f"{len(resultados)} resultados")

            for r in resultados:
                link = r.get("link", "")
                pagemap = r.get("pagemap")
                persona, cargo = _persona_y_cargo_de_pagemap(pagemap)
                meta = {
                    "titulo": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "link": link,
                    "frase": frase,
                    "tipo_evento": tipo_evento,
                    "fecha_publicacion": _fecha_de_pagemap(pagemap),
                    "persona_citada": persona,
                    "cargo": cargo,
                }
                crudo = json.dumps(r, ensure_ascii=False)
                items.append(RawItem(url=link, contenido=crudo, formato="json", meta=meta))
        return items

    # -- fetch ------------------------------------------------------------
    def fetch(self, url: str) -> RawItem:
        """Trae el HTML de una URL puntual (crudo, sin parsear)."""
        html = self.rate_limiter.run(lambda: self._get(url))
        return RawItem(url=url, contenido=html, formato="html", meta={})

    def _get(self, url: str) -> str:
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_json(texto: str) -> dict:
        texto = (texto or "").strip()
        if not texto:
            return {"items": []}
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            return {"items": []}

    # -- normalize ----------------------------------------------------------
    def normalize(self, raw: RawItem) -> EvidenceRecord:
        m = raw.meta
        url_fuente = m.get("link") or raw.url
        empresa = m.get("frase", "")
        titulo = (m.get("titulo") or "").strip()
        snippet = (m.get("snippet") or "").strip()
        cita = " — ".join(x for x in (titulo, snippet) if x)
        return EvidenceRecord(
            cita_textual=cita,
            fecha_extraccion=ahora_iso(),
            url_fuente=url_fuente,
            nombre_medio=_host(url_fuente),
            empresa_mencionada=empresa,
            tipo_evento=m.get("tipo_evento", ""),
            origen_declaracion=self.origen_declaracion_default,
            hash_dedup=calcular_hash_dedup(empresa, url_fuente),
            fecha_publicacion=m.get("fecha_publicacion"),
            persona_citada=m.get("persona_citada"),
            cargo=m.get("cargo"),
            connector=self.name,
        )
