"""Consultas temáticas por ecosistema (descubrimiento por categoría).

Cada categoría tiene un conjunto de consultas DECLARADAS (no inferidas): son las
palabras con las que el operador decide rastrear ese ecosistema. El motor trae
titulares que coinciden y los etiqueta con la categoría; NO decide qué empresa
menciona cada nota (eso lo hace el operador al curar). Enfoque LatAm/México,
ajustable por entorno con HD_DISCOVERY_<CATEGORIA> (términos separados por '|').

Cada entrada es (términos_de_búsqueda, tipo_evento_declarado).
"""
from __future__ import annotations

import os

# (consulta, tipo_evento) por categoría. tipo_evento es la intención declarada.
CATEGORIA_QUERIES_DEFAULT: dict[str, list[tuple[str, str]]] = {
    "VC": [
        ("venture capital México ronda inversión", "ronda"),
        ("fondo de inversión startups Latinoamérica", "ronda"),
    ],
    "Startup": [
        ("startup mexicana ronda de inversión", "ronda"),
        ("startup Latinoamérica lanzamiento producto", "lanzamiento"),
    ],
    "Incubadora": [
        ("aceleradora de startups México demo day", "lanzamiento"),
        ("incubadora programa startups Latinoamérica", "lanzamiento"),
    ],
    "Corporativo": [
        ("corporativo innovación abierta México", "lanzamiento"),
        ("corporate venture capital Latinoamérica", "ronda"),
    ],
}


def queries_para(categoria: str) -> list[tuple[str, str]]:
    """Consultas de una categoría. Permite override por entorno.

    HD_DISCOVERY_VC="term1|term2" reemplaza las consultas de VC (tipo_evento=ronda
    por defecto en el override).
    """
    override = os.getenv(f"HD_DISCOVERY_{categoria.upper()}")
    if override:
        return [(t.strip(), "ronda") for t in override.split("|") if t.strip()]
    return CATEGORIA_QUERIES_DEFAULT.get(categoria, [])
