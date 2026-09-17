"""Bug real 2026-09-17: la automatización de ingesta (GitHub Actions) hizo
visible en /expedientes una "tarjeta" con nombre "startup tecnológica ronda
de inversión" — el término de una consulta libre (buscador de Android o
descubrimiento por categoría), nunca una organización real. Ningún artículo
mencionaba esa frase como entidad; el titular no traía ningún nombre propio
detectable, así que `_construir_expedientes` caía en su fallback y aceptaba
`empresa_mencionada` (la consulta misma) sin verificar que fuera, ella
también, un nombre propio.

Corrección: `empresa_mencionada` solo se acepta como organización cuando
supera el mismo filtro de nombre propio (`detectar_empresa`) que ya se exige
al titular. Reutiliza la función existente; no duplica su lógica.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar_evidencia(db, *, empresa, cita_textual, categoria_query="Startup"):
    db.execute(
        """
        INSERT INTO evidencias (
            cita_textual, fecha_extraccion, url_fuente, nombre_medio,
            empresa_mencionada, tipo_evento, origen_declaracion, hash_dedup,
            fecha_publicacion, connector, estado, categoria, keywords,
            confianza, creado_en
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cita_textual, ahora_iso(), "https://ejemplo.com/nota", "Medio de Prueba",
            empresa, "queja", "prensa",
            calcular_hash_dedup(empresa, cita_textual),
            "2026-09-08", "manual_test", ESTADO_OK, categoria_query, "[]", 1.0,
            ahora_iso(),
        ),
    )


def test_frase_de_consulta_generica_no_aparece_como_organizacion(cli, db):
    """Reproduce el bug: empresa_mencionada es la consulta libre, el titular
    no menciona ninguna entidad. Debe descartarse, no aparecer como candidato."""
    _sembrar_evidencia(
        db, empresa="startup tecnológica ronda de inversión",
        cita_textual="Una firma del sector cerró una ronda para expandirse en la región",
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "startup tecnológica ronda de inversión" not in nombres

    rechazo = db.fetch_one(
        "SELECT motivo FROM rechazos WHERE connector = 'api:_construir_expedientes' "
        "ORDER BY id DESC LIMIT 1")
    assert rechazo is not None
    assert rechazo["motivo"] == "sin_empresa_deteccion"


def test_organizacion_real_sin_nombre_en_el_titular_sigue_apareciendo(cli, db):
    """Control: una organización real (nombre propio genuino) declarada en
    empresa_mencionada, con un titular que tampoco la nombra literalmente,
    debe seguir aceptándose por el fallback — el fix no debe romper el caso
    legítimo que ese fallback existe para cubrir."""
    _sembrar_evidencia(
        db, empresa="Toku",
        cita_textual="La compañía anunció una alianza estratégica en la región",
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Toku" in nombres
