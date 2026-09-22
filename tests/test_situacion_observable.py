from hd_scraper.situacion_observable import (
    TIPO_HUELLA_GENERICA,
    TIPO_RUIDO,
    TIPO_SITUACION_UTIL,
    clasificar_situacion,
)


def test_sin_senal_primaria_es_ruido():
    s = clasificar_situacion({
        "tipo_epistemologico": "contextual",
        "cita_textual": "user friction and churn everywhere",
    })
    assert s.tipo == TIPO_RUIDO
    assert s.marcador is None


def test_corroborante_tambien_es_ruido_para_esta_capa():
    """La REGLA DURA de Entrega 2 no se reinterpreta aquí: corroborante no
    es señal primaria, así que nunca alimenta la ficha de prospección."""
    s = clasificar_situacion({
        "tipo_epistemologico": "corroborante",
        "cita_textual": "root causes of user friction",
    })
    assert s.tipo == TIPO_RUIDO


def test_senal_primaria_sin_marcador_es_huella_generica():
    s = clasificar_situacion({
        "tipo_epistemologico": "senal_primaria_huella_practica",
        "cita_textual": "Buscamos optimizar procesos y mejorar eficiencia.",
    })
    assert s.tipo == TIPO_HUELLA_GENERICA
    assert s.marcador is None


def test_senal_primaria_con_marcador_de_friccion_es_situacion_util():
    """El texto contiene dos marcadores válidos ("user friction" y "root
    causes of user"); el clasificador devuelve el primero que coincide según
    el orden del léxico cerrado — cualquiera de los dos es una situación
    observable legítima, así que basta con no perder la clasificación."""
    s = clasificar_situacion({
        "tipo_epistemologico": "senal_primaria_huella_practica",
        "cita_textual": "We want to identify root causes of user friction.",
    })
    assert s.tipo == TIPO_SITUACION_UTIL
    assert s.marcador in ("user friction", "root causes of user")


def test_marcador_churn_detectado():
    s = clasificar_situacion({
        "tipo_epistemologico": "senal_primaria_autodeclaracion",
        "cita_textual": "Track churn risk scoring and product adoption.",
    })
    assert s.tipo == TIPO_SITUACION_UTIL
    assert s.marcador in ("churn", "adoption")


def test_contexto_empresarial_no_es_situacion_util():
    """Caso C del encargo: contexto (ronda) no debe colarse como situación,
    aunque tenga señal primaria (huella_practica es posible en teoría; aquí
    simplemente no hay marcador de situación al cliente)."""
    s = clasificar_situacion({
        "tipo_epistemologico": "senal_primaria_huella_practica",
        "cita_textual": "La empresa levantó $10 millones en su ronda Serie A.",
    })
    assert s.tipo == TIPO_HUELLA_GENERICA


def test_ruido_de_crecimiento_generico_no_es_situacion_util():
    """Caso D del encargo: 'la empresa creció 40%' es ruido para esta capa,
    aunque en teoría tuviera señal primaria."""
    s = clasificar_situacion({
        "tipo_epistemologico": "senal_primaria_huella_practica",
        "cita_textual": "La empresa creció 40% el último trimestre.",
    })
    assert s.tipo == TIPO_HUELLA_GENERICA


def test_texto_vacio_sin_señal_primaria_es_ruido():
    s = clasificar_situacion({"tipo_epistemologico": None, "cita_textual": ""})
    assert s.tipo == TIPO_RUIDO
