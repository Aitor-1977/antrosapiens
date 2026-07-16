"""Directorio de empresas (Wikidata) con la red inyectada por fixture."""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper import directorio
from hd_scraper.config import settings

# Respuesta SPARQL simulada de Wikidata (formato results/bindings).
FIXTURE_WD = {
    "results": {"bindings": [
        {"empresaLabel": {"value": "Klar"},
         "sitio": {"value": "https://www.klar.mx/"},
         "descripcion": {"value": "empresa fintech de servicios financieros en México"}},
        {"empresaLabel": {"value": "Kavak"},
         "sitio": {"value": "https://www.kavak.com/"},
         "descripcion": {"value": "plataforma de compraventa de autos usados"}},
        {"empresaLabel": {"value": "Google México"},   # gigante -> se filtra
         "sitio": {"value": "https://google.com.mx/"},
         "descripcion": {"value": "filial mexicana de Google"}},
        {"empresaLabel": {"value": "Q123456"},         # sin etiqueta -> se ignora
         "sitio": {"value": "https://x.example/"}},
    ]},
}


# ── unidad ───────────────────────────────────────────────────────────────────

def test_url_consulta_conoce_paises():
    assert "Q96" in directorio.url_consulta("México")
    assert directorio.url_consulta("Europa") == ""


def test_parse_filtra_gigantes_y_sin_label():
    emp = directorio.parse_empresas(FIXTURE_WD, vertical="todas")
    nombres = [e["nombre"] for e in emp]
    assert "Klar" in nombres and "Kavak" in nombres
    assert "Google México" not in nombres   # gigante fuera
    assert not any("Q123456" == n for n in nombres)  # sin etiqueta fuera


def test_parse_filtra_por_vertical():
    emp = directorio.parse_empresas(FIXTURE_WD, vertical="fintech")
    nombres = [e["nombre"] for e in emp]
    assert "Klar" in nombres            # descripción fintech
    assert "Kavak" not in nombres       # no es fintech


def test_buscar_nunca_lanza():
    def falla(url):
        raise RuntimeError("wikidata caída")
    assert directorio.buscar_empresas("México", "todas", falla) == []


# ── endpoint ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    yield api, TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


H = {"X-Ingest-Token": "secreto-123"}


def test_directorio_requiere_token(cli):
    _, c = cli
    assert c.post("/directorio", json={"region": "México"}).status_code == 401


def test_directorio_region_invalida_400(cli):
    _, c = cli
    assert c.post("/directorio", json={"region": "Europa"}, headers=H).status_code == 400


def test_directorio_guarda_prospectos_y_salen_en_informe(cli, monkeypatch):
    api, c = cli
    monkeypatch.setattr(api.directorio, "buscar_empresas",
                        lambda pais, vert, getter, limite=40: directorio.parse_empresas(FIXTURE_WD, vert))
    r = c.post("/directorio", json={"region": "México", "categoria": "Startup",
                                    "vertical": "todas", "limite": 40}, headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["nuevos"] == 2 and d["encontradas"] == 2   # Klar + Kavak (Google filtrado)
    # Aparecen en el informe profundo como empresas reales.
    inf = c.get("/informe").json()
    empresas = {t["empresa"] for t in inf["prospectos"]}
    assert "Klar" in empresas and "Kavak" in empresas
