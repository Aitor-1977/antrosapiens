"""Tests: paridad de forma del Expediente Vivo (Cutover Arquitectura 1.0).

Verifica que Motor A emite EXACTAMENTE las formas OrganizacionObservada (listado),
Dossier (detalle) y Drift que consumen los componentes tipados de RadarHD, de
forma determinista y sin inventar campos (comercial → null; DolorMap → null).
"""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper import expediente_vivo as ev


# ── Datos de expediente sintéticos (forma _construir_expedientes) ─────────────

def _ev_dict(url, fecha="2026-07-01", fuente=None, tipo="queja", conf=0.8, texto="t"):
    return {"url": url, "fuente": fuente or url, "fecha": fecha,
            "tipo_evento": tipo, "confianza": conf, "texto": texto}


def _exp(nombre, tipo_deuda="Deuda Relacional", vertical="fintech", categoria="Startup",
         viabilidad="alta", intensidad="Alta", scoring="A", score_icp=70, profundidad=80,
         keywords=None, deuda_secundaria="", evs=None, senal_dominante="churn"):
    evs = evs or [_ev_dict("u1", fuente="M1", tipo="queja"),
                  _ev_dict("u2", fuente="M2", tipo="contratacion"),
                  _ev_dict("u3", fuente="M3", tipo="lanzamiento")]
    return {
        "nombre": nombre, "tipo_deuda": tipo_deuda, "vertical": vertical,
        "categoria": categoria, "viabilidad": viabilidad, "intensidad": intensidad,
        "scoring": scoring, "score_icp": score_icp, "profundidad_dolor": profundidad,
        "senal_dominante": senal_dominante, "deuda_razon": "fricción de retención",
        "deuda_secundaria": deuda_secundaria, "razon": "señal de dolor; profundidad 80.",
        "decisor_sugerido": "CEO", "angulo_conversacion": "retención",
        "keywords": keywords or ["friccion_retencion"],
        "patrones": [{"patron": "P1", "senales": ["friccion_retencion", "churn"]}],
        "total_evidencias": len(evs), "evidencias": evs,
    }


def _conjunto():
    return [
        _exp("Nubank", "Deuda Relacional", "fintech", score_icp=80),
        _exp("Kavak", "Deuda Relacional", "fintech", viabilidad="baja", intensidad="Baja",
             scoring="B", score_icp=40, keywords=["expansion"], senal_dominante="expansion",
             evs=[_ev_dict("k1", fuente="M4", tipo="ronda")]),
        _exp("Clip", "Deuda Temporal", "healthtech", score_icp=95, profundidad=95,
             keywords=["cierre_operaciones"], evs=[_ev_dict("c1", "2026-05-01", tipo="despido")]),
    ]


# ── Listado (OrganizacionObservada) ──────────────────────────────────────────

CLAVES_ORG = {
    "organizacion_id", "nombre_display", "intensidad_label", "consistencia_label",
    "calidad_evidencia_label", "num_senales", "num_fuentes_distintas", "tipos_evidencia",
    "madurez", "patrones_observados", "que_cambio", "hipotesis_deuda", "viabilidad_hd",
    "taxonomia", "implicacion_sistemica", "alerta", "tiene_evidencia_operativa",
    "tiene_evidencia_narrativa", "fecha_ultima_senal", "curaduria", "inferencia_antropologica",
}


def test_listado_forma_y_orden():
    d = ev.listado(_conjunto())
    assert set(d) == {"resumen", "total", "organizaciones"}
    assert d["total"] == 3
    for o in d["organizaciones"]:
        assert set(o) == CLAVES_ORG
        assert set(o["viabilidad_hd"]) == {"nivel", "razon"}
        assert set(o["taxonomia"]) == {"marco", "subtipo"}
        assert o["taxonomia"]["marco"] == "Deuda Cultural Situacional-Simbólica™"


def test_listado_ids_deterministas_alfabeticos():
    d = ev.listado(_conjunto())
    ids = {o["nombre_display"]: o["organizacion_id"] for o in d["organizaciones"]}
    # Orden alfabético: Clip=0, Kavak=1, Nubank=2.
    assert ids == {"Clip": 0, "Kavak": 1, "Nubank": 2}


