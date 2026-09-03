"""Pruebas del endpoint TEMPORAL de diagnóstico /_debug/db.

Endpoint de un solo propósito (identificar en qué etapa falla la conexión
de producción a Postgres), protegido por HD_INGEST_TOKEN vía
``Authorization: Bearer``. Estas pruebas cubren autenticación y que ningún
secreto (DSN, token) aparezca nunca en la respuesta.
"""
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


def test_sin_token_401(cli):
    r = cli.get("/_debug/db")
    assert r.status_code == 401


def test_token_incorrecto_401(cli):
    r = cli.get("/_debug/db", headers={"Authorization": "Bearer malo"})
    assert r.status_code == 401


def test_header_x_ingest_token_no_sirve_aqui(cli):
    """Este endpoint exige específicamente Authorization: Bearer, no
    X-Ingest-Token (a diferencia del resto de la API)."""
    r = cli.get("/_debug/db", headers={"X-Ingest-Token": "secreto-123"})
    assert r.status_code == 401


def test_token_correcto_devuelve_diagnostico(cli):
    r = cli.get("/_debug/db", headers={"Authorization": "Bearer secreto-123"})
    assert r.status_code == 200
    body = r.json()
    assert "variable_ganadora" in body
    assert body["variable_presente"] in ("PRESENT", "AUSENTE")
    assert "dialecto_detectado" in body
    # En el entorno de tests no hay variables de Postgres configuradas:
    # cae al fallback SQLite, así que la conexión no se prueba de verdad.
    assert body["dialecto_detectado"] == "sqlite"
    assert body["conexion"] == "N/A (dialecto no es postgres)"


def test_ningun_secreto_aparece_en_respuesta_ante_fallo_de_conexion(cli, monkeypatch):
    """DSN falsa con credenciales embebidas y host inexistente: la conexión
    debe fallar, pero ni el password ni la cadena completa pueden aparecer
    en la respuesta."""
    dsn_falsa = "postgresql://usuario_secreto:password_secreto_123@" \
                "host-que-no-existe.invalid.test:5432/basededatos"
    dsn_original = settings.database_url
    object.__setattr__(settings, "database_url", dsn_falsa)
    try:
        r = cli.get("/_debug/db", headers={"Authorization": "Bearer secreto-123"})
        assert r.status_code == 200
        body = r.json()
        assert body["dialecto_detectado"] == "postgres"
        assert body["conexion"] == "FAILED"
        assert "excepcion_conexion" in body
        texto_completo = str(body)
        assert "password_secreto_123" not in texto_completo
        assert "usuario_secreto" not in texto_completo
        assert dsn_falsa not in texto_completo
        assert "postgresql://" not in texto_completo
    finally:
        object.__setattr__(settings, "database_url", dsn_original)


def test_probar_init_schema_por_defecto_no_se_ejecuta_si_la_conexion_falla(cli):
    """Con dialecto postgres y conexión fallida, la etapa de init_schema ni
    se menciona: el endpoint corta en la etapa 4, antes de llegar ahí."""
    dsn_falsa = "postgresql://u:p@host-inexistente.invalid.test:5432/db"
    dsn_original = settings.database_url
    object.__setattr__(settings, "database_url", dsn_falsa)
    try:
        r = cli.get("/_debug/db", headers={"Authorization": "Bearer secreto-123"})
        body = r.json()
        assert body["conexion"] == "FAILED"
        assert "init_schema_y_singleton" not in body
    finally:
        object.__setattr__(settings, "database_url", dsn_original)
