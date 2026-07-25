"""Tests: Comparador Temporal y Ecosistémico (Capa 14)."""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper.comparador import (
    comparar_dolor,
    comparar_ecosistemas,
    comparar_narrativas,
    comparar_organizaciones,
    comparar_patrones,
    comparar_periodos,
    comparar_validaciones,
    detectar_convergencias,
    detectar_divergencias,
    generar_matriz,
)


def _ev(url, fecha, tipo="queja"):
    return {"url": url, "fuente": url, "fecha": fecha, "tipo_evento": tipo,
            "confianza": 0.8, "texto": "t"}


def _exp(nombre="A", scoring="A", tipo_deuda="Deuda Relacional", vertical="fintech",
         score_icp=70, keywords=None, patrones=None, evs=None):
    return {
        "nombre": nombre, "scoring": scoring, "tipo_deuda": tipo_deuda,
        "vertical": vertical, "score_icp": score_icp, "intensidad": "Alta",
        "senal_dominante": "friccion_retencion", "profundidad_dolor": 80,
        "total_evidencias": len(evs or []),
        "keywords": keywords or ["friccion_retencion", "crecimiento"],
        "patrones": patrones if patrones is not None else [{"patron": "P1"}],
        "evidencias": evs or [],
    }


# ── 1. comparar_organizaciones ────────────────────────────────────────────────

def test_comparar_organizaciones():
    a = _exp("A", keywords=["friccion_retencion", "expansion"])
    b = _exp("B", tipo_deuda="Deuda Moral", keywords=["reduccion_personal", "expansion"])
    r = comparar_organizaciones(a, b)
    assert r["org_a"] == "A" and r["org_b"] == "B"
    assert r["keywords_comunes"] == ["expansion"]
    campo_deuda = next(c for c in r["campos"] if c["campo"] == "tipo_deuda")
    assert campo_deuda["igual"] is False


# ── 2. comparar_ecosistemas ───────────────────────────────────────────────────

def test_comparar_ecosistemas():
    a = [_exp(keywords=["friccion_retencion"]), _exp(keywords=["reduccion_personal"])]
    b = [_exp(keywords=["crecimiento"])]
    r = comparar_ecosistemas(a, b, "fintech", "edtech")
    assert r["resumen_a"]["organizaciones"] == 2
    assert r["resumen_a"]["tasa_dolor"] == 1.0
    assert r["resumen_b"]["tasa_dolor"] == 0.0
    assert r["deltas"]["organizaciones"] == 1


def test_comparar_ecosistemas_vacio():
    r = comparar_ecosistemas([], [])
    assert r["resumen_a"]["organizaciones"] == 0
    assert r["resumen_a"]["tasa_dolor"] == 0.0


# ── 3. comparar_periodos ──────────────────────────────────────────────────────

def test_comparar_periodos():
    exp = _exp(evs=[_ev("u1", "2026-01-01"), _ev("u2", "2026-06-01", "despido")])
    r = comparar_periodos(exp, "2026-03-01")
    assert r["antes"]["evidencias"] == 1
    assert r["despues"]["evidencias"] == 1
    assert r["delta_evidencias"] == 0
    assert r["despues"]["tipos_evento"]["despido"] == 1


def test_comparar_periodos_forma_dolormap():
    exp = _exp()
    exp["evidencias"] = {"total": 1, "items": [_ev("u1", "2026-01-01")]}
    r = comparar_periodos(exp, "2026-03-01")
    assert r["antes"]["evidencias"] == 1


# ── 4. comparar_patrones ──────────────────────────────────────────────────────

def test_comparar_patrones():
    a = [_exp(patrones=[{"patron": "P1"}, {"patron": "P2"}])]
    b = [_exp(patrones=[{"patron": "P2"}, {"patron": "P3"}])]
    r = comparar_patrones(a, b)
    assert r["comunes"] == ["P2"]
    assert r["solo_a"] == ["P1"]
    assert r["solo_b"] == ["P3"]


# ── 5. comparar_narrativas ────────────────────────────────────────────────────

def test_comparar_narrativas():
    r = comparar_narrativas("crecimiento acelerado fricción cliente",
                            "fricción cliente recorte equipo")
    assert 0.0 < r["solapamiento"] <= 1.0
    assert "fricción" in r["tokens_comunes"] or "cliente" in r["tokens_comunes"]


