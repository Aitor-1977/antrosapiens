"""Pruebas del endpoint temporal de solo lectura
GET /ops/diag-conector-mundi-3381536e7e77d2de (encargo de Mario 2026-09-20).
Nunca escribe: solo expone el campo `connector` de TODAS las evidencias de
"Mundi", para decidir el alcance de la Guardia 2 de identidad.

Primera versión de este endpoint filtraba por `cita_textual` exacto y no
devolvía nada en producción real: el valor real incluye el sufijo del medio
("El fuego del ébola - Substack"), distinto del texto sin sufijo usado en el
filtro. Corregido a devolver TODAS las evidencias de la organización, sin
depender de un match exacto de texto — `test_no_depende_de_match_exacto_de_texto`
reproduce exactamente ese bug.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from hd_scraper.db.models import ahora_iso, calcular_hash_dedup

RUTA = "/ops/diag-conector-mundi-3381536e7e77d2de"


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


H = {"X-Ingest-Token": "secreto-123"}


def _sembrar(db, n, *, cita_textual, connector, empresa="Mundi"):
    db.execute(
        "INSERT INTO evidencias (id, cita_textual, fecha_extraccion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, "
        "origen_declaracion, hash_dedup, connector, estado, creado_en) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (n, cita_textual, ahora_iso(), f"https://ej.test/{n}", "Medio X",
         empresa, "ronda", "prensa", calcular_hash_dedup(empresa, cita_textual),
         connector, "ok", ahora_iso()))


def test_requiere_token(cli):
    assert cli.get(RUTA).status_code == 401


def test_expone_connector_de_las_3_evidencias_conocidas(cli, db):
    _sembrar(db, 1, cita_textual="El fuego del ébola", connector="busqueda_dinamica_founder")
    _sembrar(db, 2, cita_textual="15 años de una promesa fallida", connector="busqueda_dinamica_founder")
    _sembrar(db, 3, cita_textual="Un fondo para subirse a la nueva ola tecnológica",
             connector="busqueda_dinamica_founder")

    r = cli.get(RUTA, headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 3
    conectores = {ev["connector"] for ev in d["evidencias"]}
    assert conectores == {"busqueda_dinamica_founder"}


def test_no_incluye_evidencias_de_otras_organizaciones(cli, db):
    _sembrar(db, 1, cita_textual="El fuego del ébola - Substack", connector="busqueda_dinamica_founder")
    _sembrar(db, 2, cita_textual="Mundi anuncia una ronda de inversión", connector="google_news")
    _sembrar(db, 3, cita_textual="El fuego del ébola - Substack", connector="gdelt", empresa="Acme")

    r = cli.get(RUTA, headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 2
    conectores = {ev["connector"] for ev in d["evidencias"]}
    assert conectores == {"busqueda_dinamica_founder", "google_news"}


def test_no_depende_de_match_exacto_de_texto(cli, db):
    """Reproduce el bug real de la primera versión: el texto real incluye el
    sufijo del medio, distinto del texto 'limpio' que se conocía de
    antemano. El endpoint debe encontrar la fila de todas formas."""
    _sembrar(db, 1, cita_textual="El fuego del ébola - Substack",
             connector="busqueda_dinamica_founder")

    r = cli.get(RUTA, headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 1
    assert d["evidencias"][0]["cita_textual"] == "El fuego del ébola - Substack"
