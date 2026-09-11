"""Incidente real 2026-09-10: Anthropic apareció con ICP 81 en INDAGAR porque
no tenía fila en `prospectos` y el sistema, sin fila estructural, hereda la
categoria con la que se etiquetó la CONSULTA de captura (por defecto
'Startup' en el endpoint de un clic). Cualquier organización nueva mencionada
en prensa entraba así, sin importar su tamaño real, hasta que alguien la
excluyera a mano.

Corrección (autorizada por el operador): GIGANTES (relevance.py) se reutiliza
en `_construir_expedientes` (api/app.py) para forzar categoria='Corporativo'
en cualquier organización reconocible como gran tecnológica, SIN depender de
una fila en `prospectos`. No borra evidencia: solo deja de calificar como
candidato ICP.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup
from hd_scraper.relevance import GIGANTES


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar_evidencia(db, *, empresa, cita_textual, categoria_query="Startup"):
    """categoria_query = la etiqueta de ecosistema con la que se capturó (query-time),
    NO la categoria estructural de prospectos (que aquí no existe)."""
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


def test_gigantes_incluye_laboratorios_de_ia_y_grandes_tecnologicas():
    """Regresión directa del incidente: los nombres que motivaron la ampliación
    deben estar en el léxico, no solo documentados en un comentario."""
    esperados = {
        "anthropic", "openai", "chatgpt", "deepmind", "mistral ai", "xai",
        "perplexity ai", "ibm", "oracle", "salesforce", "sap",
    }
    faltantes = esperados - set(GIGANTES)
    assert not faltantes, f"faltan en GIGANTES: {faltantes}"


def test_anthropic_sin_fila_en_prospectos_queda_forzado_a_corporativo(cli, db):
    """Reproduce el incidente real: sin fila en prospectos, categoria_query='Startup'.

    El titular deliberadamente NO repite el nombre "Anthropic" ni ningún otro
    token capitalizado detectable (queda solo en empresa_mencionada, como
    ocurre con capturas dirigidas por nombre exacto o conectores que no lo
    extraen del título): así se aísla la corrección nueva (forzar categoria
    en _construir_expedientes por nombre de organización) del filtro de
    ruido ya existente (evaluar_relevancia, que rechaza por GIGANTES si el
    titular literalmente nombra al gigante) Y de detectar_empresa (que si no,
    "descubriría" otra palabra capitalizada como organización). Ambos
    mecanismos comparten GIGANTES y se refuerzan, no se duplican.

    Actualización 2026-09-11 (corrección "identidad ≠ relación/contexto",
    autorizada por el operador): `evaluar_relevancia` ahora recibe la
    organización ya identificada y descarta por `relevancia:gigante` cuando
    ESA organización coincide con `GIGANTES` — sin importar si el gigante se
    nombra literalmente en el titular. Decisión explícita del operador: un
    gigante sin fila en `prospectos` ya no se muestra reclasificado como
    Corporativo, se descarta por completo (mismo criterio que si el titular
    lo nombrara directamente).
    """
    _sembrar_evidencia(
        db, empresa="Anthropic",
        cita_textual="La empresa pagará mil quinientos millones de dólares por demanda colectiva de autores",
        categoria_query="Startup",
    )
    assert db.fetch_one("SELECT id FROM prospectos WHERE LOWER(nombre) = 'anthropic'") is None

    r_startup = cli.get("/expedientes", params={"categoria": "Startup", "limite": 30})
    nombres_startup = {e["nombre"] for e in r_startup.json()["expedientes"]}
    assert "Anthropic" not in nombres_startup, (
        "Anthropic NO debe calificar como candidato Startup/ICP")

    # Con la corrección de identidad-vs-contexto, un gigante sin fila en
    # prospectos se descarta por relevancia:gigante antes de llegar a
    # _construir_expedientes: no aparece en /expedientes bajo ningún filtro.
    r_todas = cli.get("/expedientes", params={"limite": 100})
    por_nombre = {e["nombre"]: e["categoria"] for e in r_todas.json()["expedientes"]}
    assert "Anthropic" not in por_nombre, (
        "Anthropic (gigante sin fila en prospectos) debe descartarse por "
        "completo, no solo dejar de calificar como Startup/ICP")


def test_organizacion_no_gigante_sin_fila_conserva_categoria_de_la_consulta(cli, db):
    """Control: una organización real que NO es un gigante reconocible no debe
    verse afectada por este cambio — sigue heredando la categoria de la
    consulta como antes (comportamiento preexistente, no se amplía)."""
    _sembrar_evidencia(
        db, empresa="Fintual",
        cita_textual="Fintual despide al 10% de su plantilla tras ronda fallida",
        categoria_query="Startup",
    )
    r = cli.get("/expedientes", params={"categoria": "Startup", "limite": 30})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Fintual" in nombres


def test_fila_estructural_en_prospectos_sigue_ganando_sobre_gigantes(cli, db):
    """La categoria declarada por el operador en `prospectos` sigue siendo la
    autoridad final (doctrina: 'categoria sigue siendo declarada, no
    inferida') — GIGANTES es solo el respaldo cuando NO hay fila.

    Titular sin el nombre "Oracle" ni otro token capitalizado detectable (ver
    nota en el test de Anthropic): aísla esta prioridad del filtro de ruido
    evaluar_relevancia, que rechazaría cualquier titular que sí lo nombre,
    sin mirar `prospectos`.
    """
    ahora = ahora_iso()
    db.execute(
        """INSERT INTO prospectos (nombre, categoria, escala, hash_dedup, creado_en, actualizado_en)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("Oracle", "Startup", "indeterminada", "hash-test-oracle-startup", ahora, ahora),
    )
    _sembrar_evidencia(
        db, empresa="Oracle",
        cita_textual="La compañía despidió a 21 mil personas citando eficiencias por automatización",
        categoria_query="Startup",
    )
    r = cli.get("/expedientes", params={"categoria": "Startup", "limite": 30})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Oracle" in nombres, (
        "la fila estructural declarada por el operador debe ganar, aunque "
        "Oracle esté en GIGANTES")
