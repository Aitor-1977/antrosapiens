"""Hotfix de producción (autorizado por el operador): /expedientes debía
devolver `categoria` desde prospectos.categoria (autoridad estructural
declarada por el operador), no desde evidencias.categoria (etiqueta de
momento de captura, vacía en consulta dirigida por nombre — ver hallazgo
en producción: 95/100 expedientes con categoria="" y cero "Startup").

Estas pruebas demuestran PROCEDENCIA, no solo presencia del string: cada
caso siembra evidencias.categoria y prospectos.categoria con valores
DISTINTOS a propósito, para que una prueba que pasara por coincidencia
(ambas columnas con el mismo valor) no pueda esconder una regresión.

Implementación: hd_scraper/api/app.py:_construir_expedientes, línea
"categoria": categorias_prospecto.get(key) or row["categoria"] or "".
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


def _sembrar_prospecto(db, *, nombre, categoria):
    ahora = ahora_iso()
    db.execute(
        """INSERT INTO prospectos (nombre, categoria, escala, hash_dedup, creado_en, actualizado_en)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (nombre, categoria, "indeterminada", f"hash-autoridad-{nombre}", ahora, ahora),
    )


def _sembrar_evidencia(db, *, empresa, cita_textual, categoria_evidencia):
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
            cita_textual, ahora_iso(), f"https://ejemplo.com/{empresa}", "Medio de Prueba",
            empresa, "queja", "prensa",
            calcular_hash_dedup(empresa, cita_textual),
            "2026-09-08", "manual_test", ESTADO_OK, categoria_evidencia, "[]", 1.0,
            ahora_iso(),
        ),
    )


def test_categoria_procede_de_prospectos_no_de_evidencias_caso_startup(cli, db):
    """Caso crítico: prospectos.categoria='Startup', evidencias.categoria=''
    (el caso real y mayoritario de producción: consulta dirigida por
    nombre, que nunca puebla evidencias.categoria). Debe salir 'Startup'."""
    _sembrar_prospecto(db, nombre="Fintual", categoria="Startup")
    _sembrar_evidencia(db, empresa="Fintual",
                       cita_textual="Fintual despide al 10% de su plantilla tras ronda fallida",
                       categoria_evidencia="")

    r = cli.get("/expedientes", params={"limite": 30})
    por_nombre = {e["nombre"]: e["categoria"] for e in r.json()["expedientes"]}
    assert por_nombre.get("Fintual") == "Startup", (
        f"esperaba 'Startup' desde prospectos.categoria, obtuve {por_nombre.get('Fintual')!r}")


def test_categoria_estructural_gana_aunque_evidencia_diga_otra_cosa(cli, db):
    """Regresión: prospectos.categoria='Corporativo' pero la evidencia trae
    categoria='Startup' (etiqueta de captura desactualizada/legada). La
    estructural debe seguir ganando: NO debe convertirse en 'Startup'."""
    _sembrar_prospecto(db, nombre="Cemex", categoria="Corporativo")
    _sembrar_evidencia(db, empresa="Cemex",
                       cita_textual="Cemex lanza nueva línea de negocio digital",
                       categoria_evidencia="Startup")

    r = cli.get("/expedientes", params={"limite": 30})
    por_nombre = {e["nombre"]: e["categoria"] for e in r.json()["expedientes"]}
    assert por_nombre.get("Cemex") == "Corporativo", (
        f"la categoria estructural debe ganar; obtuve {por_nombre.get('Cemex')!r}")


def test_sin_fila_en_prospectos_cae_al_fallback_tecnico_de_evidencias(cli, db):
    """Sin fila estructural, el fallback documentado (evidencias.categoria)
    sigue aplicando — no se inventa nada y no se rompe el caso ya cubierto
    por test_gigantes_categoria.py."""
    _sembrar_evidencia(db, empresa="Oficializa",
                       cita_textual="Oficializa lanza nuevo producto de facturación",
                       categoria_evidencia="Startup")

    r = cli.get("/expedientes", params={"limite": 30})
    por_nombre = {e["nombre"]: e["categoria"] for e in r.json()["expedientes"]}
    assert por_nombre.get("Oficializa") == "Startup"
