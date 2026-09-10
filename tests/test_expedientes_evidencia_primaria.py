"""Auditoría 2026-09-10: /expedientes debe exponer quién habló (persona_citada,
cargo), no solo texto/fuente/fecha. Faltaban en la evidencia de cada expediente
aunque ya existían en la tabla `evidencias` — sin ellos la pantalla de
prospección no puede responder "¿quién habló?" (ver CLAUDE.md, contrato de
datos: persona_citada y cargo son campos opcionales del contrato)."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar_evidencia(db, *, persona_citada, cargo):
    db.execute(
        """
        INSERT INTO evidencias (
            cita_textual, fecha_extraccion, url_fuente, nombre_medio,
            empresa_mencionada, tipo_evento, origen_declaracion, hash_dedup,
            fecha_publicacion, persona_citada, cargo,
            connector, estado, categoria, keywords, confianza, creado_en
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Fintual despide al 10% de su plantilla tras ronda fallida",
            ahora_iso(), "https://ejemplo.com/nota", "Medio de Prueba",
            "Fintual", "despido", "prensa",
            calcular_hash_dedup("Fintual", "https://ejemplo.com/nota"),
            "2026-08-01", persona_citada, cargo,
            "manual_test", ESTADO_OK, "Startup", "[]", 0.9, ahora_iso(),
        ),
    )


def test_expedientes_expone_quien_hablo(cli, db):
    _sembrar_evidencia(db, persona_citada="Ana Ríos", cargo="CEO")

    r = cli.get("/expedientes", params={"categoria": "Startup", "limite": 30})
    assert r.status_code == 200
    expedientes = r.json()["expedientes"]
    assert len(expedientes) == 1
    ev = expedientes[0]["evidencias"][0]

    # Dato trazable: quién habló y con qué cargo, tal como lo declaró la fuente.
    assert ev["persona_citada"] == "Ana Ríos"
    assert ev["cargo"] == "CEO"


def test_expedientes_persona_citada_ausente_es_none_no_inventado(cli, db):
    """Regla 13 (incertidumbre): sin dato, None — nunca se completa por inferencia."""
    _sembrar_evidencia(db, persona_citada=None, cargo=None)

    r = cli.get("/expedientes", params={"categoria": "Startup", "limite": 30})
    ev = r.json()["expedientes"][0]["evidencias"][0]

    assert ev["persona_citada"] is None
    assert ev["cargo"] is None
