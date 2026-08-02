"""Lectura estructural del discurso: determinista, grounded, siempre preliminar."""
from hd_scraper.lectura_estructural import (
    MARCO_DEUDA,
    leer_discurso,
    normalizar,
)


def test_sin_discurso_requiere_campo():
    r = leer_discurso(None, empresa="Acme")
    assert r["estado"] == "requiere_campo"
    assert r["tipo_deuda_preliminar"] is None
    assert "PRELIMINAR" in r["nota"]


def test_discurso_sin_marcadores_requiere_campo():
    r = leer_discurso("Somos una empresa de logística en la región.", empresa="Acme")
    assert r["estado"] == "requiere_campo"
    assert r["tipo_deuda_preliminar"] is None


def test_detecta_deuda_relacional_grounded_y_citable():
    disc = "Abre tu cuenta 100% digital, sin intermediarios y en un clic."
    r = leer_discurso(disc, empresa="Fintech X")
    assert r["estado"] == "grounded"
    assert r["tipo_deuda_preliminar"] == "Relacional"
    # el síntoma cita marcadores REALES del discurso (no fabricados).
    assert any(m in disc.lower() for m in r["sintoma_observable"])
    assert r["pregunta_cultural"]
    assert r["compite_contra"]
    assert "PRELIMINAR" in r["nota"]


def test_detecta_deuda_epistemica():
    r = leer_discurso("Es fácil, cualquiera puede invertir sin ser experto.", empresa="Y")
    assert r["estado"] == "grounded"
    assert r["tipo_deuda_preliminar"] == "Epistémica"


def test_es_determinista():
    disc = "Tú decides, control total de tu dinero tus reglas; sin intermediarios."
    a = leer_discurso(disc, empresa="Z")
    b = leer_discurso(disc, empresa="Z")
    assert a == b  # mismo insumo ⇒ misma lectura


def test_principal_es_el_de_mas_marcadores():
    # 2 marcadores relacionales vs 1 ontológico → principal Relacional, secundaria Ontológica.
    disc = "Sin intermediarios, en un clic. Tú decides."
    r = leer_discurso(disc, empresa="Z")
    assert r["tipo_deuda_preliminar"] == "Relacional"
    assert r["tipo_deuda_secundaria"] == "Ontológica"


def test_normalizar_quita_acentos():
    assert normalizar("Educación Financiera") == "educacion financiera"


def test_marco_cubre_los_cinco_tipos():
    tipos = {td.tipo for td in MARCO_DEUDA}
    assert tipos == {"Ontológica", "Moral", "Temporal", "Relacional", "Epistémica"}


def test_cobertura_ampliada_es_y_pt():
    casos = {
        "Vive a tu manera, tú al mando.": "Ontológica",
        "Constrúyelo paso a paso, con visión a futuro.": "Temporal",
        "Ábrela sin burocracia, sin salir de casa.": "Relacional",
        "Tan fácil como enviar un mensaje, sin curva de aprendizaje.": "Epistémica",
        # portugués
        "Faça do seu jeito, você no comando.": "Ontológica",
        "Passo a passo, sustentável no tempo.": "Temporal",
    }
    for disc, esperado in casos.items():
        r = leer_discurso(disc, empresa="X")
        assert r["estado"] == "grounded", disc
        assert r["tipo_deuda_preliminar"] == esperado, (disc, r["tipo_deuda_preliminar"])


def test_precision_no_sobre_dispara_con_texto_generico():
    # Lenguaje de producto neutro (sin marcadores del marco) NO debe etiquetar Deuda.
    disc = "Ofrecemos una plataforma para empresas de logística en toda la región."
    r = leer_discurso(disc, empresa="X")
    assert r["estado"] == "requiere_campo"
