"""Pruebas de la intake autenticada de prospectos (POST) y la pantalla /admin."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


def _payload(**over):
    base = {"nombre": "Kaszek", "categoria": "VC",
            "discurso_corporativo": "Tesis: fintech LatAm."}
    base.update(over)
    return base


def test_post_sin_token_401(cli):
    r = cli.post("/prospectos", json=_payload())
    assert r.status_code == 401


def test_post_token_malo_401(cli):
    r = cli.post("/prospectos", json=_payload(), headers={"X-Ingest-Token": "malo"})
    assert r.status_code == 401


def test_post_ok_inserta_y_actualiza(cli, db):
    h = {"X-Ingest-Token": "secreto-123"}
    r = cli.post("/prospectos", json=_payload(), headers=h)
    assert r.status_code == 201 and r.json()["accion"] == "insertado"
    # Segundo POST del mismo => upsert (actualizado), sin duplicar.
    r2 = cli.post("/prospectos", json=_payload(discurso_corporativo="v2"), headers=h)
    assert r2.json()["accion"] == "actualizado"
    assert db.fetch_one("SELECT COUNT(*) n FROM prospectos")["n"] == 1
    assert db.fetch_one("SELECT discurso_corporativo d FROM prospectos")["d"] == "v2"


def test_post_categoria_invalida_400(cli):
    h = {"X-Ingest-Token": "secreto-123"}
    r = cli.post("/prospectos", json=_payload(categoria="Fondo"), headers=h)
    assert r.status_code == 400
    assert "categoria_invalida" in r.json()["detail"]


def test_bulk(cli, db):
    h = {"X-Ingest-Token": "secreto-123"}
    lote = [_payload(nombre="Kaszek", categoria="VC"),
            _payload(nombre="Nubank", categoria="Startup"),
            _payload(nombre="X", categoria="Fondo")]  # inválido
    r = cli.post("/prospectos/bulk", json=lote, headers=h)
    assert r.status_code == 201
    d = r.json()
    assert d["total"] == 3
    acciones = {x["nombre"]: x["accion"] for x in d["resultados"]}
    assert acciones["Kaszek"] == "insertado" and acciones["X"] == "rechazado"
    assert db.fetch_one("SELECT COUNT(*) n FROM prospectos")["n"] == 2


def test_intake_deshabilitada_si_no_hay_token(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "")  # sin token => 503
    cli = TestClient(api.app)
    r = cli.post("/prospectos", json=_payload(), headers={"X-Ingest-Token": "x"})
    assert r.status_code == 503


def test_admin_sirve_formulario(cli):
    r = cli.get("/admin")
    assert r.status_code == 200
    assert "Buscar por ecosistema" in r.text   # descubrimiento por categoría
    assert "Alta de prospecto" in r.text        # sección de alta
    assert "HD_INGEST_TOKEN" in r.text
    for cat in ("VC", "Startup", "Incubadora", "Corporativo"):
        assert f'data-cat="{cat}"' in r.text
