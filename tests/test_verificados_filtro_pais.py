"""FASE territorial (autorizada por el operador —Mario—, 2026-09-11).

Incidente detectado en FASE 0: el directorio semilla (`seed_prospectos.py`)
que alimenta INDAGAR listaba organizaciones de toda LATAM (Socialab en
Uruguay, Start-Up Chile y Toku en Chile, entre otras) sin ningún dato de país,
así que `/verificados` no tenía forma de restringir por territorio. Este test
reproduce ese hueco con el seed real (no un fixture inventado) y exige que,
tras declarar `pais` en el directorio curado, `/verificados` no devuelva
ninguna organización cuyo país declarado sea distinto de México.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.candidatos_verificados import listar_candidatos_verificados
from hd_scraper.db.models import ahora_iso
from hd_scraper.seed_prospectos import asegurar_directorio_semilla


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _evidencia(db, n, org, cita):
    return db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (cita, ahora_iso(), f"https://ej.test/pais/{n}", "Prensa X", org,
         "lanzamiento", "prensa", f"hpais{n}", "google_news", ahora_iso()))


def _expediente_candidato(db, org):
    exp_id = db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        (org, "candidato"))
    ev_id = _evidencia(db, exp_id, org, f"{org} anuncia una autodeclaración de prueba")
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico) VALUES (?,?,?)",
        (exp_id, ev_id, "senal_primaria_autodeclaracion"))
    return exp_id


def test_verificados_no_incluye_organizaciones_de_pais_distinto_a_mexico(db):
    """Reproduce el incidente real: Socialab (Uruguay), Start-Up Chile y Toku
    (Chile) son organizaciones reales del seed curado, sin filtro territorial
    hasta ahora. Con el seed sembrado, ninguna debe aparecer en /verificados;
    Kavak (México) sí."""
    asegurar_directorio_semilla(db)

    for org in ("Socialab", "Start-Up Chile", "Toku", "Kavak"):
        _expediente_candidato(db, org)

    items = listar_candidatos_verificados(db, limite=100)
    organizaciones = {i["organizacion"] for i in items}

    assert "Kavak" in organizaciones
    for org_no_mx in ("Socialab", "Start-Up Chile", "Toku"):
        assert org_no_mx not in organizaciones, (
            f"{org_no_mx!r} tiene país distinto de México en el seed y no "
            "debe aparecer en /verificados")


def test_verificados_conserva_organizacion_sin_fila_en_prospectos(db):
    """Control de no regresión: una organización que NO está en el directorio
    semilla (sin dato de país) se sigue mostrando igual que antes — la
    ausencia de país no es motivo de exclusión."""
    _expediente_candidato(db, "Acme")

    items = listar_candidatos_verificados(db)
    assert [i["organizacion"] for i in items] == ["Acme"]


def test_endpoint_get_verificados_aplica_el_filtro_territorial(cli, db):
    asegurar_directorio_semilla(db)
    _expediente_candidato(db, "Toku")
    _expediente_candidato(db, "Kavak")

    r = cli.get("/verificados", params={"limite": 100})
    assert r.status_code == 200
    organizaciones = {i["organizacion"] for i in r.json()["items"]}
    assert organizaciones == {"Kavak"}
