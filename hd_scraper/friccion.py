"""Fricción organizacional documentada — gate de VISIBILIDAD para /verificados.

Autorizado por el operador (Mario) el 2026-09-19/20, entrada "Visibilidad del
Radar condicionada a fricción documentada" de la Frontera de Interpretación en
CLAUDE.md. Mismo patrón determinista que `receptividad.py` (vocabulario
cerrado, sin IA, sin red): NO decide promoción (eso sigue siendo exclusivo de
`promocion_candidatos.py`) ni clasifica Deuda Cultural™. Solo dice si, en el
texto ya extraído por este motor, existe un marcador léxico de fricción cuyo
sujeto gramatical — por posición dentro de la misma oración, no por NLP — es
la propia organización, y no un tercero mencionado en la misma nota (p. ej.
"el proveedor X canceló su contrato con Acme" no cuenta para Acme: Acme
aparece DESPUÉS del marcador, como objeto, no como sujeto).

Las 15 palabras del vocabulario cerrado fueron aprobadas explícitamente por el
operador (2026-09-19). Variantes verbales agregadas (2026-09-20, autorizadas):
solo formas conjugadas de esas mismas 15 palabras, ninguna categoría nueva.
"cancelo" (cubre "canceló"), "discontinuo" (cubre "discontinuó") y "conflicto"
(cubre "entró en conflicto") ya cubrían su variante verbal por normalización
de acentos o por ser subcadena; la única variante que necesitaba una entrada
propia era "degrado" (cubre "degradó"/"se degradó"). No se agregó "disputo"
(verbo de "disputar"): su uso más frecuente en español es "impugnó una
decisión", sentido distinto de "tuvo una disputa" — se dejó fuera para no
correr el vocabulario cerrado más allá de lo aprobado.
"""
from __future__ import annotations

import json
import re
import unicodedata

MARCADORES_FRICCION = {
    "churn",
    "cancelacion", "cancelo", "cancelled", "canceled",
    "downgrade",
    "no renovo",
    "discontinued", "discontinuo",
    "degradacion", "degrado",
    "conflicto",
    "disputa", "dispute",
    "perdio traccion",
    "stalled",
}


def _sin_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm(texto: str) -> str:
    return _sin_acentos((texto or "").lower())


def _oraciones(texto: str) -> list[str]:
    return [o for o in re.split(r"[.!?\n]+", texto or "") if o.strip()]


def _keywords_de(fila) -> list[str]:
    try:
        return json.loads(fila["keywords"]) if fila["keywords"] else []
    except (ValueError, TypeError):
        return []


def _oracion_tiene_friccion_de_la_organizacion(oracion: str, organizacion_norm: str) -> bool:
    """Cuenta solo si el nombre de la organización aparece en la oración Y
    aparece ANTES de algún marcador (heurística de sujeto por posición, SVO
    por defecto en español e inglés). Conservador por diseño: prefiere un
    falso negativo a inventar fricción sobre un tercero mencionado en la nota.
    """
    oracion_norm = _norm(oracion)
    idx_org = oracion_norm.find(organizacion_norm)
    if idx_org == -1:
        return False
    for marcador in MARCADORES_FRICCION:
        idx_marcador = oracion_norm.find(marcador)
        if idx_marcador != -1 and idx_org < idx_marcador:
            return True
    return False


def existe_friccion(db, organizacion: str) -> bool:
    """Determinista: recorre las evidencias YA extraídas de `organizacion`
    (match exacto de nombre, mismo criterio que `PAIS_PERMITIDO`) buscando el
    vocabulario cerrado de `MARCADORES_FRICCION`. Sin IA, sin red.
    """
    organizacion_norm = _norm((organizacion or "").strip())
    if not organizacion_norm:
        return False

    filas = db.fetch_all(
        "SELECT cita_textual, keywords FROM evidencias "
        "WHERE LOWER(TRIM(empresa_mencionada)) = LOWER(TRIM(?))",
        (organizacion,),
    )
    for fila in filas:
        for oracion in _oraciones(fila["cita_textual"]):
            if _oracion_tiene_friccion_de_la_organizacion(oracion, organizacion_norm):
                return True
        # Los keywords ya están scopeados a esta organización (son metadata
        # de una evidencia cuyo empresa_mencionada ya filtramos arriba), así
        # que aquí no aplica la guardia de sujeto: un tag exacto basta.
        for kw in _keywords_de(fila):
            if _norm(kw) in MARCADORES_FRICCION:
                return True
    return False
