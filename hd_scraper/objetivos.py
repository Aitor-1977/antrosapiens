"""Objetivos por defecto de Motor A (operación autónoma).

Cubre la decisión de operar SIN peticiones manuales de datos/URLs: cuando un
script o el scheduler no recibe una empresa explícita, se barre una lista por
defecto. La lista es:

1. ``HD_TRACKED_EMPRESAS`` (coma-separada) si está configurada, o
2. el directorio semilla curado de organizaciones reales de LATAM
   (``DIRECTORIO_SEMILLA`` en ``seed_prospectos``), que Motor A asegura en la BD
   desde el primer arranque.

Frontera Motor A: aquí solo hay NOMBRES de organizaciones (objetivos
estructurales). No se puntúa, clasifica ni interpreta; la categoría/escala viven
en la semilla y en la base de datos.
"""
from __future__ import annotations

import os

_VAR = "HD_TRACKED_EMPRESAS"


def objetivos_por_defecto() -> tuple[str, ...]:
    """Objetivos por defecto: ``HD_TRACKED_EMPRESAS`` o el directorio semilla.

    Nunca lanza: si no hay configuración ni semilla (improbable), devuelve una
    tupla vacía y el llamador decide cómo degradar.
    """
    env = tuple(
        e.strip() for e in os.getenv(_VAR, "").split(",") if e.strip()
    )
    if env:
        return env
    from .seed_prospectos import DIRECTORIO_SEMILLA

    return tuple(nombre for nombre, *_ in DIRECTORIO_SEMILLA)
