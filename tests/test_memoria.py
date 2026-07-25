"""Tests: Memoria Científica (Capa 13) — historial longitudinal inmutable."""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper.validacion_cientifica import validar_expediente
from hd_scraper.gobernanza import generar_huella_digital
from hd_scraper import memoria_store as store
from hd_scraper.memoria import (
    calcular_evolucion,
    comparar_versiones,
    construir_timeline,
    crear_version,
    detectar_cambios,
    emitir_historial,
)


def _ev(url="https://a.com/1", fuente="Medio A", fecha="2026-07-01",
        tipo_evento="queja", confianza=0.8, texto="fricción"):
    return {"url": url, "fuente": fuente, "fecha": fecha,
            "tipo_evento": tipo_evento, "confianza": confianza, "texto": texto}


def _exp(tipo_deuda="Deuda Relacional", scoring="A", keywords=None, evs=None):
    return {
        "nombre": "Nubank", "vertical": "fintech", "scoring": scoring,
        "score_icp": 80, "profundidad_dolor": 90, "viabilidad": "alta",
        "tipo_deuda": tipo_deuda, "deuda_razon": "fricción",
        "keywords": keywords or ["friccion_retencion", "reduccion_personal"],
        "patrones": [{"patron": "x", "razonamiento": "y", "senales": []}],
        "evidencias": evs or [
            _ev(url="https://a.com/1", fuente="A"),
            _ev(url="https://b.com/2", fuente="B", tipo_evento="despido"),
            _ev(url="https://c.com/3", fuente="C"),
        ],
    }


def _version(exp, fecha="2026-07-25", num=1, previo=""):
    val = validar_expediente(exp)
    huella = generar_huella_digital(exp, val, fecha)
    return crear_version(exp, val, huella, "sistema", num, previo)


# ── crear_version ─────────────────────────────────────────────────────────────

def test_crear_version_campos_completos():
    v = _version(_exp())
    for campo in ("version", "hash", "hash_previo", "fecha", "usuario", "motor",
                  "pipeline", "hipotesis", "scoring", "veredicto", "solidez",
                  "suficiencia", "nivel_evidencia", "nivel_confianza",
                  "dolor_cultural", "patrones", "narrativa", "keywords"):
        assert campo in v
    assert v["version"] == 1
    assert len(v["hash"]) == 64


def test_crear_version_hash_ignora_fecha():
    a = _version(_exp(), fecha="2000-01-01")
    b = _version(_exp(), fecha="2099-12-31")
    assert a["hash"] == b["hash"]


# ── comparar_versiones / detectar_cambios ─────────────────────────────────────

def test_comparar_versiones_detecta_cambio_dolor():
    a = _version(_exp(tipo_deuda="Deuda Relacional"))
    b = _version(_exp(tipo_deuda="Deuda Moral"))
    campos = {c["campo"] for c in comparar_versiones(a, b)}
    assert "dolor_cultural" in campos or "hipotesis" in campos


def test_comparar_versiones_vacio():
    assert comparar_versiones({}, {"x": 1}) == []


def test_detectar_cambios():
    a = _version(_exp(scoring="A"))
    b = dict(a); b["scoring"] = "B"
    r = detectar_cambios(a, b)
    assert r["hubo_cambio"] is True
    assert "scoring" in r["campos"]


def test_detectar_sin_cambios():
    a = _version(_exp())
    assert detectar_cambios(a, dict(a))["hubo_cambio"] is False


# ── timeline / evolución / historial ──────────────────────────────────────────

def _serie():
    v1 = _version(_exp(), num=1)
    v2 = dict(v1); v2.update(version=2, solidez=v1["solidez"] + 10,
                             suficiencia=v1["suficiencia"] + 5, narrativa="otra",
                             dolor_cultural="Deuda Moral", veredicto="VALIDADA")
    return [v2, v1]  # desordenadas a propósito


def test_timeline_ordenada():
    tl = construir_timeline(_serie())
    assert [t["version"] for t in tl] == [1, 2]


def test_calcular_evolucion():
    ev = calcular_evolucion(_serie())
    assert ev["versiones"] == 2
    assert ev["solidez"]["tendencia"] == "ascendente"
    assert ev["solidez"]["delta"] == 10
    assert ev["dolor_cambio"] is True
    assert ev["narrativa_cambios"] == 1


