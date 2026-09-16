"""Prueba de extremo a extremo del contrato canónico del expediente
(Fase 4, contrato confirmado por Mario en Fase 1.5, 2026-09-16).

Usa EXCLUSIVAMENTE el fixture congelado en
`tests/fixture_contrato_canonico_expediente.py` como referencia esperada.
Ese fixture se construyó ANTES de escribir `schema_expediente.py`, a partir
solo de la decisión de Mario y de una verificación empírica de que el texto
elegido produce ese resultado con el clasificador REAL (ver historial de la
sesión) — nunca se generó desde el código que aquí se prueba.

Recorrido real, sin mocks de la lógica de negocio:

    evidencias (entrada)
    -> clasificacion_store.clasificar_lote (clasificación real)
    -> promocion_store.promover_lote (promoción real)
    -> expedientes_candidatos / evidencia_clasificada (persistencia real)
    -> GET /verificados (endpoint real, vía TestClient)

Si esta prueba falla, la regla es investigar la frontera exacta donde se
rompe (entrada / clasificación / promoción / persistencia / API), nunca
parchear el test ni ajustar el fixture para que pase.
"""
from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.clasificacion_store import clasificar_lote
from hd_scraper.db.models import ahora_iso
from hd_scraper.promocion_store import promover_lote
from tests.fixture_contrato_canonico_expediente import (
    CLAVES_ITEM_EXPEDIENTE_CANONICO,
    FIXTURE_ITEM_CATEGORIA_NO_CANONICA,
    FIXTURE_ITEM_EXPEDIENTE_CANONICO,
)


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar_evidencia_cruda(db, n: int, *, empresa: str, cita: str,
                              origen: str, url: str, medio: str,
                              fecha_publicacion: str | None,
                              categoria: str | None = None):
    """Entrada al pipeline en el punto más temprano razonable: una fila de
    `evidencias` con la misma forma que escribiría un conector real (ver
    contrato de datos, CLAUDE.md). ``categoria`` es la etiqueta de captura de
    la consulta que trajo esta evidencia (`evidencias.categoria`, TEXT
    libre) — no hay fila en `prospectos` para esta organización sintética,
    así que es la única fuente de `categoria` para este expediente."""
    db.execute(
        "INSERT INTO evidencias (id, cita_textual, fecha_extraccion, "
        "fecha_publicacion, url_fuente, nombre_medio, empresa_mencionada, "
        "tipo_evento, origen_declaracion, hash_dedup, connector, estado, "
        "categoria, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (n, cita, ahora_iso(), fecha_publicacion, url, medio, empresa,
         "ronda", origen, f"hash-e2e-{n}", "google_news", "ok", categoria,
         ahora_iso()))


def test_extremo_a_extremo_expediente_autodeclaracion_contra_fixture_congelado(cli, db):
    """Caso 1 del fixture: autodeclaración de máxima autoridad -> candidato
    con los 11 campos del contrato canónico, enunciador_* y persona_citada/
    cargo SIN fusionar."""
    esperado = FIXTURE_ITEM_EXPEDIENTE_CANONICO

    _sembrar_evidencia_cruda(
        db, 9101, empresa=esperado["organizacion"],
        cita=esperado["cita_textual"], origen="prensa",
        url=esperado["url_fuente"], medio=esperado["nombre_medio"],
        fecha_publicacion=esperado["fecha_publicacion"],
        categoria=esperado["categoria"])

    rep_clas = clasificar_lote(db, org=esperado["organizacion"], aplicar=True)
    assert rep_clas["escritas"] == 1
    rep_prom = promover_lote(db, org=esperado["organizacion"], aplicar=True)
    assert rep_prom["promovidos"] == 1

    r = cli.get("/verificados", params={"limite": 100})
    assert r.status_code == 200
    items = [it for it in r.json()["items"]
             if it["organizacion"] == esperado["organizacion"]]
    assert len(items) == 1, "debe existir exactamente un candidato para esta organización"
    real = items[0]

    # Estructura: mismas claves, ni una de más ni una de menos.
    assert set(real.keys()) == CLAVES_ITEM_EXPEDIENTE_CANONICO

    # Valores: comparación campo por campo contra el fixture congelado.
    for campo, valor_esperado in esperado.items():
        assert real[campo] == valor_esperado, (
            f"campo {campo!r}: esperado {valor_esperado!r}, real {real[campo]!r}")

    # persona_citada/cargo (estructurales) y enunciador_nombre/enunciador_cargo
    # (de la clasificación) NUNCA se fusionan (Fase 1.5, decisión 3): en este
    # caso real, los estructurales son None (ningún conector los declara) y
    # los de enunciador SÍ tienen valor — la prueba viva de que son columnas
    # distintas, no alias una de la otra.
    assert real["persona_citada"] is None and real["cargo"] is None
    assert real["enunciador_nombre"] == "Ana Torres"
    assert real["enunciador_cargo"] == "CEO"


def test_extremo_a_extremo_categoria_no_canonica_se_normaliza_a_vacio(cli, db):
    """Caso 2 del fixture: origen sin categoria canónica declarada ->
    `categoria` sale "" (Fase 1.5, decisión 2), nunca un valor inventado ni
    la etiqueta libre de captura."""
    esperado = FIXTURE_ITEM_CATEGORIA_NO_CANONICA

    _sembrar_evidencia_cruda(
        db, 9102, empresa=esperado["organizacion"],
        cita=esperado["cita_textual"], origen="operador",
        url=esperado["url_fuente"], medio=esperado["nombre_medio"],
        fecha_publicacion=esperado["fecha_publicacion"])
    # Categoria de captura NO canónica (etiqueta libre de una consulta
    # temática, no uno de los 4 literales estructurales).
    db.execute("UPDATE evidencias SET categoria = ? WHERE id = ?",
               ("vertical_fintech", 9102))

    clasificar_lote(db, org=esperado["organizacion"], aplicar=True)
    promover_lote(db, org=esperado["organizacion"], aplicar=True)

    r = cli.get("/verificados", params={"limite": 100})
    items = [it for it in r.json()["items"]
             if it["organizacion"] == esperado["organizacion"]]
    assert len(items) == 1
    real = items[0]

    assert set(real.keys()) == CLAVES_ITEM_EXPEDIENTE_CANONICO
    for campo, valor_esperado in esperado.items():
        assert real[campo] == valor_esperado, (
            f"campo {campo!r}: esperado {valor_esperado!r}, real {real[campo]!r}")
