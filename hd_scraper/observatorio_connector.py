"""Conector de ingesta del Observatorio Antropológico del Ecosistema.

Clase INDEPENDIENTE, deliberadamente sin heredar `Connector`
(`hd_scraper/connectors/base.py`): ese contrato devuelve un `EvidenceRecord`
para la tabla `evidencias` y su ejecución (`pipeline.run_connector`) pasa por
`evaluar_relevancia`/`calcular_confianza`/`calcular_calidad` — maquinaria de
scoring del radar comercial que el Observatorio no usa. Decisión del Fase 1
del encargo (operador —Mario—, 2026-09-18, camino (a)): reutiliza solo el
cliente HTTP y el rate limiter, sin heredar search/normalize/validate/
run_connector.

Fuente: Apple Podcasts Search API (pública, sin API key, sin costo). Busca
episodios de podcast/entrevista que mencionan a un actor u organización
dada. `tipo_fuente="podcast"` es estructural (lo declara este conector, no
se infiere del contenido) — mismo principio que `tipo_evento` en `QuerySpec`
para el radar comercial.

NUNCA importa `clasificacion_epistemologica.py` ni `promocion_candidatos.py`.
El texto capturado es `texto_citable` tal cual lo publica la plataforma
(descripción del episodio): no se resume, no se interpreta, no se infiere
ningún patrón — eso es lectura humana de Mario, no de este conector.
"""
from __future__ import annotations

import httpx

from .config import settings
from .db.models import ahora_iso, calcular_hash_dedup
from .governance.rate_limit import RateLimiter

BUSQUEDA_PODCAST_API = "https://itunes.apple.com/search"


def _duracion_legible(track_time_millis: int | None) -> str | None:
    if not track_time_millis:
        return None
    minutos = round(track_time_millis / 60000)
    return f"{minutos} min"


class ObservatorioPodcastConnector:
    """Busca y normaliza episodios de podcast/entrevista para un actor dado.

    No implementa `search`/`fetch`/`normalize`/`validate` del contrato de
    `Connector`: `buscar()` y `normalizar()` son sus propios métodos, con su
    propia forma de salida (`fuente_discursiva`/`fragmento_observado`, no
    `EvidenceRecord`).
    """

    name = "observatorio_podcast"

    def __init__(self, client: httpx.Client | None = None,
                 rate_limiter: RateLimiter | None = None, limite: int = 10) -> None:
        self._own_client = client is None
        self.client = client or httpx.Client(
            timeout=settings.request_timeout_s,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        )
        self.rate_limiter = rate_limiter or RateLimiter(self.name)
        self.limite = max(1, min(limite, 50))

    def close(self) -> None:
        if self._own_client:
            self.client.close()

    def __enter__(self) -> "ObservatorioPodcastConnector":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def buscar(self, actor: str) -> list[dict]:
        """Episodios crudos (JSON de Apple Podcasts) que mencionan `actor`."""
        def _peticion():
            resp = self.client.get(BUSQUEDA_PODCAST_API, params={
                "term": actor, "media": "podcast", "entity": "podcastEpisode",
                "limit": self.limite,
            })
            resp.raise_for_status()
            return resp.json().get("results", [])
        return self.rate_limiter.run(_peticion)

    def normalizar(self, actor: str, episodio: dict) -> tuple[dict, dict]:
        """Mapea un episodio crudo a (fuente_discursiva, fragmento_observado).

        Extracción estructural: reordena campos ya presentes en la respuesta
        de la plataforma. No interpreta ni infiere contenido nuevo.
        """
        url = episodio.get("trackViewUrl") or episodio.get("episodeUrl") or ""
        fuente = {
            "tipo_fuente": "podcast",
            "url": url,
            "plataforma": "Apple Podcasts",
            "actor_principal": actor,
            "fecha_publicacion": episodio.get("releaseDate"),
            "fecha_captura": ahora_iso(),
            "duracion_aprox": _duracion_legible(episodio.get("trackTimeMillis")),
            "hash_contenido": calcular_hash_dedup(actor, url),
        }
        generos = episodio.get("genres") or []
        genero = generos[0].get("name") if generos else None
        fragmento = {
            "texto_citable": (episodio.get("description")
                              or episodio.get("shortDescription") or "").strip(),
            "minuto_aproximado": None,
            "tema_libre": genero,
            "tipo_registro": "dato",
            "estado": "capturado",
        }
        return fuente, fragmento


def buscar_y_normalizar(actor: str, limite: int = 10) -> list[tuple[dict, dict]]:
    """Corrida completa (búsqueda + normalización) para un actor, sin tocar
    la base de datos — la persistencia la decide quien llama (endpoint o
    script), igual que `guardar_fuente_y_fragmento` en `observatorio_store`.

    Descarta episodios sin texto citable real (sin descripción publicada):
    no hay nada que observar, no se inventa contenido.
    """
    with ObservatorioPodcastConnector(limite=limite) as conector:
        crudos = conector.buscar(actor)
        pares = [conector.normalizar(actor, ep) for ep in crudos]
    return [(f, g) for f, g in pares if g["texto_citable"]]
