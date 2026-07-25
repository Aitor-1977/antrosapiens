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
from .predictivo import calcular_madurez, estimar_riesgo


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


# ══════════════════════════════════════════════════════════════════════════════
# Cutover Arquitectura 1.0 — inteligencia ecosistémica adicional para RadarHD.
# Todo determinista. Reutiliza validacion_cientifica adjunta al expediente
# (`validacion_cientifica`), el ranking del Dictamen, el riesgo y la madurez del
# Predictivo. NO recalcula inferencia: la lee.
# ══════════════════════════════════════════════════════════════════════════════

def _validacion(exp: dict) -> dict:
    return exp.get("validacion_cientifica", {}) or {}


def _nivel_confianza(exp: dict) -> str:
    """Nivel de confianza a partir del nivel de evidencia (GRADE) de la validación."""
    nivel = _validacion(exp).get("nivel_evidencia", "")
    return {"I": "Alta", "II": "Media", "III": "Baja", "IV": "Baja"}.get(nivel, "Baja")


def _evidencias(exp: dict) -> list[dict]:
    ev = exp.get("evidencias", [])
    if isinstance(ev, dict):
        return list(ev.get("items", []))
    return list(ev or [])


# ── Clusters (agrupación determinista por deuda + vertical) ───────────────────
def detectar_clusters(exps: list[dict]) -> list[dict]:
    """Agrupa organizaciones por (tipo_deuda, vertical). Clusters = grupos de 2+."""
    grupos: dict[tuple, list[dict]] = {}
    for e in exps:
        clave = (e.get("tipo_deuda", "") or "sin_deuda", (e.get("vertical", "") or "sin_vertical"))
        grupos.setdefault(clave, []).append(e)
    clusters = []
    for (deuda, vertical), miembros in grupos.items():
        if len(miembros) < 2:
            continue
        senales = Counter(k for m in miembros for k in _kwset(m))
        clusters.append({
            "clave": f"{deuda}|{vertical}",
            "tipo_deuda": deuda, "vertical": vertical,
            "tamano": len(miembros),
            "organizaciones": sorted(m.get("nombre", "") for m in miembros),
            "senales_comunes": [k for k, _ in senales.most_common(5)],
        })
    return sorted(clusters, key=lambda c: (-c["tamano"], c["clave"]))


# ── Outliers (organizaciones atípicas, por reglas deterministas) ──────────────
def detectar_outliers(exps: list[dict]) -> list[dict]:
    """Organizaciones atípicas: ICP desviado (>1σ), deuda única o profundidad sin volumen."""
    if not exps:
        return []
    icps = [e.get("score_icp", 0) for e in exps]
    media = sum(icps) / len(icps)
    var = sum((x - media) ** 2 for x in icps) / len(icps)
    desv = var ** 0.5
    freq_deuda = Counter(e.get("tipo_deuda", "") for e in exps if e.get("tipo_deuda"))

    outliers = []
    for e in exps:
        razones = []
        icp = e.get("score_icp", 0)
        if desv > 0 and abs(icp - media) > desv:
            razones.append(f"ICP {icp} se desvía de la media {round(media, 1)} (>1σ)")
        deuda = e.get("tipo_deuda", "")
        if deuda and freq_deuda.get(deuda, 0) == 1:
            razones.append(f"única con {deuda} en el ecosistema")
        if float(e.get("profundidad_dolor", 0) or 0) >= 70 and e.get("total_evidencias", 0) <= 1:
            razones.append("profundidad alta sostenida por 1 evidencia")
        if razones:
            outliers.append({"nombre": e.get("nombre", ""), "score_icp": icp,
                             "tipo_deuda": deuda, "razones": razones})
    return sorted(outliers, key=lambda o: (-o["score_icp"], o["nombre"]))


# ── Centinelas (señal temprana: dolor profundo aún poco corroborado) ──────────
def detectar_centinelas(exps: list[dict]) -> list[dict]:
    """Organizaciones-centinela: dolor profundo emergente que merece vigilancia."""
    centinelas = []
    for e in exps:
        if (_kwset(e) & SENALES_DOLOR) and float(e.get("profundidad_dolor", 0) or 0) >= 70 \
                and e.get("total_evidencias", 0) <= 2:
            centinelas.append({
                "nombre": e.get("nombre", ""),
                "tipo_deuda": e.get("tipo_deuda", ""),
                "profundidad_dolor": e.get("profundidad_dolor", 0),
                "total_evidencias": e.get("total_evidencias", 0),
                "motivo": "Dolor estructural profundo con corpus aún escaso: vigilar antes de concluir.",
            })
    return sorted(centinelas, key=lambda c: (-c["profundidad_dolor"], c["nombre"]))


