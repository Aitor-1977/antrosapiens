"""Motor de reglas Capa 0: matches deterministas, pesos, alerta y persistencia."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings
from hd_scraper.engine.rule_engine import RuleEngine


# ── unidad: RuleEngine ───────────────────────────────────────────────────────

def test_match_operativa_y_peso():
    eng = RuleEngine()
    s = eng.evaluar("Buscamos head of growth para retention", "https://x/1")
    tipos = {x.tipo_señal for x in s}
    assert "Operativa" in tipos
    assert all(x.score_deuda == 1.5 for x in s if x.tipo_señal == "Operativa")
    # Motivo auditable presente.
    assert all("Match determinista" in x.motivo_match for x in s)


def test_sin_match_no_devuelve_senales():
    assert RuleEngine().evaluar("Comunicado institucional de rutina", "https://x/2") == []


def test_id_determinista():
    eng = RuleEngine()
    a = eng.evaluar("growth", "https://x/3")[0]
    b = eng.evaluar("growth", "https://x/3")[0]
    assert a.id == b.id  # mismo insumo -> mismo id (auditable, no hash() aleatorio)


def test_no_duplica_misma_keyword():
    s = RuleEngine().evaluar("growth growth growth", "https://x/4")
    assert len([x for x in s if "growth" in x.motivo_match]) == 1


def test_alerta_critica_por_umbral():
    eng = RuleEngine()
    # Rescate (3.0) + Discursiva (2.0) = 5.0 >= umbral -> Crítica.
    s = eng.evaluar("down round y hay que evangelizar al mercado", "https://x/5")
    score, alerta = eng.calcular_alerta(s)
    assert score >= 5.0 and alerta == "Crítica"


def test_alerta_normal_bajo_umbral():
    eng = RuleEngine()
    s = eng.evaluar("head of growth", "https://x/6")  # Operativa 1.5 (una sola)
    _, alerta = eng.calcular_alerta(s)
    assert alerta == "Normal"


# ── endpoint /webhook/ingesta + /senales-capa0 ───────────────────────────────

@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


H = {"X-Ingest-Token": "secreto-123"}


def test_ingesta_requiere_token(cli):
    assert cli.post("/webhook/ingesta", json={"texto": "growth"}).status_code == 401


def test_ingesta_persiste_y_se_lee(cli):
    r = cli.post("/webhook/ingesta", json={
        "texto": "El founder habla de down round y expansión lenta",
        "url": "https://yt/abc", "timestamp": "00:12:30",
        "org_name": "Acme",
    }, headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["senales_detectadas"] >= 2 and d["nivel_alerta"] == "Crítica"
    # Se persistieron y se pueden leer.
    lista = cli.get("/senales-capa0", params={"nivel_alerta": "Crítica"}).json()
    assert lista["total"] >= 2
    assert all(i["org_nombre"] == "Acme" for i in lista["items"])


def test_ingesta_dedup_por_id(cli):
    payload = {"texto": "growth y head of", "url": "https://yt/dup"}
    cli.post("/webhook/ingesta", json=payload, headers=H)
    r2 = cli.post("/webhook/ingesta", json=payload, headers=H)
    # La segunda no crea nuevas (mismo id determinista).
    assert r2.json()["senales_nuevas"] == 0


def test_ingesta_sin_match_no_persiste(cli):
    r = cli.post("/webhook/ingesta", json={"texto": "nota de rutina", "url": "https://x/9"}, headers=H)
    assert r.json()["senales_detectadas"] == 0


# ── ingesta de noticias EN LA APP (servidor lee el RSS) ──────────────────────

_RSS_CAP0 = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <item>
    <title>Startup busca head of growth y admite un down round - Medio</title>
    <link>https://n/1</link>
    <source url="https://medio.com">Medio</source>
  </item>
</channel></rss>"""


def test_ingesta_noticias_corre_en_la_app(cli, monkeypatch):
    apimod = importlib.import_module("hd_scraper.api.app")
    # El servidor "lee" el RSS (inyectado) y procesa cada nota con la Capa 0.
    monkeypatch.setattr(apimod._noticias, "_http_get", lambda url: _RSS_CAP0)
    r = cli.post("/ingesta/noticias", json={"query": "startup"}, headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["items"] == 1 and d["senales_detectadas"] >= 1  # head of / growth / down round
    assert cli.get("/senales-capa0").json()["total"] >= 1


def test_ingesta_noticias_requiere_token_y_query(cli):
    assert cli.post("/ingesta/noticias", json={"query": "x"}).status_code == 401
    assert cli.post("/ingesta/noticias", json={}, headers=H).status_code == 400
