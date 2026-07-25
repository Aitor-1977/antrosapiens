"""Tests: Cutover Arquitectura 1.0 — inteligencia ecosistémica en Motor A.

Cubre las funciones nuevas de observatorio.py (clusters, outliers, centinelas,
calidad_corpus, riesgos_culturales, madurez_ecosistema, ranking_hd, prioridades,
oportunidades, contexto_ecosistemico, panorama_ecosistemico) y los endpoints
nuevos + el dossier JSON. 100% offline, determinista, sin IA.
"""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper.observatorio import (
    calidad_corpus,
    contexto_ecosistemico,
    detectar_centinelas,
    detectar_clusters,
    detectar_outliers,
    madurez_ecosistema,
    oportunidades,
    panorama_ecosistemico,
    prioridades,
    ranking_hd,
    riesgos_culturales,
    _nivel_confianza,
)


def _ev(url, fecha="2026-07-01", fuente=None, conf=0.8):
    return {"url": url, "fuente": fuente or url, "fecha": fecha,
            "tipo_evento": "queja", "confianza": conf, "texto": "t"}


def _exp(nombre, tipo_deuda="Deuda Relacional", vertical="fintech", scoring="A",
         score_icp=70, profundidad=80, total_ev=3, keywords=None, veredicto="VALIDADA",
         bloqueada=False, evs=None):
    return {
        "nombre": nombre, "tipo_deuda": tipo_deuda, "vertical": vertical,
        "scoring": scoring, "score_icp": score_icp, "profundidad_dolor": profundidad,
        "intensidad": "Alta", "total_evidencias": total_ev,
        "keywords": keywords or ["friccion_retencion"],
        "patrones": [{"patron": "P1"}],
        "decisor_sugerido": "CEO", "angulo_conversacion": "x", "deuda_razon": "fricción",
        "evidencias": evs or [_ev("u1"), _ev("u2", fuente="M2"), _ev("u3", fuente="M3")],
        "validacion_cientifica": {"veredicto": veredicto, "hipotesis_bloqueada": bloqueada,
                                  "solidez": 70, "suficiencia": 65, "nivel_evidencia": "I"},
    }


def _conjunto():
    return [
        _exp("Nubank", "Deuda Relacional", "fintech", score_icp=80),
        _exp("Kavak", "Deuda Relacional", "fintech", score_icp=40, keywords=["expansion"], veredicto="BLOQUEADA", bloqueada=True),
        _exp("Clip", "Deuda Estructural", "fintech", score_icp=95, profundidad=95, total_ev=1,
             keywords=["cierre_operaciones"], evs=[_ev("c1")]),
    ]


# ── clusters ──────────────────────────────────────────────────────────────────

def test_clusters_agrupa_por_deuda_vertical():
    cl = detectar_clusters(_conjunto())
    assert cl and cl[0]["tamano"] == 2  # Nubank + Kavak (Deuda Relacional|fintech)
    assert set(cl[0]["organizaciones"]) == {"Nubank", "Kavak"}


def test_clusters_ignora_singletons():
    cl = detectar_clusters([_exp("Solo", "Deuda X", "v")])
    assert cl == []


# ── outliers ──────────────────────────────────────────────────────────────────

def test_outliers_detecta_deuda_unica_y_profundidad():
    out = {o["nombre"]: o for o in detectar_outliers(_conjunto())}
    assert "Clip" in out  # deuda única (Estructural) + profundidad sin volumen
    assert any("única" in r or "profundidad" in r for r in out["Clip"]["razones"])


def test_outliers_vacio():
    assert detectar_outliers([]) == []


# ── centinelas ────────────────────────────────────────────────────────────────

def test_centinelas():
    cen = detectar_centinelas(_conjunto())
    assert any(c["nombre"] == "Clip" for c in cen)  # dolor profundo + corpus escaso


# ── calidad_corpus ────────────────────────────────────────────────────────────

def test_calidad_corpus():
    q = calidad_corpus(_conjunto())
    assert q["organizaciones"] == 3
    assert q["evidencias_totales"] == 7
    assert 0.0 <= q["ratio_fechado"] <= 1.0
    assert q["organizaciones_corpus_suficiente"] == 2  # Nubank, Kavak (3 ev)


def test_calidad_corpus_vacio():
    q = calidad_corpus([])
    assert q["evidencias_totales"] == 0 and q["ratio_fechado"] == 0.0


# ── riesgos / madurez ─────────────────────────────────────────────────────────

def test_riesgos_culturales():
    r = riesgos_culturales(_conjunto())
    assert "distribucion" in r and r["top_riesgo"]
    assert all(0 <= d["riesgo_global"] <= 100 for d in r["top_riesgo"])


def test_madurez_ecosistema():
    m = madurez_ecosistema(_conjunto())
    assert 0 <= m["promedio"] <= 100 and m["distribucion"]
    assert madurez_ecosistema([])["promedio"] == 0


# ── ranking_hd ────────────────────────────────────────────────────────────────

def test_ranking_hd():
    r = ranking_hd(_conjunto(), 10)
    assert r and r[0]["posicion"] == 1
    for item in r:
        assert item["prioridad"] in ("Alta", "Media", "Baja")
        assert "motivo" in item and "nivel_confianza" in item and "evidencias" in item


def test_nivel_confianza_mapea_grade():
    assert _nivel_confianza({"validacion_cientifica": {"nivel_evidencia": "I"}}) == "Alta"
    assert _nivel_confianza({"validacion_cientifica": {"nivel_evidencia": "II"}}) == "Media"
    assert _nivel_confianza({"validacion_cientifica": {"nivel_evidencia": "IV"}}) == "Baja"
    assert _nivel_confianza({}) == "Baja"