def test_curaduria_y_inferencia_forma():
    o = ev.listado(_conjunto())["organizaciones"][0]
    cur = o["curaduria"]
    assert set(cur) == {"narrativa_dominante", "nivel_confianza", "patrones",
                        "contradicciones", "vacios", "duplicadas_descartadas"}
    assert cur["nivel_confianza"] in {"Alto", "Medio", "Bajo"}
    for p in cur["patrones"]:
        assert set(p) == {"patron", "num_senales", "fuentes"}
    inf = o["inferencia_antropologica"]
    assert set(inf) == {"patron_dominante", "tensiones", "contradicciones_estructurales",
                        "vacios_criticos", "clasificacion_deuda", "hipotesis", "explicacion",
                        "solidez", "trazabilidad_valida"}
    assert inf["solidez"] in {"Alta", "Media", "Baja"}
    assert set(inf["clasificacion_deuda"]) == {"subtipo", "evidencia_ids"}
    assert set(inf["hipotesis"]) == {"texto", "evidencia_ids"}
    if inf["patron_dominante"] is not None:
        assert set(inf["patron_dominante"]) == {"patron", "num_senales", "evidencia_ids"}


def test_evidencia_operativa_vs_narrativa():
    o = {x["nombre_display"]: x for x in ev.listado(_conjunto())["organizaciones"]}
    # Nubank tiene contratacion (operativa) y queja/lanzamiento (narrativa).
    assert o["Nubank"]["tiene_evidencia_operativa"] is True
    assert o["Nubank"]["tiene_evidencia_narrativa"] is True
    # Kavak solo ronda (operativa), sin narrativa.
    assert o["Kavak"]["tiene_evidencia_operativa"] is True
    assert o["Kavak"]["tiene_evidencia_narrativa"] is False


def test_determinista():
    assert ev.listado(_conjunto()) == ev.listado(_conjunto())


# ── Detalle (Dossier) ─────────────────────────────────────────────────────────

CLAVES_DOSSIER_EXTRA = {
    "cadena_evidencia", "fuentes", "contexto_ecosistemico",
    "recomendacion_estrategica", "dictamen_pericial", "tiene_analisis_onlife", "dolormap",
}


def test_detalle_forma_completa():
    exps = _conjunto()
    d = ev.detalle(exps, 2)  # Nubank
    assert d is not None and d["nombre_display"] == "Nubank"
    assert CLAVES_ORG | CLAVES_DOSSIER_EXTRA <= set(d)
    # Comercial (Motor C) y DolorMap: null, nunca inventados.
    assert d["recomendacion_estrategica"] is None
    assert d["dictamen_pericial"] is None
    assert d["dolormap"] is None
    # cadena_evidencia con ids deterministas 0..n-1 y forma EvidenciaItem.
    for i, item in enumerate(d["cadena_evidencia"]):
        assert item["id"] == i
        assert set(item) == {"id", "fecha", "fuente", "tipo_fuente", "tipo_evento",
                             "tipo_deuda", "cita_textual", "url", "confianza"}


def test_detalle_contexto_ecosistemico_forma():
    ctx = ev.detalle(_conjunto(), 2)["contexto_ecosistemico"]
    assert set(ctx) == {"posicion_relativa", "cluster", "organizaciones_relacionadas",
                        "patrones_compartidos", "es_centinela", "es_atipica",
                        "centinelas_cercanos", "atipicos_cercanos", "hipotesis_vinculada"}
    # Nubank y Kavak comparten cluster Deuda Relacional|fintech.
    assert ctx["cluster"] is not None
    assert 1 in ctx["organizaciones_relacionadas"]  # Kavak


def test_detalle_id_inexistente_none():
    assert ev.detalle(_conjunto(), 999) is None


def test_evidencia_ids_trazables_a_cadena():
    d = ev.detalle(_conjunto(), 2)
    ids_validos = {it["id"] for it in d["cadena_evidencia"]}
    inf = d["inferencia_antropologica"]
    assert set(inf["hipotesis"]["evidencia_ids"]) <= ids_validos
    assert set(inf["clasificacion_deuda"]["evidencia_ids"]) <= ids_validos
    for t in inf["tensiones"]:
        assert set(t["evidencia_ids"]) <= ids_validos


# ── Drift ─────────────────────────────────────────────────────────────────────

def test_drift_forma():
    d = ev.drift(_conjunto(), 2)  # Nubank: queja + lanzamiento son narrativos
    assert set(d) == {"organizacion_id", "drift"}
    assert set(d["drift"]) == {"detectado", "resumen", "ultima_fecha", "num_observaciones"}
    assert d["drift"]["detectado"] is True
    assert d["drift"]["num_observaciones"] == 2


def test_drift_sin_narrativa():
    d = ev.drift(_conjunto(), 1)  # Kavak: solo ronda (operativa)
    assert d["drift"]["detectado"] is False
    assert d["drift"]["num_observaciones"] == 0


