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

# Señal (tipo_evento del contrato) → VARIANTES de consulta. Cada variante es una
# frase temática que se combina con base+vertical para formar UNA consulta
# independiente. Usar varias frases cortas (en vez de una sola frase larga)
# amplía el descubrimiento: Google News trata los términos como conjunción, así
# que una frase larga estrecha demasiado. El vocabulario literal del contrato
# (las claves) NO cambia; solo se enriquecen las frases de búsqueda.
#
# Cambio principal de Captura Inteligente: el tipo "queja" (bucket de fricción)
# deja de ser un único término y pasa a cubrir explícitamente pérdida de
# clientes, despidos, conflictos regulatorios, caídas de crecimiento,
# cancelación de servicios, demandas, reestructuración y crisis operativas.
TIPO_KEYWORDS: dict[str, list[str]] = {
    "ronda": [
        "ronda de inversión",
        "levanta capital serie A",
        "recauda financiamiento",
    ],
    "contratacion": [
        "contratación masiva de personal",
        "nuevo ejecutivo head of",
        "plan de contratación empleos",
    ],
    "despido": [
        "despidos masivos",
        "reestructuración recorte de personal",
        "cierre de operaciones",
    ],
    "lanzamiento": [
        "lanzamiento de producto",
        "nueva plataforma estrena",
    ],
    # Bucket de fricción — ampliado (mejora #4). Cada línea es una consulta.
    "queja": [
        "pérdida de clientes fuga de usuarios",
        "quejas churn baja retención",
        "cancelación de servicio cancelaciones",
        "demanda colectiva denuncia",
        "conflicto regulatorio multa sanción",
        "caída de crecimiento desaceleración",
        "reestructuración crisis operativa",
        "despidos cierre de operaciones",
    ],
    "cambio_sitio": [
        "rediseño de marca pivote",
        "nuevo modelo de negocio relanzamiento",
    ],
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

    Compone base del ecosistema + vertical (HD) + cada VARIANTE del tipo. Se
    emite una consulta por variante para ampliar el descubrimiento (sobre todo
    en el bucket de fricción "queja"). Las consultas duplicadas se colapsan
    conservando el orden. La zona geográfica se añade aparte en el pipeline.
    """
    variantes = TIPO_KEYWORDS.get(tipo_evento) or [""]
    vkw = VERTICALES_HD.get(vertical, "")
    salida: list[tuple[str, str]] = []
    vistos: set[str] = set()
    for base in _bases(categoria):
        for kw in variantes:
            texto = " ".join(x for x in (base, vkw, kw) if x).strip()
            if texto and texto not in vistos:
                vistos.add(texto)
                salida.append((texto, tipo_evento))
    return salida
