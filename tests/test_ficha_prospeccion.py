from hd_scraper.estado_evidencia import (
    ESTADO_PROSPECTO_INVESTIGABLE,
    ESTADO_SITUACION_OBSERVABLE,
)
from hd_scraper.ficha_prospeccion import _fragmento, _persona_cargo, generar_fichas


def _fila(**kwargs):
    base = {
        "cita_textual": "",
        "url_fuente": "https://example.com/a",
        "nombre_medio": "Greenhouse",
        "fecha_publicacion": "2026-01-01",
        "persona_citada": None,
        "cargo": None,
        "enunciador_nombre": None,
        "enunciador_cargo": None,
        "origen_declaracion": "operador",
        "tipo_epistemologico": "senal_primaria_huella_practica",
    }
    base.update(kwargs)
    return base


def test_dos_documentos_con_mismo_marcador_colapsan_en_una_ficha_con_recurrencia_dos():
    filas = [
        _fila(
            cita_textual="Reduce customer churn across all accounts this quarter.",
            url_fuente="https://example.com/1",
            fecha_publicacion="2026-01-01",
        ),
        _fila(
            cita_textual="Investigate churn drivers reported by the support team.",
            url_fuente="https://example.com/2",
            fecha_publicacion="2026-01-05",
        ),
    ]
    fichas = generar_fichas("Clara", filas)
    # ambos textos contienen "churn" -> mismo marcador -> 1 ficha
    assert len(fichas) == 1
    ficha = fichas[0]
    assert ficha.recurrencia == 2
    assert ficha.estado_evaluacion == ESTADO_PROSPECTO_INVESTIGABLE
    assert ficha.corroboracion == "2 documentos"
    assert ficha.organizacion == "Clara"


def test_evidencia_generica_no_produce_ficha():
    filas = [
        _fila(cita_textual="Buscamos optimizar procesos y mejorar eficiencia."),
    ]
    fichas = generar_fichas("Clara", filas)
    assert fichas == []


def test_evidencia_sin_senal_primaria_no_produce_ficha():
    filas = [
        _fila(
            cita_textual="root causes of user friction",
            tipo_epistemologico="contextual",
        ),
    ]
    fichas = generar_fichas("Clara", filas)
    assert fichas == []


def test_situacion_unica_con_recurrencia_uno_es_situacion_observable_no_prospecto():
    filas = [_fila(cita_textual="We track customer churn closely.")]
    fichas = generar_fichas("Clara", filas)
    assert len(fichas) == 1
    assert fichas[0].recurrencia == 1
    assert fichas[0].estado_evaluacion == ESTADO_SITUACION_OBSERVABLE
    assert fichas[0].corroboracion == "ninguna"


def test_fit_comercial_no_influye_en_que_situaciones_aparecen():
    filas = [_fila(cita_textual="We track customer churn closely.")]
    fichas_sin_score = generar_fichas("Clara", filas, score_icp=None)
    fichas_con_score = generar_fichas("Clara", filas, score_icp=87.5)
    assert len(fichas_sin_score) == len(fichas_con_score) == 1
    assert fichas_sin_score[0].situacion_observable == fichas_con_score[0].situacion_observable
    assert fichas_sin_score[0].fit_comercial == {"score_icp": None}
    assert fichas_con_score[0].fit_comercial == {"score_icp": 87.5}


def test_to_dict_contiene_todos_los_campos_minimos():
    filas = [_fila(cita_textual="We track customer churn closely.")]
    ficha = generar_fichas("Clara", filas)[0]
    d = ficha.to_dict()
    campos_esperados = {
        "organizacion", "situacion_observable", "que_esta_ocurriendo",
        "evidencia_textual", "fuentes", "fechas", "persona_cargo",
        "tipo_epistemologico", "origen_declaracion", "corroboracion",
        "recurrencia", "contexto_organizacional", "estado_evaluacion",
        "fit_comercial",
    }
    assert campos_esperados <= d.keys()


def test_persona_cargo_con_persona_y_cargo():
    fila = _fila(persona_citada="Ana Pérez", cargo="CEO")
    assert _persona_cargo(fila) == "Ana Pérez, CEO"


def test_persona_cargo_solo_persona():
    fila = _fila(persona_citada="Ana Pérez")
    assert _persona_cargo(fila) == "Ana Pérez"


def test_persona_cargo_solo_cargo():
    fila = _fila(cargo="CEO")
    assert _persona_cargo(fila) == "CEO"


def test_persona_cargo_ninguno_es_none():
    fila = _fila()
    assert _persona_cargo(fila) is None


def test_persona_cargo_prioriza_enunciador_sobre_persona_citada():
    fila = _fila(
        enunciador_nombre="Ana Pérez", enunciador_cargo="CEO",
        persona_citada="Otro Nombre", cargo="Otro Cargo",
    )
    assert _persona_cargo(fila) == "Ana Pérez, CEO"


def test_fragmento_recorta_alrededor_del_marcador():
    cita = "x" * 200 + "root causes of user friction" + "y" * 200
    frag = _fragmento(cita, "root causes of user")
    assert "root causes of user" in frag.lower()
    assert len(frag) < len(cita)


def test_fragmento_degrada_si_marcador_no_aparece_en_texto():
    cita = "texto sin el marcador esperado"
    frag = _fragmento(cita, "root causes of user")
    assert frag == cita