# ── Calidad del corpus ────────────────────────────────────────────────────────
def calidad_corpus(exps: list[dict]) -> dict:
    """Métricas deterministas de calidad del corpus agregado del ecosistema."""
    evs = [ev for e in exps for ev in _evidencias(e)]
    n = len(evs)
    def _fecha(ev): return (ev.get("fecha") or ev.get("fecha_publicacion") or "").strip()
    fechadas = sum(1 for ev in evs if len(_fecha(ev)) >= 8 and _fecha(ev)[:4].isdigit())
    fuentes = len({(ev.get("fuente") or ev.get("nombre_medio") or "").strip() for ev in evs} - {""})
    confs = [float(ev.get("confianza") or 0) for ev in evs]
    orgs_suf = sum(1 for e in exps if e.get("total_evidencias", 0) >= 3)
    return {
        "organizaciones": len(exps),
        "evidencias_totales": n,
        "fuentes_distintas": fuentes,
        "ratio_fechado": round(fechadas / n, 4) if n else 0.0,
        "confianza_promedio": round(sum(confs) / n, 4) if n else 0.0,
        "organizaciones_corpus_suficiente": orgs_suf,
        "cobertura_suficiente": round(orgs_suf / len(exps), 4) if exps else 0.0,
    }


# ── Riesgos culturales (reutiliza el Predictivo) ──────────────────────────────
def riesgos_culturales(exps: list[dict], limite: int = 10) -> dict:
    """Riesgo cultural agregado del ecosistema (reutiliza predictivo.estimar_riesgo)."""
    detalle = []
    niveles = Counter()
    for e in exps:
        r = estimar_riesgo(e)
        niveles[r["nivel"]] += 1
        detalle.append({"nombre": e.get("nombre", ""), "tipo_deuda": e.get("tipo_deuda", ""),
                        "riesgo_global": r["riesgo_global"], "nivel": r["nivel"]})
    detalle.sort(key=lambda d: (-d["riesgo_global"], d["nombre"]))
    return {
        "distribucion": dict(niveles),
        "organizaciones_riesgo_alto": niveles.get("alto", 0),
        "top_riesgo": detalle[:limite],
    }


# ── Madurez del ecosistema (reutiliza el Predictivo) ──────────────────────────
def madurez_ecosistema(exps: list[dict]) -> dict:
    """Madurez agregada (reutiliza predictivo.calcular_madurez)."""
    if not exps:
        return {"promedio": 0, "distribucion": {}}
    niveles = Counter()
    total = 0
    for e in exps:
        m = calcular_madurez(e)
        niveles[m["nivel"]] += 1
        total += m["score"]
    return {"promedio": round(total / len(exps), 1), "distribucion": dict(niveles)}


# ── Ranking HD (reutiliza el ranking del Dictamen, enriquecido) ───────────────
def ranking_hd(exps: list[dict], limite: int = 10) -> list[dict]:
    """Ranking HD: TOP organizaciones con prioridad, motivo, evidencias y confianza."""
    por_nombre = {e.get("nombre", ""): e for e in exps}
    base = generar_ranking(exps, limite)
    salida = []
    for r in base:
        e = por_nombre.get(r["nombre"], {})
        score = r.get("score_compuesto", 0)
        prioridad = "Alta" if score >= 60 else ("Media" if score >= 35 else "Baja")
        salida.append({
            "posicion": r["posicion"],
            "nombre": r["nombre"],
            "prioridad": prioridad,
            "score_compuesto": score,
            "motivo": "; ".join(r.get("motivos", [])) or "sin motivo destacado",
            "evidencias": r.get("total_evidencias", 0),
            "tipo_deuda": r.get("tipo_deuda", ""),
            "nivel_confianza": _nivel_confianza(e),
            "veredicto": _validacion(e).get("veredicto", ""),
        })
    return salida


