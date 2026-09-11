"""Cuello de botella identificado en la revisión de cierre (2026-09-11):
/expedientes (lo que realmente consume la app) nunca exponía la
clasificación epistemológica que Entrega 2 ya calcula en
`evidencia_clasificada` — Mario tenía que releer cada nota y volver a
juzgar quién habla y con qué autoridad, exactamente la investigación que el
sistema ya había hecho.

Este test exige que cada evidencia de `/expedientes` traiga su
`tipo_epistemologico`, `enunciador_dominio` y `evidencia_id` (trazabilidad),
exactamente la clasificación ya producida por
`clasificacion_epistemologica.clasificar()` — nunca inferida ni fabricada en
la capa de API.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.clasificacion_epistemologica import clasificar
from hd_scraper.clasificacion_store import guardar_clasificacion, obtener_o_crear_expediente
from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar_evidencia(db, *, n, empresa, cita_textual, origen_declaracion="prensa"):
    return db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, fecha_publicacion, connector, estado, categoria, "
        "keywords, confianza, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (cita_textual, ahora_iso(), f"https://ejemplo.com/clas-epis/{n}",
         "Medio de Prueba", empresa, "queja", origen_declaracion,
         calcular_hash_dedup(empresa, cita_textual), "2026-09-11",
         "manual_test", ESTADO_OK, "Startup", "[]", 1.0, ahora_iso()))


def _clasificar_evidencia_real(db, evidencia_id, evidencia_dict):
    """Usa el clasificador determinista real (no un valor inventado en el
    test) para producir la fila de evidencia_clasificada, igual que hace
    clasificar_lote en producción."""
    clas = clasificar(evidencia_dict)
    expediente_id, _ = obtener_o_crear_expediente(db, evidencia_dict["empresa_mencionada"])
    guardar_clasificacion(db, expediente_id, evidencia_id, clas)
    return clas


def test_expedientes_expone_tipo_epistemologico_de_autodeclaracion(cli, db):
    """Vacante publicada por la propia organización (origen_declaracion=
    'operador', sin declaración de persona) -> huella_practica según la
    cascada real. Se usa ese caso porque es el más fácil de producir sin
    depender de heurísticas de atribución de texto."""
    ev = {
        "cita_textual": "Kavak publica una vacante para su equipo de ingeniería",
        "empresa_mencionada": "Kavak",
        "nombre_medio": "Medio de Prueba",
        "origen_declaracion": "operador",
        "persona_citada": None,
        "cargo": None,
    }
    ev_id = _sembrar_evidencia(db, n=1, empresa="Kavak", cita_textual=ev["cita_textual"],
                               origen_declaracion="operador")
    clas = _clasificar_evidencia_real(db, ev_id, ev)
    assert clas.tipo == "senal_primaria_huella_practica"  # control: el caso es el esperado

    r = cli.get("/expedientes", params={"limite": 100})
    ev_api = r.json()["expedientes"][0]["evidencias"][0]
    assert ev_api["tipo_epistemologico"] == "senal_primaria_huella_practica"
    assert ev_api["evidencia_id"] == ev_id


def test_expedientes_evidencia_sin_clasificar_expone_null_no_inventado(cli, db):
    """Sin fila en evidencia_clasificada (aún no procesada): tipo_epistemologico
    debe ser None, nunca un valor fabricado por la API."""
    _sembrar_evidencia(db, n=2, empresa="Fintual",
                       cita_textual="Fintual despide al 10% de su plantilla")

    r = cli.get("/expedientes", params={"limite": 100})
    ev_api = r.json()["expedientes"][0]["evidencias"][0]
    assert ev_api["tipo_epistemologico"] is None
    assert ev_api["enunciador_dominio"] is None
    assert ev_api["evidencia_id"] is not None  # la trazabilidad no depende de estar clasificada


def test_expedientes_expone_enunciador_dominio_cuando_existe(cli, db):
    ev = {
        "cita_textual": "soy CFO de Cobre y anuncio una ronda de inversion",
        "empresa_mencionada": "Cobre",
        "nombre_medio": "Medio de Prueba",
        "origen_declaracion": "prensa",
        "persona_citada": None,
        "cargo": None,
    }
    ev_id = _sembrar_evidencia(db, n=3, empresa="Cobre", cita_textual=ev["cita_textual"])
    clas = _clasificar_evidencia_real(db, ev_id, ev)
    assert clas.enunciador_dominio == "finanzas"  # control: CFO + "ronda"/"inversion"

    r = cli.get("/expedientes", params={"limite": 100})
    ev_api = r.json()["expedientes"][0]["evidencias"][0]
    assert ev_api["enunciador_dominio"] == "finanzas"


def test_expedientes_no_altera_orden_ni_filtro_existente_con_clasificacion_mixta(cli, db):
    """Control de no regresión: mezclar evidencia clasificada y sin clasificar
    en la misma organización no cambia cuántos expedientes ni cuántas
    evidencias se devuelven, ni el filtro de categoria."""
    ev_clasificada = {
        "cita_textual": "Kavak publica una vacante para su equipo de ingeniería",
        "empresa_mencionada": "Kavak", "nombre_medio": "Medio de Prueba",
        "origen_declaracion": "operador", "persona_citada": None, "cargo": None,
    }
    ev_id = _sembrar_evidencia(db, n=4, empresa="Kavak", cita_textual=ev_clasificada["cita_textual"],
                               origen_declaracion="operador")
    _clasificar_evidencia_real(db, ev_id, ev_clasificada)
    _sembrar_evidencia(db, n=5, empresa="Kavak",
                       cita_textual="Kavak anuncia una reestructuracion interna")

    r = cli.get("/expedientes", params={"categoria": "Startup", "limite": 100})
    body = r.json()
    assert body["total"] == 1
    assert len(body["expedientes"][0]["evidencias"]) == 2
