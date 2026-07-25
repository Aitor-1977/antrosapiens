"""Sistema Operativo del Laboratorio — Capa 18.

Integra todas las capas en un único flujo operativo: dashboard maestro con el
estado de motores, corpus, pipeline, validación, gobernanza y observatorio.

No genera conocimiento nuevo: agrega estados ya calculados por las capas
anteriores de forma determinista. Las funciones puras reciben conteos/summaries
(no tocan disco): el endpoint reúne los datos y se los pasa. Sin IA, sin red.
"""
from __future__ import annotations

from collections import Counter

from .gobernanza import MOTOR_NOMBRE, VERSION_PIPELINE
from .observatorio import calcular_indicadores, identificar_tensiones

# Las 19 capas del Motor A (0–18), en orden. Estado declarado: operativa.
CAPAS = (
    (0, "Captura e Ingesta"),
    (1, "Normalización"),
    (2, "Evidencia (contrato)"),
    (3, "Inferencia Antropológica"),
    (4, "Relevancia y Señales"),
    (5, "Enriquecimiento"),
    (6, "Drift Narrativo"),
    (7, "Onlife"),
    (8, "Pipeline Comercial"),
    (9, "Dolor Cultural / DolorMap"),
    (10, "Curaduría Antropológica"),
    (11, "Validación Científica"),
    (12, "Gobernanza Científica"),
    (13, "Memoria Científica"),
    (14, "Comparador Temporal y Ecosistémico"),
    (15, "Motor Predictivo Antropológico"),
    (16, "Observatorio LATAM"),
    (17, "Publicador Científico"),
    (18, "Sistema Operativo del Laboratorio"),
)


# ── Estado de capas ───────────────────────────────────────────────────────────
def estado_capas() -> dict:
    """Inventario de las 19 capas del Motor A y su estado (determinista)."""
    capas = [{"numero": n, "nombre": nom, "estado": "operativa"} for n, nom in CAPAS]
    return {"total": len(capas), "operativas": len(capas), "capas": capas}


# ── Estado de corpus ──────────────────────────────────────────────────────────
def estado_corpus(conteos: dict) -> dict:
    """Estado del corpus de evidencia a partir de conteos ya obtenidos."""
    total = conteos.get("evidencias_total", 0)
    ok = conteos.get("evidencias_ok", 0)
    no_fechado = conteos.get("evidencias_no_fechado", 0)
    return {
        "evidencias_total": total,
        "evidencias_ok": ok,
        "evidencias_no_fechado": no_fechado,
        "rechazos": conteos.get("rechazos", 0),
        "prospectos": conteos.get("prospectos", 0),
        "tasa_consumible": round(ok / total, 4) if total else 0.0,
        "estado": "poblado" if total > 0 else "vacio",
    }


# ── Estado de pipeline ────────────────────────────────────────────────────────
def estado_pipeline(conteos: dict) -> dict:
    """Estado del pipeline (jobs y pipeline comercial gestionado por Motor C)."""
    return {
        "jobs": conteos.get("jobs", 0),
        "pipeline_comercial": conteos.get("pipeline_comercial", 0),
        "version_pipeline": VERSION_PIPELINE,
        "estado": "activo",
        "nota": "El pipeline comercial es responsabilidad de Motor C.",
    }


# ── Estado de validación ──────────────────────────────────────────────────────
def estado_validacion(expedientes: list[dict]) -> dict:
    """Distribución de veredictos científicos sobre los expedientes vigentes."""
    veredictos = Counter()
    bloqueadas = 0
    for e in expedientes:
        v = (e.get("validacion_cientifica") or {}).get("veredicto", "")
        if v:
            veredictos[v] += 1
        if e.get("hipotesis_bloqueada"):
            bloqueadas += 1
    n = len(expedientes)
    return {
        "expedientes": n,
        "distribucion_veredicto": dict(veredictos),
        "hipotesis_bloqueadas": bloqueadas,
        "tasa_bloqueo": round(bloqueadas / n, 4) if n else 0.0,
    }


# ── Estado de gobernanza ──────────────────────────────────────────────────────
def estado_gobernanza(conteos: dict) -> dict:
    """Estado de la gobernanza (huellas, certificados, auditorías, memoria)."""
    return {
        "huellas_digitales": conteos.get("huellas", 0),
        "certificados": conteos.get("certificados", 0),
        "auditorias": conteos.get("auditorias", 0),
        "versiones_memoria": conteos.get("memoria", 0),
        "decisiones_bitacora": conteos.get("bitacora", 0),
        "estado": "auditable",
    }


# ── Estado del observatorio ───────────────────────────────────────────────────
def estado_observatorio(expedientes: list[dict]) -> dict:
    """Resumen ecosistémico para el dashboard (reutiliza el Observatorio)."""
    return {
        "indicadores": calcular_indicadores(expedientes),
        "tensiones": identificar_tensiones(expedientes),
    }


# ── Estado general ────────────────────────────────────────────────────────────
def estado_general(corpus: dict, validacion: dict, gobernanza: dict,
                   observatorio: dict) -> dict:
    """Estado general del laboratorio a partir de los estados de cada área."""
    return {
        "motor": MOTOR_NOMBRE,
        "estado": "operativo",
        "motores": {
            "A": "operativo (este repositorio: captura → gobernanza → capas)",
            "B": "externo (únicamente renderiza)",
            "C": "externo (únicamente gestiona el pipeline comercial)",
        },
        "resumen": {
            "evidencias": corpus.get("evidencias_total", 0),
            "expedientes": validacion.get("expedientes", 0),
            "certificados": gobernanza.get("certificados", 0),
            "versiones_memoria": gobernanza.get("versiones_memoria", 0),
            "organizaciones_observadas": observatorio.get("indicadores", {}).get("organizaciones", 0),
        },
        "estado_metodologico": "determinista y reproducible",
        "estado_cientifico": "auditable",
    }
