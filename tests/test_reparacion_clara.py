"""Regresión end-to-end del caso real "Clara" en /verificados.

Reproduce EXACTAMENTE la forma de los datos que hoy están en producción
(auditoría 2026-09-15, confirmado en vivo vía GET /verificados): una fila
histórica en evidencia_clasificada, clasificada ANTES del fix de
_es_parte_de_nombre_mas_largo (commit 64ae6f7), que vincula la evidencia
de "Clara Brugada" (persona) al expediente "Clara" (fintech homónima) como
senal_primaria_autodeclaracion. Nunca se reprocesó porque clasificar_lote
es de un solo disparo (ver clasificacion_store.py).

Cubre lo que las suites de clasificacion_epistemologica.py y relevance.py
ya prueban a nivel de función pura, pero a nivel de INTEGRACIÓN real:
el endpoint administrativo (GET /ops/reparar-clara-...) contra el dato
persistido, y su efecto observable en /verificados.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.api.app import _EVIDENCIA_ID_CLARA_OBSOLETA
from hd_scraper.candidatos_verificados import listar_candidatos_verificados
from hd_scraper.config import settings
from hd_scraper.db.models import ahora_iso

RUTA_REPARACION = f"/ops/reparar-clara-0e72ee25e22c6f67"


def _sembrar_caso_clara_obsoleto(db):
    """Reproduce el dato real de producción, id incluido (el endpoint está
    deliberadamente acotado a este evidencia_id conocido de antemano)."""
    db.execute(
        "INSERT INTO evidencias (id, cita_textual, fecha_extraccion, "
        "fecha_publicacion, url_fuente, nombre_medio, empresa_mencionada, "
        "tipo_evento, origen_declaracion, hash_dedup, connector, creado_en) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (_EVIDENCIA_ID_CLARA_OBSOLETA,
         'Clara Brugada acompaña a la Presidenta Claudia Sheinbaum en el '
         'arranque de "Sí al Desarme, Sí a la Paz"; destaca reducción de '
         'homicidios en la Ciudad de México - CDMX',
         ahora_iso(), "2026-07-09", "https://news.example/clara-brugada",
         "CDMX", "Clara", "ronda", "prensa", "hash-clara-obsoleta",
         "google_news", ahora_iso()))
    exp_id = db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        ("Clara", "candidato"))
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico, enunciador_nombre, enunciador_cargo) "
        "VALUES (?,?,?,?,?)",
        (exp_id, _EVIDENCIA_ID_CLARA_OBSOLETA, "senal_primaria_autodeclaracion",
         "Clara Brugada", "Presidenta"))
    return exp_id


def _sembrar_candidato_legitimo(db, n=1):
    """Control: un candidato verificado real, sin relación con el caso
    Clara, que la reparación NUNCA debe tocar."""
    db.execute(
        "INSERT INTO evidencias (id, cita_textual, fecha_extraccion, "
        "fecha_publicacion, url_fuente, nombre_medio, empresa_mencionada, "
        "tipo_evento, origen_declaracion, hash_dedup, connector, creado_en) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (900 + n, "Fundador de Acme anuncia ronda serie A", ahora_iso(),
         "2026-08-01", f"https://news.example/acme-{n}", "Prensa X", "Acme",
         "ronda", "prensa", f"hash-acme-{n}", "google_news", ahora_iso()))
    exp_id = db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        ("Acme", "candidato"))
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico, enunciador_nombre, enunciador_cargo) "
        "VALUES (?,?,?,?,?)",
        (exp_id, 900 + n, "senal_primaria_autodeclaracion", "Fundador de Acme",
         "Fundador"))
    return exp_id


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


H = {"X-Ingest-Token": "secreto-123"}


def test_clara_aparece_en_verificados_antes_de_reparar(db):
    _sembrar_caso_clara_obsoleto(db)
    nombres = {c["organizacion"]
               for c in listar_candidatos_verificados(db, estado_visibilidad="todos")}
    assert "Clara" in nombres


def test_reparacion_elimina_clara_de_verificados_sin_tocar_evidencia(cli, db):
    _sembrar_caso_clara_obsoleto(db)
    _sembrar_candidato_legitimo(db)

    antes = {c["organizacion"]
             for c in listar_candidatos_verificados(db, estado_visibilidad="todos")}
    assert "Clara" in antes and "Acme" in antes

    r = cli.get(RUTA_REPARACION, params={"aplicar": "true"}, headers=H)
    assert r.status_code == 200
    assert r.json()["estado"] == "reparada"

    despues = {c["organizacion"]
               for c in listar_candidatos_verificados(db, estado_visibilidad="todos")}
    assert "Clara" not in despues, "Clara sigue apareciendo como candidato falso"
    assert "Acme" in despues, "un candidato legítimo no debe verse afectado"

    # La evidencia cruda de Clara Brugada se conserva intacta (no se borra).
    fila = db.fetch_one("SELECT id, cita_textual FROM evidencias WHERE id = ?",
                        (_EVIDENCIA_ID_CLARA_OBSOLETA,))
    assert fila is not None
    assert "Clara Brugada" in fila["cita_textual"]


def test_reparacion_es_idempotente_segunda_llamada_no_cambia_nada(cli, db):
    _sembrar_caso_clara_obsoleto(db)
    cli.get(RUTA_REPARACION, params={"aplicar": "true"}, headers=H)

    total_antes = db.fetch_one("SELECT COUNT(*) n FROM evidencia_clasificada")["n"]
    expedientes_antes = db.fetch_one("SELECT COUNT(*) n FROM expedientes_candidatos")["n"]

    r2 = cli.get(RUTA_REPARACION, params={"aplicar": "true"}, headers=H)
    assert r2.json()["estado"] == "ya_reparada"

    assert db.fetch_one("SELECT COUNT(*) n FROM evidencia_clasificada")["n"] == total_antes
    assert db.fetch_one("SELECT COUNT(*) n FROM expedientes_candidatos")["n"] == expedientes_antes
    assert "Clara" not in {c["organizacion"] for c in listar_candidatos_verificados(db)}
