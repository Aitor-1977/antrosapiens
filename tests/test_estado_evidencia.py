from hd_scraper.estado_evidencia import (
    ESTADO_DESCARTADO,
    ESTADO_PROSPECTO_INVESTIGABLE,
    ESTADO_SIN_SITUACION,
    ESTADO_SITUACION_OBSERVABLE,
    UMBRAL_CORROBORACION,
    estado_de,
)
from hd_scraper.situacion_observable import (
    TIPO_HUELLA_GENERICA,
    TIPO_RUIDO,
    TIPO_SITUACION_UTIL,
    Situacion,
)


def test_huella_generica_es_sin_situacion():
    s = Situacion(TIPO_HUELLA_GENERICA, None, "razon")
    assert estado_de(s, recurrencia=1) == ESTADO_SIN_SITUACION


def test_ruido_es_descartado():
    s = Situacion(TIPO_RUIDO, None, "razon")
    assert estado_de(s, recurrencia=1) == ESTADO_DESCARTADO


def test_situacion_util_con_recurrencia_uno_es_situacion_observable():
    s = Situacion(TIPO_SITUACION_UTIL, "churn", "razon")
    assert estado_de(s, recurrencia=1) == ESTADO_SITUACION_OBSERVABLE


def test_situacion_util_con_recurrencia_en_el_umbral_es_prospecto_investigable():
    s = Situacion(TIPO_SITUACION_UTIL, "churn", "razon")
    assert estado_de(s, recurrencia=UMBRAL_CORROBORACION) == ESTADO_PROSPECTO_INVESTIGABLE


def test_situacion_util_con_recurrencia_alta_sigue_siendo_prospecto_investigable():
    s = Situacion(TIPO_SITUACION_UTIL, "churn", "razon")
    assert estado_de(s, recurrencia=5) == ESTADO_PROSPECTO_INVESTIGABLE


def test_umbral_de_corroboracion_es_dos():
    """Documenta explícitamente la decisión de diseño: CORROBORADO y
    PROSPECTO_INVESTIGABLE se colapsan en un único estado terminal gateado
    por recurrencia >= 2, sin distinción arbitraria adicional."""
    assert UMBRAL_CORROBORACION == 2
