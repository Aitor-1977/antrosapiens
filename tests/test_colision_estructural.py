from hd_scraper.colision_estructural import (
    ESTADO_COLISION_DETECTADA,
    ESTADO_SENAL_AISLADA,
    ESTADO_SIN_SENAL,
    VECTOR_NARRATIVA,
    VECTOR_OPERATIVO,
    detectar_colision,
    es_vector_narrativa,
    es_vector_operativo,
)


def _narrativa(fecha=None):
    return {
        "origen_declaracion": "prensa",
        "connector": "google_news",
        "cita_textual": "Acme anuncia una ronda de inversión récord",
        "fecha_publicacion": fecha,
    }


def _operativo(fecha=None, keyword="retention"):
    return {
        "origen_declaracion": "operador",
        "connector": "job_boards",
        "cita_textual": f"Customer Success Manager - foco en {keyword} y crecimiento",
        "fecha_publicacion": fecha,
    }


def test_es_vector_narrativa_por_origen_prensa():
    assert es_vector_narrativa(_narrativa()) is True
    assert es_vector_narrativa({"origen_declaracion": "operador"}) is False


def test_es_vector_operativo_exige_connector_y_keyword():
    assert es_vector_operativo(_operativo()) is True
    sin_keyword = _operativo(keyword="")
    sin_keyword["cita_textual"] = "Vacante genérica sin marcador correctivo"
    assert es_vector_operativo(sin_keyword) is False
    otro_connector = dict(_operativo(), connector="google_news")
    assert es_vector_operativo(otro_connector) is False


def test_es_vector_operativo_detecta_las_cuatro_palabras():
    for kw in ("retention", "onboarding", "customer success", "behavioral"):
        assert es_vector_operativo(_operativo(keyword=kw)) is True


def test_sin_evidencia_es_sin_senal():
    c = detectar_colision([])
    assert c.estado == ESTADO_SIN_SENAL
    assert c.vectores_presentes == ()


def test_solo_narrativa_es_senal_aislada():
    c = detectar_colision([_narrativa("2026-01-15")])
    assert c.estado == ESTADO_SENAL_AISLADA
    assert c.vectores_presentes == (VECTOR_NARRATIVA,)


def test_solo_operativo_es_senal_aislada():
    c = detectar_colision([_operativo("2026-01-15")])
    assert c.estado == ESTADO_SENAL_AISLADA
    assert c.vectores_presentes == (VECTOR_OPERATIVO,)


def test_colision_dentro_de_nueve_meses():
    filas = [_narrativa("2026-01-01"), _operativo("2026-09-01")]
    c = detectar_colision(filas)
    assert c.estado == ESTADO_COLISION_DETECTADA
    assert set(c.vectores_presentes) == {VECTOR_NARRATIVA, VECTOR_OPERATIVO}
    assert c.par_narrativa is not None
    assert c.par_operativo is not None


def test_ambos_vectores_pero_fuera_de_ventana_es_senal_aislada():
    filas = [_narrativa("2026-01-01"), _operativo("2026-11-01")]
    c = detectar_colision(filas)
    assert c.estado == ESTADO_SENAL_AISLADA
    assert set(c.vectores_presentes) == {VECTOR_NARRATIVA, VECTOR_OPERATIVO}


def test_exactamente_nueve_meses_cuenta_como_colision():
    filas = [_narrativa("2026-01-01"), _operativo("2026-10-01")]
    c = detectar_colision(filas, ventana_meses=9)
    assert c.estado == ESTADO_COLISION_DETECTADA


def test_evidencia_sin_fecha_no_participa_de_la_ventana():
    """no_fechado nunca inventa una colisión (mismo criterio que freshness.py)."""
    filas = [_narrativa(None), _operativo(None)]
    c = detectar_colision(filas)
    assert c.estado == ESTADO_SENAL_AISLADA
    assert set(c.vectores_presentes) == {VECTOR_NARRATIVA, VECTOR_OPERATIVO}


def test_elige_el_par_mas_cercano_cuando_hay_varios():
    filas = [
        _narrativa("2026-01-01"),
        _operativo("2026-09-01", keyword="onboarding"),
        _operativo("2026-03-01", keyword="behavioral"),
    ]
    c = detectar_colision(filas)
    assert c.estado == ESTADO_COLISION_DETECTADA
    assert c.par_operativo["fecha_publicacion"] == "2026-03-01"
