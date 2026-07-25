"""Tests: Observatorio LATAM (Capa 16) — inteligencia ecosistémica."""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper.observatorio import (
    analizar_ecosistema,
    analizar_region,
    analizar_vertical,
    calcular_indicadores,
    emitir_reporte_regional,
    identificar_patrones_regionales,
    identificar_tensiones,
)


def _exp(nombre="A", scoring="A", tipo_deuda="Deuda Relacional", vertical="fintech",
         categoria="Startup", keywords=None, patrones=None, bloqueada=False,
         total_ev=5, score_icp=70):
    return {
        "nombre": nombre, "scoring": scoring, "tipo_deuda": tipo_deuda,
        "vertical": vertical, "categoria": categoria, "score_icp": score_icp,
        "intensidad": "Alta", "profundidad_dolor": 80,
        "hipotesis_bloqueada": bloqueada, "total_evidencias": total_ev,
        "keywords": keywords or ["friccion_retencion"],
        "patrones": patrones if patrones is not None else [{"patron": "P1"}],
        "evidencias": [{"url": "u", "fuente": "M", "fecha": "2026-01-01",
                        "tipo_evento": "queja", "confianza": 0.8, "texto": "t"}],
    }


# ── calcular_indicadores ──────────────────────────────────────────────────────

def test_indicadores():
    exps = [_exp(keywords=["friccion_retencion"]),
            _exp(keywords=["crecimiento"], bloqueada=True)]
    ind = calcular_indicadores(exps)
    assert ind["organizaciones"] == 2
    assert ind["tasa_dolor"] == 0.5
    assert ind["tasa_cambio"] == 0.5
    assert ind["tasa_bloqueo"] == 0.5


def test_indicadores_vacio():
    ind = calcular_indicadores([])
    assert ind["organizaciones"] == 0 and ind["tasa_dolor"] == 0.0


# ── patrones / tensiones ──────────────────────────────────────────────────────

def test_patrones_regionales_ordenados():
    exps = [_exp(patrones=[{"patron": "P1"}]), _exp(patrones=[{"patron": "P1"}]),
            _exp(patrones=[{"patron": "P2"}])]
    pat = identificar_patrones_regionales(exps)
    assert pat[0] == {"patron": "P1", "organizaciones": 2}


def test_tensiones_recurrentes():
    exps = [_exp(tipo_deuda="Deuda Relacional"), _exp(tipo_deuda="Deuda Relacional"),
            _exp(tipo_deuda="Deuda Moral")]
    t = identificar_tensiones(exps)
    assert t["deudas_recurrentes"][0]["deuda"] == "Deuda Relacional"
    assert t["deudas_recurrentes"][0]["organizaciones"] == 2


def test_tensiones_convergencia():
    exps = [_exp(keywords=["friccion_retencion", "crecimiento"])]
    assert identificar_tensiones(exps)["organizaciones_en_convergencia"] == 1


# ── analizar_region / vertical / ecosistema ──────────────────────────────────

def test_analizar_region():
    r = analizar_region([_exp(), _exp()], "LATAM")
    assert r["etiqueta"] == "LATAM"
    assert r["indicadores"]["organizaciones"] == 2


def test_analizar_vertical_filtra():
    exps = [_exp(vertical="fintech"), _exp(vertical="edtech")]
    r = analizar_vertical(exps, "fintech")
    assert r["indicadores"]["organizaciones"] == 1


def test_analizar_ecosistema_filtra():
    exps = [_exp(categoria="VC"), _exp(categoria="Startup")]
    r = analizar_ecosistema(exps, "VC")
    assert r["indicadores"]["organizaciones"] == 1


# ── emitir_reporte_regional ───────────────────────────────────────────────────

def test_reporte_regional_completo():
    exps = [_exp("A", keywords=["friccion_retencion", "reduccion_personal"]),
            _exp("B", vertical="", bloqueada=True, total_ev=1)]
    rep = emitir_reporte_regional(exps, "LATAM")
    for clave in ("indicadores", "tensiones", "patrones_compartidos", "ranking",
                  "riesgos_comunes", "vacios_sistemicos"):
        assert clave in rep
    assert rep["total_organizaciones"] == 2
    assert rep["vacios_sistemicos"]["sin_vertical"] == 1
    assert rep["vacios_sistemicos"]["corpus_escaso"] == 1
    assert "distribucion_riesgo" in rep["riesgos_comunes"]


def test_reporte_reproducible():
    exps = [_exp("A"), _exp("B")]
    assert emitir_reporte_regional(exps, "LATAM") == emitir_reporte_regional(exps, "LATAM")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, empresa, url, medio, keywords, texto_extra=""):
    import hashlib
    h = hashlib.sha256(f"{empresa}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{empresa} enfrenta fricción {texto_extra}", ahora_iso(), "2026-01-01", url,
         medio, empresa, "queja", "prensa", h, "google_news", _json.dumps(keywords),
         0.8, "Alta", "Startup", "ok", ahora_iso()))


def test_endpoint_latam(client, db):
    _insertar(db, "OrgLat", "https://l.com/1", "M1", ["friccion_retencion"])
    r = client.get("/latam")
    assert r.status_code == 200
    assert r.json()["region"] == "LATAM"
    assert r.json()["total_organizaciones"] >= 1


def test_endpoint_latam_pais(client, db):
    _insertar(db, "OrgMx", "https://mx.com/1", "M1", ["friccion_retencion"], "en México")
    r = client.get("/latam/Mexico")
    assert r.status_code == 200
    assert r.json()["region"] == "Mexico"
    assert r.json()["total_organizaciones"] == 1


def test_endpoint_vertical(client, db):
    _insertar(db, "OrgFin", "https://f.com/1", "M1", ["friccion_retencion"])
    r = client.get("/vertical/fintech")
    assert r.status_code == 200
    assert "analisis" in r.json() and "reporte" in r.json()