def test_calcular_evolucion_vacia():
    assert calcular_evolucion([])["versiones"] == 0


def test_calcular_evolucion_tendencias():
    v1 = _version(_exp(), num=1)
    baja = dict(v1); baja.update(version=2, solidez=v1["solidez"] - 20,
                                 suficiencia=v1["suficiencia"])
    ev = calcular_evolucion([v1, baja])
    assert ev["solidez"]["tendencia"] == "descendente"
    assert ev["suficiencia"]["tendencia"] == "estable"


def test_emitir_historial():
    h = emitir_historial("Nubank", _serie())
    assert h["org"] == "Nubank"
    assert h["total_versiones"] == 2
    assert len(h["cambios"]) == 1
    assert h["timeline"] and h["evolucion"]["versiones"] == 2


# ── Persistencia inmutable ────────────────────────────────────────────────────

def _guardar(db, exp, fecha="2026-07-25"):
    val = validar_expediente(exp)
    huella = generar_huella_digital(exp, val, fecha)
    return store.guardar_version(db, exp["nombre"], exp, val, huella)


def test_guardar_version_inmutable_dedup(db):
    exp = _exp()
    r1 = _guardar(db, exp)
    assert r1["guardado"] is True and r1["version"] == 1
    # Mismo estado ⇒ no crea versión nueva (inmutable, sin duplicar).
    r2 = _guardar(db, exp)
    assert r2["guardado"] is False and r2["version"] == 1
    assert db.fetch_one("SELECT COUNT(*) c FROM memoria_cientifica")["c"] == 1


def test_guardar_version_nueva_si_cambia(db):
    _guardar(db, _exp(tipo_deuda="Deuda Relacional"))
    r2 = _guardar(db, _exp(tipo_deuda="Deuda Moral", keywords=["reduccion_personal"]))
    assert r2["guardado"] is True and r2["version"] == 2
    hist = store.recuperar_historial(db, "Nubank")
    assert len(hist) == 2
    assert hist[1]["hash_previo"] == hist[0]["hash"]  # enlazado


# ── Endpoints ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, empresa, url, medio, keywords):
    import hashlib
    h = hashlib.sha256(f"{empresa}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{empresa} enfrenta fricción", ahora_iso(), "2026-07-01", url, medio, empresa,
         "queja", "prensa", h, "google_news", _json.dumps(keywords), 0.8, "Alta",
         "Startup", "ok", ahora_iso()))


def test_endpoint_historial(client, db):
    for i, m in enumerate(["Medio A", "Medio B", "Medio C"]):
        _insertar(db, "Memo", f"https://m{i}.com/1", m, ["friccion_retencion", "reduccion_personal"])
    r = client.get("/historial/Memo")
    assert r.status_code == 200
    data = r.json()
    assert data["org"] == "Memo"
    assert data["total_versiones"] == 1
    assert "timeline" in data and "evolucion" in data


def test_endpoint_timeline_y_versiones(client, db):
    _insertar(db, "Memo2", "https://x.com/1", "Medio X", ["friccion_retencion"])
    assert client.get("/timeline/Memo2").json()["total"] == 1
    v = client.get("/versiones/Memo2").json()
    assert v["total"] == 1 and v["versiones"][0]["version"] == 1


def test_endpoint_historial_reproducible(client, db):
    _insertar(db, "Memo3", "https://y.com/1", "Medio Y", ["friccion_retencion"])
    client.get("/historial/Memo3")
    client.get("/historial/Memo3")  # idempotente: no crea versión nueva
    assert db.fetch_one(
        "SELECT COUNT(*) c FROM memoria_cientifica WHERE org_nombre='Memo3'")["c"] == 1


def test_auditoria_registra_memoria(client, db):
    _insertar(db, "MemoAud", "https://z.com/1", "Medio Z", ["friccion_retencion"])
    client.get("/auditoria/MemoAud")
    assert db.fetch_one(
        "SELECT COUNT(*) c FROM memoria_cientifica WHERE org_nombre='MemoAud'")["c"] == 1
