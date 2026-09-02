"""Orquestador de fuentes — coordinación multifuente (Entrega 4).

Una sola capa que, dada una ``QuerySpec``, ejecuta los conectores habilitados y
reúne su resultado. **No reimplementa el pipeline**: delega en
``pipeline.run_connector``, que ya hace search → normalize → validate →
(guardar crudo + escribir con dedup) | rechazo. **No clasifica, no puntúa, no
interpreta**: la clasificación epistemológica sigue siendo exclusiva de
``clasificacion_epistemologica.py``, aguas abajo.

Fuentes habilitadas (prioridad):
  1. el argumento ``fuentes=`` de ``OrquestadorFuentes``;
  2. ``settings.fuentes_activas`` (``HD_FUENTES_ACTIVAS``);
  3. todas las registradas en ``connectors.REGISTRY``.

El ``scheduler`` NO usa esta clase (sigue barriendo el ``REGISTRY`` completo).
El orquestador es para corridas dirigidas: scripts, benchmark de fuentes y tests.
"""
from __future__ import annotations

import logging
from typing import Iterable

from .config import settings
from .connectors import REGISTRY
from .db.database import Database
from .db.models import EvidenceRecord, QuerySpec
from .pipeline import RunResult, run_connector

log = logging.getLogger("hd_scraper.orquestador")


class FuenteDesconocida(ValueError):
    """Se pidió una fuente que no está en ``connectors.REGISTRY``."""


def _resolver_fuentes(fuentes: Iterable[str] | None) -> list[str]:
    """Nombres de conector a usar, validados contra ``REGISTRY``.

    Devuelve la lista en el orden estable del ``REGISTRY`` (no en el orden en que
    las pidió el llamador), para que dos corridas con el mismo conjunto de
    fuentes las ejecuten siempre igual.
    """
    pedidas = list(fuentes) if fuentes is not None else list(settings.fuentes_activas)
    if not pedidas:
        return list(REGISTRY)
    desconocidas = [f for f in pedidas if f not in REGISTRY]
    if desconocidas:
        raise FuenteDesconocida(
            f"fuentes no registradas: {desconocidas}. "
            f"disponibles: {sorted(REGISTRY)}"
        )
    pedidas_set = set(pedidas)
    return [nombre for nombre in REGISTRY if nombre in pedidas_set]


class OrquestadorFuentes:
    """Coordina los conectores habilitados para una consulta."""

    def __init__(self, db: Database, fuentes: Iterable[str] | None = None) -> None:
        self.db = db
        self._fuentes = _resolver_fuentes(fuentes)

    def fuentes_habilitadas(self) -> list[str]:
        return list(self._fuentes)

    def _aplica(self, nombre: str, query: QuerySpec) -> bool:
        """Un conector por slug (job boards) solo aplica si la query trae slug."""
        cls = REGISTRY[nombre]
        if getattr(cls, "requires_slug", False):
            return bool(query.slug)
        return True

    def ejecutar(self, query: QuerySpec) -> dict[str, RunResult]:
        """Ejecuta cada fuente habilitada que aplique y persiste vía el pipeline.

        Devuelve ``{nombre_fuente: RunResult}``. Un fallo de una fuente no
        detiene a las demás: queda reflejado en su ``RunResult`` y en
        ``salud_fuentes`` (lo registra ``run_connector``).
        """
        resultados: dict[str, RunResult] = {}
        for nombre in self._fuentes:
            if not self._aplica(nombre, query):
                log.debug("orquestador: %s no aplica a la query (sin slug)", nombre)
                continue
            with REGISTRY[nombre]() as connector:
                resultados[nombre] = run_connector(self.db, connector, query)
        return resultados

    def evidencia_normalizada(self, query: QuerySpec) -> list[EvidenceRecord]:
        """Records normalizados de las fuentes habilitadas, **sin persistir**.

        Solo search → normalize: sin validar, sin enriquecer (keywords /
        confianza), sin dedup ni escritura. Es para el benchmark de fuentes y la
        comparación aislada; ``ejecutar`` es el único camino que escribe en
        ``evidencias``. Un fallo de una fuente se registra y se salta.
        """
        registros: list[EvidenceRecord] = []
        for nombre in self._fuentes:
            if not self._aplica(nombre, query):
                continue
            with REGISTRY[nombre]() as connector:
                try:
                    crudos = list(connector.search(query))
                except Exception as exc:  # noqa: BLE001 - el benchmark tolera fallo de fuente
                    log.warning("orquestador: search de %s falló: %s", nombre, exc)
                    continue
                for raw in crudos:
                    try:
                        registros.append(connector.normalize(raw))
                    except Exception as exc:  # noqa: BLE001
                        log.warning(
                            "orquestador: normalize de %s falló: %s", nombre, exc
                        )
        return registros
