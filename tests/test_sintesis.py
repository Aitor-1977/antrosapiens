"""Capa 19 · Síntesis Estructural: determinismo, grounding y contrato.

Verifica que la síntesis por organización reordena las señales Nivel 1 en el
esquema estricto [patrón, tensión/dolor, actores, sustancia] + evidencia_urls,
SIEMPRE grounded y reproducible (mismo insumo ⇒ mismo JSON).
"""
import importlib

import pytest

from hd_scraper.sintesis import sintetizar


def _evidencia(cita, *, url="https://medio.com/1", medio="Medio A",
               empresa="Acme", persona=None, cargo=None, tipo_evento="ronda",
               fecha="2026-07-01", confianza=0.8, keywords=None):
    return {
        "cita_textual": cita,
        "url_fuente": url,
        "nombre_medio": medio,
        "empresa_mencionada": empresa,
        "persona_citada": persona,
        "cargo": cargo,
        "tipo_evento": tipo_evento,
        "fecha_publicacion": fecha,
        "confianza": confianza,
        "keywords": keywords or [],
    }


def _corpus_ronda():
    return [
        _evidencia(f"Acme cierra una ronda de financiamiento {i}",
                   url=f"https://medio.com/ronda{i}", medio=f"Medio {i}",
                   keywords=["ronda_inversion"])
        for i in range(1, 5)
    ]


def test_sintetizar_esquema_y_patron():
    s = sintetizar(_corpus_ronda(), "Acme")
    assert s["org"] == "Acme"
    assert s["version_esquema"] == "sintesis_estructural.v1"
    assert s["estado"] == "sintetizado"
    assert s["patron_comportamiento"] == "levantamiento de capital (ronda de financiamiento)"
    assert s["nota"].startswith("Síntesis determinista preliminar")


def test_sintetizar_tension_grounded_cita_literal():
    evs = _corpus_ronda() + [
        _evidencia("Acme anuncia despidos y recorte de personal esta semana",
                   url="https://medio.com/despido", medio="Medio 9",
                   keywords=["reduccion_personal"]),
    ]
    s = sintetizar(evs, "Acme")
    assert s["tension_presente"] is True
    assert "recorte de personal" in s["senal_tension_dolor"]
    assert "despido" in s["marcadores_textuales"]
    assert "despidos y recorte de personal" in s["cita_tension"]


def test_sintetizar_sin_tension_no_inventa():
    s = sintetizar(_corpus_ronda(), "Acme")
    assert s["tension_presente"] is False
    assert s["senal_tension_dolor"] == "sin marcador de tensión explícito en el corpus"
    assert s["marcadores_textuales"] == []
    assert s["cita_tension"] == ""


def test_sintetizar_insuficiente_corpus():
    s = sintetizar(_corpus_ronda()[:1], "Acme")
    assert s["estado"] == "insuficiente"
    assert "se requieren 3" in s["motivo"]


def test_sintetizar_sin_marcador():
    evs = [_evidencia(f"Noticia neutral {i}", url=f"https://m.com/n{i}",
                      medio=f"Medio {i}", tipo_evento="", keywords=[])
           for i in range(1, 5)]
    s = sintetizar(evs, "Acme")
    assert s["estado"] == "sin_marcador"
    assert s["patron_comportamiento"] is None
    assert s["tension_presente"] is False


def test_sintetizar_determinista_mismo_insumo():
    a = sintetizar(_corpus_ronda(), "Acme")
    b = sintetizar(_corpus_ronda(), "Acme")
    assert a == b


def test_sintetizar_actores_involucrados():
    evs = _corpus_ronda() + [
        _evidencia("La directora María López dice que Acme crece",
                   url="https://medio.com/persona", medio="Medio 8",
                   persona="María López", cargo="Directora General"),
        _evidencia("Competidor S.A. invierte en Acme", url="https://medio.com/otra",
                   medio="Medio 7", empresa="Competidor S.A.",
                   keywords=["ronda_inversion"]),
    ]
    s = sintetizar(evs, "Acme")
    roles = {a["rol"]: a["nombre"] for a in s["actores_involucrados"]}
    assert roles["organización observada"] == "Acme"
    assert roles["persona citada — Directora General"] == "María López"
    assert roles["organización mencionada"] == "Competidor S.A."


def test_sintetizar_sustancia_y_urls():
    s = sintetizar(_corpus_ronda(), "Acme")
    m = s["sustancia_metrica"]
    assert m["evidencias"] == 4
    assert m["fuentes_distintas"] == 4
    assert m["umbral"] == "conforme"
    assert 0.0 <= m["indice_sustancia"] <= 1.0
    assert m["meses_cobertura"] == 1
    assert len(s["evidencia_urls"]) == 4
    assert len(s["evidencia_urls"]) == len(set(s["evidencia_urls"]))


@pytest.fixture()
def client(db, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    TestClient = fastapi.testclient.TestClient
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, empresa, url, keywords, tipo_evento="ronda", confianza=0.8):
    import hashlib
    import json as _json
    from hd_scraper.db.models import ahora_iso
    h = hashlib.sha256(f"{empresa}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{empresa} anuncia ronda de financiamiento", ahora_iso(), "2026-07-01",
         url, f"Medio {keywords[0]}" if keywords else "Medio A", empresa,
         tipo_evento, "prensa", h, "google_news", _json.dumps(keywords),
         confianza, "Alta", "Startup", "ok", ahora_iso()),
    )


def test_endpoint_sintesis_org(client, db):
    for i in range(1, 5):
        _insertar(db, "Nubank", f"https://medio{i}.com/1", ["ronda_inversion"])
    r = client.get("/sintesis/Nubank")
    assert r.status_code == 200
    d = r.json()
    assert d["org"] == "Nubank"
    assert d["estado"] == "sintetizado"
    assert set(d) >= {
        "org", "version_esquema", "estado", "patron_comportamiento",
        "senal_tension_dolor", "actores_involucrados", "sustancia_metrica",
        "evidencia_urls",
    }
    assert len(d["evidencia_urls"]) == 4


def test_endpoint_sintesis_sin_evidencia(client, db):
    r = client.get("/sintesis/Desconocida")
    assert r.status_code == 200
    d = r.json()
    assert d["org"] == "Desconocida"
    assert d["estado"] == "insuficiente"
    assert d["evidencia_urls"] == []
