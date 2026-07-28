"""Tests: paridad de forma del panel ecosistémico (Cutover 1.0).

Verifica que `panel_ecosistemico` produce EXACTAMENTE la interfaz Dashboard que
consume el componente InteligenciaEcosistemica de RadarHD, de forma determinista.
"""
import importlib
import json as _json

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ahora_iso
from hd_scraper.observatorio import panel_ecosistemico, _subtipo


def _ev(url, fecha="2026-07-01", fuente=None, conf=0.8):
    return {"url": url, "fuente": fuente or url, "fecha": fecha,
            "tipo_evento": "queja", "confianza": conf, "texto": "t"}


def _exp(nombre, tipo_deuda="Deuda Relacional", vertical="fintech", categoria="Startup",
         score_icp=70, profundidad=80, total_ev=3, keywords=None, veredicto="VALIDADA",
         evs=None):
    return {
        "nombre": nombre, "tipo_deuda": tipo_deuda, "vertical": vertical,
        "categoria": categoria, "score_icp": score_icp, "profundidad_dolor": profundidad,
        "intensidad": "Alta", "total_evidencias": total_ev,
        "keywords": keywords or ["friccion_retencion"], "patrones": [{"patron": "P1"}],
        "evidencias": evs or [_ev("u1"), _ev("u2", fuente="M2"), _ev("u3", fuente="M3")],
        "validacion_cientifica": {"veredicto": veredicto, "hipotesis_bloqueada": False,
                                  "solidez": 70, "suficiencia": 65, "nivel_evidencia": "I"},
    }


def _conjunto():
    return [
        _exp("Nubank", "Deuda Relacional", "fintech", score_icp=80),
        _exp("Kavak", "Deuda Relacional", "fintech", score_icp=40, keywords=["expansion"]),
        _exp("Clip", "Deuda Estructural", "healthtech", score_icp=95, profundidad=95,
             total_ev=1, keywords=["cierre_operaciones"], evs=[_ev("c1", "2026-05-01")]),
    ]


# ── Forma exacta (paridad con la interfaz Dashboard) ─────────────────────────

def test_panel_tiene_todas_las_claves():
    d = panel_ecosistemico(_conjunto())
    for k in ("total_organizaciones", "periodo", "madurez", "riesgo_cultural",
              "calidad_corpus", "distribuciones", "patrones_dominantes",
              "tendencias_emergentes", "clusters", "centinelas", "atipicos",
              "hipotesis_ecosistemicas", "trazabilidad_valida"):
        assert k in d


def test_periodo_min_max():
    d = panel_ecosistemico(_conjunto())
    assert d["periodo"] == {"desde": "2026-05-01", "hasta": "2026-07-01"}


def test_riesgo_cultural_shape():
    r = panel_ecosistemico(_conjunto())["riesgo_cultural"]
    assert set(r) == {"indice", "nivel", "fundamento"}
    assert r["nivel"] in ("Alto", "Medio", "Bajo")
    assert isinstance(r["fundamento"], dict)


def test_calidad_corpus_shape():
    c = panel_ecosistemico(_conjunto())["calidad_corpus"]
    assert set(c) == {"indice", "nivel", "distribucion_confianza"}
    assert c["nivel"] in ("Alta", "Media", "Baja")


def test_distribuciones_frecuencia_shape():
    dist = panel_ecosistemico(_conjunto())["distribuciones"]
    assert set(dist) == {"deuda_cultural", "por_vertical", "por_pais", "por_categoria"}
    for f in dist["deuda_cultural"]:
        assert set(f) == {"valor", "cantidad", "organizaciones"}
        assert all(isinstance(i, int) for i in f["organizaciones"])
    assert dist["por_pais"] == []  # Motor A no estructura país


def test_deuda_cultural_usa_subtipo_corto():
    dist = panel_ecosistemico(_conjunto())["distribuciones"]["deuda_cultural"]
    valores = {f["valor"] for f in dist}
    assert "Relacional" in valores and "Estructural" in valores  # sin prefijo "Deuda "


