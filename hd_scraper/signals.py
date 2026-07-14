"""Extracción objetiva Nivel 1: keywords de señal + confianza.

Esto es Motor A (hechos), NO Motor B (HD). Detecta frases de señal con una
taxonomía GENÉRICA y pública (ronda, despidos, churn/retención, expansión,
cambio de liderazgo, lanzamiento, adquisición) — vocabulario estándar de
negocio, no la taxonomía propietaria de Deuda Cultural™. La conversión de estas
señales en Deuda Cultural (Moral/Temporal/Relacional…) es responsabilidad del
Motor B (RadarHD), fuera de este repo.

La ``confianza`` mide la CALIDAD OBJETIVA de la extracción (¿está fechada?,
¿fuente nombrada?, ¿trae señales?), no un juicio semántico del contenido.
"""
from __future__ import annotations

# Taxonomía genérica de señales (objetiva). tag -> frases que la disparan.
# Cubre los eventos de negocio que el operador pidió conservar: ronda, despidos,
# fricción, expansión, cambio de liderazgo, lanzamiento, adquisición/fusión,
# alianza estratégica, contratación masiva, cierre de operaciones, crecimiento
# relevante y regulación con impacto empresarial. Sigue siendo vocabulario
# ESTÁNDAR de negocio (Motor A), no la taxonomía propietaria de Deuda Cultural™.
SENALES: dict[str, tuple[str, ...]] = {
    "ronda_inversion": ("ronda", "levanta capital", "serie a", "serie b", "serie c",
                        "financiamiento", "recauda", "inversión", "capital semilla"),
    "reduccion_personal": ("despido", "despidos", "reducción de personal", "recorte",
                           "recortes", "layoff", "layoffs", "reestructura",
                           "reestructuración", "reducción de plantilla"),
    "friccion_retencion": ("churn", "baja retención", "abandono", "fricción", "quejas",
                           "cancelaciones", "cancelación", "deserción", "insatisfacción",
                           "pérdida de clientes", "fuga de clientes", "demanda colectiva",
                           "demandan a", "denuncia contra"),
    "expansion": ("expansión", "nuevo mercado", "nuevos mercados", "aterriza en",
                  "apertura", "se expande", "abre operaciones"),
    "cambio_liderazgo": ("nuevo ceo", "cambio de ceo", "nombra", "ficha a", "contratando",
                         "head of", "nuevo director", "renuncia", "designa", "sale de la"),
    "lanzamiento": ("lanzamiento", "nuevo producto", "lanza", "presenta", "estrena"),
    "adquisicion": ("adquisición", "adquiere", "compra de", "fusión", "fusiona",
                    "se fusiona", "absorbe"),
    "alianza": ("alianza", "alianza estratégica", "acuerdo con", "se asocia",
                "asociación con", "partnership", "colaboración estratégica",
                "joint venture"),
    "contratacion_masiva": ("contratación masiva", "contrataciones masivas",
                            "sumará empleos", "creará empleos", "nuevos empleos",
                            "plan de contratación", "vacantes masivas"),
    "cierre_operaciones": ("cierre de operaciones", "cierra operaciones", "quiebra",
                           "cese de operaciones", "liquidación", "suspende operaciones",
                           "echa el cierre", "deja de operar"),
    "crecimiento": ("crecimiento", "duplica ingresos", "triplica", "récord de ingresos",
                    "aumento de ingresos", "crece", "rentabilidad récord",
                    "supera los", "millones en ventas"),
    "regulacion": ("regulación", "regulador", "multa", "sanción", "normativa",
                   "ley fintech", "cnbv", "banxico", "cofece", "sec ",
                   "conflicto regulatorio", "prohíbe", "suspende licencia"),
}

# Fuentes genéricas (no son un medio nombrado): bajan la confianza.
FUENTES_GENERICAS = {"google news", "gdelt", ""}


def detectar_keywords(texto: str) -> list[str]:
    """Devuelve las etiquetas de señal (objetivas) presentes en el texto."""
    t = (texto or "").lower()
    tags = [tag for tag, frases in SENALES.items() if any(f in t for f in frases)]
    return tags


def fuente_confiable(nombre_medio: str) -> bool:
    """True si el medio es una fuente nombrada (no un agregador genérico)."""
    return (nombre_medio or "").strip().lower() not in FUENTES_GENERICAS


def calcular_confianza(fecha_publicacion, nombre_medio: str, keywords: list[str]) -> float:
    """Confianza objetiva 0–1 según calidad de la extracción (no del contenido)."""
    score = 0.4
    if fecha_publicacion:
        score += 0.25
    if (nombre_medio or "").strip().lower() not in FUENTES_GENERICAS:
        score += 0.20
    if keywords:
        score += 0.15
    return round(min(score, 1.0), 2)
