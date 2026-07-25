"""Tests: Motor Predictivo Antropológico (Capa 15) — reglas deterministas."""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper.predictivo import (
    calcular_estabilidad,
    calcular_madurez,
    calcular_tendencia,
    calcular_volatilidad,
    detectar_inflexiones,
    emitir_proyeccion,
    estimar_riesgo,
    proyectar_escenarios,
    serie_temporal,
)


def _ev(url, fecha, fuente="M", tipo="queja"):
    return {"url": url, "fuente": fuente, "fecha": fecha, "tipo_evento": tipo,
            "confianza": 0.8, "texto": "t"}


def _exp(keywords=None, profundidad=80, bloqueada=False, evs=None):
    return {
        "nombre": "Nubank", "keywords": keywords or ["friccion_retencion"],
        "profundidad_dolor": profundidad, "hipotesis_bloqueada": bloqueada,
        "evidencias": evs or [
            _ev("u1", "2026-01-05"), _ev("u2", "2026-02-05", "M2"),
            _ev("u3", "2026-02-15", "M3"), _ev("u4", "2026-04-05", "M4"),
        ],
    }


# ── serie_temporal ────────────────────────────────────────────────────────────

def test_serie_temporal_agrupa_por_mes():
    s = serie_temporal(_exp())
    assert s["periodos"] == ["2026-01", "2026-02", "2026-04"]
    assert s["valores"] == [1, 2, 1]


def test_serie_ignora_fechas_invalidas():
    exp = _exp(evs=[_ev("u1", ""), _ev("u2", "no_fechado"), _ev("u3", "2026-03-01")])
    assert serie_temporal(exp)["valores"] == [1]


# ── tendencia ─────────────────────────────────────────────────────────────────

def test_tendencia_ascendente():
    assert calcular_tendencia([1, 2, 3, 4])["direccion"] == "ascendente"


def test_tendencia_descendente():
    assert calcular_tendencia([4, 3, 2, 1])["direccion"] == "descendente"


def test_tendencia_estable_y_corta():
    assert calcular_tendencia([2, 2, 2])["direccion"] == "estable"
    assert calcular_tendencia([5])["direccion"] == "estable"


# ── estabilidad ───────────────────────────────────────────────────────────────

def test_estabilidad_maxima_serie_constante():
    assert calcular_estabilidad([3, 3, 3]) == 100


def test_estabilidad_corta_y_ceros():
    assert calcular_estabilidad([1]) == 100
    assert calcular_estabilidad([0, 0, 0]) == 100
    assert calcular_estabilidad([0, 5, 0]) == 0  # media 5/3? no: media>0


def test_estabilidad_baja_con_variacion():
    assert calcular_estabilidad([1, 10, 1, 10]) < 60


# ── inflexiones ───────────────────────────────────────────────────────────────

def test_inflexiones():
    assert detectar_inflexiones([1, 3, 2, 4]) == [1, 2]
    assert detectar_inflexiones([1, 2, 3]) == []
    assert detectar_inflexiones([1, 2]) == []


# ── volatilidad ───────────────────────────────────────────────────────────────

def test_volatilidad_rango():
    v = calcular_volatilidad([1, 10, 1, 10])
    assert 0 <= v <= 100 and v > 0
    assert calcular_volatilidad([5]) == 0


# ── escenarios ────────────────────────────────────────────────────────────────

def test_escenarios_deterministas():
    a = proyectar_escenarios([1, 2, 3, 4])
    b = proyectar_escenarios([1, 2, 3, 4])
    assert a == b
    assert a["optimista"] >= a["base"] >= a["pesimista"]


def test_escenarios_vacio():
    assert proyectar_escenarios([])["base"] == 0.0


# ── riesgo ────────────────────────────────────────────────────────────────────

def test_riesgo_alto_con_dolor_profundo():
    r = estimar_riesgo(_exp(keywords=["friccion_retencion", "reduccion_personal"],
                            profundidad=95, bloqueada=True))
    assert r["riesgo_cultural"] > 50
    assert r["nivel"] in ("alto", "medio", "bajo")
    assert 0 <= r["riesgo_global"] <= 100


def test_riesgo_bajo_sin_dolor():
    r = estimar_riesgo(_exp(keywords=["crecimiento"], profundidad=10),
                       serie=[1, 1, 1])
    assert r["riesgo_cultural"] < 40


# ── madurez ───────────────────────────────────────────────────────────────────

def test_madurez():
    m = calcular_madurez(_exp())
    assert 0 <= m["score"] <= 100
    assert m["nivel"] in ("naciente", "en_desarrollo", "consolidado", "maduro")
    assert m["fuentes"] == 4


def test_madurez_naciente_una_evidencia():
    m = calcular_madurez(_exp(evs=[_ev("u1", "2026-01-01")]))
    assert m["nivel"] == "naciente"


def test_madurez_maduro():
    evs = [_ev(f"u{i}", f"2026-0{i}-01", f"M{i}") for i in range(1, 7)]
    assert calcular_madurez(_exp(evs=evs))["nivel"] == "maduro"


def test_madurez_en_desarrollo():
    evs = [_ev("u1", "2026-01-01", "M1"), _ev("u2", "2026-02-01", "M2")]
    assert calcular_madurez(_exp(evs=evs))["nivel"] == "en_desarrollo"


def test_serie_forma_dolormap():
    exp = _exp()
    exp["evidencias"] = {"total": 1, "items": [_ev("u1", "2026-05-01")]}
    assert serie_temporal(exp)["valores"] == [1]


def test_helpers_defensivos():
    from hd_scraper.predictivo import _pendiente, _stddev
    assert _pendiente([1]) == 0.0
    assert _stddev([1]) == 0.0


# ── emitir_proyeccion ─────────────────────────────────────────────────────────

def test_emitir_proyeccion_completa_y_reproducible():
    exp = _exp()
    a = emitir_proyeccion(exp)
    b = emitir_proyeccion(exp)
    assert a == b
    for clave in ("serie", "tendencia", "estabilidad", "volatilidad",
                  "inflexiones", "escenarios", "riesgo", "madurez"):
        assert clave in a


# ── Endpoints ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, empresa, url, medio, fecha):
    import hashlib
    h = hashlib.sha256(f"{empresa}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{empresa} enfrenta fricción", ahora_iso(), fecha, url, medio, empresa,
         "queja", "prensa", h, "google_news", _json.dumps(["friccion_retencion"]),
         0.8, "Alta", "Startup", "ok", ahora_iso()))


def test_endpoint_proyeccion(client, db):
    for i, f in enumerate(["2026-01-05", "2026-02-05", "2026-03-05"]):
        _insertar(db, "Proy", f"https://p.com/{i}", f"M{i}", f)
    r = client.get("/proyeccion/Proy")
    assert r.status_code == 200
    data = r.json()
    assert data["org"] == "Proy"
    assert "tendencia" in data and "riesgo" in data and "madurez" in data


def test_endpoint_escenarios(client, db):
    _insertar(db, "Esc", "https://e.com/1", "M1", "2026-01-05")
    r = client.get("/escenarios/Esc")
    assert r.status_code == 200
    assert "escenarios" in r.json() and "serie" in r.json()
