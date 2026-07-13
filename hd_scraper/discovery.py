"""Consultas temáticas por ecosistema (descubrimiento por categoría).

Cada consulta se compone de dos partes DECLARADAS (no inferidas):

    base del ecosistema  +  palabra del tipo de señal

Así, elegir el tipo de señal cambia qué se busca (p. ej. Startup + despido →
"startup mexicana despidos recorte de personal") y la etiqueta queda consistente.
El motor trae titulares que coinciden y los etiqueta con la categoría; NO decide
qué empresa menciona cada nota (eso lo hace el operador al curar). Enfoque
LatAm/México, ajustable con HD_DISCOVERY_<CATEGORIA> (bases separadas por '|').
"""
from __future__ import annotations

import os

# Bases por ecosistema (el CONTEXTO del sector).
CATEGORIA_BASE_DEFAULT: dict[str, list[str]] = {
    "VC": ["venture capital México", "fondo de inversión startups Latinoamérica"],
    "Startup": ["startup mexicana", "startup Latinoamérica"],
    "Incubadora": ["aceleradora de startups México", "incubadora de startups Latinoamérica"],
    "Corporativo": ["corporativo innovación abierta México", "corporate venture capital Latinoamérica"],
}

# Palabra(s) por tipo de señal (el EVENTO buscado).
TIPO_KEYWORDS: dict[str, str] = {
    "ronda": "ronda de inversión",
    "contratacion": "contratación nuevo ejecutivo",
    "despido": "despidos recorte de personal",
    "lanzamiento": "lanzamiento de producto",
    "queja": "quejas usuarios problema",
    "cambio_sitio": "nuevo sitio web rebranding",
}


def _bases(categoria: str) -> list[str]:
    override = os.getenv(f"HD_DISCOVERY_{categoria.upper()}")
    if override:
        return [b.strip() for b in override.split("|") if b.strip()]
    return CATEGORIA_BASE_DEFAULT.get(categoria, [])


def queries_para(categoria: str, tipo_evento: str) -> list[tuple[str, str]]:
    """Consultas (texto, tipo_evento) para una categoría y un tipo de señal.

    Compone cada base del ecosistema con la palabra del tipo elegido.
    """
    kw = TIPO_KEYWORDS.get(tipo_evento, "")
    salida = []
    for base in _bases(categoria):
        texto = f"{base} {kw}".strip()
        salida.append((texto, tipo_evento))
    return salida
