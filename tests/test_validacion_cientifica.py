"""Tests: Validación Científica del Peritaje Antropológico (Capa 11).

Cubre las 14 funciones puras + la integración con el pipeline de inferencia,
el endpoint GET /validacion/{org} y la ampliación del dossier. 100% offline.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from hd_scraper.db.models import ahora_iso
from hd_scraper.validacion_cientifica import (
    MIN_EVIDENCIAS,
    MIN_FUENTES_INDEPENDIENTES,
    UMBRAL_SOLIDEZ_BLOQUEO,
    VEREDICTOS,
    calcular_confianza_agregada,
    calcular_solidez,
    calcular_suficiencia_corpus,
    clasificar_veredicto,
    contar_fuentes_independientes,
    detectar_contradicciones,
    detectar_vacios,
    emitir_dictamen_cientifico,
    evaluar_bloqueo_hipotesis,
    nivel_evidencia,
    validar_expediente,
    validar_fechado,
    validar_reproducibilidad,
    validar_trazabilidad,
)


# ── Fixtures de expedientes ───────────────────────────────────────────────────

def _ev(url="https://a.com/1", fuente="Medio A", fecha="2026-07-01",
        tipo_evento="ronda", confianza=0.8):
    return {"url": url, "fuente": fuente, "fecha": fecha,
            "tipo_evento": tipo_evento, "confianza": confianza}


def _exp_solido():
    """Expediente con evidencia suficiente, sólida y corroborada."""
    return {
        "nombre": "Nubank",
        "vertical": "fintech",
        "scoring": "A",
        "score_icp": 80,
        "profundidad_dolor": 90,
        "viabilidad": "alta",
        "tipo_deuda": "Deuda Relacional",
        "keywords": ["friccion_retencion", "reduccion_personal"],
        "patrones": [{"patron": "x", "razonamiento": "y", "senales": []}],
        "evidencias": [
            _ev(url="https://medioa.com/1", fuente="Medio A", tipo_evento="queja"),
            _ev(url="https://mediob.com/2", fuente="Medio B", tipo_evento="despido"),
            _ev(url="https://medioc.com/3", fuente="Medio C", tipo_evento="queja"),
            _ev(url="https://mediod.com/4", fuente="Medio D", tipo_evento="queja"),
        ],
    }


def _exp_pobre():
    """Expediente insuficiente: una sola evidencia, una sola fuente."""
    return {
        "nombre": "Startup X",
        "vertical": "",
        "scoring": "A",
        "score_icp": 40,
        "profundidad_dolor": 90,
        "viabilidad": "media",
        "tipo_deuda": "Deuda Relacional",
        "keywords": ["friccion_retencion"],
        "patrones": [],
        "evidencias": [_ev(url="https://unica.com/1", fuente="Único")],
    }


# ── 1. contar_fuentes_independientes ─────────────────────────────────────────

def test_fuentes_independientes_cuenta_dominios_distintos():
    assert contar_fuentes_independientes(_exp_solido()["evidencias"]) == 4


def test_fuentes_independientes_no_acumula_mismo_dominio():
    evs = [_ev(url="https://mismo.com/1"), _ev(url="https://mismo.com/2")]
    assert contar_fuentes_independientes(evs) == 1


def test_fuentes_independientes_cae_a_nombre_medio_sin_url():
    evs = [_ev(url="", fuente="Solo Nombre")]
    assert contar_fuentes_independientes(evs) == 1


def test_fuentes_independientes_vacio():
    assert contar_fuentes_independientes([]) == 0


# ── 2. calcular_confianza_agregada ───────────────────────────────────────────

def test_confianza_agregada_sube_con_fuentes_independientes():
    una = calcular_confianza_agregada([_ev(url="https://a.com/1", confianza=0.6)])
    dos = calcular_confianza_agregada([
        _ev(url="https://a.com/1", confianza=0.6),
        _ev(url="https://b.com/2", confianza=0.6),
    ])
    assert dos > una
    assert 0.0 <= dos <= 1.0


def test_confianza_agregada_no_acumula_mismo_dominio():
    una = calcular_confianza_agregada([_ev(url="https://a.com/1", confianza=0.6)])
    repetida = calcular_confianza_agregada([
        _ev(url="https://a.com/1", confianza=0.6),
        _ev(url="https://a.com/2", confianza=0.6),
    ])
    assert repetida == una


def test_confianza_agregada_vacia_es_cero():
    assert calcular_confianza_agregada([]) == 0.0


# ── 3. validar_trazabilidad ──────────────────────────────────────────────────

def test_trazabilidad_completa():
    t = validar_trazabilidad(_exp_solido())
    assert t["completa"] is True
    assert t["no_trazables"] == 0
    assert t["ratio"] == 1.0


def test_trazabilidad_detecta_faltantes():
    exp = _exp_solido()
    exp["evidencias"].append(_ev(url="", fuente=""))
    t = validar_trazabilidad(exp)
    assert t["completa"] is False
    assert t["no_trazables"] == 1
    assert "url_fuente" in t["detalle"][0]["faltan"]
    assert "nombre_medio" in t["detalle"][0]["faltan"]


# ── 4. validar_fechado ───────────────────────────────────────────────────────

def test_fechado_todas_consumibles():
    f = validar_fechado(_exp_solido())
    assert f["todas_consumibles"] is True
    assert f["no_fechadas"] == 0


def test_fechado_detecta_no_fechado():
    exp = _exp_solido()
    exp["evidencias"].append(_ev(fecha="no_fechado"))
    exp["evidencias"].append(_ev(fecha=""))
    f = validar_fechado(exp)
    assert f["no_fechadas"] == 2
    assert f["todas_consumibles"] is False


# ── 5. calcular_suficiencia_corpus ───────────────────────────────────────────

def test_suficiencia_alta_con_corpus_solido():
    s = calcular_suficiencia_corpus(_exp_solido())
    assert s["suficiente"] is True
    assert s["nivel"] == "suficiente"
    assert s["fuentes_independientes"] >= MIN_FUENTES_INDEPENDIENTES


def test_suficiencia_insuficiente_con_corpus_pobre():
    s = calcular_suficiencia_corpus(_exp_pobre())
    assert s["suficiente"] is False
    assert s["evidencias"] < MIN_EVIDENCIAS


# ── 6. calcular_solidez ──────────────────────────────────────────────────────

def test_solidez_acotada_0_100():
    s = calcular_solidez(_exp_solido())
    assert 0 <= s["score"] <= 100
    assert s["nivel"] in ("alta", "media", "baja")


def test_solidez_pobre_menor_que_solida():
    assert calcular_solidez(_exp_pobre())["score"] < calcular_solidez(_exp_solido())["score"]


# ── 7. detectar_contradicciones ──────────────────────────────────────────────

def test_contradiccion_dolor_y_crecimiento_sin_patron():
    exp = _exp_pobre()
    exp["keywords"] = ["friccion_retencion", "crecimiento"]
    exp["patrones"] = []
    tipos = {c["tipo"] for c in detectar_contradicciones(exp)}
    assert "dolor_y_crecimiento_sin_patron" in tipos


def test_contradiccion_eventos_opuestos():
    exp = _exp_solido()
    exp["evidencias"] = [
        _ev(url="https://a.com/1", tipo_evento="despido"),
        _ev(url="https://b.com/2", tipo_evento="contratacion"),
    ]
    tipos = {c["tipo"] for c in detectar_contradicciones(exp)}
    assert "eventos_opuestos" in tipos


def test_contradiccion_prioridad_vs_viabilidad():
    exp = _exp_solido()
    exp["viabilidad"] = "descartable"
    tipos = {c["tipo"] for c in detectar_contradicciones(exp)}
    assert "prioridad_vs_viabilidad" in tipos


def test_sin_contradicciones_en_expediente_limpio():
    assert detectar_contradicciones(_exp_solido()) == []


# ── 8. detectar_vacios ───────────────────────────────────────────────────────

def test_vacios_en_expediente_pobre():
    tipos = {v["tipo"] for v in detectar_vacios(_exp_pobre())}
    assert "sin_vertical" in tipos
    assert "fuente_unica" in tipos
    assert "corpus_escaso" in tipos
    assert "senal_unica" in tipos
    assert "sin_convergencia" in tipos


def test_expediente_solido_sin_vacios_criticos():
    tipos = {v["tipo"] for v in detectar_vacios(_exp_solido())}
    assert "fuente_unica" not in tipos
    assert "corpus_escaso" not in tipos


# ── 9. validar_reproducibilidad ──────────────────────────────────────────────

def test_reproducibilidad_consistente():
    r = validar_reproducibilidad(_exp_solido())
    assert r["determinista"] is True
    assert r["consistente"] is True
    assert r["reproducible"] is True


def test_reproducibilidad_detecta_discrepancia():
    exp = _exp_solido()
    exp["scoring"] = "C"  # incoherente con keywords de dolor (debería ser A)
    r = validar_reproducibilidad(exp)
    assert r["consistente"] is False
    assert any(d["campo"] == "scoring" for d in r["discrepancias"])


# ── 10. nivel_evidencia ──────────────────────────────────────────────────────

def test_nivel_evidencia_alta_para_solido():
    assert nivel_evidencia(_exp_solido())["nivel"] == "I"


def test_nivel_evidencia_bajo_para_pobre():
    assert nivel_evidencia(_exp_pobre())["nivel"] in ("III", "IV")


# ── 11. evaluar_bloqueo_hipotesis ────────────────────────────────────────────

def test_bloqueo_por_evidencia_insuficiente():
    b = evaluar_bloqueo_hipotesis(_exp_pobre())
    assert b["bloqueada"] is True
    assert b["motivos"]


def test_no_bloqueo_con_corpus_solido():
    assert evaluar_bloqueo_hipotesis(_exp_solido())["bloqueada"] is False


def test_bloqueo_sin_hipotesis():
    exp = _exp_solido()
    exp["tipo_deuda"] = ""
    b = evaluar_bloqueo_hipotesis(exp)
    assert b["bloqueada"] is True


# ── 12. clasificar_veredicto ─────────────────────────────────────────────────

def test_clasificar_veredicto_valores():
    assert clasificar_veredicto(80, 80, 0, False, True) == "VALIDADA"
    assert clasificar_veredicto(50, 50, 0, False, True) == "VALIDADA_PARCIAL"
    assert clasificar_veredicto(80, 80, 1, False, True) == "NO_VALIDADA"
    assert clasificar_veredicto(10, 10, 0, True, True) == "BLOQUEADA"
    assert clasificar_veredicto(80, 80, 0, False, False) == "SIN_HIPOTESIS"
    # Sin contradicción, sin bloqueo, pero por debajo del umbral parcial.
    assert clasificar_veredicto(30, 30, 0, False, True) == "NO_VALIDADA"


# ── 13. emitir_dictamen_cientifico ───────────────────────────────────────────

def test_dictamen_solido_validado():
    d = emitir_dictamen_cientifico(_exp_solido())
    assert d["veredicto"] in VEREDICTOS
    assert d["veredicto"] == "VALIDADA"
    assert d["hipotesis_bloqueada"] is False
    assert d["reproducible"] is True
    assert d["resumen"]
    assert d["recomendacion"]


def test_dictamen_pobre_bloqueado():
    d = emitir_dictamen_cientifico(_exp_pobre())
    assert d["veredicto"] == "BLOQUEADA"
    assert d["hipotesis_bloqueada"] is True
    assert d["limitaciones"]


def test_dictamen_determinista():
    exp = _exp_solido()
    assert emitir_dictamen_cientifico(exp) == emitir_dictamen_cientifico(exp)


# ── 14. validar_expediente ───────────────────────────────────────────────────

def test_validar_expediente_estructura_completa():
    r = validar_expediente(_exp_solido())
    for clave in ("trazabilidad", "fechado", "suficiencia_corpus", "solidez",
                  "contradicciones", "vacios", "reproducibilidad",
                  "nivel_evidencia", "bloqueo", "dictamen_cientifico"):
        assert clave in r
    assert r["dictamen_cientifico"]["veredicto"] == "VALIDADA"


# ── Integración: pipeline, endpoint y dossier ────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar_evidencia(db, empresa, url, medio, keywords, tipo_evento="queja",
                        confianza=0.8, fecha="2026-07-01"):
    import hashlib
    import json as _json
    h = hashlib.sha256(f"{empresa}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{empresa} enfrenta fricción y churn de clientes", ahora_iso(), fecha, url,
         medio, empresa, tipo_evento, "prensa", h, "google_news", _json.dumps(keywords),
         confianza, "Alta", "Startup", "ok", ahora_iso()),
    )


def test_endpoint_validacion_bloquea_org_con_una_fuente(client, db):
    _insertar_evidencia(db, "SoloUna", "https://x.com/1", "Medio X",
                        ["friccion_retencion"])
    r = client.get("/validacion/SoloUna")
    assert r.status_code == 200
    data = r.json()
    assert data["org"] == "SoloUna"
    assert data["bloqueo"]["bloqueada"] is True
    assert data["dictamen_cientifico"]["veredicto"] == "BLOQUEADA"


def test_endpoint_validacion_valida_org_corroborada(client, db):
    for i, medio in enumerate(["Medio A", "Medio B", "Medio C"]):
        _insertar_evidencia(db, "Corroborada", f"https://medio{i}.com/1", medio,
                            ["friccion_retencion", "reduccion_personal"])
    r = client.get("/validacion/Corroborada")
    assert r.status_code == 200
    data = r.json()
    assert data["suficiencia_corpus"]["fuentes_independientes"] == 3
    assert data["dictamen_cientifico"]["veredicto"] in ("VALIDADA", "VALIDADA_PARCIAL")
    assert data["reproducibilidad"]["reproducible"] is True


def test_endpoint_validacion_sin_evidencia(client, db):
    r = client.get("/validacion/Fantasma")
    assert r.status_code == 200
    data = r.json()
    assert data["dictamen_cientifico"]["veredicto"] in ("BLOQUEADA", "SIN_HIPOTESIS")


def test_expedientes_incluyen_validacion(client, db):
    _insertar_evidencia(db, "ConVal", "https://y.com/1", "Medio Y",
                        ["friccion_retencion"])
    r = client.get("/expedientes")
    assert r.status_code == 200
    exps = r.json()["expedientes"]
    assert exps
    exp = exps[0]
    assert "validacion_cientifica" in exp
    assert "hipotesis_bloqueada" in exp
    assert exp["validacion_cientifica"]["veredicto"] in VEREDICTOS


def test_dossier_incluye_validacion_cientifica(client, db):
    _insertar_evidencia(db, "Dossierable", "https://z.com/1", "Medio Z",
                        ["friccion_retencion"])
    r = client.get("/dossier/Dossierable")
    assert r.status_code == 200
    assert "Validación Científica (Capa 11)" in r.text


# ── Cobertura de ramas adicionales ───────────────────────────────────────────

def test_acepta_evidencias_forma_dolormap():
    """La validación tolera evidencias anidadas {total, items} (forma dolormap)."""
    exp = _exp_solido()
    exp["evidencias"] = {"total": 4, "items": _exp_solido()["evidencias"]}
    t = validar_trazabilidad(exp)
    assert t["total"] == 4
    assert contar_fuentes_independientes(exp["evidencias"]["items"]) == 4


def test_confianza_malformada_no_rompe():
    evs = [{"url": "https://a.com/1", "confianza": "no-es-numero"}]
    assert calcular_confianza_agregada(evs) == 0.0


def test_dominio_con_www_se_normaliza():
    evs = [
        _ev(url="https://www.mismo.com/1"),
        _ev(url="https://mismo.com/2"),
    ]
    assert contar_fuentes_independientes(evs) == 1


def test_url_malformada_no_rompe():
    evs = [_ev(url="http://[::malformada", fuente="")]
    # No debe lanzar; cae a nombre de medio (vacío) ⇒ 0 fuentes.
    assert contar_fuentes_independientes(evs) == 0


def test_vacio_evidencia_sin_fecha():
    exp = _exp_solido()
    exp["evidencias"].append(_ev(fecha="no_fechado"))
    tipos = {v["tipo"] for v in detectar_vacios(exp)}
    assert "evidencia_sin_fecha" in tipos


def test_dictamen_no_validada_por_contradiccion_con_corpus():
    """Corpus suficiente pero con contradicción ⇒ NO_VALIDADA (no bloqueada)."""
    exp = _exp_solido()
    exp["evidencias"] = [
        _ev(url="https://a.com/1", tipo_evento="despido"),
        _ev(url="https://b.com/2", tipo_evento="contratacion"),
        _ev(url="https://c.com/3", tipo_evento="queja"),
        _ev(url="https://d.com/4", tipo_evento="queja"),
    ]
    d = emitir_dictamen_cientifico(exp)
    assert d["contradicciones"] >= 1
    assert d["veredicto"] == "NO_VALIDADA"
    assert "NO se valida" in d["resumen"]


def test_dictamen_limitacion_por_irreproducibilidad():
    exp = _exp_solido()
    exp["scoring"] = "C"  # incoherente con las señales de dolor
    d = emitir_dictamen_cientifico(exp)
    assert any("no se reproduce" in lim for lim in d["limitaciones"])


def test_bloqueo_por_suficiencia_bajo_umbral():
    """Una evidencia sin fecha y una sola señal ⇒ suficiencia bajo umbral."""
    exp = _exp_pobre()
    exp["evidencias"] = [_ev(url="https://a.com/1", fecha="no_fechado")]
    b = evaluar_bloqueo_hipotesis(exp)
    assert b["bloqueada"] is True
    assert any("Suficiencia de corpus bajo umbral" in m for m in b["motivos"])
