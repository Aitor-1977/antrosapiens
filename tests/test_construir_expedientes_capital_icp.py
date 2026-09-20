"""Penalización por escala excesiva del ICP en /expedientes (2026-09-20).

Caso real que motivó el ajuste: Jüsto (ICP 99) y Nowports (ICP 94) son
unicornios o cercanos, con capital acumulado muy por encima de la ventana de
intervención de HD (Seed a Serie A, 1.5 a 10 millones de dólares), pero
score_icp nunca miraba el capital: solo medía profundidad de señal y encaje
de vertical. `capital_acumulado_usd` es un campo DECLARADO por el operador en
`prospectos` (nunca inferido de texto libre); sin declararlo, /expedientes se
comporta exactamente igual que antes de este cambio.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup
from hd_scraper.prospectos import nuevo_prospecto, upsert_prospecto


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar_evidencia(db, *, empresa, cita_textual, n=1):
    for i in range(n):
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
                f"{cita_textual} ({i})", ahora_iso(), f"https://ejemplo.com/{empresa}/{i}",
                "Medio de Prueba", empresa, "despido", "prensa",
                calcular_hash_dedup(empresa, f"https://ejemplo.com/{empresa}/{i}"),
                "2026-09-08", "manual_test", ESTADO_OK, "Startup",
                '["friccion_retencion", "reduccion_personal"]', 1.0, "Alta", ahora_iso(),
            ),
        )


def _score_icp_de(cli, nombre):
    r = cli.get("/expedientes", params={"limite": 100})
    for e in r.json()["expedientes"]:
        if e["nombre"] == nombre:
            return e
    return None


def test_sin_capital_declarado_expediente_no_cambia(cli, db):
    """Control de no regresión: una organización sin capital_acumulado_usd
    declarado en prospectos se comporta exactamente igual que antes."""
    upsert_prospecto(db, nuevo_prospecto("Palenca", "Startup"))
    _sembrar_evidencia(db, empresa="Palenca", cita_textual="Palenca despide personal tras fricción de retención")
    e = _score_icp_de(cli, "Palenca")
    assert e is not None
    assert e["capital_acumulado_usd"] is None
    assert e["score_icp"] > 55  # sin penalizar, sigue alto por señal de dolor real


def test_organizacion_unicornio_con_capital_declarado_baja_a_20(cli, db):
    """Reproduce el caso real: unicornio con señales de dolor genuinas, pero
    muy por encima de la ventana de HD. Con capital_acumulado_usd declarado,
    el score_icp queda topado a 20, sin importar cuánta señal de dolor haya."""
    upsert_prospecto(db, nuevo_prospecto("Jüsto", "Startup",
                                         capital_acumulado_usd=217_000_000))
    _sembrar_evidencia(db, empresa="Jüsto", cita_textual="Jüsto recorta personal en su segunda reestructura")
    e = _score_icp_de(cli, "Jüsto")
    assert e is not None
    assert e["capital_acumulado_usd"] == 217_000_000
    assert e["score_icp"] == 20


def test_organizacion_con_capital_moderado_baja_a_55(cli, db):
    """Trace Finance: capital real por encima de la ventana (32 millones)
    pero lejos de escala unicornio. Queda en la banda intermedia (55), por
    encima de cualquier unicornio, nunca peor."""
    upsert_prospecto(db, nuevo_prospecto("Trace Finance", "Startup",
                                         capital_acumulado_usd=32_000_000))
    _sembrar_evidencia(db, empresa="Trace Finance",
                       cita_textual="Trace Finance ajusta su equipo tras fricción de retención")
    e = _score_icp_de(cli, "Trace Finance")
    assert e is not None
    assert e["score_icp"] == 55


def test_organizacion_dentro_de_la_ventana_hd_no_se_penaliza(cli, db):
    """Palenca con capital declarado pero DENTRO de la ventana de HD
    (menor al techo de 15 millones): no se penaliza."""
    upsert_prospecto(db, nuevo_prospecto("Palenca", "Startup",
                                         capital_acumulado_usd=6_600_000))
    _sembrar_evidencia(db, empresa="Palenca", cita_textual="Palenca ajusta su equipo tras fricción de retención")
    e = _score_icp_de(cli, "Palenca")
    assert e is not None
    assert e["score_icp"] > 55


def test_unicornio_declarado_queda_mejor_posicionado_relativo_a_otro_unicornio_no(cli, db):
    """Verificación explícita pedida por el operador: tras el ajuste, una
    organización con capital moderado (Trace Finance) nunca queda peor
    posicionada que un unicornio (Jüsto) con el mismo patrón de señales."""
    upsert_prospecto(db, nuevo_prospecto("Jüsto", "Startup",
                                         capital_acumulado_usd=217_000_000))
    upsert_prospecto(db, nuevo_prospecto("Trace Finance", "Startup",
                                         capital_acumulado_usd=32_000_000))
    _sembrar_evidencia(db, empresa="Jüsto", cita_textual="Jüsto recorta personal en su segunda reestructura")
    _sembrar_evidencia(db, empresa="Trace Finance",
                       cita_textual="Trace Finance ajusta su equipo tras fricción de retención")
    justo = _score_icp_de(cli, "Jüsto")
    trace = _score_icp_de(cli, "Trace Finance")
    assert trace["score_icp"] >= justo["score_icp"]
