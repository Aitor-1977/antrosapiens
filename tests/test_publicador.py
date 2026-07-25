"""Tests: Publicador Científico (Capa 17) — documentos desde evidencia validada."""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper.validacion_cientifica import validar_expediente
from hd_scraper.gobernanza import emitir_certificado, generar_huella_digital
from hd_scraper.publicador import (
    firmar_documento,
    generar_csv,
    generar_html,
    generar_informe,
    generar_json,
    generar_pdf,
    generar_peritaje,
)


def _ev(url="https://a.com/1", fuente="Medio A", fecha="2026-07-01", tipo="queja"):
    return {"url": url, "fuente": fuente, "fecha": fecha, "tipo_evento": tipo,
            "confianza": 0.8, "texto": "fricción y churn de clientes"}


def _exp(tipo_deuda="Deuda Relacional", scoring="A", evs=None, keywords=None):
    return {
        "nombre": "Nubank", "vertical": "fintech", "scoring": scoring,
        "score_icp": 80, "profundidad_dolor": 90, "viabilidad": "alta",
        "tipo_deuda": tipo_deuda, "deuda_razon": "fricción",
        "keywords": keywords or ["friccion_retencion", "reduccion_personal"],
        "patrones": [{"patron": "x", "razonamiento": "y", "senales": []}],
        "evidencias": evs or [
            _ev("https://a.com/1", "A"), _ev("https://b.com/2", "B", tipo="despido"),
            _ev("https://c.com/3", "C")],
    }


def _peritaje(exp=None, fecha="2026-07-25"):
    exp = exp or _exp()
    val = validar_expediente(exp)
    huella = generar_huella_digital(exp, val, fecha)
    cert = emitir_certificado(exp, val, huella, fecha)
    return generar_peritaje(exp, val, huella, cert)


# ── generar_peritaje ──────────────────────────────────────────────────────────

def test_peritaje_validado_publicable():
    p = _peritaje()
    assert p["publicable"] is True
    assert p["veredicto"] in ("VALIDADA", "VALIDADA_PARCIAL")
    assert p["evidencias"] and p["firma"].startswith("AS-MOTORA::")
    assert "anexo_metodologico" in p


def test_peritaje_no_publicable_si_bloqueado():
    p = _peritaje(_exp(evs=[_ev()]))  # una sola fuente ⇒ bloqueada
    assert p["publicable"] is False
    assert p["limitaciones"]


def test_peritaje_hash_reproducible():
    a = _peritaje(fecha="2000-01-01")
    b = _peritaje(fecha="2099-12-31")
    assert a["hash"] == b["hash"]
    assert a["firma"] == b["firma"]  # la fecha no entra en el hash ni la firma


# ── firmar_documento ──────────────────────────────────────────────────────────

def test_firmar_documento_determinista():
    doc = {"veredicto": "VALIDADA", "x": 1}
    assert firmar_documento(doc) == firmar_documento(doc)
    assert firmar_documento({"veredicto": "VALIDADA", "x": 2}) != firmar_documento(doc)


# ── formatos ──────────────────────────────────────────────────────────────────

def test_generar_json():
    p = _peritaje()
    assert generar_json(p) == p


def test_peritaje_acepta_evidencias_forma_dolormap():
    exp = _exp()
    exp["evidencias"] = {"total": 1, "items": [_ev()]}
    p = _peritaje(exp)
    assert len(p["evidencias"]) == 1


def test_generar_csv():
    csv_txt = generar_csv(_peritaje())
    assert csv_txt.startswith("org,fuente,fecha,url,texto")
    assert "Nubank" in csv_txt
    assert len(csv_txt.strip().splitlines()) == 4  # cabecera + 3 evidencias


def test_generar_html():
    html = generar_html(_peritaje())
    assert "<!doctype html>" in html
    assert "Peritaje Antropológico" in html
    assert "Nubank" in html


def test_generar_pdf():
    pdf = generar_pdf(_peritaje())
    assert "@page" in pdf and "Peritaje Antropológico" in pdf


# ── generar_informe ───────────────────────────────────────────────────────────

def test_generar_informe():
    inf = generar_informe([_exp(), _exp()], titulo="Informe Test", vertical="fintech")
    assert inf["tipo"] == "informe_cientifico"
    assert inf["total_organizaciones"] == 2
    assert "dictamen" in inf and inf["firma"].startswith("AS-MOTORA::")


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
        (f"{empresa} enfrenta fricción y churn", ahora_iso(), "2026-07-01", url, medio,
         empresa, "queja", "prensa", h, "google_news", _json.dumps(keywords), 0.8,
         "Alta", "Startup", "ok", ahora_iso()))


def test_endpoint_peritaje_json_csv_html(client, db):
    for i, m in enumerate(["Medio A", "Medio B", "Medio C"]):
        _insertar(db, "Pub", f"https://p{i}.com/1", m, ["friccion_retencion", "reduccion_personal"])
    rj = client.get("/publicar/peritaje/Pub")
    assert rj.status_code == 200 and rj.json()["org"] == "Pub"
    rc = client.get("/publicar/peritaje/Pub", params={"formato": "csv"})
    assert rc.status_code == 200 and "text/csv" in rc.headers["content-type"]
    rh = client.get("/publicar/peritaje/Pub", params={"formato": "html"})
    assert rh.status_code == 200 and "Peritaje Antropológico" in rh.text


def test_endpoint_informe(client, db):
    _insertar(db, "Inf", "https://i.com/1", "M1", ["friccion_retencion"])
    r = client.get("/publicar/informe/Inf")
    assert r.status_code == 200 and r.json()["tipo"] == "informe_cientifico"


def test_endpoint_pdf(client, db):
    _insertar(db, "Pdf", "https://d.com/1", "M1", ["friccion_retencion"])
    r = client.get("/publicar/pdf/Pdf")
    assert r.status_code == 200 and "@page" in r.text
