"""Reparación BC-I ↔ BC-II — Candidatos Comerciales (identidad referencial).

Cubre la batería obligatoria:
  A. A y B producen IDs diferentes.
  B. Reprocesar A produce el mismo ID.
  C. Evidencias de A y B nunca se mezclan.
  D. Candidato → prospecto correcto.
  E. Candidato → expediente correcto.
  F. Una transición de A no altera B.
  G. Transición → evidencia trazable.
  H. Datos existentes compatibles.
  I. Radar/scrape siguen funcionando.
Más: Regla Cero (G0) gateando detectado → observado.
"""
import hashlib

import pytest

from hd_scraper import candidato as cand
from hd_scraper import pipeline_comercial as pipe
from hd_scraper.db.database import Database
from hd_scraper.db.models import ahora_iso


# ── helpers ───────────────────────────────────────────────────────────────────

def _insertar_evidencia(db, empresa, url, texto=" enfrenta fricción"):
    h = hashlib.sha256(f"{empresa}{url}".encode()).hexdigest()
    db.execute(
        """INSERT INTO evidencias
             (cita_textual, fecha_extraccion, fecha_publicacion, url_fuente,
              nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion,
              hash_dedup, connector, keywords, confianza, calidad_captura,
              categoria, estado, creado_en)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (f"{empresa}{texto}", ahora_iso(), "2026-01-01", url, "Medio",
         empresa, "queja", "prensa", h, "google_news", '["friccion_retencion"]',
         0.8, "Alta", "Startup", "ok", ahora_iso()),
    )
    return db.fetch_one("SELECT id FROM evidencias WHERE url_fuente = ?",
                        (url,))["id"]


def _exp(nombre, url, huella="h-exp", veredicto="VALIDADA", bloqueada=False,
         confianza=0.8):
    return {
        "nombre": nombre,
        "huella": huella,
        "total_evidencias": 1,
        "evidencias": [{"url": url, "texto": f"{nombre} señal",
                        "confianza": confianza}],
        "validacion_cientifica": {"veredicto": veredicto,
                                  "hipotesis_bloqueada": bloqueada},
    }


@pytest.fixture()
def db():
    d = Database(":memory:")
    d.init_schema()
    yield d
    d.close()


@pytest.fixture(autouse=True)
def _monkey_db(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.pipeline_comercial.get_db", lambda: db)


# ── A. A y B producen IDs diferentes ──────────────────────────────────────────

def test_ids_distintos_para_orgs_distintas():
    assert cand.candidato_id("Acme Corp") != cand.candidato_id("Beta Inc")
    assert cand.candidato_id("A") != cand.candidato_id("B")


# ── B. Reprocesar A produce el mismo ID ───────────────────────────────────────

def test_id_reproducible():
    assert cand.candidato_id("Acme Corp") == cand.candidato_id("Acme Corp")
    assert cand.candidato_id("Acme Corp") == cand.candidato_id("acme corp")
    assert cand.candidato_id(" Acme  Corp ") == cand.candidato_id("Acme Corp")


def test_materializacion_idempotente(db):
    _insertar_evidencia(db, "Acme Corp", "https://a.com/1")
    exp = _exp("Acme Corp", "https://a.com/1")
    r1 = cand.materializar_candidatos(db, [exp])
    r2 = cand.materializar_candidatos(db, [exp])
    assert r1["materializados"] == 1
    assert r2["materializados"] == 0 and r2["actualizados"] == 1
    assert r1["candidatos"][0]["candidato_id"] == r2["candidatos"][0]["candidato_id"]
    filas = db.fetch_all("SELECT * FROM candidatos")
    assert len(filas) == 1
    trans = db.fetch_all("SELECT * FROM candidato_transiciones")
    assert len(trans) == 1  # la transición inicial no se duplica


# ── C. Evidencias de A y B nunca se mezclan ───────────────────────────────────

def test_evidencias_no_se_mezclan(db):
    eva = _insertar_evidencia(db, "Acme Corp", "https://a.com/1")
    evb = _insertar_evidencia(db, "Beta Inc", "https://b.com/1")
    cand.materializar_candidatos(db, [
        _exp("Acme Corp", "https://a.com/1"),
        _exp("Beta Inc", "https://b.com/1"),
    ])
    ca = cand.obtener_candidato(db, "Acme Corp")
    cb = cand.obtener_candidato(db, "Beta Inc")
    assert ca["candidato_id"] != cb["candidato_id"]
    assert ca["transiciones"][0]["evidencia_id"] == eva
    assert cb["transiciones"][0]["evidencia_id"] == evb
    assert ca["transiciones"][0]["evidencia_url"] == "https://a.com/1"
    assert cb["transiciones"][0]["evidencia_url"] == "https://b.com/1"
    # Las transiciones de A solo referencian evidencia de A.
    urls_a = {t["evidencia_url"] for t in ca["transiciones"]}
    assert "https://b.com/1" not in urls_a


# ── D. Candidato → prospecto correcto ─────────────────────────────────────────

def test_candidato_prospecto_correcto(db):
    db.execute(
        """INSERT INTO prospectos (nombre, categoria, escala, hash_dedup,
             creado_en, actualizado_en)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ("Acme Corp", "Startup", "11-50",
         hashlib.sha256("Acme Corp|Startup".encode()).hexdigest(),
         ahora_iso(), ahora_iso()),
    )
    pid = db.fetch_one("SELECT id FROM prospectos WHERE nombre = ?",
                       ("Acme Corp",))["id"]
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1")])
    c = cand.obtener_candidato(db, "Acme Corp")
    assert c["prospecto_id"] == pid
    assert c["prospecto"]["nombre"] == "Acme Corp"
    assert c["prospecto"]["categoria"] == "Startup"