def test_drift_id_inexistente_none():
    assert ev.drift(_conjunto(), 999) is None


# ── Ramas deterministas (etiquetas cualitativas y casos límite) ───────────────

def test_solidez_alta_y_consistencia_solida():
    evs = [_ev_dict(f"s{i}", fuente=f"M{i}", tipo="queja") for i in range(6)]
    exp = _exp("Fuerte", score_icp=95, profundidad=100, evs=evs,
               keywords=["friccion_retencion", "reduccion_personal"])
    o = ev.organizacion_observada(exp, {"Fuerte": 0})
    assert o["inferencia_antropologica"]["solidez"] == "Alta"
    assert o["consistencia_label"] == "Sólida"


def test_consistencia_moderada_dos_fuentes():
    evs = [_ev_dict("a", fuente="M1"), _ev_dict("b", fuente="M2")]
    o = ev.organizacion_observada(_exp("Dos", evs=evs), {"Dos": 0})
    assert o["consistencia_label"] == "Moderada"


def test_viabilidad_no_determinada_sin_deuda():
    exp = _exp("Vacia", tipo_deuda="", viabilidad="descartable", intensidad="Baja",
               keywords=["sin_senal"])
    o = ev.organizacion_observada(exp, {"Vacia": 0})
    assert o["viabilidad_hd"]["nivel"] == "No determinada"
    assert o["hipotesis_deuda"] == ""
    assert o["taxonomia"]["subtipo"] == "No determinado"
    assert "sin implicación sistémica determinable" in o["implicacion_sistemica"].lower()
    assert o["alerta"] is None


def test_alerta_alta_sin_intensidad_alta():
    o = ev.organizacion_observada(_exp("Media", viabilidad="alta", intensidad="Media"),
                                  {"Media": 0})
    assert o["alerta"] == "Alta"


def test_tension_dolor_y_crecimiento():
    exp = _exp("Mixta", keywords=["friccion_retencion", "expansion"])
    inf = ev.organizacion_observada(exp, {"Mixta": 0})["inferencia_antropologica"]
    assert any("dolor y de crecimiento" in t["descripcion"] for t in inf["tensiones"])


# ── Endpoints (stack completo con BD real) ────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    import hd_scraper.onlife as ol
    monkeypatch.setattr(ol, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, emp, url, medio, kws, tipo="queja", fecha="2026-07-01"):
    import hashlib
    h = hashlib.sha256(f"{emp}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{emp} fintech enfrenta fricción y churn", ahora_iso(), fecha, url, medio, emp,
         tipo, "prensa", h, "google_news", _json.dumps(kws), 0.8, "Alta", "Startup",
         "ok", ahora_iso()))


@pytest.fixture()
def poblado(client, db):
    for i, m in enumerate(["Medio A", "Medio B", "Medio C"]):
        _insertar(db, "Nubank", f"https://n{i}.com/1", m,
                  ["friccion_retencion", "reduccion_personal"])
    _insertar(db, "Kavak", "https://k.com/1", "Medio D", ["expansion"], tipo="contratacion")
    return client


def test_endpoint_listado(poblado):
    r = poblado.get("/organizaciones")
    assert r.status_code == 200
    d = r.json()
    assert "generado_en" in d and d["total"] >= 1
    assert all(set(o) == CLAVES_ORG for o in d["organizaciones"])


def test_endpoint_detalle_por_id(poblado):
    listado = poblado.get("/organizaciones").json()["organizaciones"]
    oid = listado[0]["organizacion_id"]
    r = poblado.get(f"/organizaciones/{oid}")
    assert r.status_code == 200
    d = r.json()
    assert d["organizacion_id"] == oid
    assert "cadena_evidencia" in d and d["recomendacion_estrategica"] is None
    assert d["tiene_analisis_onlife"] is False  # sin señales onlife


def test_endpoint_detalle_404(poblado):
    assert poblado.get("/organizaciones/9999").status_code == 404


def test_endpoint_drift(poblado):
    listado = poblado.get("/organizaciones").json()["organizaciones"]
    oid = next(o["organizacion_id"] for o in listado if o["nombre_display"] == "Nubank")
    r = poblado.get(f"/organizaciones/{oid}/drift")
    assert r.status_code == 200
    assert r.json()["drift"]["detectado"] is True


def test_endpoint_drift_404(poblado):
    assert poblado.get("/organizaciones/9999/drift").status_code == 404
