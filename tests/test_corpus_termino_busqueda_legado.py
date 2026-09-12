"""Regresión: /corpus no debe propagar un término de búsqueda como "empresa".

Hallazgo en producción (auditoría 2026-09-12): evidencia capturada por
descubrimiento por categoría ANTES de que `pipeline.run_connector` reescribiera
`empresa_mencionada` con la organización detectada del titular (ver el
comentario en `listar_evidencias`, api/app.py) quedó con el grupo OR compuesto
por `discovery.queries_para` — p. ej.
'(startup OR startups OR emprendimiento) ("despidos" OR ...)' — como si fuera
la empresa observada. `GET /evidencias?limpio=...` ya corrige esto para la UI;
`GET /corpus` (el contrato `motor_a.corpus.v1` que consume RadarHD) no lo
hacía y seguía propagando el término crudo tal cual a Motor B.

La corrección es de LECTURA (no toca la tabla ni requiere una migración/purga
de producción): se reconoce el término crudo de forma estructural (contiene
" OR " o empieza con paréntesis — ninguna empresa se llama así) y solo en ese
caso se deriva la organización real del titular, igual que ya hace
`GET /evidencias`. El resto de las filas (la inmensa mayoría) no se toca.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup

TERMINO_CRUDO = (
    '(startup OR startups OR emprendimiento) ("caída de crecimiento" OR '
    'desaceleración OR reestructuración OR "crisis operativa" OR despidos '
    'OR "cierre de operaciones")'
)


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar_evidencia(db, *, empresa, cita_textual, categoria="Startup"):
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
            cita_textual, ahora_iso(), "https://ejemplo.com/nota-legado",
            "Ecosistema Startup", empresa, "queja", "prensa",
            calcular_hash_dedup(empresa, cita_textual),
            "2026-07-15", "google_news", ESTADO_OK, categoria, "[]", 1.0,
            ahora_iso(),
        ),
    )


def test_corpus_deriva_organizacion_real_cuando_empresa_mencionada_es_termino_crudo(cli, db):
    _sembrar_evidencia(
        db, empresa=TERMINO_CRUDO,
        cita_textual="Fintual despide al 10% de su plantilla tras ronda fallida",
    )
    items = cli.get("/corpus", params={"limite": 100}).json()["items"]
    item = next(i for i in items if i["texto"].startswith("Fintual"))
    assert item["empresa"] == "Fintual"
    assert " OR " not in item["empresa"]


def test_corpus_sin_organizacion_detectable_conserva_el_crudo_sin_inventar(cli, db):
    """Si el titular tampoco trae un nombre propio detectable, no se inventa
    una organización: se conserva el valor crudo (visible, no silencioso)."""
    _sembrar_evidencia(
        db, empresa=TERMINO_CRUDO,
        cita_textual="despidos y cierre de operaciones golpean al sector",
    )
    items = cli.get("/corpus", params={"limite": 100}).json()["items"]
    item = next(i for i in items if i["texto"].startswith("despidos"))
    assert item["empresa"] == TERMINO_CRUDO


def test_corpus_no_toca_empresa_mencionada_declarada_normalmente(cli, db):
    """Control: una captura normal (empresa_mencionada ya es la compañía real,
    declarada o ya corregida por el pipeline) no se ve afectada por esta
    corrección — solo aplica a la forma estructural del término crudo."""
    _sembrar_evidencia(
        db, empresa="Konfío",
        cita_textual="Konfío anuncia nueva línea de crédito para pymes",
    )
    items = cli.get("/corpus", params={"limite": 100}).json()["items"]
    item = next(i for i in items if i["texto"].startswith("Konfío"))
    assert item["empresa"] == "Konfío"
