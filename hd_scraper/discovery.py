"""Consultas de descubrimiento alineadas al perfil de prospecto ideal de HD.

Hamaca Digital busca (ver docs/perfil_prospecto_hd.md):
  - Verticales dependientes de contexto: fintech, edtech, healthtech / salud
    mental, logística agrícola, identidad.
  - Fase de escala o estancamiento con señales de fricción cultural: churn alto,
    baja adopción/retención, fricción "inexplicable por datos".
  - VCs que necesitan due diligence cualitativo de su portafolio.

Cada consulta se compone de partes DECLARADAS (no inferidas):

    base del ecosistema  +  vertical  +  señal (tipo)   ( +  zona geográfica )

La zona geográfica se añade aparte (OR de países). El motor trae titulares que
coinciden y los etiqueta; NO decide qué empresa menciona ni puntúa Deuda
Cultural (eso es interpretación de HD, no del scraper). Ajustable con
HD_DISCOVERY_<CATEGORIA> (bases separadas por '|').
"""
from __future__ import annotations

import os

# Bases por ecosistema, orientadas al prospecto ideal de HD.
CATEGORIA_BASE_DEFAULT: dict[str, list[str]] = {
    "VC": ["venture capital", "corporate venture capital",
           "fondo de inversión due diligence portafolio"],
    "Startup": ["startup"],  # la especificidad la aporta la vertical + señal
    "Incubadora": ["aceleradora de startups", "incubadora de startups"],
    "Corporativo": ["corporativo innovación abierta", "corporativo transformación digital"],
}

# Verticales dependientes de contexto que le interesan a HD.
VERTICALES_HD: dict[str, str] = {
    "todas": "",
    "fintech": "fintech",
    "edtech": "edtech educación",
    "healthtech": "healthtech salud digital",
    "salud mental": '"salud mental"',
    "logística agrícola": "logística agrícola agtech",
    "identidad": "identidad digital",
}

# Señal (tipo_evento del contrato) → palabras. Se afinan hacia las señales de
# fricción cultural que busca HD (churn, adopción, retención), sin cambiar el
# vocabulario literal del contrato.
TIPO_KEYWORDS: dict[str, str] = {
    "ronda": "ronda de inversión",
    "contratacion": "contratación nuevo ejecutivo head of research",
    "despido": "despidos reestructura estancamiento",
    "lanzamiento": "lanzamiento de producto",
    "queja": "churn abandono baja retención fricción usuarios quejas",
    "cambio_sitio": "rediseño pivote nuevo modelo de producto",
}

PAISES_LATAM = ["México", "Colombia", "Chile", "Perú", "Argentina", "Brasil",
                "Costa Rica", "Panamá"]

REGIONES: dict[str, list[str]] = {"LATAM": PAISES_LATAM, **{p: [p] for p in PAISES_LATAM}}


def _comilla_si_espacio(pais: str) -> str:
    return f'"{pais}"' if " " in pais else pais


def region_clause(region: str) -> str:
    """Cláusula de zona, p. ej. (México OR Colombia OR …). Vacía si es desconocida."""
    paises = REGIONES.get(region)
    if not paises:
        return ""
    return "(" + " OR ".join(_comilla_si_espacio(p) for p in paises) + ")"


def _bases(categoria: str) -> list[str]:
    override = os.getenv(f"HD_DISCOVERY_{categoria.upper()}")
    if override:
        return [b.strip() for b in override.split("|") if b.strip()]
    return CATEGORIA_BASE_DEFAULT.get(categoria, [])


def queries_para(categoria: str, tipo_evento: str, vertical: str = "todas") -> list[tuple[str, str]]:
    """Consultas (texto, tipo_evento) para categoría + tipo de señal + vertical.

    Compone base del ecosistema + vertical (HD) + palabra del tipo. La zona
    geográfica se añade aparte en el pipeline (vía QuerySpec.terminos).
    """
    kw = TIPO_KEYWORDS.get(tipo_evento, "")
    vkw = VERTICALES_HD.get(vertical, "")
    salida = []
    for base in _bases(categoria):
        texto = " ".join(x for x in (base, vkw, kw) if x).strip()
        salida.append((texto, tipo_evento))
    return salida
