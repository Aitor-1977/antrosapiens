"""Orquestador multifuente (PASO 3–4 de la integración de arquitectura
multifuente gratuita).

Este módulo es NUEVO y AISLADO: no reemplaza ``pipeline.run_connector``, lo
INVOCA una vez por cada fuente activa. No toca
``clasificacion_epistemologica.py``, ``promocion_candidatos.py``, la lógica
del conector de Tavily (``busqueda_dinamica_founder``), Android, ni ninguna
tabla productiva más allá de las que ``run_connector`` ya escribe hoy
(``evidencias``, ``rechazos``, ``raw_store``, ``salud_fuentes``).

"Tavily" en el vocabulario de la tarea corresponde en este repo al conector
ya registrado como ``busqueda_dinamica_founder`` (ver
``hd_scraper/connectors/__init__.py``). Por eso ``FUENTES_ACTIVAS_POR_DEFECTO``
solo contiene esa clave: activar cualquier otra fuente (incluida GDELT, que
ya está implementada y registrada) requiere primero el benchmark de valor
agregado a costo $0 que exige la especificación, no basta con que esté en
``REGISTRY``.

Este módulo NO decide identidad organizacional ni agrupa evidencia entre
fuentes (eso sigue siendo, respectivamente, ``clasificacion_epistemologica.py``
y el futuro "Concentrador de Evidencia" — pendiente de reconciliar con
``candidato.py`` antes de construirse). Solo abre una fuente registrada,
corre el pipeline existente sobre ella, y agrega los ``RunResult`` en un
único reporte.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .connectors import REGISTRY
from .db.database import Database
from .db.models import QuerySpec
from .pipeline import RunResult, run_connector

# Única fuente activa hoy: Tavily, registrada como "busqueda_dinamica_founder".
# Ninguna otra fuente se activa desde aquí sin el benchmark previo que exige
# la especificación (PASO 12).
FUENTES_ACTIVAS_POR_DEFECTO: tuple[str, ...] = ("busqueda_dinamica_founder",)


@dataclass
class ResultadoOrquestacion:
    """Agregado de los ``RunResult`` de cada fuente consultada en una corrida."""

    resultados_por_fuente: dict[str, RunResult] = field(default_factory=dict)
    # Nombres pasados en `fuentes` que no existen en REGISTRY: se omiten sin
    # interrumpir la corrida de las demás fuentes, y quedan aquí para reporte.
    fuentes_no_registradas: list[str] = field(default_factory=list)

    @property
    def escritos_totales(self) -> int:
        return sum(r.escritos for r in self.resultados_por_fuente.values())

    def resumen(self) -> str:
        lineas = [r.resumen() for r in self.resultados_por_fuente.values()]
        if self.fuentes_no_registradas:
            lineas.append(
                "fuentes no registradas (omitidas): "
                + ", ".join(self.fuentes_no_registradas)
            )
        return "\n".join(lineas)


def orquestar(
    db: Database,
    query: QuerySpec,
    fuentes: tuple[str, ...] = FUENTES_ACTIVAS_POR_DEFECTO,
) -> ResultadoOrquestacion:
    """Corre ``pipeline.run_connector`` para cada fuente en ``fuentes``.

    Cada fuente listada debe existir en ``connectors.REGISTRY``; una fuente
    desconocida se omite (se registra en ``fuentes_no_registradas``) sin
    afectar a las demás. No hay comportamiento nuevo de clasificación,
    dedup ni persistencia: cada fuente pasa por el mismo ``run_connector``
    que ya se usa hoy fuente por fuente.
    """
    resultado = ResultadoOrquestacion()
    for nombre in fuentes:
        connector_cls = REGISTRY.get(nombre)
        if connector_cls is None:
            resultado.fuentes_no_registradas.append(nombre)
            continue
        with connector_cls() as connector:
            resultado.resultados_por_fuente[nombre] = run_connector(db, connector, query)
    return resultado
