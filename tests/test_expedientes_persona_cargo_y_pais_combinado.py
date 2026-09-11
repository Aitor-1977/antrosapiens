"""Componente 8 del cierre de 15: /expedientes debe devolver persona_citada
y cargo POR EVIDENCIA, con el mismo filtro territorial por país ya aplicado
en /verificados, y ambas propiedades deben sostenerse EN LA MISMA LLAMADA
(no solo por separado, que es lo que ya cubrían test_expedientes_evidencia_primaria.py
y test_expedientes_filtro_pais.py): una organización excluida por país no
debe aparecer en absoluto (con o sin persona_citada), y una organización
mexicana incluida debe traer persona_citada/cargo intactos.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup
from hd_scraper.seed_prospectos import asegurar_directorio_semilla


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar(db, *, empresa, cita_textual, persona_citada=None, cargo=None,
            categoria_query="Startup"):
    db.execute(
        """
        INSERT INTO evidencias (
            cita_textual, fecha_extraccion, url_fuente, nombre_medio,
            empresa_mencionada, tipo_evento, origen_declaracion, hash_dedup,
            fecha_publicacion, persona_citada, cargo, connector, estado,
            categoria, keywords, confianza, creado_en
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            cita_textual, ahora_iso(), f"https://ejemplo.com/{empresa.lower()}",
            "Medio de Prueba", empresa, "queja", "prensa",
            calcular_hash_dedup(empresa, cita_textual), "2026-09-11",
            persona_citada, cargo, "manual_test", ESTADO_OK, categoria_query,
            "[]", 1.0, ahora_iso(),
        ),
    )


def test_expedientes_combina_persona_cargo_y_filtro_territorial(cli, db):
    asegurar_directorio_semilla(db)

    # Toku (Chile, seed): con persona_citada/cargo declarados. Debe quedar
    # EXCLUIDO por país, pese a traer datos de atribución completos — el
    # filtro territorial actúa sobre la organización, no sobre si la
    # evidencia trae o no persona_citada.
    _sembrar(db, empresa="Toku",
             cita_textual="La compañía anuncia una nueva ronda de financiamiento",
             persona_citada="Rodrigo Tapia", cargo="CEO")

    # Kavak (México, seed, reclasificado a Corporativo): sin persona_citada
    # declarada — debe aparecer con persona_citada/cargo en None (nunca
    # inventados) y sí debe pasar el filtro territorial.
    _sembrar(db, empresa="Kavak",
             cita_textual="La empresa despide al 10% de su plantilla en reestructuración")

    r = cli.get("/expedientes", params={"limite": 100})
    assert r.status_code == 200
    expedientes = {e["nombre"]: e for e in r.json()["expedientes"]}

    assert "Toku" not in expedientes, (
        "Toku (Chile) no debe aparecer en /expedientes aunque traiga "
        "persona_citada/cargo declarados")

    assert "Kavak" in expedientes
    ev_kavak = expedientes["Kavak"]["evidencias"][0]
    assert ev_kavak["persona_citada"] is None
    assert ev_kavak["cargo"] is None


def test_expedientes_organizacion_mexicana_con_atribucion_expone_persona_y_cargo(cli, db):
    """cita_textual deliberadamente sin ningún token capitalizado detectable
    (mismo criterio que test_gigantes_categoria.py): aísla este caso de
    detectar_empresa(), que si el titular nombrara "Ana Ríos, CEO de Kavak"
    detectaría "Ana" como organización (limitación preexistente y ajena a
    este componente) en vez de usar empresa_mencionada='Kavak'."""
    asegurar_directorio_semilla(db)

    _sembrar(db, empresa="Kavak",
             cita_textual="la empresa despide al 10% de su plantilla en una reestructuración interna",
             persona_citada="Ana Ríos", cargo="CEO")

    r = cli.get("/expedientes", params={"limite": 100})
    expedientes = {e["nombre"]: e for e in r.json()["expedientes"]}

    assert "Kavak" in expedientes
    ev = expedientes["Kavak"]["evidencias"][0]
    assert ev["persona_citada"] == "Ana Ríos"
    assert ev["cargo"] == "CEO"
