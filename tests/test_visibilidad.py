"""Mecanismo compartido de visibilidad (2026-09-20), extraído de la
duplicación entre candidatos_verificados.py (fricción, /verificados) y
_construir_expedientes (escala, INDAGAR)."""
from hd_scraper.visibilidad import LATENTE, VISIBLE, incluir_segun_visibilidad


def test_constantes_literales():
    assert VISIBLE == "visible"
    assert LATENTE == "latente"


def test_todos_deja_pasar_visible():
    assert incluir_segun_visibilidad(VISIBLE, "todos") is True


def test_todos_deja_pasar_latente():
    assert incluir_segun_visibilidad(LATENTE, "todos") is True


def test_visible_deja_pasar_solo_visible():
    assert incluir_segun_visibilidad(VISIBLE, "visible") is True
    assert incluir_segun_visibilidad(LATENTE, "visible") is False


def test_cualquier_valor_distinto_de_todos_exige_visible():
    # Mismo criterio que el código previo a la extracción: cualquier valor
    # que no sea literalmente "todos" filtra a solo VISIBLE.
    assert incluir_segun_visibilidad(VISIBLE, "cualquier-otra-cosa") is True
    assert incluir_segun_visibilidad(LATENTE, "cualquier-otra-cosa") is False
