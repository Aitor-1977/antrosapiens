"""Memoria Científica — Capa 13.

Construye la memoria longitudinal del conocimiento producido por el motor. Cada
expediente conserva TODAS sus versiones históricas: nunca se sobrescribe, solo
se añade. Sobre esa memoria inmutable se calcula la línea temporal científica,
la evolución del dolor cultural y la comparación entre versiones.

100% determinista y reproducible: el hash de cada versión proviene de la huella
de gobernanza (Capa 12), que ignora la fecha de emisión. Sin IA, sin red.

Las funciones puras viven aquí; la persistencia inmutable (append-only) vive en
``memoria_store.py``.
"""
from __future__ import annotations

from .gobernanza import MOTOR_NOMBRE, _nivel_confianza

# Campos cuya variación entre versiones cuenta como "cambio científico".
CAMPOS_COMPARABLES = (
    "scoring", "hipotesis", "veredicto", "solidez", "suficiencia",
    "nivel_evidencia", "dolor_cultural", "patrones", "keywords", "narrativa",
)


# ── 1. Crear versión (snapshot inmutable) ─────────────────────────────────────
def crear_version(expediente: dict, validacion: dict, huella: dict,
                  usuario: str = "sistema", version: int = 1,
                  hash_previo: str = "") -> dict:
    """Construye el snapshot científico inmutable de un expediente.

    Reúne hipótesis, dictamen, validación, clasificación, patrones, narrativa,
    dolor cultural, niveles, hash, versión, fecha, usuario, motor y pipeline.
    """
    dic = validacion.get("dictamen_cientifico", {}) or {}
    sol = validacion.get("solidez", {}) or {}
    return {
        "version": version,
        "hash": huella.get("hash", ""),
        "hash_previo": hash_previo,
        "fecha": huella.get("fecha", ""),
        "usuario": usuario,
        "motor": huella.get("motor", MOTOR_NOMBRE),
        "pipeline": huella.get("versiones", {}).get("pipeline", ""),
        "hipotesis": expediente.get("tipo_deuda", ""),
        "scoring": expediente.get("scoring", ""),
        "clasificacion": expediente.get("scoring", ""),
        "veredicto": dic.get("veredicto", ""),
        "solidez": dic.get("solidez", 0),
        "suficiencia": dic.get("suficiencia", 0),
        "nivel_evidencia": dic.get("nivel_evidencia", ""),
        "nivel_confianza": _nivel_confianza(sol.get("confianza_agregada", 0.0)),
        "dolor_cultural": expediente.get("tipo_deuda", ""),
        "deuda_razon": expediente.get("deuda_razon", ""),
        "patrones": sorted(p.get("patron", "") for p in expediente.get("patrones", []) or []),
        "narrativa": dic.get("resumen", ""),
        "keywords": sorted(expediente.get("keywords", []) or []),
    }


# ── 2. Comparar versiones ─────────────────────────────────────────────────────
def comparar_versiones(version_a: dict, version_b: dict) -> list[dict]:
    """Diferencias campo a campo entre dos versiones (determinista, sin juicio)."""
    if not version_a or not version_b:
        return []
    cambios: list[dict] = []
    for campo in CAMPOS_COMPARABLES:
        a, b = version_a.get(campo), version_b.get(campo)
        if a != b:
            cambios.append({"campo": campo, "antes": a, "despues": b})
    return cambios


# ── 3. Detectar cambios ───────────────────────────────────────────────────────
def detectar_cambios(version_a: dict, version_b: dict) -> dict:
    """¿Cambió el estado científico entre dos versiones? Qué campos."""
    cambios = comparar_versiones(version_a, version_b)
    return {"hubo_cambio": len(cambios) > 0,
            "campos": [c["campo"] for c in cambios],
            "detalle": cambios}


# ── 4. Construir timeline ─────────────────────────────────────────────────────
def construir_timeline(versiones: list[dict]) -> list[dict]:
    """Línea temporal científica: una entrada por versión, en orden ascendente."""
    ordenadas = sorted(versiones or [], key=lambda v: v.get("version", 0))
    return [{
        "version": v.get("version", 0),
        "fecha": v.get("fecha", ""),
        "veredicto": v.get("veredicto", ""),
        "solidez": v.get("solidez", 0),
        "suficiencia": v.get("suficiencia", 0),
        "hipotesis": v.get("hipotesis", ""),
        "hash": v.get("hash", ""),
    } for v in ordenadas]


def _tendencia(inicial: float, final: float) -> str:
    if final > inicial:
        return "ascendente"
    if final < inicial:
        return "descendente"
    return "estable"


# ── 5. Calcular evolución ─────────────────────────────────────────────────────
def calcular_evolucion(versiones: list[dict]) -> dict:
    """Evolución de solidez, suficiencia, veredicto, dolor cultural y narrativa."""
    ordenadas = sorted(versiones or [], key=lambda v: v.get("version", 0))
    if not ordenadas:
        return {"versiones": 0, "solidez": {}, "suficiencia": {},
                "veredictos": [], "dolor_cultural": [], "narrativa_cambios": 0}

    primero, ultimo = ordenadas[0], ordenadas[-1]
    sol_i, sol_f = primero.get("solidez", 0), ultimo.get("solidez", 0)
    suf_i, suf_f = primero.get("suficiencia", 0), ultimo.get("suficiencia", 0)

    veredictos = [v.get("veredicto", "") for v in ordenadas]
    dolores = [v.get("dolor_cultural", "") for v in ordenadas]
    narr_cambios = sum(
        1 for i in range(1, len(ordenadas))
        if ordenadas[i].get("narrativa") != ordenadas[i - 1].get("narrativa"))

    return {
        "versiones": len(ordenadas),
        "solidez": {"inicial": sol_i, "final": sol_f, "delta": sol_f - sol_i,
                    "tendencia": _tendencia(sol_i, sol_f)},
        "suficiencia": {"inicial": suf_i, "final": suf_f, "delta": suf_f - suf_i,
                        "tendencia": _tendencia(suf_i, suf_f)},
        "veredictos": veredictos,
        "veredicto_cambio": veredictos[0] != veredictos[-1],
        "dolor_cultural": dolores,
        "dolor_cambio": dolores[0] != dolores[-1],
        "narrativa_cambios": narr_cambios,
    }


# ── 6. Emitir historial ───────────────────────────────────────────────────────
def emitir_historial(org: str, versiones: list[dict]) -> dict:
    """Historial completo: timeline + evolución + versiones (memoria inmutable)."""
    ordenadas = sorted(versiones or [], key=lambda v: v.get("version", 0))
    cambios_por_version: list[dict] = []
    for i in range(1, len(ordenadas)):
        cambios_por_version.append({
            "de_version": ordenadas[i - 1].get("version", 0),
            "a_version": ordenadas[i].get("version", 0),
            **detectar_cambios(ordenadas[i - 1], ordenadas[i]),
        })
    return {
        "org": org,
        "total_versiones": len(ordenadas),
        "timeline": construir_timeline(ordenadas),
        "evolucion": calcular_evolucion(ordenadas),
        "cambios": cambios_por_version,
        "versiones": ordenadas,
    }