def test_clusters_shape_y_subtipo():
    cl = panel_ecosistemico(_conjunto())["clusters"]
    assert cl and cl[0]["subtipo"] == "Relacional"  # Nubank+Kavak
    for c in cl:
        assert set(c) == {"subtipo", "num_organizaciones", "organizaciones", "evidencia_ids"}


def test_centinelas_shape():
    cen = panel_ecosistemico(_conjunto())["centinelas"]
    assert any(c["nombre_display"] == "Clip" for c in cen)
    for c in cen:
        assert set(c) == {"organizacion_id", "nombre_display", "subtipo",
                          "fecha_primera_senal", "motivo"}
        assert isinstance(c["organizacion_id"], int)


def test_atipicos_shape():
    at = panel_ecosistemico(_conjunto())["atipicos"]
    for a in at:
        assert set(a) == {"organizacion_id", "nombre_display", "motivo"}


def test_patrones_ecosistemicos_shape():
    p = panel_ecosistemico(_conjunto())["patrones_dominantes"]
    for pat in p:
        assert set(pat) == {"patron", "num_organizaciones", "organizaciones", "evidencia_ids"}


def test_hipotesis_ecosistemicas_shape():
    h = panel_ecosistemico(_conjunto())["hipotesis_ecosistemicas"]
    # Deuda Relacional recurrente (Nubank+Kavak) ⇒ 1 hipótesis.
    assert any("Relacional" in x["texto"] for x in h)
    for x in h:
        assert set(x) == {"texto", "organizaciones", "nivel_confianza",
                          "cantidad_evidencias", "periodo"}


def test_madurez_shape():
    m = panel_ecosistemico(_conjunto())["madurez"]
    assert set(m) == {"nivel_dominante", "distribucion"}


def test_subtipo_helper():
    assert _subtipo("Deuda Relacional") == "Relacional"
    assert _subtipo("Deuda de Escalamiento") == "de Escalamiento"
    assert _subtipo("") == "No determinado"


def test_panel_vacio():
    d = panel_ecosistemico([])
    assert d["total_organizaciones"] == 0
    assert d["periodo"] == {"desde": None, "hasta": None}
    assert d["riesgo_cultural"]["indice"] == 0
    assert d["trazabilidad_valida"] is False


def test_panel_determinista():
    exps = _conjunto()
    assert panel_ecosistemico(exps) == panel_ecosistemico(exps)


def test_frecuencia_ignora_valores_vacios():
    # Organización sin vertical ni deuda ⇒ no aparece en esas distribuciones.
    exps = _conjunto() + [_exp("SinDatos", tipo_deuda="", vertical="", categoria="")]
    dist = panel_ecosistemico(exps)["distribuciones"]
    ids_vertical = {i for f in dist["por_vertical"] for i in f["organizaciones"]}
    # El id de "SinDatos" no está en la distribución por vertical.
    from hd_scraper.observatorio import _id_map
    sd_id = _id_map(exps)["SinDatos"]
    assert sd_id not in ids_vertical


# ── Endpoint ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, emp, url, medio, kws, fecha="2026-07-01", cat="Startup"):
    import hashlib
    h = hashlib.sha256(f"{emp}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{emp} fintech enfrenta fricción y churn", ahora_iso(), fecha, url, medio, emp,
         "queja", "prensa", h, "google_news", _json.dumps(kws), 0.8, "Alta", cat,
         "ok", ahora_iso()))


def test_endpoint_panel(client, db):
    for i, m in enumerate(["Medio A", "Medio B", "Medio C"]):
        _insertar(db, "Nubank", f"https://n{i}.com/1", m, ["friccion_retencion", "reduccion_personal"])
    r = client.get("/ecosistema/panel")
    assert r.status_code == 200
    d = r.json()
    assert "generado_en" in d and d["cacheado"] is False
    assert d["total_organizaciones"] >= 1
    assert "distribuciones" in d and "clusters" in d