def test_comparar_narrativas_vacio():
    assert comparar_narrativas("", "")["solapamiento"] == 0.0


# ── 6. comparar_dolor ─────────────────────────────────────────────────────────

def test_comparar_dolor():
    a = [_exp(tipo_deuda="Deuda Relacional"), _exp(tipo_deuda="Deuda Moral")]
    b = [_exp(tipo_deuda="Deuda Moral")]
    r = comparar_dolor(a, b)
    assert "Deuda Moral" in r["comunes"]
    assert "Deuda Relacional" in r["solo_a"]


# ── 7. comparar_validaciones ──────────────────────────────────────────────────

def test_comparar_validaciones():
    va = {"dictamen_cientifico": {"veredicto": "VALIDADA", "solidez": 80, "suficiencia": 70, "nivel_evidencia": "I"}}
    vb = {"dictamen_cientifico": {"veredicto": "BLOQUEADA", "solidez": 30, "suficiencia": 20, "nivel_evidencia": "IV"}}
    r = comparar_validaciones(va, vb)
    assert r["mismo_veredicto"] is False
    assert r["delta_solidez"] == 50
    assert r["delta_suficiencia"] == 50


# ── 8-9. convergencias / divergencias ─────────────────────────────────────────

def test_convergencias_y_divergencias():
    a = [_exp(tipo_deuda="Deuda Relacional", keywords=["friccion_retencion", "expansion"],
              patrones=[{"patron": "P1"}])]
    b = [_exp(tipo_deuda="Deuda Relacional", keywords=["reduccion_personal", "expansion"],
              patrones=[{"patron": "P2"}])]
    conv = detectar_convergencias(a, b)
    assert "Deuda Relacional" in conv["dolor_comun"]
    assert "expansion" in conv["senales_comunes"]
    div = detectar_divergencias(a, b)
    assert "friccion_retencion" in div["senales_solo_a"]
    assert "P1" in div["patrones_solo_a"]
    assert "P2" in div["patrones_solo_b"]


# ── 10. generar_matriz ────────────────────────────────────────────────────────

def test_generar_matriz():
    m = generar_matriz([_exp("B"), _exp("A")])
    assert m["organizaciones"] == 2
    assert [f["org"] for f in m["filas"]] == ["A", "B"]  # orden determinista
    assert m["filas"][0]["valores"]["n_patrones"] == 1


# ── Endpoints ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, empresa, url, medio, keywords, vertical_kw="fintech",
              fecha="2026-07-01", tipo="queja"):
    import hashlib
    h = hashlib.sha256(f"{empresa}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{empresa} {vertical_kw} enfrenta fricción", ahora_iso(), fecha, url, medio,
         empresa, tipo, "prensa", h, "google_news", _json.dumps(keywords), 0.8, "Alta",
         "Startup", "ok", ahora_iso()))


def test_endpoint_comparar(client, db):
    _insertar(db, "OrgA", "https://a.com/1", "M1", ["friccion_retencion"])
    _insertar(db, "OrgB", "https://b.com/1", "M2", ["reduccion_personal"])
    r = client.get("/comparar", params={"a": "OrgA", "b": "OrgB"})
    assert r.status_code == 200
    data = r.json()
    assert data["comparacion"]["org_a"] == "OrgA"
    assert data["matriz"]["organizaciones"] == 2


def test_endpoint_periodos(client, db):
    _insertar(db, "OrgP", "https://p.com/1", "M1", ["friccion_retencion"], fecha="2026-01-01")
    _insertar(db, "OrgP", "https://p.com/2", "M2", ["reduccion_personal"], fecha="2026-06-01")
    r = client.get("/periodos", params={"org": "OrgP", "corte": "2026-03-01"})
    assert r.status_code == 200
    data = r.json()
    assert data["antes"]["evidencias"] == 1
    assert data["despues"]["evidencias"] == 1


def test_endpoint_ecosistema_comparar(client, db):
    _insertar(db, "OrgF", "https://f.com/1", "M1", ["friccion_retencion"])
    r = client.get("/ecosistema/comparar", params={"a": "fintech", "b": "edtech"})
    assert r.status_code == 200
    assert "resumen_a" in r.json() and "deltas" in r.json()
