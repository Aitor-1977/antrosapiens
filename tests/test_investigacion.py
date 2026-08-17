"""Tests del flujo real de investigación antropológica (AntroSapiens).

Cubre: captura, deduplicación, curaduría, persistencia, relaciones, tensiones,
hipótesis, trazabilidad y la API. Todo OFFLINE: los conectores se simulan con
una clase falsa que emite RawItems deterministas (no hay red).
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from hd_scraper.connectors.base import Connector
from hd_scraper.db.models import EvidenceRecord, RawItem, ahora_iso
from hd_scraper import investigacion as ENG
from hd_scraper import investigacion_store as S
from hd_scraper.db.database import Database, get_db


# --- Conector falso (sin red) -------------------------------------------
class _FakeConnector(Connector):
    name = "fake"
    origen_declaracion_default = "prensa"
    requires_slug = False

    def __init__(self, items):
        super().__init__(client=__import__("httpx").Client())
        self._items = items

    def search(self, query):
        return list(self._items)

    def fetch(self, url):
        return RawItem(url=url, contenido="", formato="json")

    def normalize(self, raw):
        return raw._rec


def _rec(titulo, url, medio="FakeNews", empresa="Acme", fecha="2026-01-01"):
    return EvidenceRecord(
        cita_textual=titulo, fecha_extraccion=ahora_iso(), url_fuente=url,
        nombre_medio=medio, empresa_mencionada=empresa, tipo_evento="ronda",
        origen_declaracion="prensa",
        hash_dedup=empresa + "|" + url, fecha_publicacion=fecha,
    )


def _raw(titulo, url, medio="FakeNews", empresa="Acme", fecha="2026-01-01"):
    class _R:
        pass
    _R.url = url
    _R.meta = {}
    _R._rec = _rec(titulo, url, medio, empresa, fecha)
    return _R()


@pytest.fixture()
def inv_db():
    d = Database(":memory:")
    d.init_schema()
    S.init_investigacion_schema(d)
    yield d
    d.close()


def _dos_conectores():
    items_a = [
        _raw("Acme levanta ronda serie B", "https://news.example/acme-ronda"),
        _raw("Acme despide la mitad del equipo", "https://news.example/acme-despido"),
    ]
    items_b = [
        # Misma nota que items_a[0] pero distinta URL -> debe deduplicar por contenido.
        _raw("Acme levanta ronda serie B", "https://otro.example/acme-ronda-2"),
        _raw("Acme abre oficina en Bogotá", "https://news.example/acme-bogota"),
    ]
    return [_FakeConnector(items_a), _FakeConnector(items_b)]


# --- Captura + dedup ----------------------------------------------------
def test_captura_y_dedup(inv_db):
    inv_id = ENG.crear_investigacion(inv_db, "Acme", "¿Cómo cambia Acme?")
    res = ENG.capturar(inv_db, inv_id, "Acme", "ronda", _dos_conectores())
    # 4 vistos, pero la nota repetida colapsa -> 3 escritos, 1 duplicado.
    assert res["vistos"] == 4
    assert res["escritos"] == 3
    assert res["duplicados"] == 1
    senales = S.listar_senales(inv_db, inv_id)
    assert len(senales) == 3
    # Persistencia: la investigación existe tras "cerrar" el objeto.
    assert ENG.obtener_estado(inv_db, inv_id)["investigacion"]["foco"] == "Acme"


def test_dedup_por_url_igual(inv_db):
    inv_id = ENG.crear_investigacion(inv_db, "Acme", "p")
    r = ENG.capturar(inv_db, inv_id, "Acme", "ronda", [_FakeConnector([
        _raw("T1", "https://x.example/1"),
        _raw("T1", "https://x.example/1"),
    ])])
    assert r["escritos"] == 1 and r["duplicados"] == 1


# --- Curaduría ----------------------------------------------------------
def test_curaduria_aceptar_descartar(inv_db):
    inv_id = ENG.crear_investigacion(inv_db, "Acme", "p")
    ENG.capturar(inv_db, inv_id, "Acme", "ronda", [_FakeConnector([
        _raw("A", "https://x.example/a"),
        _raw("B", "https://x.example/b"),
    ])])
    senales = S.listar_senales(inv_db, inv_id)
    a, b = senales[0]["id"], senales[1]["id"]
    ENG.curar(inv_db, inv_id, a, "aceptar", nota="clave", autor="Mario")
    ENG.curar(inv_db, inv_id, b, "descartar")
    est = ENG.obtener_estado(inv_db, inv_id)
    assert est["conteos"]["evidencias"] == 1
    assert est["conteos"]["descartadas"] == 1
    ev = S.obtener_senal(inv_db, a)
    assert ev["estado_curaduria"] == S.ESTADO_EVIDENCIA
    assert ev["decisor"] == "Mario" and ev["nota"] == "clave"


def test_senal_no_es_evidencia_automaticamente(inv_db):
    inv_id = ENG.crear_investigacion(inv_db, "Acme", "p")
    ENG.capturar(inv_db, inv_id, "Acme", "ronda", [_FakeConnector([_raw("A", "https://x.example/a")])])
    assert ENG.obtener_estado(inv_db, inv_id)["conteos"]["evidencias"] == 0


# --- Relaciones ---------------------------------------------------------
def test_relaciones_validas(inv_db):
    inv_id = ENG.crear_investigacion(inv_db, "Acme", "p")
    ENG.capturar(inv_db, inv_id, "Acme", "ronda", [_FakeConnector([
        _raw("A", "https://x.example/a"),
        _raw("B", "https://x.example/b"),
    ])])
    s = S.listar_senales(inv_db, inv_id)
    rid = ENG.relacionar(inv_db, inv_id, s[0]["id"], s[1]["id"], S.REL_REFUERZA)
    assert rid > 0
    rels = S.listar_relaciones(inv_db, inv_id)
    assert rels[0]["tipo"] == S.REL_REFUERZA
    # Tipo inválido rechazado.
    with pytest.raises(ValueError):
        ENG.relacionar(inv_db, inv_id, s[0]["id"], s[1]["id"], "RARA")


# --- Tensiones ----------------------------------------------------------
def test_tensiones(inv_db):
    inv_id = ENG.crear_investigacion(inv_db, "Acme", "p")
    ENG.capturar(inv_db, inv_id, "Acme", "ronda", [_FakeConnector([
        _raw("Acme crece", "https://x.example/a"),
        _raw("Acme cae", "https://x.example/b"),
    ])])
    s = S.listar_senales(inv_db, inv_id)
    tid = ENG.registrar_tension(inv_db, inv_id, s[0]["id"], s[1]["id"],
                                "Crecimiento y caída simultáneos", autor="Mario")
    assert S.listar_tensiones(inv_db, inv_id)[0]["explicacion"]
    assert tid > 0


# --- Hipótesis + triangulación + peritaje -------------------------------
def test_hipotesis_y_peritaje(inv_db):
    inv_id = ENG.crear_investigacion(inv_db, "Acme", "p")
    ENG.capturar(inv_db, inv_id, "Acme", "ronda", [_FakeConnector([
        _raw("Acme levanta ronda", "https://x.example/a", medio="DiarioX"),
        _raw("Acme contrata 100", "https://y.example/b", medio="DiarioY"),
    ])])
    s = S.listar_senales(inv_db, inv_id)
    for ev in s:
        ENG.curar(inv_db, inv_id, ev["id"], "aceptar")
    tri = ENG.triangulacion(inv_db, inv_id)
    assert tri["n_evidencias"] == 2
    assert tri["fuentes_independientes"] == 2  # DiarioX y DiarioY
    hips = ENG.generar_hipotesis(inv_db, inv_id, usar_ia=False)
    assert hips and "preliminar" in hips[0]["texto"].lower()
    dictamen = ENG.cerrar_peritaje(inv_db, inv_id)
    assert "veredicto" in dictamen
    assert ENG.obtener_estado(inv_db, inv_id)["investigacion"]["estado"] == "cerrada"


def test_sugerir_tensiones(inv_db):
    inv_id = ENG.crear_investigacion(inv_db, "Acme", "p")
    ENG.capturar(inv_db, inv_id, "Acme", "ronda", [_FakeConnector([
        _raw("Acme ronda", "https://x.example/a"),
    ])])
    # Menos de 2 evidencias -> sin sugerencias.
    assert ENG.sugerir_tensiones(inv_db, inv_id) == []


# --- Trazabilidad -------------------------------------------------------
def test_trazabilidad_campos(inv_db):
    inv_id = ENG.crear_investigacion(inv_db, "Acme", "p")
    ENG.capturar(inv_db, inv_id, "Acme", "ronda", [_FakeConnector([
        _raw("Acme ronda", "https://x.example/a", medio="DiarioX", fecha="2026-03-04"),
    ])])
    s = S.listar_senales(inv_db, inv_id)[0]
    for campo in ("fuente", "url", "fecha_publicacion", "fecha_captura", "tipo_fuente", "hash", "id_interno"):
        assert s[campo], f"falta trazabilidad: {campo}"


# --- API (TestClient) ---------------------------------------------------
def _cliente(tmp_path):
    db_path = tmp_path / "antro_api.db"
    object.__setattr__(settings, "database_url", f"sqlite:///{db_path}")
    # Reinicia el singleton para apuntar a la base de test.
    import hd_scraper.db.database as _dbmod
    _dbmod._db_singleton = None
    _dbmod._schema_ready = False
    from hd_scraper.api.investigacion_router import build_app
    app = build_app()
    return TestClient(app)


def test_api_flujo_completo(tmp_path):
    c = _cliente(tmp_path)
    r = c.post("/investigacion/crear", json={"foco": "Acme", "pregunta": "¿?"})
    assert r.status_code == 200
    inv_id = r.json()["id"]
    # Inyecta señales directo a la base para no depender de red en la API.
    db = get_db()
    ENG.capturar(db, inv_id, "Acme", "ronda", [_FakeConnector([
        _raw("Acme ronda", "https://x.example/a"),
        _raw("Acme crece", "https://y.example/b"),
    ])])
    est = c.get(f"/investigacion/{inv_id}").json()
    assert est["conteos"]["senales"] == 2
    s = est["senales"][0]
    rc = c.post("/investigacion/curar", json={"inv_id": inv_id, "senal_id": s["id"], "accion": "aceptar"})
    assert rc.status_code == 200
    # Relacionar por API.
    rr = c.post("/investigacion/relacionar", json={
        "inv_id": inv_id, "a": est["senales"][0]["id"], "b": est["senales"][1]["id"],
        "tipo": "REFUERZA"})
    assert rr.status_code == 200
    tri = c.get(f"/investigacion/{inv_id}/triangulacion").json()
    assert tri["n_evidencias"] == 1
