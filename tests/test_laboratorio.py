"""Tests: Sistema Operativo del Laboratorio (Capa 18) — dashboard maestro."""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper.laboratorio import (
    CAPAS,
    estado_capas,
    estado_corpus,
    estado_general,
    estado_gobernanza,
    estado_observatorio,
    estado_pipeline,
    estado_validacion,
)


def _exp(nombre="A", veredicto="VALIDADA", bloqueada=False, keywords=None,
         tipo_deuda="Deuda Relacional"):
    return {
        "nombre": nombre, "vertical": "fintech", "score_icp": 70,
        "tipo_deuda": tipo_deuda, "hipotesis_bloqueada": bloqueada,
        "keywords": keywords or ["friccion_retencion"],
        "patrones": [{"patron": "P1"}], "total_evidencias": 3,
        "validacion_cientifica": {"veredicto": veredicto},
    }


# ── estado_capas ──────────────────────────────────────────────────────────────

def test_estado_capas():
    ec = estado_capas()
    assert ec["total"] == len(CAPAS) == 19
    assert ec["operativas"] == 19
    assert ec["capas"][0]["numero"] == 0
    assert ec["capas"][-1]["nombre"] == "Sistema Operativo del Laboratorio"
    assert all(c["estado"] == "operativa" for c in ec["capas"])


# ── estado_corpus ─────────────────────────────────────────────────────────────

def test_estado_corpus():
    c = estado_corpus({"evidencias_total": 10, "evidencias_ok": 8,
                       "evidencias_no_fechado": 2, "rechazos": 1, "prospectos": 5})
    assert c["tasa_consumible"] == 0.8
    assert c["estado"] == "poblado"


def test_estado_corpus_vacio():
    c = estado_corpus({})
    assert c["estado"] == "vacio" and c["tasa_consumible"] == 0.0


# ── estado_pipeline ───────────────────────────────────────────────────────────

def test_estado_pipeline():
    p = estado_pipeline({"jobs": 3, "pipeline_comercial": 2})
    assert p["jobs"] == 3 and p["estado"] == "activo"
    assert "Motor C" in p["nota"]


# ── estado_validacion ─────────────────────────────────────────────────────────

def test_estado_validacion():
    exps = [_exp("A", "VALIDADA"), _exp("B", "BLOQUEADA", bloqueada=True)]
    v = estado_validacion(exps)
    assert v["expedientes"] == 2
    assert v["distribucion_veredicto"]["VALIDADA"] == 1
    assert v["hipotesis_bloqueadas"] == 1
    assert v["tasa_bloqueo"] == 0.5


def test_estado_validacion_vacio():
    assert estado_validacion([])["tasa_bloqueo"] == 0.0


# ── estado_gobernanza ─────────────────────────────────────────────────────────

def test_estado_gobernanza():
    g = estado_gobernanza({"huellas": 5, "certificados": 4, "auditorias": 3,
                           "memoria": 2, "bitacora": 20})
    assert g["huellas_digitales"] == 5 and g["estado"] == "auditable"
    assert g["versiones_memoria"] == 2


# ── estado_observatorio ───────────────────────────────────────────────────────

def test_estado_observatorio():
    o = estado_observatorio([_exp("A"), _exp("B")])
    assert o["indicadores"]["organizaciones"] == 2
    assert "tensiones" in o


# ── estado_general ────────────────────────────────────────────────────────────

def test_estado_general():
    corpus = estado_corpus({"evidencias_total": 10, "evidencias_ok": 9})
    val = estado_validacion([_exp("A")])
    gob = estado_gobernanza({"certificados": 4, "memoria": 2})
    obs = estado_observatorio([_exp("A")])
    g = estado_general(corpus, val, gob, obs)
    assert g["estado"] == "operativo"
    assert g["motores"]["A"].startswith("operativo")
    assert "B" in g["motores"] and "C" in g["motores"]
    assert g["resumen"]["evidencias"] == 10
    assert g["resumen"]["certificados"] == 4


def test_estado_general_reproducible():
    corpus = estado_corpus({"evidencias_total": 5})
    val = estado_validacion([_exp("A")])
    gob = estado_gobernanza({})
    obs = estado_observatorio([_exp("A")])
    assert estado_general(corpus, val, gob, obs) == estado_general(corpus, val, gob, obs)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, empresa, url, medio, keywords):
    import hashlib
    h = hashlib.sha256(f"{empresa}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{empresa} enfrenta fricción", ahora_iso(), "2026-07-01", url, medio, empresa,
         "queja", "prensa", h, "google_news", _json.dumps(keywords), 0.8, "Alta",
         "Startup", "ok", ahora_iso()))


def test_endpoint_laboratorio(client, db):
    _insertar(db, "Lab", "https://l.com/1", "M1", ["friccion_retencion"])
    r = client.get("/laboratorio")
    assert r.status_code == 200
    data = r.json()
    for clave in ("general", "capas", "corpus", "pipeline", "validacion",
                  "gobernanza", "observatorio"):
        assert clave in data
    assert data["capas"]["total"] == 19
    assert data["corpus"]["evidencias_total"] >= 1


def test_endpoint_estado(client, db):
    _insertar(db, "Est", "https://e.com/1", "M1", ["friccion_retencion"])
    r = client.get("/estado")
    assert r.status_code == 200
    assert r.json()["estado"] == "operativo"


def test_endpoint_dashboard_html(client, db):
    _insertar(db, "Dash", "https://d.com/1", "M1", ["friccion_retencion"])
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Sistema Operativo del Laboratorio" in r.text
    assert "Motores" in r.text and "Capas" in r.text
