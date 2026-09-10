"""Comparador Temporal y Ecosistémico — Capa 14.

Compara organizaciones entre sí, ecosistemas, periodos y patrones. **Nunca
interpreta**: solo contrasta estructuras ya producidas (scoring, dolor cultural,
patrones, keywords, validaciones). Diferencias deterministas y reproducibles,
sin juicio de valor. Sin IA, sin red.
"""
from __future__ import annotations

from collections import Counter

# Campos escalares comparables de un expediente.
_CAMPOS_ORG = ("scoring", "tipo_deuda", "score_icp", "intensidad", "vertical",
               "senal_dominante", "profundidad_dolor", "total_evidencias")

# Señales de dolor y de cambio (para tasas ecosistémicas). Se importan de la
# frontera de interpretación existente; no se redefinen aquí.
from .analisis import SENALES_CAMBIO, SENALES_DOLOR


def _kwset(exp: dict) -> set:
    return set(exp.get("keywords", []) or [])


def _patset(exp: dict) -> set:
    return {p.get("patron", "") for p in (exp.get("patrones", []) or []) if p.get("patron")}


def _dist(exps: list[dict], campo: str) -> dict:
    return dict(Counter(e.get(campo, "") for e in exps if e.get(campo)))


def _ev_fecha(ev: dict) -> str:
    return (ev.get("fecha") or ev.get("fecha_publicacion") or "").strip()


def _evidencias(exp: dict) -> list[dict]:
    ev = exp.get("evidencias", [])
    if isinstance(ev, dict):
        return list(ev.get("items", []))
    return list(ev or [])


# ── 1. Comparar organizaciones ────────────────────────────────────────────────
def comparar_organizaciones(exp_a: dict, exp_b: dict) -> dict:
    """Contraste campo a campo entre dos organizaciones (sin interpretar)."""
    campos = []
    for c in _CAMPOS_ORG:
        va, vb = exp_a.get(c), exp_b.get(c)
        campos.append({"campo": c, "a": va, "b": vb, "igual": va == vb})
    ka, kb = _kwset(exp_a), _kwset(exp_b)
    pa, pb = _patset(exp_a), _patset(exp_b)
    return {
        "org_a": exp_a.get("nombre", ""),
        "org_b": exp_b.get("nombre", ""),
        "campos": campos,
        "keywords_comunes": sorted(ka & kb),
        "keywords_solo_a": sorted(ka - kb),
        "keywords_solo_b": sorted(kb - ka),
        "patrones_comunes": sorted(pa & pb),
    }


def _resumen_ecosistema(exps: list[dict]) -> dict:
    n = len(exps)
    n_dolor = sum(1 for e in exps if _kwset(e) & SENALES_DOLOR)
    n_cambio = sum(1 for e in exps if _kwset(e) & SENALES_CAMBIO)
    icp = [e.get("score_icp", 0) for e in exps]
    return {
        "organizaciones": n,
        "distribucion_deuda": _dist(exps, "tipo_deuda"),
        "distribucion_scoring": _dist(exps, "scoring"),
        "distribucion_vertical": _dist(exps, "vertical"),
        "tasa_dolor": round(n_dolor / n, 4) if n else 0.0,
        "tasa_cambio": round(n_cambio / n, 4) if n else 0.0,
        "icp_promedio": round(sum(icp) / n, 2) if n else 0.0,
    }


# ── 2. Comparar ecosistemas ───────────────────────────────────────────────────
def comparar_ecosistemas(exps_a: list[dict], exps_b: list[dict],
                         etiqueta_a: str = "A", etiqueta_b: str = "B") -> dict:
    """Compara dos conjuntos (verticales, regiones, ecosistemas) por agregados."""
    ra, rb = _resumen_ecosistema(exps_a), _resumen_ecosistema(exps_b)
    return {
        "etiqueta_a": etiqueta_a, "etiqueta_b": etiqueta_b,
        "resumen_a": ra, "resumen_b": rb,
        "deltas": {
            "organizaciones": ra["organizaciones"] - rb["organizaciones"],
            "tasa_dolor": round(ra["tasa_dolor"] - rb["tasa_dolor"], 4),
            "tasa_cambio": round(ra["tasa_cambio"] - rb["tasa_cambio"], 4),
            "icp_promedio": round(ra["icp_promedio"] - rb["icp_promedio"], 2),
        },
    }


# ── 3. Comparar periodos ──────────────────────────────────────────────────────
def comparar_periodos(expediente: dict, corte: str) -> dict:
    """Compara la evidencia de una organización antes y después de una fecha."""
    antes, despues = [], []
    for ev in _evidencias(expediente):
        f = _ev_fecha(ev)
        (antes if (f and f < corte) else despues).append(ev)

    def _res(evs):
        return {"evidencias": len(evs),
                "tipos_evento": dict(Counter((e.get("tipo_evento") or "") for e in evs if e.get("tipo_evento")))}

    ra, rb = _res(antes), _res(despues)
    return {
        "org": expediente.get("nombre", ""),
        "corte": corte,
        "antes": ra,
        "despues": rb,
        "delta_evidencias": rb["evidencias"] - ra["evidencias"],
    }


