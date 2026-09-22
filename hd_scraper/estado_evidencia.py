"""Estados de evaluación de la Ficha de Prospección (Capa 20).

Autorizado por el operador —Mario— el 2026-09-22 (ver CLAUDE.md → «Frontera
de Interpretación»). "No encontré evidencia" y "no pude evaluar la fuente"
son estados epistemológicamente distintos: este módulo nombra el punto exacto
donde una evidencia se detuvo en la cadena

    CAPTURADO → RECUPERADO → PERTINENTE → SEÑAL_EPISTEMOLOGICA →
    SITUACION_OBSERVABLE → PROSPECTO_INVESTIGABLE (recurrencia ≥ 2)

o el motivo por el que no avanzó (``DESCARTADO``, ``SIN_SITUACION``).
``NO_EVALUABLE`` es un estado de FUENTE (no de fila): la fuente no fue
accesible técnicamente, no que la organización carezca de evidencia
antropológica.

Determinista, sin IA, sin red: mismo insumo ⇒ mismo estado.
"""
from __future__ import annotations

from .situacion_observable import Situacion, TIPO_HUELLA_GENERICA, TIPO_SITUACION_UTIL

ESTADO_DESCARTADO = "DESCARTADO"
ESTADO_SIN_SITUACION = "SIN_SITUACION"
ESTADO_SITUACION_OBSERVABLE = "SITUACION_OBSERVABLE"
ESTADO_PROSPECTO_INVESTIGABLE = "PROSPECTO_INVESTIGABLE"

# Estado de FUENTE (no de fila): la fuente no fue accesible técnicamente.
ESTADO_NO_EVALUABLE = "NO_EVALUABLE"

UMBRAL_CORROBORACION = 2


def estado_de(situacion: Situacion, recurrencia: int) -> str:
    """Estado de evaluación de una situación ya agrupada por marcador.

    ``recurrencia`` es el número de documentos distintos que comparten el
    mismo marcador de situación para la misma organización.
    """
    if situacion.tipo == TIPO_HUELLA_GENERICA:
        return ESTADO_SIN_SITUACION
    if situacion.tipo != TIPO_SITUACION_UTIL:
        return ESTADO_DESCARTADO
    if recurrencia >= UMBRAL_CORROBORACION:
        return ESTADO_PROSPECTO_INVESTIGABLE
    return ESTADO_SITUACION_OBSERVABLE
