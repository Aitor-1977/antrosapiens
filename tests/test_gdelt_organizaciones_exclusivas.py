"""Pruebas del endpoint temporal de solo lectura
GET /ops/gdelt-exclusivo-0bcd2097ddbe200e (criterio de continuidad de GDELT,
encargo de Mario 2026-09-16). Nunca escribe: agrega sobre `evidencias` para
contar organizaciones donde GDELT es la fuente más temprana de todo el
corpus.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings

RUTA = "/ops/gdelt-exclusivo-0bcd2097ddbe200e"


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


H = {"X-Ingest-Token": "secreto-123"}


def _sembrar(db, n, *, empresa, connector, creado_en):
    db.execute(
        "INSERT INTO evidencias (id, cita_textual, fecha_extraccion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, "
        "origen_declaracion, hash_dedup, connector, estado, creado_en) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (n, f"cita {n}", "2026-09-01T00:00:00+00:00", f"https://ej.test/{n}",
         "Medio X", empresa, "ronda", "prensa", f"hash-gdeltex-{n}",
         connector, "ok", creado_en))


def test_requiere_token(cli):
    assert cli.get(RUTA).status_code == 401


def test_organizacion_encontrada_primero_por_gdelt_cuenta(cli, db):
    _sembrar(db, 1, empresa="SoloGdelt", connector="gdelt",
              creado_en="2026-09-10T00:00:00+00:00")
    r = cli.get(RUTA, headers=H)
    assert r.status_code == 200
    d = r.json()
    orgs = {o["organizacion"] for o in d["organizaciones"]}
    assert "SoloGdelt" in orgs
    assert d["total_organizaciones_exclusivas_de_gdelt"] == 1


def test_organizacion_encontrada_antes_por_otro_conector_no_cuenta(cli, db):
    _sembrar(db, 1, empresa="Nowports", connector="google_news",
              creado_en="2026-09-01T00:00:00+00:00")
    _sembrar(db, 2, empresa="Nowports", connector="gdelt",
              creado_en="2026-09-10T00:00:00+00:00")
    r = cli.get(RUTA, headers=H)
    orgs = {o["organizacion"] for o in r.json()["organizaciones"]}
    assert "Nowports" not in orgs


def test_organizacion_sin_evidencia_gdelt_no_cuenta(cli, db):
    _sembrar(db, 1, empresa="SoloPrensa", connector="google_news",
              creado_en="2026-09-01T00:00:00+00:00")
    r = cli.get(RUTA, headers=H)
    orgs = {o["organizacion"] for o in r.json()["organizaciones"]}
    assert "SoloPrensa" not in orgs


def test_filtro_desde_acota_por_fecha_de_la_primera_evidencia_gdelt(cli, db):
    _sembrar(db, 1, empresa="ViejaGdelt", connector="gdelt",
              creado_en="2026-09-05T00:00:00+00:00")
    _sembrar(db, 2, empresa="NuevaGdelt", connector="gdelt",
              creado_en="2026-09-20T00:00:00+00:00")
    r = cli.get(RUTA, params={"desde": "2026-09-15T00:00:00+00:00"}, headers=H)
    orgs = {o["organizacion"] for o in r.json()["organizaciones"]}
    assert "ViejaGdelt" not in orgs
    assert "NuevaGdelt" in orgs


def test_nunca_escribe_nada(cli, db):
    _sembrar(db, 1, empresa="X", connector="gdelt", creado_en="2026-09-10T00:00:00+00:00")
    antes = db.fetch_one("SELECT COUNT(*) n FROM evidencias")["n"]
    cli.get(RUTA, headers=H)
    despues = db.fetch_one("SELECT COUNT(*) n FROM evidencias")["n"]
    assert antes == despues
