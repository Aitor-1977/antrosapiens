"""Fase 6 del encargo del Observatorio Antropológico del Ecosistema
(2026-09-18): pruebas de no contaminación con el radar comercial + E2E
propio.

1. Ningún archivo del observatorio importa clasificacion_epistemologica.py
   ni promocion_candidatos.py (búsqueda estática de imports, sin ejecutar
   nada).
2. GET /verificados devuelve exactamente lo mismo antes y después de
   escribir datos del observatorio, para el mismo estado de `evidencias`/
   `expedientes_candidatos`/`evidencia_clasificada`.
3. E2E propio: fuente sintética de tipo podcast (fixture congelado,
   `tests/fixture_observatorio_podcast.py`) -> fragmento_observado ->
   GET /observatorio, comparado campo por campo.
"""
import ast
import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from hd_scraper.db.models import ahora_iso
from hd_scraper.observatorio_connector import ObservatorioPodcastConnector
from hd_scraper.observatorio_store import guardar_fuente_y_fragmento

from .fixture_observatorio_podcast import (
    ACTOR_PRUEBA,
    EPISODIO_CRUDO,
    FRAGMENTO_ESPERADO,
    FUENTE_ESPERADA,
)

ARCHIVOS_OBSERVATORIO = [
    Path("hd_scraper/observatorio_connector.py"),
    Path("hd_scraper/observatorio_store.py"),
]

MODULOS_PROHIBIDOS = {"clasificacion_epistemologica", "promocion_candidatos"}


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


# ── 1. No contaminación: imports estáticos ──────────────────────────────

def _nombres_importados(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    nombres: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                nombres.add(alias.name.split(".")[-1])
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.module:
                nombres.add(nodo.module.split(".")[-1])
            for alias in nodo.names:
                nombres.add(alias.name)
    return nombres


def test_observatorio_no_importa_modulos_del_radar_comercial():
    for ruta in ARCHIVOS_OBSERVATORIO:
        assert ruta.is_file(), f"no encontrado: {ruta}"
        importados = _nombres_importados(ruta)
        colision = importados & MODULOS_PROHIBIDOS
        assert not colision, f"{ruta} importa módulos prohibidos: {colision}"


# ── 2. /verificados sin cambios antes/después del observatorio ─────────

def _sembrar_candidato_verificado(db):
    ev_id = db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("Ana Ríos, fundadora de Acme, anunció la ronda", ahora_iso(),
         "https://ej.test/acme", "Prensa X", "Acme", "ronda", "prensa",
         "hash-obs-noconta-1", "google_news", ahora_iso()))
    exp_id = db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        ("Acme", "candidato"))
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico) VALUES (?,?,?)",
        (exp_id, ev_id, "senal_primaria_autodeclaracion"))


def test_verificados_identico_antes_y_despues_del_observatorio(cli, db):
    _sembrar_candidato_verificado(db)

    parametros = {"estado_visibilidad": "todos"}
    antes = cli.get("/verificados", params=parametros).json()
    assert antes["total"] == 1

    # Escribe datos del observatorio, sin relación con "Acme": misma
    # operación que produciría un uso real de /observatorio/ingesta.
    fuente, fragmento = ObservatorioPodcastConnector().normalizar(
        ACTOR_PRUEBA, EPISODIO_CRUDO)
    guardar_fuente_y_fragmento(db, fuente, fragmento)

    despues = cli.get("/verificados", params=parametros).json()
    assert despues == antes, (
        "GET /verificados cambió tras escribir datos del observatorio")


# ── 3. E2E propio del observatorio, contra el fixture congelado ────────

def test_e2e_fuente_podcast_hasta_get_observatorio(cli, monkeypatch):
    object.__setattr__(settings, "ingest_token", "secreto-observatorio")
    try:
        def _buscar_fake(self, actor):
            assert actor == ACTOR_PRUEBA
            return [EPISODIO_CRUDO]

        monkeypatch.setattr(ObservatorioPodcastConnector, "buscar", _buscar_fake)

        r_ingesta = cli.post(
            "/observatorio/ingesta",
            json={"actor": ACTOR_PRUEBA, "limite": 5},
            headers={"X-Ingest-Token": "secreto-observatorio"},
        )
        assert r_ingesta.status_code == 200
        assert r_ingesta.json() == {
            "actor": ACTOR_PRUEBA, "vistos": 1, "guardados": 1, "duplicados": 0,
        }
    finally:
        object.__setattr__(settings, "ingest_token", "")

    r = cli.get("/observatorio", params={"actor": ACTOR_PRUEBA})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    frag = data["fragmentos"][0]

    for campo, esperado in FUENTE_ESPERADA.items():
        assert frag[campo] == esperado, f"fuente.{campo}"
    for campo, esperado in FRAGMENTO_ESPERADO.items():
        assert frag[campo] == esperado, f"fragmento.{campo}"
