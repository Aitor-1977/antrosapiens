"""Tests: Gobernanza Científica, Auditoría y Reproducibilidad (Capa 12).

Cubre las 14 funciones puras + persistencia + endpoints + dossier. Verifica
determinismo y reproducibilidad (mismo insumo ⇒ misma huella, mismo certificado,
misma auditoría, ignorando la fecha de emisión). 100% offline.
"""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from hd_scraper.db.models import ahora_iso
from hd_scraper.validacion_cientifica import validar_expediente
from hd_scraper import gobernanza_store as store
from hd_scraper.gobernanza import (
    ETAPAS_PIPELINE,
    MOTOR_NOMBRE,
    VERSION_GOBERNANZA,
    VERSION_PIPELINE,
    auditar_expediente,
    comparar_versiones,
    construir_linea_tiempo,
    emitir_certificado,
    firmar_motor,
    generar_bitacora,
    generar_huella_digital,
    registrar_decision,
    registrar_version_corpus,
    registrar_version_expediente,
    registrar_version_modelo,
    registrar_version_pipeline,
    registrar_version_taxonomia,
    validar_integridad,
    verificar_consistencia,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _ev(url="https://a.com/1", fuente="Medio A", fecha="2026-07-01",
        tipo_evento="queja", confianza=0.8, texto="fricción y churn"):
    return {"url": url, "fuente": fuente, "fecha": fecha,
            "tipo_evento": tipo_evento, "confianza": confianza, "texto": texto}


def _exp_solido():
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
            _ev(url="https://medioa.com/1", fuente="Medio A"),
            _ev(url="https://mediob.com/2", fuente="Medio B", tipo_evento="despido"),
            _ev(url="https://medioc.com/3", fuente="Medio C"),
        ],
    }


def _exp_pobre():
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


@pytest.fixture()
def solido():
    exp = _exp_solido()
    return exp, validar_expediente(exp)


@pytest.fixture()
def pobre():
    exp = _exp_pobre()
    return exp, validar_expediente(exp)


# ── 1-5. Versionado ───────────────────────────────────────────────────────────

def test_version_modelo():
    v = registrar_version_modelo()
    assert v["componente"] == "motor_inferencia"
    assert v["version"] and len(v["hash"]) == 64


def test_version_taxonomia_determinista():
    a, b = registrar_version_taxonomia(), registrar_version_taxonomia()
    assert a == b
    assert a["componente"] == "taxonomia_dolor_cultural"


def test_version_corpus_depende_de_evidencias():
    h1 = registrar_version_corpus(_exp_solido()["evidencias"])["hash"]
    h2 = registrar_version_corpus(_exp_pobre()["evidencias"])["hash"]
    assert h1 != h2
    assert registrar_version_corpus([])["total_evidencias"] == 0


def test_version_pipeline_incluye_etapas():
    v = registrar_version_pipeline()
    assert v["version"] == VERSION_PIPELINE
    assert list(v["etapas"]) == list(ETAPAS_PIPELINE)


def test_version_expediente_cambia_con_contenido():
    exp = _exp_solido()
    h1 = registrar_version_expediente(exp)["hash"]
    exp["scoring"] = "C"
    h2 = registrar_version_expediente(exp)["hash"]
    assert h1 != h2


# ── 6. Huella digital ─────────────────────────────────────────────────────────

def test_huella_tiene_todos_los_campos(solido):
    exp, val = solido
    h = generar_huella_digital(exp, val, "2026-07-25")
    assert h["id"].startswith("HD-")
    assert len(h["hash"]) == 64
    assert h["version"] == VERSION_GOBERNANZA
    assert h["motor"] == MOTOR_NOMBRE
    for comp in ("motor", "taxonomia", "corpus", "pipeline", "expediente",
                 "dictamen", "dossier", "dolormap", "drift", "onlife", "validacion"):
        assert comp in h["versiones"]


def test_huella_hash_ignora_fecha(solido):
    exp, val = solido
    a = generar_huella_digital(exp, val, "2000-01-01")
    b = generar_huella_digital(exp, val, "2099-12-31")
    assert a["hash"] == b["hash"]
    assert a["id"] == b["id"]


