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


def test_forma_del_valor_diagnostica_sin_filtrar_el_contenido(cli):
    """Simula el escenario ya visto antes en esta sesión: un comando de
    shell (con el secreto real embebido) pegado por error en el campo del
    valor. La 'forma' debe detectarlo (longitud grande, contiene 'export'/
    'python', saltos de línea) sin que el secreto en sí aparezca nunca."""
    valor_pegado_por_error = (
        "export HD_DATABASE_URL=postgres://usuario_real:clave_real_xyz@"
        "ep-real-host.neon.tech/db\npython -m scripts.clasificar_evidencia --aplicar"
    )
    dsn_original = settings.database_url
    object.__setattr__(settings, "database_url", valor_pegado_por_error)
    try:
        r = cli.get("/_debug/db", headers={"Authorization": "Bearer secreto-123"})
        assert r.status_code == 200
        body = r.json()
        assert body["dialecto_detectado"] == "unknown"
        forma = body["forma_del_valor"]
        assert forma["longitud"] == len(valor_pegado_por_error)
        assert forma["contiene_saltos_de_linea"] is True
        assert forma["contiene_signo_igual"] is True
        assert forma["contiene_esquema_en_algun_lugar"] is True
        assert forma["empieza_con_postgres_tras_recortar_espacios"] is False
        assert forma["contiene_palabra_export"] is True
        assert forma["contiene_palabra_python"] is True
        # Ni el secreto ni el DSN completo aparecen en ningún lado.
        texto_completo = str(body)
        assert "clave_real_xyz" not in texto_completo
        assert "usuario_real" not in texto_completo
        assert "ep-real-host" not in texto_completo
        assert valor_pegado_por_error not in texto_completo
    finally:
        object.__setattr__(settings, "database_url", dsn_original)


def test_forma_del_valor_no_aparece_cuando_el_dialecto_es_postgres(cli):
    """El bloque forma_del_valor es solo para el caso 'unknown'/'sqlite':
    cuando el dialecto SÍ es postgres, ya sabemos que empieza con el
    esquema correcto y no hace falta diagnosticar la forma."""
    dsn_falsa = "postgresql://u:p@host-inexistente.invalid.test:5432/db"
    dsn_original = settings.database_url
    object.__setattr__(settings, "database_url", dsn_falsa)
    try:
        r = cli.get("/_debug/db", headers={"Authorization": "Bearer secreto-123"})
        body = r.json()
        assert body["dialecto_detectado"] == "postgres"
        assert "forma_del_valor" not in body
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
