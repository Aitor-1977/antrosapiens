"""Lectura de candidatos verificados para la app (proyección de Entrega 3)."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.candidatos_verificados import listar_candidatos_verificados
from hd_scraper.db.models import ahora_iso


@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _evidencia(db, n, org, cita):
    return db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (cita, ahora_iso(), f"https://ej.test/{n}", "Prensa X", org,
         "lanzamiento", "prensa", f"hcv{n}", "google_news", ahora_iso()))


def _expediente(db, org, estado):
    return db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        (org, estado))


def _clasificar(db, expediente_id, evidencia_id, tipo):
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico) VALUES (?,?,?)",
        (expediente_id, evidencia_id, tipo))


def test_solo_lista_expedientes_en_estado_candidato(db):
    exp_candidato = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp_candidato, _evidencia(db, 1, "Acme", "cita 1"),
                "senal_primaria_autodeclaracion")

    exp_abierto = _expediente(db, "Beta", "abierto")
    _clasificar(db, exp_abierto, _evidencia(db, 2, "Beta", "cita 2"),
                "senal_primaria_autodeclaracion")

    items = listar_candidatos_verificados(db)
    assert [i["organizacion"] for i in items] == ["Acme"]


def test_incluye_la_cita_textual_de_la_evidencia_primaria(db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "Juan Pérez, CEO de Acme"),
                "senal_primaria_huella_practica")

    item = listar_candidatos_verificados(db)[0]
    assert item["cita_textual"] == "Juan Pérez, CEO de Acme"
    assert item["tipo_epistemologico"] == "senal_primaria_huella_practica"
    assert item["url_fuente"] == "https://ej.test/1"


def test_ignora_evidencia_no_primaria_del_mismo_expediente(db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "cita contextual"), "contextual")
    _clasificar(db, exp, _evidencia(db, 2, "Acme", "cita primaria"),
                "senal_primaria_autodeclaracion")

    item = listar_candidatos_verificados(db)[0]
    assert item["cita_textual"] == "cita primaria"


def test_prioriza_autodeclaracion_sobre_huella_practica(db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "huella practica"),
                "senal_primaria_huella_practica")
    _clasificar(db, exp, _evidencia(db, 2, "Acme", "autodeclaracion"),
                "senal_primaria_autodeclaracion")

    item = listar_candidatos_verificados(db)[0]
    assert item["tipo_epistemologico"] == "senal_primaria_autodeclaracion"
    assert item["cita_textual"] == "autodeclaracion"


def test_candidato_sin_evidencia_primaria_localizable_se_omite(db):
    """No debería pasar dado cómo promueve Entrega 3, pero si pasa, no se
    inventa una tarjeta vacía: se omite."""
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "solo contextual"), "contextual")

    assert listar_candidatos_verificados(db) == []


def test_respeta_el_limite(db):
    for i, org in enumerate(("Acme", "Beta", "Gamma"), start=1):
        exp = _expediente(db, org, "candidato")
        _clasificar(db, exp, _evidencia(db, i, org, f"cita {org}"),
                    "senal_primaria_autodeclaracion")

    assert len(listar_candidatos_verificados(db, limite=2)) == 2


def test_orden_alfabetico_por_organizacion(db):
    for org in ("Zeta", "Acme", "Mambo"):
        exp = _expediente(db, org, "candidato")
        _clasificar(db, exp, _evidencia(db, org, org, f"cita {org}"),
                    "senal_primaria_autodeclaracion")

    items = listar_candidatos_verificados(db)
    assert [i["organizacion"] for i in items] == ["Acme", "Mambo", "Zeta"]


# ── Endpoint HTTP ────────────────────────────────────────────────────────

def test_endpoint_get_verificados(client, db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "Juan Pérez, CEO de Acme"),
                "senal_primaria_autodeclaracion")

    r = client.get("/verificados")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["organizacion"] == "Acme"
    assert body["items"][0]["cita_textual"] == "Juan Pérez, CEO de Acme"


def test_endpoint_get_verificados_vacio_sin_candidatos(client, db):
    r = client.get("/verificados")
    assert r.status_code == 200
    assert r.json() == {"total": 0, "items": []}


def test_endpoint_get_verificados_respeta_limite(client, db):
    for i, org in enumerate(("Acme", "Beta", "Gamma"), start=1):
        exp = _expediente(db, org, "candidato")
        _clasificar(db, exp, _evidencia(db, i, org, f"cita {org}"),
                    "senal_primaria_autodeclaracion")

    r = client.get("/verificados", params={"limite": 2})
    assert r.status_code == 200
    assert r.json()["total"] == 2
