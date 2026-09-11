"""PARTE B del cierre del cuello de botella (2026-09-11): la corrida
programada (`scheduler.corrida`) solo hacía purga + encolado + procesamiento
de ingesta — nunca clasificaba la evidencia nueva, así que
`evidencia_clasificada` solo se llenaba si alguien corría
`scripts.clasificar_evidencia --aplicar` a mano.

Estos tests aíslan `corrida()` de la red real: `procesar_pendientes` (que sí
llamaría a los conectores reales) se sustituye por un stub que no hace nada,
y la evidencia "ya capturada este ciclo" se siembra directamente en la base
-- exactamente el estado en el que quedaría la base justo después de que
`procesar_pendientes` hiciera su trabajo real. Lo que se prueba es el paso
NUEVO: que `corrida()` clasifica automáticamente después de procesar.
"""
import importlib

from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup


def _sembrar_evidencia(db, *, n, empresa, cita_textual, origen_declaracion="operador"):
    return db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, fecha_publicacion, connector, estado, categoria, "
        "keywords, confianza, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (cita_textual, ahora_iso(), f"https://ejemplo.com/sched/{n}",
         "Medio de Prueba", empresa, "queja", origen_declaracion,
         calcular_hash_dedup(empresa, cita_textual), "2026-09-11",
         "manual_test", ESTADO_OK, "Startup", "[]", 1.0, ahora_iso()))


def test_corrida_clasifica_evidencia_nueva_automaticamente(db, monkeypatch):
    scheduler = importlib.import_module("hd_scraper.scheduler")
    monkeypatch.setattr(scheduler, "procesar_pendientes", lambda db, **kw: 0)

    ev_id = _sembrar_evidencia(
        db, n=1, empresa="Kavak",
        cita_textual="Kavak publica una vacante para su equipo de ingeniería")

    assert db.fetch_one("SELECT id FROM evidencia_clasificada") is None

    scheduler.corrida(db)

    fila = db.fetch_one(
        "SELECT tipo_epistemologico FROM evidencia_clasificada WHERE evidencia_id = ?",
        (ev_id,))
    assert fila is not None
    assert fila["tipo_epistemologico"] == "senal_primaria_huella_practica"


def test_corrida_es_idempotente_no_duplica_clasificacion_ni_evidencia(db, monkeypatch):
    scheduler = importlib.import_module("hd_scraper.scheduler")
    monkeypatch.setattr(scheduler, "procesar_pendientes", lambda db, **kw: 0)

    _sembrar_evidencia(
        db, n=2, empresa="Fintual",
        cita_textual="Fintual publica una vacante para su equipo de riesgo")

    scheduler.corrida(db)
    total_evidencias_1 = db.fetch_one("SELECT COUNT(*) AS n FROM evidencias")["n"]
    total_clasificadas_1 = db.fetch_one("SELECT COUNT(*) AS n FROM evidencia_clasificada")["n"]

    scheduler.corrida(db)  # segunda corrida sobre la misma base
    total_evidencias_2 = db.fetch_one("SELECT COUNT(*) AS n FROM evidencias")["n"]
    total_clasificadas_2 = db.fetch_one("SELECT COUNT(*) AS n FROM evidencia_clasificada")["n"]

    assert total_evidencias_2 == total_evidencias_1
    assert total_clasificadas_2 == total_clasificadas_1


def test_fallo_de_clasificacion_no_borra_ni_corrompe_la_evidencia_cruda(db, monkeypatch, caplog):
    scheduler = importlib.import_module("hd_scraper.scheduler")
    monkeypatch.setattr(scheduler, "procesar_pendientes", lambda db, **kw: 0)

    def _clasificar_lote_roto(*args, **kwargs):
        raise RuntimeError("fallo simulado de clasificación")

    monkeypatch.setattr(scheduler, "clasificar_lote", _clasificar_lote_roto)

    ev_id = _sembrar_evidencia(
        db, n=3, empresa="Bitso", cita_textual="Bitso publica una vacante de producto")

    # corrida() no debe propagar la excepción: la ingesta/purga ya hecha en
    # el ciclo no debe perderse por un fallo del paso de clasificación.
    scheduler.corrida(db)

    fila = db.fetch_one("SELECT id, cita_textual FROM evidencias WHERE id = ?", (ev_id,))
    assert fila is not None
    assert fila["cita_textual"] == "Bitso publica una vacante de producto"
    # Sin clasificar (el fallo se registró, no se inventó una clasificación).
    assert db.fetch_one(
        "SELECT id FROM evidencia_clasificada WHERE evidencia_id = ?", (ev_id,)) is None
