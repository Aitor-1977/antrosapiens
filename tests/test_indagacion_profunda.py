"""Indagación profunda (Fase B): síntesis determinista, grounded, degrada bien.

La extracción en vivo (red) no corre en tests; se inyecta ``buscar_fn`` con
eventos fijos para probar la LÓGICA de síntesis y agregación.
"""
from hd_scraper.indagacion_profunda import (
    _deuda_dominante,
    indagar_profundo,
    sintetizar,
)
from hd_scraper.lectura_estructural import leer_discurso


def _evento(titulo, tipo_deuda=None, scoring="", fecha=None, icp=None):
    return {
        "titulo": titulo, "url": "https://x/n", "medio": "Prensa", "fecha": fecha,
        "keywords": [], "tipo_deuda": tipo_deuda, "deuda_razon": None,
        "scoring": scoring, "score_icp": icp, "fuente": "google_news",
    }


def test_sin_eventos_ni_discurso_requiere_campo():
    out = sintetizar("Acme", [], leer_discurso(None, empresa="Acme"))
    assert out["estado"] == "requiere_campo"
    assert out["total_eventos"] == 0
    assert out["deuda_dominante_preliminar"] is None


def test_grounded_con_eventos_y_citables():
    eventos = [
        _evento("Acme despide al 20% del equipo", "Deuda Temporal", "A", "2026-02-01", 80),
        _evento("Acme cambia de marca", "Deuda Relacional", "B", "2026-03-01", 55),
    ]
    out = sintetizar("Acme", eventos, leer_discurso(None, empresa="Acme"))
    assert out["estado"] == "grounded"
    assert out["total_eventos"] == 2
    # eventos ordenados por fecha descendente y citables (con URL).
    assert out["eventos"][0]["fecha"] == "2026-03-01"
    assert all(e["url"] for e in out["eventos"])
    # scoring agregado = el mejor (A).
    assert out["scoring"] == "A"
    assert out["score_icp"] == 80


def test_deuda_dominante_por_frecuencia_determinista():
    eventos = [
        _evento("n1", "Deuda Relacional"),
        _evento("n2", "Deuda Temporal"),
        _evento("n3", "Deuda Relacional"),
    ]
    assert _deuda_dominante(eventos) == "Deuda Relacional"
    # sin señal en ningún evento -> None
    assert _deuda_dominante([_evento("n", None)]) is None


def test_cae_a_deuda_del_discurso_si_no_hay_eventos():
    lectura = leer_discurso("Ábrela sin intermediarios, 100% digital.", empresa="X")
    out = sintetizar("X", [], lectura)
    assert out["estado"] == "grounded"
    assert out["deuda_dominante_preliminar"] == "Relacional"  # vino del discurso


def test_indagar_profundo_inyectando_busqueda_y_reporta_salud():
    def fake_buscar(empresa, vertical=""):
        eventos = [_evento(f"{empresa} levanta ronda", "Deuda Temporal", "A", "2026-01-10", 70)]
        salud = [("google_news", True, "1 resultados"), ("gdelt", False, "timeout")]
        return eventos, salud

    out = indagar_profundo("Acme", dominio=None, buscar_fn=fake_buscar)
    assert out["estado"] == "grounded"
    assert out["total_eventos"] == 1
    assert out["deuda_dominante_preliminar"] == "Deuda Temporal"
    # degrada con elegancia: reporta la fuente caída sin romper.
    salud = {s["fuente"]: s["ok"] for s in out["salud_fuentes"]}
    assert salud == {"google_news": True, "gdelt": False}


def test_es_determinista():
    eventos = [_evento("a", "Deuda Moral", "B", "2026-01-01"), _evento("b", "Deuda Moral", "C", "2026-02-01")]
    a = sintetizar("Z", eventos, leer_discurso(None, empresa="Z"))
    b = sintetizar("Z", eventos, leer_discurso(None, empresa="Z"))
    assert a == b
