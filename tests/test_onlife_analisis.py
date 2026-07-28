"""Tests: paridad de forma del análisis Onlife (Cutover 1.0)."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper.onlife import analisis_onlife, _estado_onlife


def _insertar_senal(db, org, fuente="github", desc="Actividad técnica alta",
                    fecha="2026-07-01T00:00:00Z"):
    import hashlib
    import json
    h = hashlib.sha256(f"{org}{fuente}{desc}".encode()).hexdigest()
    db.execute(
        "INSERT INTO onlife_signals (org_nombre, fuente, tipo_senal, dato_json, url, "
        "descripcion, fecha_observacion, hash_dedup, creado_en) VALUES (?,?,?,?,?,?,?,?,?)",
        (org, fuente, "actividad_tech", json.dumps({}), "https://x/1", desc, fecha, h,
         ahora_iso()))


# ── función pura ─────────────────────────────────────────────────────────────

def test_sin_senales_no_detectado(db, monkeypatch):
    import hd_scraper.onlife as ol
    monkeypatch.setattr(ol, "get_db", lambda: db)
    r = analisis_onlife("Fantasma")
    assert r == {"detectado": False, "mensaje": "Sin análisis Onlife previo."}


def test_con_senales_detectado_forma_completa(db, monkeypatch):
    import hd_scraper.onlife as ol
    monkeypatch.setattr(ol, "get_db", lambda: db)
    _insertar_senal(db, "Nubank", "github")
    _insertar_senal(db, "Nubank", "hackernews", "Discusión en HN")
    r = analisis_onlife("Nubank")
    assert r["detectado"] is True
    for k in ("organizacion_id", "ico_score", "estado", "ruptura_principal",
              "capas_afectadas", "continuidad_fisica", "continuidad_digital",
              "ritual_competidor", "mediacion_social", "barrera_simbolica",
              "infraestructura", "evidencias", "hipotesis_dolormap",
              "accion_sugerida", "confidence_score", "fecha_analisis"):
        assert k in r
    # Campos de campo vacíos (Motor A no los observa): sin inventar.
    assert r["ruptura_principal"] is None
    assert r["capas_afectadas"] == {"cultural": False, "social": False,
                                    "tecnica": False, "operativa": False}
    assert r["continuidad_fisica"] == "" and r["ritual_competidor"] == ""
    assert "Actividad técnica alta" in r["evidencias"]
    assert 0 <= r["ico_score"] <= 100
    assert set(r["estado"]) == {"estado", "etiqueta", "descripcion"}


def test_estado_umbrales():
    assert _estado_onlife(85)["estado"] == "Alineado"
    assert _estado_onlife(65)["estado"] == "Fragmentado"
    assert _estado_onlife(45)["estado"] == "En conflicto"
    assert _estado_onlife(10)["estado"] == "Bloqueado"
    assert _estado_onlife(-5)["estado"] == "Bloqueado"


def test_determinista(db, monkeypatch):
    import hd_scraper.onlife as ol
    monkeypatch.setattr(ol, "get_db", lambda: db)
    _insertar_senal(db, "Kavak")
    assert analisis_onlife("Kavak") == analisis_onlife("Kavak")


# ── endpoint ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    import hd_scraper.onlife as ol
    monkeypatch.setattr(ol, "get_db", lambda: db)
    yield TestClient(api.app)


def test_endpoint_analisis_sin_datos(client):
    r = client.get("/onlife/Fantasma/analisis")
    assert r.status_code == 200 and r.json()["detectado"] is False


def test_endpoint_analisis_con_datos(client, db):
    _insertar_senal(db, "OrgOnlife", "github")
    r = client.get("/onlife/OrgOnlife/analisis")
    assert r.status_code == 200
    assert r.json()["detectado"] is True and "estado" in r.json()