def test_huella_cambia_con_expediente(solido):
    exp, val = solido
    h1 = generar_huella_digital(exp, val)["hash"]
    exp2 = _exp_solido()
    exp2["tipo_deuda"] = "Deuda Moral"
    h2 = generar_huella_digital(exp2, validar_expediente(exp2))["hash"]
    assert h1 != h2


# ── 7. Integridad ─────────────────────────────────────────────────────────────

def test_integridad_ok(solido):
    exp, val = solido
    h = generar_huella_digital(exp, val)
    assert validar_integridad(exp, h)["integra"] is True


def test_integridad_detecta_manipulacion(solido):
    exp, val = solido
    h = generar_huella_digital(exp, val)
    exp["scoring"] = "C"  # alterar el expediente tras firmar
    res = validar_integridad(exp, h)
    assert res["integra"] is False
    assert res["expediente_ok"] is False


# ── 8. Consistencia ───────────────────────────────────────────────────────────

def test_consistencia_ok(solido):
    exp, val = solido
    assert verificar_consistencia(exp, val)["consistente"] is True


def test_consistencia_detecta_incoherencia(solido):
    exp, val = solido
    val["dictamen_cientifico"]["hipotesis_bloqueada"] = not val["bloqueo"]["bloqueada"]
    res = verificar_consistencia(exp, val)
    assert res["consistente"] is False
    assert "bloqueo_coherente" in res["incoherencias"]


# ── 9. Comparación de versiones ───────────────────────────────────────────────

def test_comparar_versiones_sin_previa():
    assert comparar_versiones({}, {"hash": "x"}) == []


def test_comparar_versiones_detecta_cambios(solido):
    exp, val = solido
    h1 = generar_huella_digital(exp, val)
    h2 = _json.loads(_json.dumps(h1))
    h2["versiones"]["motor"] = "9.9.9"
    h2["hash"] = "otro"
    cambios = comparar_versiones(h1, h2)
    campos = {c["campo"] for c in cambios}
    assert "version.motor" in campos
    assert "hash" in campos


# ── 10. Línea de tiempo ───────────────────────────────────────────────────────

def test_linea_tiempo_ordenada():
    exp = _exp_solido()
    exp["evidencias"] = [
        _ev(url="https://a.com/1", fecha="2026-03-01"),
        _ev(url="https://b.com/2", fecha="2026-01-01"),
        _ev(url="https://c.com/3", fecha=""),
    ]
    tl = construir_linea_tiempo(exp)
    assert [e["fecha"] for e in tl] == ["2026-01-01", "2026-03-01", "sin_fecha"]


# ── 11. Registro de decisión ──────────────────────────────────────────────────

def test_registrar_decision():
    d = registrar_decision("regla_ejecutada", "solidez", "alta", "detalle", "1.0.0")
    assert d["tipo"] == "regla_ejecutada"
    assert d["regla"] == "solidez"
    assert d["version_algoritmo"] == "1.0.0"


# ── 12. Bitácora ──────────────────────────────────────────────────────────────

def test_bitacora_registra_evidencia_y_reglas(solido):
    exp, val = solido
    bit = generar_bitacora(exp, val)
    assert bit["resumen"]["recibidas"] == 3
    assert bit["resumen"]["reglas_ejecutadas"] == 6
    tipos = {d["tipo"] for d in bit["decisiones"]}
    assert "evidencia_recibida" in tipos
    assert "regla_ejecutada" in tipos


def test_bitacora_registra_bloqueo(pobre):
    exp, val = pobre
    bit = generar_bitacora(exp, val)
    assert bit["resumen"]["reglas_bloqueo"] >= 1
    assert any(d["tipo"] == "regla_bloqueo" for d in bit["decisiones"])
    assert any(d["tipo"] == "evidencia_descartada" for d in bit["decisiones"]) or \
        bit["resumen"]["descartadas"] == 0


# ── 13. Certificado ───────────────────────────────────────────────────────────

