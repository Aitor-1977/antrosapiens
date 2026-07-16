"""Verificación de correo con Hunter (inyectando la red con fixtures)."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper import hunter
from hd_scraper.config import settings


# ── unidad: módulo hunter (sin red, http_get_json inyectado) ─────────────────

def test_disponible():
    assert hunter.disponible("clave") is True
    assert hunter.disponible("") is False


def test_email_finder_con_nombre_y_verificacion_valida():
    def fake(url):
        if "email-finder" in url:
            return {"data": {"email": "ana.ruiz@clara.com", "score": 95}}
        if "email-verifier" in url:
            return {"data": {"status": "valid", "score": 96}}
        raise AssertionError("url inesperada: " + url)
    r = hunter.enriquecer_contacto("clara.com", "Ana Ruiz", "KEY", fake)
    assert r["verificado"] is True
    assert r["email_verificado"] == "ana.ruiz@clara.com"
    assert r["status"] == "valid"


def test_domain_search_sin_nombre_elige_senior():
    def fake(url):
        if "domain-search" in url:
            return {"data": {"emails": [
                {"value": "soporte@clara.com", "position": "Support", "confidence": 80},
                {"value": "ceo@clara.com", "position": "Founder & CEO", "confidence": 70},
            ]}}
        if "email-verifier" in url:
            return {"data": {"status": "accept_all", "score": 60}}
        raise AssertionError(url)
    r = hunter.enriquecer_contacto("clara.com", "", "KEY", fake)
    assert r["email_encontrado"] == "ceo@clara.com"   # senior gana pese a menor confidence
    assert r["verificado"] is True                     # accept_all cuenta como usable


def test_correo_invalido_no_verifica():
    def fake(url):
        if "email-finder" in url:
            return {"data": {"email": "x@clara.com", "score": 10}}
        if "email-verifier" in url:
            return {"data": {"status": "invalid", "score": 5}}
        raise AssertionError(url)
    r = hunter.enriquecer_contacto("clara.com", "Ana Ruiz", "KEY", fake)
    assert r["verificado"] is False and r["email_verificado"] == ""
    assert "invalid" in r["nota"]


def test_nunca_lanza_ante_error_de_red():
    def fake(url):
        raise RuntimeError("boom cuota agotada")
    r = hunter.enriquecer_contacto("clara.com", "Ana Ruiz", "KEY", fake)
    assert r["verificado"] is False and r["status"] == "no_encontrado"


def test_sin_clave_devuelve_sin_clave():
    r = hunter.enriquecer_contacto("clara.com", "Ana Ruiz", "", lambda u: {})
    assert r["verificado"] is False and r["status"] == "sin_clave"


# ── endpoint /verificar-contacto ─────────────────────────────────────────────

@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")
    object.__setattr__(settings, "hunter_api_key", "")


H = {"X-Ingest-Token": "secreto-123"}


def test_endpoint_requiere_token(cli):
    assert cli.post("/verificar-contacto", json={"dominio": "clara.com"}).status_code == 401


def test_endpoint_sin_clave_cae_a_hipotesis(cli):
    object.__setattr__(settings, "hunter_api_key", "")
    r = cli.post("/verificar-contacto", json={"dominio": "clara.com"}, headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["modo"] == "hipotesis" and d["verificado"] is False
    assert d["hipotesis"]["email_sugerido"].endswith("@clara.com")


def test_endpoint_con_clave_verifica(cli, monkeypatch):
    object.__setattr__(settings, "hunter_api_key", "KEY")
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api.hunter, "enriquecer_contacto",
                        lambda dom, nom, key, getter: {
                            "dominio": dom, "email_verificado": "ceo@clara.com",
                            "verificado": True, "status": "valid", "nota": "ok"})
    r = cli.post("/verificar-contacto", json={"sitio_web": "https://clara.com"}, headers=H)
    assert r.status_code == 200 and r.json()["verificado"] is True
    assert r.json()["email_verificado"] == "ceo@clara.com"
