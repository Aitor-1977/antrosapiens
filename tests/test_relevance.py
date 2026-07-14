"""Captura Inteligente: filtro de relevancia y calidad (objetivos, sin IA)."""
from hd_scraper.relevance import (
    CALIDAD_ALTA,
    CALIDAD_BAJA,
    CALIDAD_MEDIA,
    MOTIVO_OPINION,
    MOTIVO_SIN_EMPRESA,
    MOTIVO_SIN_EVENTO,
    calcular_calidad,
    detectar_empresa,
    es_opinion,
    evaluar_relevancia,
)


# ── detección de empresa (nombre propio) ─────────────────────────────────────

def test_detectar_empresa_nombre_al_inicio():
    assert detectar_empresa("Nubank anuncia nueva ronda de inversión") == "Nubank"


def test_detectar_empresa_ignora_articulo_inicial_y_sector():
    # "La" es artículo, "fintech" es genérico -> la empresa es "Clara".
    assert detectar_empresa("La fintech Clara levanta capital serie B") == "Clara"


def test_detectar_empresa_acepta_siglas():
    assert detectar_empresa("BBVA lanza un nuevo producto") == "BBVA"


def test_detectar_empresa_sin_nombre_propio():
    # Tendencia genérica sin empresa nombrada.
    assert detectar_empresa("las startups enfrentan un año difícil") is None


# ── marcadores de opinión / tendencia / listículo ────────────────────────────

def test_es_opinion_detecta_marcadores():
    assert es_opinion("Opinión: por qué las fintech fracasan")
    assert es_opinion("El futuro de la banca digital en 2027")
    assert es_opinion("5 claves para entender el churn")
    assert es_opinion("Los mejores bancos digitales de la región")


def test_es_opinion_no_marca_noticia_de_evento():
    assert not es_opinion("Nubank adquiere una startup de pagos")


# ── filtro de relevancia ─────────────────────────────────────────────────────

def test_relevancia_conserva_evento_con_empresa():
    ok, motivo = evaluar_relevancia(
        "Nubank adquiere una fintech de pagos", ["adquisicion"], empresa_identificada=True)
    assert ok and motivo == ""


def test_relevancia_descarta_opinion():
    ok, motivo = evaluar_relevancia(
        "Opinión: el futuro de Nubank", ["adquisicion"], empresa_identificada=True)
    assert not ok and motivo == MOTIVO_OPINION


def test_relevancia_descarta_sin_empresa():
    ok, motivo = evaluar_relevancia(
        "Las startups enfrentan más despidos", ["reduccion_personal"],
        empresa_identificada=False)
    assert not ok and motivo == MOTIVO_SIN_EMPRESA


def test_relevancia_descarta_sin_evento():
    ok, motivo = evaluar_relevancia(
        "Nubank celebra su aniversario", [], empresa_identificada=True)
    assert not ok and motivo == MOTIVO_SIN_EVENTO


# ── calidad de captura (informativa) ─────────────────────────────────────────

def test_calidad_alta_media_baja():
    assert calcular_calidad(True, True, True) == CALIDAD_ALTA
    assert calcular_calidad(True, True, False) == CALIDAD_MEDIA
    assert calcular_calidad(True, False, False) == CALIDAD_BAJA
    assert calcular_calidad(False, False, False) == CALIDAD_BAJA


def test_calidad_duplicado_fuerza_baja():
    assert calcular_calidad(True, True, True, sin_duplicado=False) == CALIDAD_BAJA