def test_candidato_sin_prospecto_deja_nulo(db):
    _insertar_evidencia(db, "Acme Corp", "https://a.com/1")
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1")])
    c = cand.obtener_candidato(db, "Acme Corp")
    assert c["prospecto_id"] is None
    assert c["prospecto"] is None


# ── E. Candidato → expediente correcto ────────────────────────────────────────

def test_candidato_expediente_correcto(db):
    _insertar_evidencia(db, "Acme Corp", "https://a.com/1")
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1",
                                           huella="huella-acme")])
    c = cand.obtener_candidato(db, "Acme Corp")
    assert c["expediente_hash"] == "huella-acme"
    assert c["transiciones"][0]["expediente_hash"] == "huella-acme"


# ── F. Una transición de A no altera B ────────────────────────────────────────

def test_transicion_de_A_no_altera_B(db):
    cand.materializar_candidatos(db, [
        _exp("Acme Corp", "https://a.com/1"),
        _exp("Beta Inc", "https://b.com/1"),
    ])
    cand.observar(db, "Acme Corp", exp=_exp("Acme Corp", "https://a.com/1"))
    a = cand.obtener_candidato(db, "Acme Corp")
    b = cand.obtener_candidato(db, "Beta Inc")
    assert a["estado"] == "observado"
    assert b["estado"] == "detectado"   # B intacto
    assert len(b["transiciones"]) == 1  # B solo tiene su transición inicial

    cand.descartar(db, "Beta Inc", notas="fuera de alcance")
    a2 = cand.obtener_candidato(db, "Acme Corp")
    assert a2["estado"] == "observado"  # A intacto tras descartar B


# ── G. Transición → evidencia trazable ────────────────────────────────────────

def test_transicion_con_evidencia_trazable(db):
    evid = _insertar_evidencia(db, "Acme Corp", "https://a.com/1")
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1")])
    cand.observar(
        db, "Acme Corp", exp=_exp("Acme Corp", "https://a.com/1"),
        evidencia={"id": evid, "url": "https://a.com/1", "texto": "Acme Corp señal"},
        notas="confirmado por prensa",
    )
    cand.descartar(db, "Acme Corp", notas="decisión del operador",
                   evidencia={"url": "https://a.com/1", "texto": "Acme Corp señal"})
    c = cand.obtener_candidato(db, "Acme Corp")
    assert len(c["transiciones"]) == 3
    observado = c["transiciones"][1]
    assert observado["estado_hasta"] == "observado"
    assert observado["evidencia_id"] == evid
    assert observado["evidencia_url"] == "https://a.com/1"
    assert observado["evidencia_texto"] == "Acme Corp señal"
    descartado = c["transiciones"][2]
    assert descartado["estado_hasta"] == "descartado"
    assert descartado["evidencia_url"] == "https://a.com/1"
    assert descartado["notas"] == "decisión del operador"


# ── Regla Cero (G0) ───────────────────────────────────────────────────────────