# ── Prioridades (validadas primero; reutiliza ranking_hd) ─────────────────────
_PESO_VEREDICTO = {"VALIDADA": 0, "VALIDADA_PARCIAL": 1, "NO_VALIDADA": 2,
                   "BLOQUEADA": 3, "SIN_HIPOTESIS": 4, "": 5}


def prioridades(exps: list[dict], limite: int = 10) -> list[dict]:
    """Prioridades HD: como el ranking, pero las hipótesis validadas van primero."""
    r = ranking_hd(exps, max(limite, len(exps)))
    r.sort(key=lambda x: (_PESO_VEREDICTO.get(x["veredicto"], 5), -x["score_compuesto"]))
    for i, item in enumerate(r[:limite], 1):
        item["prioridad_hd"] = i
    return r[:limite]


# ── Oportunidades (analíticas, sin recomendación comercial) ───────────────────
def oportunidades(exps: list[dict], limite: int = 10) -> list[dict]:
    """Oportunidades de investigación: por qué, para quién, evidencia y confianza.

    Criterio analítico (no comercial): hipótesis con soporte (veredicto VALIDADA o
    VALIDADA_PARCIAL) y no bloqueada. NO emite recomendación de acción comercial.
    """
    ops = []
    for e in exps:
        v = _validacion(e)
        if v.get("hipotesis_bloqueada"):
            continue
        if v.get("veredicto") not in ("VALIDADA", "VALIDADA_PARCIAL"):
            continue
        deuda = e.get("tipo_deuda", "")
        ops.append({
            "nombre": e.get("nombre", ""),
            "tipo_deuda": deuda,
            "por_que": f"Hipótesis de {deuda} con soporte ({v.get('veredicto')}, "
                       f"solidez {v.get('solidez', 0)}/100).",
            "para_quien": f"Investigación cualitativa de {deuda}" if deuda else "Investigación cualitativa",
            "con_que_evidencia": {
                "total_evidencias": e.get("total_evidencias", 0),
                "nivel_evidencia": v.get("nivel_evidencia", ""),
            },
            "nivel_confianza": _nivel_confianza(e),
            "interes_analitico": e.get("score_icp", 0),
        })
    ops.sort(key=lambda o: (-o["interes_analitico"], o["nombre"]))
    return ops[:limite]


# ── Contexto ecosistémico de una organización ─────────────────────────────────
def contexto_ecosistemico(nombre: str, exps: list[dict]) -> dict:
    """Ubica a una organización en su ecosistema: cluster, outlier, centinela, ranking."""
    clusters = detectar_clusters(exps)
    mi_cluster = next((c for c in clusters if nombre in c["organizaciones"]), None)
    outliers = {o["nombre"]: o for o in detectar_outliers(exps)}
    centinelas = {c["nombre"] for c in detectar_centinelas(exps)}
    ranking = ranking_hd(exps, len(exps))
    pos = next((r["posicion"] for r in ranking if r["nombre"] == nombre), None)
    return {
        "cluster": mi_cluster,
        "es_outlier": nombre in outliers,
        "outlier_razones": outliers.get(nombre, {}).get("razones", []),
        "es_centinela": nombre in centinelas,
        "posicion_ranking": pos,
        "indicadores_ecosistema": calcular_indicadores(exps),
        "tensiones_ecosistema": identificar_tensiones(exps),
    }


# ── Panorama ecosistémico completo (endpoint /ecosistema) ─────────────────────
def panorama_ecosistemico(exps: list[dict], limite: int = 10) -> dict:
    """Vista JSON completa del ecosistema para RadarHD (todo determinista)."""
    return {
        "total_organizaciones": len(exps),
        "indicadores": calcular_indicadores(exps),
        "tensiones": identificar_tensiones(exps),
        "patrones": identificar_patrones_regionales(exps),
        "clusters": detectar_clusters(exps),
        "outliers": detectar_outliers(exps),
        "centinelas": detectar_centinelas(exps),
        "riesgos_culturales": riesgos_culturales(exps, limite),
        "madurez": madurez_ecosistema(exps),
        "calidad_corpus": calidad_corpus(exps),
        "ranking": ranking_hd(exps, limite),
        "oportunidades": oportunidades(exps, limite),
        "prioridades": prioridades(exps, limite),
    }
