"""Observatorio LATAM — Capa 16.

Pasa de organizaciones individuales a inteligencia ecosistémica: analiza
regiones, verticales, ecosistemas (VC/Startup/Incubadora/Corporativo) y produce
ranking, riesgos comunes, patrones compartidos, vacíos sistémicos, tensiones
recurrentes e indicadores regionales.

Agregación 100% determinista sobre expedientes ya producidos. Reutiliza el
ranking del Dictamen (Capa 3/Fase 2) y el riesgo del Motor Predictivo (Capa 15):
no reimplementa esa lógica. Sin IA, sin red.
"""
from __future__ import annotations

from collections import Counter

from .analisis import SENALES_CAMBIO, SENALES_DOLOR
from .dictamen import generar_ranking
from .predictivo import estimar_riesgo


def _kwset(exp: dict) -> set:
    return set(exp.get("keywords", []) or [])


def _dist(exps: list[dict], campo: str) -> dict:
    return dict(Counter(e.get(campo, "") for e in exps if e.get(campo)))


# ── Indicadores regionales ────────────────────────────────────────────────────
def calcular_indicadores(exps: list[dict]) -> dict:
    """Indicadores agregados de un conjunto de organizaciones."""
    n = len(exps)
    if n == 0:
        return {"organizaciones": 0, "tasa_dolor": 0.0, "tasa_cambio": 0.0,
                "tasa_bloqueo": 0.0, "icp_promedio": 0.0,
                "distribucion_scoring": {}, "distribucion_deuda": {}}
    n_dolor = sum(1 for e in exps if _kwset(e) & SENALES_DOLOR)
    n_cambio = sum(1 for e in exps if _kwset(e) & SENALES_CAMBIO)
    n_bloq = sum(1 for e in exps if e.get("hipotesis_bloqueada"))
    icp = [e.get("score_icp", 0) for e in exps]
    return {
        "organizaciones": n,
        "tasa_dolor": round(n_dolor / n, 4),
        "tasa_cambio": round(n_cambio / n, 4),
        "tasa_bloqueo": round(n_bloq / n, 4),
        "icp_promedio": round(sum(icp) / n, 2),
        "distribucion_scoring": _dist(exps, "scoring"),
        "distribucion_deuda": _dist(exps, "tipo_deuda"),
    }


# ── Patrones regionales ───────────────────────────────────────────────────────
def identificar_patrones_regionales(exps: list[dict]) -> list[dict]:
    """Patrones compartidos por varias organizaciones (orden desc, determinista)."""
    c: Counter = Counter()
    for e in exps:
        for p in (e.get("patrones", []) or []):
            if p.get("patron"):
                c[p["patron"]] += 1
    return [{"patron": p, "organizaciones": n}
            for p, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]


# ── Tensiones recurrentes ─────────────────────────────────────────────────────
def identificar_tensiones(exps: list[dict]) -> dict:
    """Tensiones recurrentes: deudas presentes en 2+ organizaciones y convergencias."""
    deudas = Counter(e.get("tipo_deuda", "") for e in exps if e.get("tipo_deuda"))
    recurrentes = [{"deuda": d, "organizaciones": n}
                   for d, n in sorted(deudas.items(), key=lambda kv: (-kv[1], kv[0]))
                   if n >= 2]
    convergencias = sum(
        1 for e in exps
        if (_kwset(e) & SENALES_DOLOR) and (_kwset(e) & SENALES_CAMBIO))
    return {"deudas_recurrentes": recurrentes,
            "organizaciones_en_convergencia": convergencias}


# ── Riesgos comunes ───────────────────────────────────────────────────────────
def _riesgos_comunes(exps: list[dict]) -> dict:
    niveles = Counter(estimar_riesgo(e)["nivel"] for e in exps)
    return {"distribucion_riesgo": dict(niveles),
            "organizaciones_riesgo_alto": niveles.get("alto", 0)}


# ── Vacíos sistémicos ─────────────────────────────────────────────────────────
def _vacios_sistemicos(exps: list[dict]) -> dict:
    return {
        "sin_vertical": sum(1 for e in exps if not (e.get("vertical") or "").strip()),
        "hipotesis_bloqueada": sum(1 for e in exps if e.get("hipotesis_bloqueada")),
        "corpus_escaso": sum(1 for e in exps if e.get("total_evidencias", 0) < 3),
    }


def _resumen(exps: list[dict], etiqueta: str) -> dict:
    return {
        "etiqueta": etiqueta,
        "indicadores": calcular_indicadores(exps),
        "tensiones": identificar_tensiones(exps),
        "patrones_compartidos": identificar_patrones_regionales(exps),
    }


# ── Análisis por región / vertical / ecosistema ───────────────────────────────
def analizar_region(exps: list[dict], region: str) -> dict:
    """Analiza un conjunto ya delimitado por región."""
    return _resumen(exps, region)


def analizar_vertical(exps: list[dict], vertical: str) -> dict:
    """Analiza las organizaciones de una vertical (filtra por el campo vertical)."""
    v = (vertical or "").strip().lower()
    filtrados = [e for e in exps if (e.get("vertical") or "").lower() == v]
    return _resumen(filtrados, vertical)


def analizar_ecosistema(exps: list[dict], categoria: str) -> dict:
    """Analiza un ecosistema por categoría (VC|Startup|Incubadora|Corporativo)."""
    c = (categoria or "").strip().lower()
    filtrados = [e for e in exps if (e.get("categoria") or "").lower() == c]
    return _resumen(filtrados, categoria)


# ── Reporte regional completo ─────────────────────────────────────────────────
def emitir_reporte_regional(exps: list[dict], region: str, limite: int = 10) -> dict:
    """Reporte ecosistémico: indicadores, tensiones, patrones, ranking, riesgos, vacíos."""
    return {
        "region": region,
        "total_organizaciones": len(exps),
        "indicadores": calcular_indicadores(exps),
        "tensiones": identificar_tensiones(exps),
        "patrones_compartidos": identificar_patrones_regionales(exps),
        "ranking": generar_ranking(exps, limite),
        "riesgos_comunes": _riesgos_comunes(exps),
        "vacios_sistemicos": _vacios_sistemicos(exps),
    }