def test_g0_deniega_sin_peritaje_validado(db):
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1",
                                           veredicto="BLOQUEADA", bloqueada=True)])
    with pytest.raises(cand.G0Denied):
        cand.observar(db, "Acme Corp",
                      exp=_exp("Acme Corp", "https://a.com/1",
                               veredicto="BLOQUEADA", bloqueada=True))
    assert cand.obtener_candidato(db, "Acme Corp")["estado"] == "detectado"


def test_g0_deniega_sin_dictamen(db):
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1",
                                           veredicto="BLOQUEADA", bloqueada=True)])
    with pytest.raises(cand.G0Denied):
        cand.observar(db, "Acme Corp", exp={})
    assert cand.obtener_candidato(db, "Acme Corp")["estado"] == "detectado"


def test_g0_permite_con_peritaje_validado(db):
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1")])
    r = cand.observar(db, "Acme Corp", exp=_exp("Acme Corp", "https://a.com/1"))
    assert r["estado"] == "observado"
    assert r["g0"]["permitido"] is True


def test_g0_deniega_parcial_con_hipotesis_bloqueada(db):
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1",
                                           veredicto="VALIDADA_PARCIAL",
                                           bloqueada=True)])
    with pytest.raises(cand.G0Denied):
        cand.observar(db, "Acme Corp",
                      exp=_exp("Acme Corp", "https://a.com/1",
                               veredicto="VALIDADA_PARCIAL", bloqueada=True))


def test_transiciones_invalidas_rechazadas(db):
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1")])
    exp = _exp("Acme Corp", "https://a.com/1")
    cand.observar(db, "Acme Corp", exp=exp)
    # observado → observado es inválido (el estado no cambia).
    with pytest.raises(ValueError, match="Transición inválida"):
        cand.observar(db, "Acme Corp", exp=exp)
    # observado → descartado sí es válido.
    cand.descartar(db, "Acme Corp", notas="fuera de alcance")
    # descartado → observado es inválido: solo se redetecta (descartado → detectado).
    with pytest.raises(ValueError, match="Transición inválida"):
        cand.observar(db, "Acme Corp", exp=exp)
    # descartado → descartado es inválido.
    with pytest.raises(ValueError, match="Transición inválida"):
        cand.descartar(db, "Acme Corp", notas="otra vez")
    assert cand.obtener_candidato(db, "Acme Corp")["estado"] == "descartado"


# ── H. Datos existentes compatibles ───────────────────────────────────────────

