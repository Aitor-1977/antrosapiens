"""FASE territorial, extensión a /expedientes (autorizada por el operador
—Mario—, 2026-09-11). Mismo criterio ya aplicado en /verificados
(`candidatos_verificados.listar_candidatos_verificados`): excluye
organizaciones cuyo `prospectos.pais` (resuelto por nombre exacto) esté
declarado y no sea México; una organización sin fila en `prospectos` (país
desconocido) no se excluye.
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


def _sembrar_evidencia(db, *, empresa, cita_textual, categoria_query="Startup"):
    """Mismo patrón que test_gigantes_categoria.py: cita_textual deliberadamente
    sin el nombre de la organización (ni otro token capitalizado detectable),
    para aislar el filtro territorial de detectar_empresa()/evaluar_relevancia
    y probar solo la corrección nueva (país resuelto en _construir_expedientes)."""
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
            cita_textual, ahora_iso(), f"https://ejemplo.com/{empresa.lower()}",
            "Medio de Prueba", empresa, "queja", "prensa",
            calcular_hash_dedup(empresa, cita_textual),
            "2026-09-11", "manual_test", ESTADO_OK, categoria_query, "[]", 1.0,
            ahora_iso(),
        ),
    )


def test_expedientes_no_incluye_organizaciones_de_pais_distinto_a_mexico(cli, db):
    """Reproduce el incidente real (mismo que en /verificados): Toku, Socialab
    y Start-Up Chile son organizaciones reales del seed curado, con país
    declarado distinto de México. No deben aparecer en /expedientes; Kavak
    (México) sí."""
    asegurar_directorio_semilla(db)

    _sembrar_evidencia(db, empresa="Toku",
                        cita_textual="La compañía anuncia una nueva ronda de financiamiento")
    _sembrar_evidencia(db, empresa="Socialab",
                        cita_textual="La organización lanza un nuevo programa de innovación")
    _sembrar_evidencia(db, empresa="Start-Up Chile",
                        cita_textual="El programa anuncia su nueva convocatoria")
    _sembrar_evidencia(db, empresa="Kavak",
                        cita_textual="La empresa despide al 10% de su plantilla en reestructuración",
                        categoria_query="Startup")

    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}

    assert "Kavak" in nombres
    for org_no_mx in ("Toku", "Socialab", "Start-Up Chile"):
        assert org_no_mx not in nombres, (
            f"{org_no_mx!r} tiene país distinto de México en el seed y no "
            "debe aparecer en /expedientes")


def test_expedientes_conserva_organizacion_sin_fila_en_prospectos(cli, db):
    """Control de no regresión: sin fila en prospectos (país desconocido), la
    organización se sigue mostrando igual que antes."""
    _sembrar_evidencia(db, empresa="Fintual2026XYZ",
                        cita_textual="La empresa despide al 10% de su plantilla tras ronda fallida")

    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Fintual2026XYZ" in nombres
