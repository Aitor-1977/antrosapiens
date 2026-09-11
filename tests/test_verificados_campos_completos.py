"""Componente 7 del cierre de 15: /verificados debe devolver organización,
categoría, evidencia, fecha de publicación, persona citada y cargo — no solo
organización/tipo/cita/url/medio como hasta ahora. La categoría es la
estructural de `prospectos` (autoridad, igual que en `_construir_expedientes`),
con fallback a la categoría de la evidencia cuando no hay fila en prospectos.
"""
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


def _evidencia(db, n, org, cita, *, fecha_publicacion="2026-09-01",
              persona_citada=None, cargo=None, categoria="Startup"):
    return db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, fecha_publicacion, persona_citada, cargo, "
        "categoria, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (cita, ahora_iso(), f"https://ej.test/campos/{n}", "Prensa X", org,
         "lanzamiento", "prensa", f"hcampos{n}", "google_news",
         fecha_publicacion, persona_citada, cargo, categoria, ahora_iso()))


def _expediente(db, org, estado):
    return db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        (org, estado))


def _clasificar(db, expediente_id, evidencia_id, tipo):
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico) VALUES (?,?,?)",
        (expediente_id, evidencia_id, tipo))


def test_verificados_incluye_categoria_fecha_persona_y_cargo(db):
    exp = _expediente(db, "Acme", "candidato")
    ev = _evidencia(db, 1, "Acme", "Ana Ríos, CEO de Acme, anuncia una autodeclaración",
                     fecha_publicacion="2026-08-15", persona_citada="Ana Ríos",
                     cargo="CEO", categoria="Startup")
    _clasificar(db, exp, ev, "senal_primaria_autodeclaracion")

    item = listar_candidatos_verificados(db)[0]
    assert item["organizacion"] == "Acme"
    assert item["categoria"] == "Startup"
    assert item["cita_textual"] == "Ana Ríos, CEO de Acme, anuncia una autodeclaración"
    assert item["fecha_publicacion"] == "2026-08-15"
    assert item["persona_citada"] == "Ana Ríos"
    assert item["cargo"] == "CEO"


def test_verificados_categoria_estructural_de_prospectos_gana_sobre_la_de_evidencia(db):
    """Misma doctrina que _construir_expedientes: la categoria declarada en
    prospectos es la autoridad, no la etiqueta de la consulta que capturó la
    evidencia."""
    ahora = ahora_iso()
    db.execute(
        "INSERT INTO prospectos (nombre, categoria, escala, hash_dedup, "
        "creado_en, actualizado_en) VALUES (?,?,?,?,?,?)",
        ("Acme", "Corporativo", "indeterminada", "hash-verificados-acme", ahora, ahora))
    exp = _expediente(db, "Acme", "candidato")
    ev = _evidencia(db, 1, "Acme", "Ana Ríos, CEO de Acme, anuncia una autodeclaración",
                     categoria="Startup")
    _clasificar(db, exp, ev, "senal_primaria_autodeclaracion")

    item = listar_candidatos_verificados(db)[0]
    assert item["categoria"] == "Corporativo"


def test_verificados_persona_citada_y_cargo_ausentes_son_none_no_inventados(db):
    exp = _expediente(db, "Acme", "candidato")
    ev = _evidencia(db, 1, "Acme", "Acme publica una vacante de ingeniería",
                     persona_citada=None, cargo=None)
    _clasificar(db, exp, ev, "senal_primaria_huella_practica")

    item = listar_candidatos_verificados(db)[0]
    assert item["persona_citada"] is None
    assert item["cargo"] is None


def test_endpoint_get_verificados_expone_los_campos_nuevos(client, db):
    exp = _expediente(db, "Acme", "candidato")
    ev = _evidencia(db, 1, "Acme", "Ana Ríos, CEO de Acme, anuncia una autodeclaración",
                     fecha_publicacion="2026-08-15", persona_citada="Ana Ríos",
                     cargo="CEO", categoria="Startup")
    _clasificar(db, exp, ev, "senal_primaria_autodeclaracion")

    r = client.get("/verificados")
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["categoria"] == "Startup"
    assert item["fecha_publicacion"] == "2026-08-15"
    assert item["persona_citada"] == "Ana Ríos"
    assert item["cargo"] == "CEO"
