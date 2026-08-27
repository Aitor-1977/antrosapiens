"""Conector de búsqueda dinámica de auto-declaraciones de founders.

A diferencia de los conectores de Fase 1 (que buscan por EMPRESA en una fuente
fija), este conector ejecuta un LÉXICO de frases en primera persona contra un
motor de búsqueda web general (Tavily Search API) y trae resultados nuevos en
cada corrida, sin depender de una lista fija de sitios ni de autores. El
objetivo no es una empresa: es la POSTURA de quien habla (un founder narrando
en primera persona un error, un cierre o un pivote), que es justo la señal que
hoy falta en el corpus de prensa (ver ``clasificacion_epistemologica.py``: un
titular de agencia rara vez trae una autodeclaración identificable).

Se eligió Tavily (en vez de Google Custom Search) porque su capa gratuita no
exige vincular una tarjeta/cuenta de facturación (Google Custom Search sí,
incluso dentro de sus 100 consultas/día gratis) — decisión del operador.

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
  - ``persona_citada``/``cargo`` quedan en ``None``: la respuesta de Tavily no
    trae metadata estructural de autoría (a diferencia del ``pagemap`` de
    Google CSE) y este conector no la infiere leyendo el cuerpo del texto.
    Mismo estado que los cuatro conectores de Fase 1.
  - Sin restricción de país ni categoría en la búsqueda: ese filtro ya existe
    en la app (curaduría/relevancia) y se aplica después, no aquí.

Requiere ``TAVILY_API_KEY`` (ver ``config.py``). Sin ella, ``search`` no
ejecuta ninguna llamada de red y devuelve vacío (nunca lanza): el resto del
sistema sigue funcionando sin este conector configurado.
"""
from __future__ import annotations

import json
from typing import Iterable, Optional
from urllib.parse import urlsplit

from ..config import settings
from ..db.models import (
    EvidenceRecord,
    QuerySpec,
    RawItem,
    ahora_iso,
    calcular_hash_dedup,
)
from .base import Connector

TAVILY_SEARCH_API = "https://api.tavily.com/search"

# Longitud máxima del extracto de cuerpo completo (``raw_content`` de Tavily)
# que se conserva en ``cita_textual``. Es una cita, no un volcado íntegro de la
# página; el crudo completo igual se retiene comprimido en disco (raw_store).
MAX_CUERPO_CHARS = 2000

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

RESULTADOS_POR_FRASE_DEFAULT = 10  # tope de resultados por frase


def _host(url: str) -> str:
    """Dominio de una URL, o 'desconocido' si no se puede extraer. Estructural."""
    try:
        host = urlsplit(url).netloc
    except ValueError:
        return "desconocido"
    return host or "desconocido"


class BusquedaDinamicaConnector(Connector):
    name = "busqueda_dinamica_founder"
    origen_declaracion_default = "usuario"

    def __init__(self, frases: Optional[tuple[tuple[str, str], ...]] = None,
                 resultados_por_frase: int = RESULTADOS_POR_FRASE_DEFAULT,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.frases = frases if frases is not None else FRASES_FOUNDER
        self.resultados_por_frase = max(1, min(resultados_por_frase, 20))

    def _disponible(self) -> bool:
        return bool(settings.tavily_api_key)

    def _payload(self, frase: str) -> dict:
        return {
            "query": frase,
            "max_results": self.resultados_por_frase,
            "include_raw_content": True,
            "search_depth": "basic",
        }

    # -- search ---------------------------------------------------------
    def search(self, query: QuerySpec) -> Iterable[RawItem]:
        if not self._disponible():
            self.emit_health(self.name, ok=False, detalle="sin TAVILY_API_KEY")
            return []

        items: list[RawItem] = []
        for frase, tipo_evento in self.frases:
            try:
                texto = self.rate_limiter.run(
                    lambda f=frase: self._post(TAVILY_SEARCH_API, self._payload(f)))
                data = self._parse_json(texto)
            except Exception as exc:  # una frase caída no tumba a las demás
                self.emit_health(f"{self.name}:{frase}", ok=False, detalle=str(exc)[:200])
                continue

            resultados = data.get("results", [])
            self.emit_health(f"{self.name}:{frase}", ok=True,
                              detalle=f"{len(resultados)} resultados")

            for r in resultados:
                link = r.get("url", "")
                meta = {
                    "titulo": r.get("title", ""),
                    "contenido": r.get("content", ""),
                    "cuerpo_completo": r.get("raw_content", ""),
                    "link": link,
                    "frase": frase,
                    "tipo_evento": tipo_evento,
                    # Tavily solo declara fecha en modo topic='news'; en modo
                    # general (el que usamos, sin restringir a prensa) el
                    # campo suele venir ausente. Se lee si existe (estructural,
                    # no se calcula), y si no, el registro cae a no_fechado.
                    "fecha_publicacion": r.get("published_date") or None,
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

    def _post(self, url: str, payload: dict) -> str:
        resp = self.client.post(
            url, json=payload,
            headers={"Authorization": f"Bearer {settings.tavily_api_key}"},
        )
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _parse_json(texto: str) -> dict:
        texto = (texto or "").strip()
        if not texto:
            return {"results": []}
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            return {"results": []}

    # -- normalize ----------------------------------------------------------
    def normalize(self, raw: RawItem) -> EvidenceRecord:
        m = raw.meta
        url_fuente = m.get("link") or raw.url
        empresa = m.get("frase", "")
        titulo = (m.get("titulo") or "").strip()
        contenido = (m.get("contenido") or "").strip()
        cuerpo = (m.get("cuerpo_completo") or "").strip()[:MAX_CUERPO_CHARS]
        cita = " — ".join(x for x in (titulo, contenido, cuerpo) if x)
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
            persona_citada=None,
            cargo=None,
            connector=self.name,
        )
