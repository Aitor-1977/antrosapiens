"""Fallback ante Postgres/Neon no disponible (2026-09-11).

Diagnóstico en producción: bajo cierto tráfico, `Database._connect_postgres`
agota sus reintentos y lanza `psycopg.OperationalError` (cold-start de Neon
tras suspender el cómputo, o agotamiento momentáneo de conexiones). Sin un
manejador dedicado, esa excepción sin capturar se convertía en un 500
genérico de FastAPI, o dejaba al cliente esperando hasta su propio timeout
sin ninguna señal útil. `hd_scraper/api/app.py` ahora registra un
`exception_handler` que la traduce a un 503 rápido con `Retry-After`, para
que el cliente (la app Android, que ya reintenta una vez) sepa que debe
reintentar en segundos en vez de asumir que algo está roto.
"""
import importlib

import psycopg
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def test_operational_error_se_traduce_a_503_con_retry_after(cli, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")

    def _falla(*a, **kw):
        raise psycopg.OperationalError("connection failed: timeout expired")

    monkeypatch.setattr(api, "get_db", _falla)
    r = cli.get("/health")
    assert r.status_code == 503
    assert r.headers.get("retry-after") == "5"
    assert "no disponible" in r.json()["detail"].lower()


def test_conexion_sana_no_se_ve_afectada(cli):
    r = cli.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
