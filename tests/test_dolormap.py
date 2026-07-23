"""Fase 4 — DolorMap Visual: tests de la vista consolidada por organización."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings


@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "test-tok")
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


def _insertar_evidencia(db, empresa="Acme Corp", tipo="contratacion"):
    from hd_scraper.db.models import ahora_iso
    import hashlib
    ahora = ahora_iso()
    h = hashlib.sha256(f"{empresa}|{tipo}|{ahora}".encode()).hexdigest()[:32]
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, estado, keywords, confianza, creado_en) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (f"{empresa} busca head of growth para retention", ahora,
         "https://example.com/article", "TechMedio", empresa, tipo,
         "prensa", h, "google_news", "ok",
         '["friccion_retencion","crecimiento"]', 0.7, ahora),
    )


# ── GET /dolormap/{org} ─────────────────────────────────────────────────────

def test_dolormap_sin_datos(client):
    r = client.get("/dolormap/NoExiste")
    assert r.status_code == 200
    d = r.json()
    assert d["org_nombre"] == "NoExiste"
    assert d["evidencias"]["total"] == 0
    assert d["drift"]["total_snapshots"] == 0
    assert d["onlife"]["total_señales"] == 0
    assert d["pipeline"]["etapa"] is None


def test_dolormap_con_evidencias(client, db):
    _insertar_evidencia(db)
    r = client.get("/dolormap/Acme Corp")
    assert r.status_code == 200
    d = r.json()
    assert d["org_nombre"] == "Acme Corp"
    assert d["evidencias"]["total"] >= 1
    assert d["scoring"] in ("A", "B", "C")
    assert d["tipo_deuda"] is not None or d["scoring"] == "C"


def test_dolormap_incluye_keywords(client, db):
    _insertar_evidencia(db)
    r = client.get("/dolormap/Acme Corp")
    d = r.json()
    assert "keywords" in d
    assert isinstance(d["keywords"], list)


def test_dolormap_incluye_patrones(client, db):
    _insertar_evidencia(db)
    r = client.get("/dolormap/Acme Corp")
    d = r.json()
    assert "patrones" in d
    assert isinstance(d["patrones"], list)


def test_dolormap_incluye_drift(client, db):
    _insertar_evidencia(db)
    r = client.get("/dolormap/Acme Corp")
    d = r.json()
    assert "drift" in d
    assert "total_snapshots" in d["drift"]
    assert "total_evidencias" in d["drift"]


def test_dolormap_incluye_onlife(client, db):
    _insertar_evidencia(db)
    r = client.get("/dolormap/Acme Corp")
    d = r.json()
    assert "onlife" in d
    assert "total_señales" in d["onlife"]


def test_dolormap_incluye_pipeline(client, db):
    _insertar_evidencia(db)
    r = client.get("/dolormap/Acme Corp")
    d = r.json()
    assert "pipeline" in d
    assert "etapa" in d["pipeline"]


def test_dolormap_incluye_contacto_y_links(client, db):
    _insertar_evidencia(db)
    r = client.get("/dolormap/Acme Corp")
    d = r.json()
    assert "linkedin" in d
    assert "google" in d


def test_dolormap_con_pipeline_activo(client, db):
    _insertar_evidencia(db)
    client.post("/pipeline/registrar",
                json={"org_nombre": "Acme Corp", "etapa": "vigilancia"},
                headers={"X-Ingest-Token": "test-tok"})
    r = client.get("/dolormap/Acme Corp")
    d = r.json()
    assert d["pipeline"]["etapa"] == "vigilancia"
    assert d["pipeline"]["etapa_label"] == "Vigilancia"


def test_dolormap_estructura_completa(client, db):
    _insertar_evidencia(db)
    r = client.get("/dolormap/Acme Corp")
    d = r.json()
    campos_requeridos = [
        "org_nombre", "scoring", "score_icp", "tipo_deuda",
        "deuda_razon", "intensidad", "angulo_conversacion",
        "decisor_sugerido", "keywords", "patrones",
        "evidencias", "drift", "onlife", "pipeline",
    ]
    for campo in campos_requeridos:
        assert campo in d, f"Falta campo: {campo}"