# ── prioridades ───────────────────────────────────────────────────────────────

def test_prioridades_validadas_primero():
    p = prioridades(_conjunto(), 10)
    # Kavak está BLOQUEADA ⇒ no puede ir antes que una VALIDADA.
    nombres = [x["nombre"] for x in p]
    assert nombres.index("Nubank") < nombres.index("Kavak")
    assert p[0]["prioridad_hd"] == 1


# ── oportunidades ─────────────────────────────────────────────────────────────

def test_oportunidades_solo_validadas_no_bloqueadas():
    ops = oportunidades(_conjunto(), 10)
    nombres = {o["nombre"] for o in ops}
    assert "Kavak" not in nombres  # bloqueada
    for o in ops:
        assert "por_que" in o and "para_quien" in o and "con_que_evidencia" in o
        assert "recomendacion" not in o and "accion_comercial" not in o  # sin comercial


def test_oportunidades_vacio_si_todo_bloqueado():
    exps = [_exp("X", veredicto="BLOQUEADA", bloqueada=True)]
    assert oportunidades(exps, 10) == []


def test_oportunidades_excluye_no_validada_no_bloqueada():
    # No bloqueada, pero veredicto NO_VALIDADA ⇒ no es oportunidad.
    exps = [_exp("Y", veredicto="NO_VALIDADA", bloqueada=False)]
    assert oportunidades(exps, 10) == []


def test_calidad_corpus_forma_dolormap():
    e = _exp("Z")
    e["evidencias"] = {"total": 1, "items": [_ev("z1")]}
    q = calidad_corpus([e])
    assert q["evidencias_totales"] == 1


# ── contexto / panorama ───────────────────────────────────────────────────────

def test_contexto_ecosistemico():
    ctx = contexto_ecosistemico("Clip", _conjunto())
    assert ctx["es_outlier"] is True
    assert ctx["posicion_ranking"] is not None
    assert "indicadores_ecosistema" in ctx


def test_panorama_completo_y_reproducible():
    exps = _conjunto()
    a = panorama_ecosistemico(exps, 10)
    b = panorama_ecosistemico(exps, 10)
    assert a == b  # determinista
    for k in ("indicadores", "clusters", "outliers", "centinelas", "riesgos_culturales",
              "madurez", "calidad_corpus", "ranking", "oportunidades", "prioridades"):
        assert k in a


# ══ Endpoints (integración) ══════════════════════════════════════════════════

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, emp, url, medio, kws, fecha="2026-07-01"):
    import hashlib
    h = hashlib.sha256(f"{emp}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{emp} fintech enfrenta fricción y churn", ahora_iso(), fecha, url, medio, emp,
         "queja", "prensa", h, "google_news", _json.dumps(kws), 0.8, "Alta", "Startup",
         "ok", ahora_iso()))


@pytest.fixture()
def poblado(client, db):
    for i, m in enumerate(["Medio A", "Medio B", "Medio C"]):
        _insertar(db, "Nubank", f"https://n{i}.com/1", m, ["friccion_retencion", "reduccion_personal"])
    _insertar(db, "Kavak", "https://k.com/1", "Medio D", ["expansion"])
    return client


def test_endpoint_ecosistema(poblado):
    d = poblado.get("/ecosistema").json()
    for k in ("clusters", "outliers", "centinelas", "riesgos_culturales", "madurez",
              "calidad_corpus", "ranking", "oportunidades", "prioridades"):
        assert k in d


def test_endpoints_ecosistema_sub(poblado):
    assert "clusters" in poblado.get("/ecosistema/clusters").json()
    assert "outliers" in poblado.get("/ecosistema/outliers").json()
    assert "centinelas" in poblado.get("/ecosistema/centinelas").json()
    assert "distribucion" in poblado.get("/ecosistema/riesgos").json()
    assert "promedio" in poblado.get("/ecosistema/madurez").json()
    assert "evidencias_totales" in poblado.get("/calidad-corpus").json()


def test_endpoint_ranking(poblado):
    d = poblado.get("/ranking").json()
    assert d["ranking"] and d["ranking"][0]["posicion"] == 1


def test_endpoint_oportunidades_y_prioridades(poblado):
    assert "oportunidades" in poblado.get("/oportunidades").json()
    assert "prioridades" in poblado.get("/prioridades").json()


def test_endpoint_dossier_json_completo(poblado):
    r = poblado.get("/dossier/Nubank", params={"formato": "json"})
    assert r.status_code == 200
    assert "application/json" in r.headers["content-type"]
    d = r.json()
    esperados = ["resumen_ejecutivo", "narrativa_dominante", "hipotesis_central",
                 "clasificacion_deuda_cultural", "nivel_confianza", "calidad_evidencia",
                 "profundidad_friccion", "patrones", "contradicciones", "vacios",
                 "drift", "onlife", "dolormap", "validacion_cientifica", "gobernanza",
                 "auditoria", "cronologia", "cadena_evidencia", "fuentes",
                 "clusters_relacionados", "outliers_relacionados", "contexto_ecosistemico",
                 "ranking", "prioridad_hd", "estado_pipeline"]
    faltan = [k for k in esperados if k not in d]
    assert not faltan, f"faltan claves: {faltan}"
    assert d["contrato"] == "motor_a.dossier.v1"


def test_dossier_html_sigue_funcionando(poblado):
    r = poblado.get("/dossier/Nubank")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "Dossier de Inteligencia" in r.text
