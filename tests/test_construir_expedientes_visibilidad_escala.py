"""Visibilidad de INDAGAR por escala (2026-09-20).

Mismo patrón visible/latente ya usado en `candidatos_verificados.py` para
`/verificados`, pero paralelo e independiente: aplicado aquí sobre
`_construir_expedientes` (INDAGAR, Nivel 0), sin tocar
`candidatos_verificados.py` ni `promocion_candidatos.py`. Reutiliza el MISMO
umbral ya aprobado para la penalización de score_icp
(`CAPITAL_ICP_UMBRAL_UNICORNIO`, 100 millones), sin declarar un segundo
número para la misma idea de "escala unicornio".
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup
from hd_scraper.prospectos import nuevo_prospecto, upsert_prospecto
from hd_scraper.api.app import _construir_expedientes


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar_evidencia(db, *, empresa, cita_textual):
    db.execute(
        """
        INSERT INTO evidencias (
            cita_textual, fecha_extraccion, url_fuente, nombre_medio,
            empresa_mencionada, tipo_evento, origen_declaracion, hash_dedup,
            fecha_publicacion, connector, estado, categoria, keywords,
            confianza, calidad_captura, creado_en
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cita_textual, ahora_iso(), f"https://ejemplo.com/{empresa}",
            "Medio de Prueba", empresa, "despido", "prensa",
            calcular_hash_dedup(empresa, f"https://ejemplo.com/{empresa}"),
            "2026-09-08", "manual_test", ESTADO_OK, "Startup",
            '["friccion_retencion", "reduccion_personal"]', 1.0, "Alta", ahora_iso(),
        ),
    )


def _nombres(r):
    return {e["nombre"] for e in r.json()["expedientes"]}


def test_capital_unicornio_queda_latente_por_defecto(cli, db, monkeypatch):
    upsert_prospecto(db, nuevo_prospecto("Jüsto", "Startup",
                                         capital_acumulado_usd=217_000_000))
    _sembrar_evidencia(db, empresa="Jüsto", cita_textual="Jüsto recorta personal en su segunda reestructura")
    r = cli.get("/expedientes", params={"limite": 100})  # default: estado_visibilidad="visible"
    assert "Jüsto" not in _nombres(r)


def test_capital_unicornio_reaparece_con_estado_visibilidad_todos(cli, db):
    upsert_prospecto(db, nuevo_prospecto("Nowports", "Startup",
                                         capital_acumulado_usd=210_000_000))
    _sembrar_evidencia(db, empresa="Nowports", cita_textual="Nowports recorta personal en su segunda reestructura")
    r = cli.get("/expedientes", params={"limite": 100, "estado_visibilidad": "todos"})
    assert "Nowports" in _nombres(r)
    e = next(x for x in r.json()["expedientes"] if x["nombre"] == "Nowports")
    assert e["visibilidad"] == "latente"


def test_capital_exactamente_100_millones_sigue_visible(cli, db):
    # Estrictamente mayor a 100 millones, no mayor o igual: Clara real (100
    # mdd) se mantiene visible.
    upsert_prospecto(db, nuevo_prospecto("Clara", "Startup",
                                         capital_acumulado_usd=100_000_000))
    _sembrar_evidencia(db, empresa="Clara", cita_textual="Clara despide personal tras fricción de retención")
    r = cli.get("/expedientes", params={"limite": 100})
    assert "Clara" in _nombres(r)
    e = next(x for x in r.json()["expedientes"] if x["nombre"] == "Clara")
    assert e["visibilidad"] == "visible"


def test_capital_moderado_se_mantiene_visible(cli, db):
    upsert_prospecto(db, nuevo_prospecto("Trace Finance", "Startup",
                                         capital_acumulado_usd=32_000_000))
    _sembrar_evidencia(db, empresa="Trace Finance",
                       cita_textual="Trace Finance ajusta su equipo tras fricción de retención")
    r = cli.get("/expedientes", params={"limite": 100})
    assert "Trace Finance" in _nombres(r)


def test_sin_capital_declarado_se_mantiene_visible_sin_cambios(cli, db):
    upsert_prospecto(db, nuevo_prospecto("Mundi", "Startup"))
    _sembrar_evidencia(db, empresa="Mundi", cita_textual="Mundi ajusta su equipo tras fricción de retención")
    r = cli.get("/expedientes", params={"limite": 100})
    assert "Mundi" in _nombres(r)
    e = next(x for x in r.json()["expedientes"] if x["nombre"] == "Mundi")
    assert e["visibilidad"] == "visible"
    assert e["capital_acumulado_usd"] is None


def test_llamadas_internas_sin_estado_visibilidad_ven_todo_por_defecto(cli, db):
    """Las once llamadas internas existentes a _construir_expedientes (que
    NO son INDAGAR: dashboard, comparador, observatorio, laboratorio, etc.)
    no pasan estado_visibilidad. Deben seguir viendo TODO, incluidos los
    latente, exactamente igual que antes de este cambio. `cli` ya deja
    `get_db` parcheado hacia `db`, que es lo único que
    `_construir_expedientes` necesita al llamarla directo (sin pasar por
    ninguna ruta HTTP, igual que la hacen esas once llamadas internas)."""
    upsert_prospecto(db, nuevo_prospecto("Jüsto", "Startup",
                                         capital_acumulado_usd=217_000_000))
    _sembrar_evidencia(db, empresa="Jüsto", cita_textual="Jüsto recorta personal en su segunda reestructura")

    resultado = _construir_expedientes(None, limite=500)
    nombres = {e["nombre"] for e in resultado["expedientes"]}
    assert "Jüsto" in nombres


def test_todos_incluye_visible_y_latente_juntos(cli, db):
    upsert_prospecto(db, nuevo_prospecto("Jüsto", "Startup",
                                         capital_acumulado_usd=217_000_000))
    upsert_prospecto(db, nuevo_prospecto("Palenca", "Startup",
                                         capital_acumulado_usd=6_600_000))
    _sembrar_evidencia(db, empresa="Jüsto", cita_textual="Jüsto recorta personal en su segunda reestructura")
    _sembrar_evidencia(db, empresa="Palenca", cita_textual="Palenca ajusta su equipo tras fricción de retención")
    r = cli.get("/expedientes", params={"limite": 100, "estado_visibilidad": "todos"})
    nombres = _nombres(r)
    assert {"Jüsto", "Palenca"} <= nombres