# ── 4. Comparar patrones ──────────────────────────────────────────────────────
def comparar_patrones(exps_a: list[dict], exps_b: list[dict]) -> dict:
    """Distribución de patrones en cada conjunto y su intersección/diferencia."""
    ca = Counter(p for e in exps_a for p in _patset(e))
    cb = Counter(p for e in exps_b for p in _patset(e))
    return {
        "patrones_a": dict(ca),
        "patrones_b": dict(cb),
        "comunes": sorted(set(ca) & set(cb)),
        "solo_a": sorted(set(ca) - set(cb)),
        "solo_b": sorted(set(cb) - set(ca)),
    }


# ── 5. Comparar narrativas ────────────────────────────────────────────────────
def comparar_narrativas(narrativa_a: str, narrativa_b: str) -> dict:
    """Solapamiento léxico determinista (Jaccard) entre dos narrativas."""
    ta = {t for t in (narrativa_a or "").lower().split() if len(t) > 3}
    tb = {t for t in (narrativa_b or "").lower().split() if len(t) > 3}
    union = ta | tb
    jaccard = round(len(ta & tb) / len(union), 4) if union else 0.0
    return {
        "solapamiento": jaccard,
        "tokens_comunes": sorted(ta & tb),
        "solo_a": sorted(ta - tb),
        "solo_b": sorted(tb - ta),
    }


# ── 6. Comparar dolor cultural ────────────────────────────────────────────────
def comparar_dolor(exps_a: list[dict], exps_b: list[dict]) -> dict:
    """Distribución de dolor cultural en cada conjunto y su diferencia."""
    da, db = _dist(exps_a, "tipo_deuda"), _dist(exps_b, "tipo_deuda")
    return {
        "dolor_a": da,
        "dolor_b": db,
        "comunes": sorted(set(da) & set(db)),
        "solo_a": sorted(set(da) - set(db)),
        "solo_b": sorted(set(db) - set(da)),
    }


# ── 7. Comparar validaciones ──────────────────────────────────────────────────
def comparar_validaciones(validacion_a: dict, validacion_b: dict) -> dict:
    """Contrasta dos validaciones científicas (veredicto, solidez, suficiencia)."""
    def _res(v):
        d = v.get("dictamen_cientifico", {}) or {}
        return {"veredicto": d.get("veredicto", ""), "solidez": d.get("solidez", 0),
                "suficiencia": d.get("suficiencia", 0),
                "nivel_evidencia": d.get("nivel_evidencia", "")}
    ra, rb = _res(validacion_a), _res(validacion_b)
    return {
        "a": ra, "b": rb,
        "mismo_veredicto": ra["veredicto"] == rb["veredicto"],
        "delta_solidez": ra["solidez"] - rb["solidez"],
        "delta_suficiencia": ra["suficiencia"] - rb["suficiencia"],
    }


# ── 8. Detectar convergencias ─────────────────────────────────────────────────
def detectar_convergencias(exps_a: list[dict], exps_b: list[dict]) -> dict:
    """Elementos compartidos entre dos conjuntos (dolor, patrones, señales)."""
    da, db = set(_dist(exps_a, "tipo_deuda")), set(_dist(exps_b, "tipo_deuda"))
    pa = {p for e in exps_a for p in _patset(e)}
    pb = {p for e in exps_b for p in _patset(e)}
    ka = {k for e in exps_a for k in _kwset(e)}
    kb = {k for e in exps_b for k in _kwset(e)}
    return {
        "dolor_comun": sorted(da & db),
        "patrones_comunes": sorted(pa & pb),
        "senales_comunes": sorted(ka & kb),
    }


# ── 9. Detectar divergencias ──────────────────────────────────────────────────
def detectar_divergencias(exps_a: list[dict], exps_b: list[dict]) -> dict:
    """Elementos exclusivos de cada conjunto (dolor, patrones, señales)."""
    da, db = set(_dist(exps_a, "tipo_deuda")), set(_dist(exps_b, "tipo_deuda"))
    pa = {p for e in exps_a for p in _patset(e)}
    pb = {p for e in exps_b for p in _patset(e)}
    ka = {k for e in exps_a for k in _kwset(e)}
    kb = {k for e in exps_b for k in _kwset(e)}
    return {
        "dolor_solo_a": sorted(da - db), "dolor_solo_b": sorted(db - da),
        "patrones_solo_a": sorted(pa - pb), "patrones_solo_b": sorted(pb - pa),
        "senales_solo_a": sorted(ka - kb), "senales_solo_b": sorted(kb - ka),
    }


# ── 10. Generar matriz ────────────────────────────────────────────────────────
def generar_matriz(exps: list[dict]) -> dict:
    """Matriz determinista organizaciones × dimensiones comparables."""
    dimensiones = ["scoring", "score_icp", "tipo_deuda", "intensidad",
                   "total_evidencias", "profundidad_dolor", "n_patrones"]
    filas = []
    for e in sorted(exps, key=lambda x: x.get("nombre", "")):
        filas.append({
            "org": e.get("nombre", ""),
            "valores": {
                "scoring": e.get("scoring", ""),
                "score_icp": e.get("score_icp", 0),
                "tipo_deuda": e.get("tipo_deuda", ""),
                "intensidad": e.get("intensidad", ""),
                "total_evidencias": e.get("total_evidencias", 0),
                "profundidad_dolor": e.get("profundidad_dolor", 0),
                "n_patrones": len(e.get("patrones", []) or []),
            },
        })
    return {"dimensiones": dimensiones, "organizaciones": len(filas), "filas": filas}
