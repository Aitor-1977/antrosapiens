"""Motor Predictivo Antropológico — Capa 15.

Detecta trayectorias culturales futuras usando ÚNICAMENTE evidencia histórica y
reglas deterministas explícitas. No usa IA generativa ni modelos opacos: cada
número se deriva de una fórmula auditable sobre la serie temporal de evidencia
ya capturada. Mismo insumo ⇒ misma proyección. Sin red.

La "predicción" es proyección aritmética de tendencia con banda de volatilidad,
no una afirmación probabilística oculta: se declara la fórmula y sus supuestos.
"""
from __future__ import annotations

from collections import Counter

from .analisis import SENALES_DOLOR


# ── Serie temporal de evidencia (insumo determinista) ─────────────────────────
def _evidencias(expediente: dict) -> list[dict]:
    ev = expediente.get("evidencias", [])
    if isinstance(ev, dict):
        return list(ev.get("items", []))
    return list(ev or [])


def _ev_fecha(ev: dict) -> str:
    return (ev.get("fecha") or ev.get("fecha_publicacion") or "").strip()


def serie_temporal(expediente: dict) -> dict:
    """Serie mensual (periodo→conteo de evidencias). Determinista y ordenada."""
    conteo: Counter = Counter()
    for ev in _evidencias(expediente):
        f = _ev_fecha(ev)
        if len(f) >= 7 and f[:4].isdigit():
            conteo[f[:7]] += 1
    periodos = sorted(conteo)
    return {"periodos": periodos, "valores": [conteo[p] for p in periodos]}


def _pendiente(valores: list[float]) -> float:
    """Pendiente por mínimos cuadrados sobre x = 0..n-1 (determinista)."""
    n = len(valores)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(valores) / n
    num = sum((xs[i] - mx) * (valores[i] - my) for i in range(n))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else 0.0


def _stddev(valores: list[float]) -> float:
    n = len(valores)
    if n < 2:
        return 0.0
    m = sum(valores) / n
    return (sum((v - m) ** 2 for v in valores) / n) ** 0.5


# ── 1. Tendencia ──────────────────────────────────────────────────────────────
def calcular_tendencia(serie: list[float]) -> dict:
    """Tendencia de la serie: pendiente y dirección (asc|desc|estable)."""
    if len(serie) < 2:
        return {"pendiente": 0.0, "direccion": "estable",
                "inicial": serie[0] if serie else 0, "final": serie[-1] if serie else 0,
                "delta": 0}
    p = _pendiente(serie)
    direccion = "ascendente" if p > 0 else ("descendente" if p < 0 else "estable")
    return {"pendiente": round(p, 4), "direccion": direccion,
            "inicial": serie[0], "final": serie[-1], "delta": serie[-1] - serie[0]}


# ── 2. Estabilidad ────────────────────────────────────────────────────────────
def calcular_estabilidad(serie: list[float]) -> int:
    """Estabilidad 0–100 (100 = sin variación relativa). Inverso del CV."""
    if len(serie) < 2:
        return 100
    m = sum(serie) / len(serie)
    if m == 0:
        return 100 if all(v == 0 for v in serie) else 0
    cv = _stddev(serie) / abs(m)
    return int(round(max(0.0, min(1.0, 1 - cv)) * 100))


# ── 3. Inflexiones ────────────────────────────────────────────────────────────
def detectar_inflexiones(serie: list[float]) -> list[int]:
    """Índices donde la serie cambia de dirección (subida↔bajada)."""
    if len(serie) < 3:
        return []
    deltas = [serie[i] - serie[i - 1] for i in range(1, len(serie))]
    inflexiones = []
    for i in range(1, len(deltas)):
        a, b = deltas[i - 1], deltas[i]
        if a != 0 and b != 0 and (a > 0) != (b > 0):
            inflexiones.append(i)
    return inflexiones


# ── 4. Volatilidad ────────────────────────────────────────────────────────────
def calcular_volatilidad(serie: list[float]) -> int:
    """Volatilidad 0–100: mezcla cambios de dirección y amplitud relativa."""
    if len(serie) < 2:
        return 0
    inflex = len(detectar_inflexiones(serie))
    ratio_dir = inflex / (len(serie) - 2) if len(serie) > 2 else 0.0
    rango = max(serie) - min(serie)
    amplitud = rango / (max(serie) if max(serie) else 1)
    return int(round(min(1.0, 0.6 * ratio_dir + 0.4 * amplitud) * 100))


