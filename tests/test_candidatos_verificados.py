"""Lectura de candidatos verificados para la app (proyección de Entrega 3)."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.candidatos_verificados import listar_candidatos_verificados
from hd_scraper.db.models import ahora_iso


@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _evidencia(db, n, org, cita, *, fecha_publicacion=None):
    return db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, fecha_publicacion, creado_en) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (cita, ahora_iso(), f"https://ej.test/{n}", "Prensa X", org,
         "lanzamiento", "prensa", f"hcv{n}", "google_news",
         fecha_publicacion, ahora_iso()))


def _expediente(db, org, estado):
    return db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        (org, estado))


def _clasificar(db, expediente_id, evidencia_id, tipo):
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico) VALUES (?,?,?)",
        (expediente_id, evidencia_id, tipo))


def test_solo_lista_expedientes_en_estado_candidato(db):
    exp_candidato = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp_candidato, _evidencia(db, 1, "Acme", "cita 1"),
                "senal_primaria_autodeclaracion")

    exp_abierto = _expediente(db, "Beta", "abierto")
    _clasificar(db, exp_abierto, _evidencia(db, 2, "Beta", "cita 2"),
                "senal_primaria_autodeclaracion")

    items = listar_candidatos_verificados(db, estado_visibilidad="todos")
    assert [i["organizacion"] for i in items] == ["Acme"]


def test_incluye_la_cita_textual_de_la_evidencia_primaria(db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "Juan Pérez, CEO de Acme"),
                "senal_primaria_huella_practica")

    item = listar_candidatos_verificados(db, estado_visibilidad="todos")[0]
    assert item["cita_textual"] == "Juan Pérez, CEO de Acme"
    assert item["tipo_epistemologico"] == "senal_primaria_huella_practica"
    assert item["url_fuente"] == "https://ej.test/1"
    assert item["visibilidad"] == "latente"


def test_ignora_evidencia_no_primaria_del_mismo_expediente(db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "cita contextual"), "contextual")
    _clasificar(db, exp, _evidencia(db, 2, "Acme", "cita primaria"),
                "senal_primaria_autodeclaracion")

    item = listar_candidatos_verificados(db, estado_visibilidad="todos")[0]
    assert item["cita_textual"] == "cita primaria"


def test_prioriza_autodeclaracion_sobre_huella_practica(db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "huella practica"),
                "senal_primaria_huella_practica")
    _clasificar(db, exp, _evidencia(db, 2, "Acme", "autodeclaracion"),
                "senal_primaria_autodeclaracion")

    item = listar_candidatos_verificados(db, estado_visibilidad="todos")[0]
    assert item["tipo_epistemologico"] == "senal_primaria_autodeclaracion"
    assert item["cita_textual"] == "autodeclaracion"


def test_candidato_sin_evidencia_primaria_localizable_se_omite(db):
    """No debería pasar dado cómo promueve Entrega 3, pero si pasa, no se
    inventa una tarjeta vacía: se omite."""
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "solo contextual"), "contextual")

    assert listar_candidatos_verificados(db, estado_visibilidad="todos") == []


def test_respeta_el_limite(db):
    for i, org in enumerate(("Acme", "Beta", "Gamma"), start=1):
        exp = _expediente(db, org, "candidato")
        _clasificar(db, exp, _evidencia(db, i, org, f"cita {org}"),
                    "senal_primaria_autodeclaracion")

    items = listar_candidatos_verificados(db, limite=2, estado_visibilidad="todos")
    assert len(items) == 2


def test_orden_alfabetico_por_organizacion(db):
    for org in ("Zeta", "Acme", "Mambo"):
        exp = _expediente(db, org, "candidato")
        _clasificar(db, exp, _evidencia(db, org, org, f"cita {org}"),
                    "senal_primaria_autodeclaracion")

    items = listar_candidatos_verificados(db, estado_visibilidad="todos")
    assert [i["organizacion"] for i in items] == ["Acme", "Mambo", "Zeta"]


# ── Visibilidad por score_relevancia + score_freshness (2026-09-19/20) ──────

HOY = ahora_iso()[:10]


def test_candidato_sin_friccion_queda_latente_score_relevancia_cero(db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(
        db, 1, "Acme", "Acme anuncia una ronda de inversión", fecha_publicacion=HOY),
        "senal_primaria_autodeclaracion")

    assert listar_candidatos_verificados(db) == []

    todos = listar_candidatos_verificados(db, estado_visibilidad="todos")
    assert todos[0]["score_relevancia"] == 0
    assert todos[0]["score_freshness"] == 100
    assert todos[0]["visibilidad"] == "latente"


def test_una_sola_oracion_de_friccion_no_alcanza_el_umbral(db):
    """1 oración con marcador (incluida su forma verbal 'canceló') = conteo 1
    = score_relevancia 20, por debajo del umbral de 40: sigue latente."""
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(
        db, 1, "Acme", "Acme canceló su expansión a Colombia", fecha_publicacion=HOY),
        "senal_primaria_autodeclaracion")

    todos = listar_candidatos_verificados(db, estado_visibilidad="todos")
    assert todos[0]["score_relevancia"] == 20
    assert todos[0]["score_freshness"] == 100
    assert todos[0]["visibilidad"] == "latente"


def test_dos_oraciones_de_friccion_cruzan_el_umbral_y_quedan_visibles(db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(
        db, 1, "Acme",
        "Acme entró en conflicto con su distribuidor principal. "
        "Además, Acme sufrió un fuerte churn este trimestre.",
        fecha_publicacion=HOY),
        "senal_primaria_autodeclaracion")

    items = listar_candidatos_verificados(db)
    assert len(items) == 1
    assert items[0]["organizacion"] == "Acme"
    assert items[0]["score_relevancia"] == 40
    assert items[0]["score_freshness"] == 100
    assert items[0]["visibilidad"] == "visible"


def test_friccion_de_un_tercero_no_cuenta_para_la_organizacion(db):
    """'no renovó' aparece, pero el sujeto es el proveedor, no Acme: Acme
    aparece DESPUÉS del marcador en la oración, como objeto de "con". Fecha
    reciente a propósito: si contara, pasaría por freshness; no debe pasar
    porque score_relevancia se queda en 0."""
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(
        db, 1, "Acme", "El proveedor X no renovó su contrato con Acme",
        fecha_publicacion=HOY),
        "senal_primaria_autodeclaracion")

    assert listar_candidatos_verificados(db) == []
    todos = listar_candidatos_verificados(db, estado_visibilidad="todos")
    assert todos[0]["score_relevancia"] == 0
    assert todos[0]["visibilidad"] == "latente"


def test_relevancia_alta_sin_freshness_sigue_latente_no_promedia(db):
    """Regla explícita del operador: AND, no promedio. Con score_relevancia
    en el máximo (100) pero evidencia primaria sin fecha (no_fechado -> 0 de
    freshness), el resultado sigue latente."""
    exp = _expediente(db, "Acme", "candidato")
    cita_muy_friccionada = (
        "Acme sufrió churn. Acme entró en conflicto con un socio. "
        "Acme canceló su expansión. Acme discontinuó su línea premium. "
        "Acme perdió tracción en el mercado."
    )
    _clasificar(db, exp, _evidencia(
        db, 1, "Acme", cita_muy_friccionada, fecha_publicacion=None),
        "senal_primaria_autodeclaracion")

    todos = listar_candidatos_verificados(db, estado_visibilidad="todos")
    assert todos[0]["score_relevancia"] == 100
    assert todos[0]["score_freshness"] == 0
    assert todos[0]["visibilidad"] == "latente"
    assert listar_candidatos_verificados(db) == []


def test_freshness_usa_siempre_la_evidencia_primaria_nunca_la_mas_reciente(db):
    """CLAUDE.md (2026-09-20): una nota nueva pero irrelevante para la
    promoción NO debe rejuvenecer un expediente cuya evidencia primaria es
    vieja. La evidencia primaria (autodeclaración) es de hace 400 días; una
    segunda evidencia 'contextual' (no primaria, nunca elegida por
    _ORDEN_TIPO_PRIMARIO) tiene fecha de HOY y también aporta fricción a la
    suma de score_relevancia, pero su fecha nunca debe usarse para
    freshness."""
    import datetime as _dt

    hace_400_dias = (_dt.date.today() - _dt.timedelta(days=400)).isoformat()
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(
        db, 1, "Acme",
        "Acme entró en conflicto con su distribuidor. Acme sufrió churn.",
        fecha_publicacion=hace_400_dias),
        "senal_primaria_autodeclaracion")
    _clasificar(db, exp, _evidencia(
        db, 2, "Acme", "Acme canceló otro contrato menor", fecha_publicacion=HOY),
        "contextual")

    todos = listar_candidatos_verificados(db, estado_visibilidad="todos")
    item = todos[0]
    # score_relevancia suma fricción de AMBAS evidencias (2 + 1 = 3 -> 60),
    # pero score_freshness usa SOLO la fecha de la primaria (400 días -> 0).
    assert item["score_relevancia"] == 60
    assert item["score_freshness"] == 0
    assert item["visibilidad"] == "latente"


# ── Endpoint HTTP ────────────────────────────────────────────────────────

def test_endpoint_get_verificados(client, db):
    exp = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp, _evidencia(db, 1, "Acme", "Juan Pérez, CEO de Acme"),
                "senal_primaria_huella_practica")

    r = client.get("/verificados", params={"estado_visibilidad": "todos"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["organizacion"] == "Acme"
    assert body["items"][0]["cita_textual"] == "Juan Pérez, CEO de Acme"
    assert body["items"][0]["visibilidad"] == "latente"


def test_endpoint_get_verificados_vacio_sin_candidatos(client, db):
    r = client.get("/verificados")
    assert r.status_code == 200
    assert r.json() == {"total": 0, "items": []}


def test_endpoint_get_verificados_respeta_limite(client, db):
    for i, org in enumerate(("Acme", "Beta", "Gamma"), start=1):
        exp = _expediente(db, org, "candidato")
        _clasificar(db, exp, _evidencia(db, i, org, f"cita {org}"),
                    "senal_primaria_autodeclaracion")

    r = client.get("/verificados", params={"limite": 2, "estado_visibilidad": "todos"})
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_endpoint_get_verificados_por_defecto_solo_visibles(client, db):
    hoy = ahora_iso()[:10]
    exp_sin_friccion = _expediente(db, "Acme", "candidato")
    _clasificar(db, exp_sin_friccion,
                _evidencia(db, 1, "Acme", "Acme anuncia una ronda de inversión",
                           fecha_publicacion=hoy),
                "senal_primaria_autodeclaracion")

    exp_con_friccion = _expediente(db, "Beta", "candidato")
    _clasificar(db, exp_con_friccion,
                _evidencia(db, 2, "Beta",
                           "Beta sufrió un fuerte churn este trimestre. "
                           "Beta entró en conflicto con un proveedor clave.",
                           fecha_publicacion=hoy),
                "senal_primaria_autodeclaracion")

    r = client.get("/verificados")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["organizacion"] == "Beta"
    assert body["items"][0]["score_relevancia"] == 40
    assert body["items"][0]["score_freshness"] == 100
    assert body["items"][0]["visibilidad"] == "visible"

    r_todos = client.get("/verificados", params={"estado_visibilidad": "todos"})
    assert r_todos.json()["total"] == 2
