"""Componente 5 del cierre de 15: en el pipeline de Tavily
(`busqueda_dinamica_founder`), la evidencia debe poder existir independiente
del expediente. `evidencia_clasificada.expediente_id` es nullable (migrado en
§8.3 del documento maestro, 2026-08-29, ver `db/database.py:
_migrar_expediente_id_nullable` y `clasificacion_store.guardar_clasificacion`):
sin organización identificable en el texto, la clasificación se persiste
igual, con `expediente_id = NULL`, y puede concentrarse/promoverse más
adelante si mejora la extracción de identidad — nunca se descarta por una
condición NOT NULL.

La primera prueba de este archivo reproduce, de forma aislada y sin tocar el
código de producción, exactamente el defecto histórico que existía antes de
la migración (columna NOT NULL descartando la evidencia en silencio) para
demostrar que el test es capaz de detectarlo. Las siguientes prueban el
comportamiento real actual.
"""
import sqlite3

import pytest

from hd_scraper.clasificacion_epistemologica import clasificar
from hd_scraper.clasificacion_store import (
    clasificar_lote,
    evidencias_sin_clasificar,
    guardar_clasificacion,
)
from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup

_CONECTOR = "busqueda_dinamica_founder"


def _sembrar_evidencia_tavily(db, *, cita_textual, n=1):
    """Evidencia real de `busqueda_dinamica_founder`: empresa_mencionada es la
    FRASE DE BÚSQUEDA (nunca una organización real, ver docstring de
    clasificacion_store.py), y aquí el texto tampoco declara ninguna
    organización con patrón fuerte de fundación/posesión — así
    `organizacion_mencionada` queda None, el caso que históricamente se
    perdía."""
    return db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, estado, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (cita_textual, ahora_iso(), f"https://ej.test/tavily/{n}", "Tavily",
         "founder despedido fintech mexico", "queja", "usuario",
         calcular_hash_dedup("founder despedido fintech mexico", cita_textual),
         _CONECTOR, ESTADO_OK, ahora_iso()))


def test_defecto_historico_reproducido_de_forma_aislada_sin_tocar_produccion():
    """RED de referencia: sobre una tabla `evidencia_clasificada` con
    `expediente_id NOT NULL` (el esquema ANTES de la migración §8.3), guardar
    una clasificación sin organización identificable debe fallar — así se
    demuestra que el defecto real (evidencia descartada en silencio) es
    detectable por un test, sin necesidad de romper el schema de producción
    para probarlo."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE evidencia_clasificada ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "expediente_id INTEGER NOT NULL, "  # esquema histórico, pre-§8.3
        "evidencia_id INTEGER NOT NULL, "
        "tipo_epistemologico TEXT NOT NULL)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
            "tipo_epistemologico) VALUES (?, ?, ?)",
            (None, 1, "contextual"))
    conn.close()


def test_clasificacion_store_persiste_evidencia_tavily_sin_organizacion(db):
    """GREEN: el código real de hoy no reproduce el defecto — persiste la
    clasificación con expediente_id NULL en vez de descartarla."""
    ev_id = _sembrar_evidencia_tavily(
        db, cita_textual="cerre mi startup despues de cinco semanas, esto es lo que aprendi")
    rep = clasificar_lote(db, aplicar=True)

    assert rep["escritas"] == 1  # una sola evidencia en el lote
    fila = db.fetch_one(
        "SELECT expediente_id, tipo_epistemologico FROM evidencia_clasificada "
        "WHERE evidencia_id = ?", (ev_id,))
    assert fila is not None, "la evidencia no debe perderse por falta de organización"
    assert fila["expediente_id"] is None
    assert db.fetch_one(
        "SELECT id FROM expedientes_candidatos") is None, (
        "sin organización identificable no debe crearse ningún expediente")


def test_evidencia_sin_organizacion_puede_concentrarse_despues_si_mejora_la_deteccion():
    """La evidencia sin organización sigue siendo clasificable/consultable de
    forma pura (concentrador_evidencia no la pierde): si el texto SÍ declara
    una organización con patrón fuerte, organizacion_mencionada se resuelve y
    la evidencia queda disponible para concentrarse por ese nombre más
    adelante — la independencia del expediente no significa "sin remedio"."""
    evidencia = {
        "cita_textual": "soy fundador de Acme, cerre mi startup despues de cinco semanas",
        "empresa_mencionada": "founder despedido fintech mexico",
        "nombre_medio": "Tavily",
        "origen_declaracion": "usuario",
        "persona_citada": None,
        "cargo": None,
    }
    clas = clasificar(evidencia)
    assert clas.organizacion_mencionada == "Acme"


def test_evidencia_sin_organizacion_aparece_en_evidencias_sin_clasificar_hasta_procesarse(db):
    """Confirma que la evidencia de Tavily sin organización identificable no
    desaparece del lote pendiente antes de clasificarse (existe de forma
    plenamente independiente del expediente que eventualmente pueda o no
    tener)."""
    ev_id = _sembrar_evidencia_tavily(
        db, cita_textual="trabaje en una startup que quebro despues de un año")
    pendientes = evidencias_sin_clasificar(db)
    assert any(e["id"] == ev_id for e in pendientes)

    clasificar_lote(db, aplicar=True)
    pendientes_tras = evidencias_sin_clasificar(db)
    assert not any(e["id"] == ev_id for e in pendientes_tras)