# ── 5. Proyectar escenarios ───────────────────────────────────────────────────
def proyectar_escenarios(serie: list[float]) -> dict:
    """Proyecta el siguiente periodo: base ± banda de volatilidad (determinista)."""
    if not serie:
        return {"base": 0.0, "optimista": 0.0, "pesimista": 0.0,
                "horizonte": "siguiente_periodo"}
    tend = calcular_tendencia(serie)
    vol = calcular_volatilidad(serie)
    ultimo = serie[-1]
    base = ultimo + tend["pendiente"]
    rango = max(serie) - min(serie)
    banda = (vol / 100) * (rango if rango else 1)
    return {
        "base": round(base, 2),
        "optimista": round(base + banda, 2),
        "pesimista": round(max(0.0, base - banda), 2),
        "horizonte": "siguiente_periodo",
    }


# ── 6. Estimar riesgo ─────────────────────────────────────────────────────────
def estimar_riesgo(expediente: dict, serie: list[float] | None = None) -> dict:
    """Riesgo narrativo y cultural desde señales de dolor y volatilidad."""
    if serie is None:
        serie = serie_temporal(expediente)["valores"]
    kws = set(expediente.get("keywords", []) or [])
    n_dolor = len(kws & SENALES_DOLOR)
    profundidad = float(expediente.get("profundidad_dolor", 0) or 0)
    bloqueada = bool(expediente.get("hipotesis_bloqueada"))

    riesgo_cultural = int(round(min(100.0,
        profundidad * 0.5 + n_dolor * 15 + (10 if bloqueada else 0))))
    vol = calcular_volatilidad(serie)
    tipos = {(_e.get("tipo_evento") or "") for _e in _evidencias(expediente)}
    riesgo_narrativo = int(round(min(100.0, vol * 0.7 + len(tipos) * 5)))
    global_ = int(round((riesgo_cultural + riesgo_narrativo) / 2))
    nivel = "alto" if global_ >= 66 else ("medio" if global_ >= 33 else "bajo")
    return {"riesgo_cultural": riesgo_cultural, "riesgo_narrativo": riesgo_narrativo,
            "riesgo_global": global_, "nivel": nivel}


# ── 7. Calcular madurez ───────────────────────────────────────────────────────
def calcular_madurez(expediente: dict) -> dict:
    """Madurez 0–100 del expediente: volumen, diversidad de fuentes y lapso."""
    evs = _evidencias(expediente)
    n = len(evs)
    fuentes = len({(e.get("fuente") or e.get("nombre_medio") or "").strip() for e in evs} - {""})
    fechas = sorted(f for f in (_ev_fecha(e)[:7] for e in evs) if len(f) >= 7)
    span = len(set(fechas))

    score = min(100, int(round(
        min(n, 6) / 6 * 40 + min(fuentes, 4) / 4 * 30 + min(span, 6) / 6 * 30)))
    if score >= 75:
        nivel = "maduro"
    elif score >= 50:
        nivel = "consolidado"
    elif score >= 25:
        nivel = "en_desarrollo"
    else:
        nivel = "naciente"
    return {"score": score, "nivel": nivel, "evidencias": n,
            "fuentes": fuentes, "periodos": span}


# ── 8. Emitir proyección ──────────────────────────────────────────────────────
def emitir_proyeccion(expediente: dict) -> dict:
    """Proyección antropológica completa a partir de la evidencia histórica."""
    serie_d = serie_temporal(expediente)
    serie = serie_d["valores"]
    return {
        "org": expediente.get("nombre", ""),
        "serie": serie_d,
        "tendencia": calcular_tendencia(serie),
        "estabilidad": calcular_estabilidad(serie),
        "volatilidad": calcular_volatilidad(serie),
        "inflexiones": detectar_inflexiones(serie),
        "escenarios": proyectar_escenarios(serie),
        "riesgo": estimar_riesgo(expediente, serie),
        "madurez": calcular_madurez(expediente),
        "nota": ("Proyección determinista basada solo en evidencia histórica; "
                 "no es una predicción probabilística ni usa IA."),
    }
