"""Diagnóstico de solo lectura del backend (Motor A en Vercel).

Funciones puras (reciben ``db``, nunca abren su propia conexión): auditan lo
que YA existe en la base — salud por conector (`salud_fuentes`, ya la escribe
`governance/health.py` en cada corrida), cola de jobs, y calidad estructural
de lo capturado. No interpreta contenido, no clasifica Deuda Cultural, no
escribe nada: es lectura y conteo, del mismo tipo que `validacion_cientifica.py`.

Nota deliberada: este backend usa PostgreSQL (Neon) en producción y SQLite en
local/tests (`hd_scraper/db/database.py`), no MongoDB. Y no hay un scheduler
en proceso corriendo de forma confiable en Vercel (las funciones serverless no
mantienen un `BackgroundScheduler` vivo entre invocaciones): la corrida
periódica real hoy es el workflow de GitHub Actions
`.github/workflows/prospeccion-tavily.yml` (lunes y jueves), más las corridas
manuales vía `POST /scrape`. Por eso "última corrida" se lee de la evidencia
y de `salud_fuentes`, no de un proceso en memoria que no existe en este
entorno.
"""
from __future__ import annotations

from ..db.database import Database
from ..db.models import ESTADO_OK


def check_database_connection(db: Database) -> dict:
    """Prueba una conexión real con un SELECT trivial. Nunca lanza: si falla,
    lo dice en el resultado en vez de tumbar el endpoint que lo llama."""
    try:
        db.fetch_one("SELECT 1 AS ok")
        return {"conectado": True, "dialecto": db.dialect, "error": None}
    except Exception as exc:  # noqa: BLE001 — diagnóstico: se reporta, no se propaga
        return {"conectado": False, "dialecto": db.dialect, "error": str(exc)}


def check_scraper_health(db: Database) -> dict:
    """Salud real por conector (tabla `salud_fuentes`, ya mantenida por
    `governance/health.py` en cada corrida de `run_connector`) + cola de jobs
    + timestamp de la evidencia más reciente (proxy de "última vez que se
    escribió algo real", más confiable que un scheduler que en Vercel no
    persiste entre invocaciones). Si una tabla no existe todavía (base recién
    creada) u otra consulta falla, se reporta el error específico, nunca un
    500 genérico ni un dict a medio llenar."""
    try:
        fuentes = [dict(f) for f in db.fetch_all(
            "SELECT fuente, ultima_corrida, ultimo_estado, fallos_consecutivos, "
            "alerta, detalle FROM salud_fuentes ORDER BY fuente"
        )]
        jobs_pendientes = db.fetch_one(
            "SELECT COUNT(*) AS n FROM jobs WHERE estado = 'pending'")["n"]
        jobs_error = db.fetch_one(
            "SELECT COUNT(*) AS n FROM jobs WHERE estado = 'error'")["n"]
        ultima = db.fetch_one(
            "SELECT MAX(creado_en) AS t FROM evidencias WHERE estado = ?", (ESTADO_OK,))
        return {
            "ok": True,
            "error": None,
            "fuentes": fuentes,
            "alguna_fuente_en_alerta": any(f["alerta"] for f in fuentes),
            "jobs_pendientes": jobs_pendientes,
            "jobs_con_error": jobs_error,
            "ultima_evidencia_escrita_en": ultima["t"] if ultima else None,
        }
    except Exception as exc:  # noqa: BLE001 — diagnóstico: se reporta, no se propaga
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "fuentes": [],
            "alguna_fuente_en_alerta": False,
            "jobs_pendientes": None,
            "jobs_con_error": None,
            "ultima_evidencia_escrita_en": None,
        }


def check_data_quality(db: Database) -> dict:
    """Conteos estructurales de calidad, sin juzgar contenido: evidencia sin
    organización identificada (se conserva, nunca se descarta, per doctrina),
    y prospectos con más de una categoría para el mismo nombre (el conflicto
    documentado en `promocion_store.categoria_de_organizacion`). Igual que
    check_scraper_health: ante un fallo real, error específico, no un 500."""
    try:
        total_evidencias = db.fetch_one(
            "SELECT COUNT(*) AS n FROM evidencias WHERE estado = ?", (ESTADO_OK,))["n"]
        sin_empresa = db.fetch_one(
            "SELECT COUNT(*) AS n FROM evidencias WHERE estado = ? "
            "AND (empresa_mencionada IS NULL OR TRIM(empresa_mencionada) = '')",
            (ESTADO_OK,))["n"]
        no_fechadas = db.fetch_one(
            "SELECT COUNT(*) AS n FROM evidencias WHERE estado = 'no_fechado'")["n"]
        conflictos = db.fetch_all(
            "SELECT LOWER(TRIM(nombre)) AS nombre, COUNT(DISTINCT categoria) AS n_categorias "
            "FROM prospectos GROUP BY LOWER(TRIM(nombre)) HAVING COUNT(DISTINCT categoria) > 1"
        )
        return {
            "ok": True,
            "error": None,
            "total_evidencias_ok": total_evidencias,
            "evidencias_sin_empresa_identificada": sin_empresa,
            "evidencias_no_fechadas": no_fechadas,
            "prospectos_con_categoria_en_conflicto": len(conflictos),
            "nombres_en_conflicto": [c["nombre"] for c in conflictos][:20],
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "total_evidencias_ok": None,
            "evidencias_sin_empresa_identificada": None,
            "evidencias_no_fechadas": None,
            "prospectos_con_categoria_en_conflicto": None,
            "nombres_en_conflicto": [],
        }


def diagnostico_completo(db: Database) -> dict:
    """Junta las tres verificaciones en un solo dict. Punto único que usan
    `/audit/database` y `scripts/audit_backend.py`, para no duplicar criterio.
    Cada sub-función ya blinda sus propios errores, así que esto nunca lanza."""
    return {
        "base_de_datos": check_database_connection(db),
        "scraper": check_scraper_health(db),
        "calidad_de_datos": check_data_quality(db),
    }