def test_pipeline_legacy_compatible(db):
    """Un registro de pipeline preexistente (sin candidato_id) sigue vivo."""
    dedup = hashlib.sha256("Acme Corp".lower().encode()).hexdigest()[:32]
    db.execute(
        """INSERT INTO pipeline_comercial
             (org_nombre, etapa, notas, resultado, hash_dedup, creado_en, actualizado_en)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("Acme Corp", "observacion", "", "", dedup, ahora_iso(), ahora_iso()),
    )
    r = pipe.avanzar("Acme Corp", "vigilancia", notas="migrado")
    assert r["etapa_anterior"] == "observacion"
    assert r["etapa"] == "vigilancia"
    p = pipe.obtener_pipeline("Acme Corp")
    assert p is not None
    assert p["candidato_id"] == cand.candidato_id("Acme Corp")  # backfilleado
    assert p["etapa"] == "vigilancia"
    # Solo una fila: el legacy se actualizó, no se duplicó.
    filas = db.fetch_all("SELECT * FROM pipeline_comercial")
    assert len(filas) == 1


def test_pipeline_y_candidato_mismo_org_mismo_id(db):
    _insertar_evidencia(db, "Acme Corp", "https://a.com/1")
    cand.materializar_candidatos(db, [_exp("Acme Corp", "https://a.com/1")])
    r = pipe.registrar_org("Acme Corp", etapa="vigilancia")
    assert r["candidato_id"] == cand.candidato_id("Acme Corp")
    p = pipe.obtener_pipeline("Acme Corp")
    assert p["candidato_id"] == cand.candidato_id("Acme Corp")
    assert p["estado_candidato"] == "detectado"
    assert p["expediente_hash"] == "h-exp"


def test_pipeline_listar_referencial(db):
    pipe.registrar_org("Acme Corp")
    pipe.registrar_org("Beta Inc", etapa="vigilancia")
    r = pipe.listar_pipeline()
    assert r["total"] == 2
    orgs = {o["org_nombre"]: o for o in r["organizaciones"]}
    assert orgs["Acme Corp"]["candidato_id"] == cand.candidato_id("Acme Corp")
    assert orgs["Beta Inc"]["candidato_id"] == cand.candidato_id("Beta Inc")
    assert orgs["Beta Inc"]["estado_candidato"] == "detectado"


# ── I. Radar/scrape siguen funcionando ────────────────────────────────────────

def test_radar_loop_sin_hook_no_cambia(monkeypatch):
    """radar_loop sin materializar_fn conserva exactamente el comportamiento."""
    from hd_scraper.db.models import QuerySpec
    from hd_scraper.radar import radar_loop
    monkeypatch.setattr(
        "hd_scraper.radar._tareas",
        lambda f, t: [QuerySpec(empresa="Acme", tipo_evento="ronda")],
    )

    def ejecutar(db, query, conectores):
        return [{"connector": "google_news", "escritos": 2, "vistos": 5}]

    def expedientes(categorias, limite):
        return {"total": 1, "resumen_scoring": {"A": 1, "B": 0, "C": 0},
                "expedientes": [_exp("Acme", "https://a.com/1")]}

    res = radar_loop(
        __import__("hd_scraper.filtros", fromlist=["FiltrosRadar"]).FiltrosRadar(),
        db=object(), ejecutar_fn=ejecutar, expedientes_fn=expedientes,
        presupuesto_s=60.0, max_rondas=2,
    )
    assert res["detencion"] in ("plan_completado", "max_rondas")
    assert res["total_escritos"] == 2
    assert res["rondas"][0]["orgs_nuevas"] == ["acme"]


def test_radar_loop_con_hook_materializa(db, monkeypatch):
    from hd_scraper.db.models import QuerySpec
    from hd_scraper.radar import radar_loop
    from hd_scraper.filtros import FiltrosRadar
    monkeypatch.setattr(
        "hd_scraper.radar._tareas",
        lambda f, t: [QuerySpec(empresa="Acme", tipo_evento="ronda")],
    )

    def ejecutar(db, query, conectores):
        return [{"connector": "google_news", "escritos": 1, "vistos": 1}]

    def expedientes(categorias, limite):
        return {"total": 1, "resumen_scoring": {"A": 1, "B": 0, "C": 0},
                "expedientes": [_exp("Acme", "https://a.com/1")]}

    res = radar_loop(FiltrosRadar(), db=db, ejecutar_fn=ejecutar,
                     expedientes_fn=expedientes, presupuesto_s=60.0,
                     max_rondas=2, materializar_fn=cand.materializar_candidatos)
    assert res["candidatos"] is not None
    c = cand.obtener_candidato(db, "Acme")
    assert c is not None and c["estado"] == "detectado"
    assert c["transiciones"][0]["estado_hasta"] == "detectado"


# ── API ───────────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    import importlib
    from hd_scraper.config import settings
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "test-token")
    from fastapi.testclient import TestClient
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


def test_api_materializar_y_listar(client, db):
    _insertar_evidencia(db, "Acme Corp", "https://a.com/1")
    r = client.post("/candidatos/materializar",
                    headers={"X-Ingest-Token": "test-token"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    # La API detecta la empresa desde el texto → "Acme" (determinista).
    assert body["candidatos"][0]["org_nombre"] == "Acme"

    lista = client.get("/candidatos")
    assert lista.status_code == 200
    assert lista.json()["total"] == 1
    assert lista.json()["candidatos"][0]["etiqueta_estado"] == "Detectado"

    detalle = client.get("/candidatos/Acme")
    assert detalle.status_code == 200
    # El expediente lo construye la API (huella real, no la del fixture).
    assert detalle.json()["expediente_hash"]
    assert detalle.json()["estado"] == "detectado"


def test_api_observar_g0_bloquea(client, db):
    _insertar_evidencia(db, "Acme Corp", "https://a.com/1")
    client.post("/candidatos/materializar",
                headers={"X-Ingest-Token": "test-token"})
    # Con una sola evidencia el Dictamen Científico es SIN_HIPOTESIS (hipótesis
    # bloqueada) ⇒ la Regla Cero impide avanzar → 409, determinista.
    r = client.post("/candidatos/observar",
                    headers={"X-Ingest-Token": "test-token"},
                    json={"org_nombre": "Acme Corp"})
    assert r.status_code == 409
    assert "Regla Cero" in r.json()["detail"]


def test_api_requires_token(client, db):
    _insertar_evidencia(db, "Acme Corp", "https://a.com/1")
    r = client.post("/candidatos/materializar")
    # HD_INGEST_TOKEN está configurado pero la cabecera falta → 401.
    assert r.status_code == 401