def test_certificado_completo(solido):
    exp, val = solido
    h = generar_huella_digital(exp, val, "2026-07-25")
    cert = emitir_certificado(exp, val, h, "2026-07-25")
    for campo in ("certificado_id", "fecha", "id", "hash", "version", "estado",
                  "veredicto", "nivel_evidencia", "nivel_confianza", "solidez",
                  "suficiencia", "firma_motor", "motor"):
        assert campo in cert
    assert cert["estado"] in ("CERTIFICADO", "CERTIFICADO_PRELIMINAR")
    assert cert["firma_motor"].startswith("AS-MOTORA::")


def test_certificado_bloqueado(pobre):
    exp, val = pobre
    h = generar_huella_digital(exp, val)
    cert = emitir_certificado(exp, val, h)
    assert cert["estado"] == "BLOQUEADO"


def test_firma_motor_determinista():
    assert firmar_motor("abc", "1.0.0", "VALIDADA") == firmar_motor("abc", "1.0.0", "VALIDADA")
    assert firmar_motor("abc", "1.0.0", "VALIDADA") != firmar_motor("abc", "1.0.0", "BLOQUEADA")


# ── 14. Auditoría (orquestador) ───────────────────────────────────────────────

def test_auditoria_estructura_completa(solido):
    exp, val = solido
    aud = auditar_expediente(exp, val, "2026-07-25")
    for clave in ("resumen", "historial", "versionado", "bitacora", "cambios",
                  "huellas_digitales", "trazabilidad", "integridad",
                  "consistencia", "reproducibilidad", "certificado"):
        assert clave in aud
    assert aud["resumen"]["integra"] is True
    assert len(aud["versionado"]) == 5


# ── Reproducibilidad (evidencia) ──────────────────────────────────────────────

def test_auditoria_reproducible_ignora_fecha(solido):
    exp, val = solido
    a = auditar_expediente(exp, val, "2000-01-01")
    b = auditar_expediente(exp, val, "2099-12-31")
    assert a["resumen"]["hash"] == b["resumen"]["hash"]
    assert a["certificado"]["firma_motor"] == b["certificado"]["firma_motor"]
    assert a["bitacora"] == b["bitacora"]


# ── Persistencia (tablas de gobernanza) ───────────────────────────────────────

def test_persistencia_idempotente(db, solido):
    exp, val = solido
    aud = auditar_expediente(exp, val, ahora_iso())
    r1 = store.persistir_gobernanza(db, exp["nombre"], aud)
    assert r1["huella"] is True
    assert r1["auditoria"] is True
    assert r1["certificado"] is True
    assert r1["bitacora"] > 0
    # Reejecutar no duplica.
    r2 = store.persistir_gobernanza(db, exp["nombre"], aud)
    assert r2["huella"] is False
    assert r2["auditoria"] is False
    assert r2["certificado"] is False
    assert r2["bitacora"] == 0
    # Verificar filas.
    assert db.fetch_one("SELECT COUNT(*) c FROM huellas_digitales")["c"] == 1
    assert db.fetch_one("SELECT COUNT(*) c FROM certificados")["c"] == 1
    assert db.fetch_one("SELECT COUNT(*) c FROM versionado_modelo")["c"] == 5


# ── Integración: endpoints y dossier ──────────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar_evidencia(db, empresa, url, medio, keywords, tipo_evento="queja",
                        confianza=0.8, fecha="2026-07-01"):
    import hashlib
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


def test_endpoint_auditoria(client, db):
    for i, medio in enumerate(["Medio A", "Medio B", "Medio C"]):
        _insertar_evidencia(db, "Auditable", f"https://m{i}.com/1", medio,
                            ["friccion_retencion", "reduccion_personal"])
    r = client.get("/auditoria/Auditable")
    assert r.status_code == 200
    data = r.json()
    assert data["resumen"]["org"] == "Auditable"
    assert data["integridad"]["integra"] is True
    assert data["certificado"]["firma_motor"].startswith("AS-MOTORA::")
    # Persistió en tablas.
    assert db.fetch_one("SELECT COUNT(*) c FROM auditoria_expedientes")["c"] == 1
    assert db.fetch_one("SELECT COUNT(*) c FROM bitacora_decisiones")["c"] > 0


