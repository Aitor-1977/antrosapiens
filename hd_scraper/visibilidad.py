"""Mecanismo compartido de visibilidad (visible/latente).

Extraído el 2026-09-20 tras encontrar el mismo patrón reimplementado por
separado en `candidatos_verificados.py` (fricción + frescura, para
`/verificados`) y en `_construir_expedientes` de `api/app.py` (escala de
capital, para INDAGAR). Cada módulo sigue calculando su propio booleano de
dominio con su propia regla declarada (eso NO se comparte ni se mueve
aquí); lo único que este módulo centraliza es el etiquetado literal
("visible"/"latente") y el predicado de filtrado, para que la próxima regla
de visibilidad que se necesite no sea otro copy-paste de esas dos piezas.
"""
from __future__ import annotations

VISIBLE = "visible"
LATENTE = "latente"


def incluir_segun_visibilidad(etiqueta: str, estado_visibilidad: str) -> bool:
    """True si un item con esta etiqueta debe incluirse en el resultado.

    ``estado_visibilidad="todos"`` deja pasar cualquier etiqueta (incluida
    ``LATENTE``); cualquier otro valor exige que la etiqueta sea ``VISIBLE``.
    """
    return estado_visibilidad == "todos" or etiqueta == VISIBLE