def test_endpoint_auditoria_es_reproducible(client, db):
    _insertar_evidencia(db, "Repro", "https://r.com/1", "Medio R", ["friccion_retencion"])
    h1 = client.get("/auditoria/Repro").json()["resumen"]["hash"]
    h2 = client.get("/auditoria/Repro").json()["resumen"]["hash"]
    assert h1 == h2  # mismo insumo ⇒ misma huella (ignora fecha)


def test_endpoint_certificado(client, db):
    for i, medio in enumerate(["Medio A", "Medio B", "Medio C"]):
        _insertar_evidencia(db, "Certificable", f"https://c{i}.com/1", medio,
                            ["friccion_retencion", "reduccion_personal"])
    r = client.get("/certificado/Certificable")
    assert r.status_code == 200
    cert = r.json()
    assert cert["estado"] in ("CERTIFICADO", "CERTIFICADO_PRELIMINAR")
    assert len(cert["hash"]) == 64
    assert db.fetch_one("SELECT COUNT(*) c FROM certificados")["c"] == 1


def test_expedientes_llevan_gobernanza(client, db):
    _insertar_evidencia(db, "ConGob", "https://g.com/1", "Medio G", ["friccion_retencion"])
    exp = client.get("/expedientes").json()["expedientes"][0]
    assert "gobernanza" in exp
    assert "huella" in exp and len(exp["huella"]) == 64
    assert exp["gobernanza"]["huella_digital"]["id"].startswith("HD-")


def test_dossier_incluye_gobernanza(client, db):
    _insertar_evidencia(db, "DossierGob", "https://d.com/1", "Medio D", ["friccion_retencion"])
    r = client.get("/dossier/DossierGob")
    assert r.status_code == 200
    assert "Gobernanza Científica (Capa 12)" in r.text
    assert "Huella Digital" in r.text
    assert "Certificado Científico" in r.text
    assert "Firma del Motor" in r.text


# ── Cobertura de ramas adicionales ───────────────────────────────────────────

def test_evidencias_forma_dolormap_en_linea_tiempo():
    exp = _exp_solido()
    exp["evidencias"] = {"total": 1, "items": [_ev(fecha="2025-05-05")]}
    tl = construir_linea_tiempo(exp)
    assert tl and tl[0]["fecha"] == "2025-05-05"


def test_integridad_detecta_taxonomia_y_corpus_alterados(solido):
    exp, val = solido
    h = generar_huella_digital(exp, val)
    h["hashes"]["taxonomia"] = "bad"
    h["hashes"]["corpus"] = "bad"
    res = validar_integridad(exp, h)
    assert res["integra"] is False
    assert res["taxonomia_ok"] is False
    assert res["corpus_ok"] is False
    assert len(res["detalle"]) == 2


def test_bitacora_descarta_evidencia_sin_fecha():
    exp = _exp_solido()
    exp["evidencias"].append(_ev(url="https://sinfecha.com/9", fuente="SF", fecha=""))
    val = validar_expediente(exp)
    bit = generar_bitacora(exp, val)
    assert bit["resumen"]["descartadas"] >= 1
    assert any(d["tipo"] == "evidencia_descartada" for d in bit["decisiones"])


def _val_con_confianza(c):
    exp = _exp_solido()
    val = validar_expediente(exp)
    val["solidez"]["confianza_agregada"] = c
    return exp, val


def test_certificado_nivel_confianza_media():
    exp, val = _val_con_confianza(0.6)
    h = generar_huella_digital(exp, val)
    assert emitir_certificado(exp, val, h)["nivel_confianza"] == "Media"


def test_certificado_nivel_confianza_baja():
    exp, val = _val_con_confianza(0.2)
    h = generar_huella_digital(exp, val)
    assert emitir_certificado(exp, val, h)["nivel_confianza"] == "Baja"
