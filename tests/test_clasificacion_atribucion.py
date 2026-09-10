"""Estados de atribución de cita (auditoría 2026-09-10, instrucción de Mario).

Pregunta distinta de la clasificación epistemológica (`clasificar`): aquí solo
importa si el texto ATRIBUYE la cita a alguien identificable y si esa
atribución quedó capturada en `persona_citada`/`cargo`, o si el texto la
tiene pero el pipeline la perdió. Determinista, reutiliza el léxico existente
de `clasificacion_epistemologica.py` sin duplicarlo.
"""
from hd_scraper.clasificacion_epistemologica import (
    ATRIB_AMBIGUA,
    ATRIB_EXPLICITA,
    ATRIB_EXPLICITA_NO_EXTRAIDA,
    ATRIB_SIN_ATRIBUCION,
    ESTADOS_ATRIBUCION,
    clasificar_atribucion,
)


def _ev(texto, persona_citada=None, cargo=None, empresa="", medio=""):
    return {
        "cita_textual": texto,
        "persona_citada": persona_citada,
        "cargo": cargo,
        "empresa_mencionada": empresa,
        "nombre_medio": medio,
    }


def test_estados_son_los_cuatro_literales_del_contrato():
    assert set(ESTADOS_ATRIBUCION) == {
        ATRIB_EXPLICITA, ATRIB_EXPLICITA_NO_EXTRAIDA, ATRIB_AMBIGUA,
        ATRIB_SIN_ATRIBUCION,
    }


def test_atribucion_explicita_cuando_persona_citada_ya_viene_declarada():
    r = clasificar_atribucion(_ev(
        "Fintual despide al 10% de su plantilla", persona_citada="Ana Ríos", cargo="CEO",
    ))
    assert r.estado == ATRIB_EXPLICITA
    assert r.nombre == "Ana Ríos"
    assert r.cargo == "CEO"
    assert r.fragmento == "Ana Ríos, CEO"


def test_atribucion_explicita_prioriza_dato_declarado_sobre_el_texto():
    """persona_citada declarada manda, aunque el texto también tenga un
    patrón distinto — no se reinterpreta un dato ya estructural."""
    r = clasificar_atribucion(_ev(
        "Juan Pérez, CEO de Acme, dijo que recortará personal",
        persona_citada="Otra Persona", cargo=None,
    ))
    assert r.estado == ATRIB_EXPLICITA
    assert r.nombre == "Otra Persona"


def test_no_extraida_nombre_adjunto_a_cargo_con_senal_de_habla():
    r = clasificar_atribucion(_ev(
        "Juan Pérez, CEO de Kavak, dijo que la empresa recortará personal",
    ))
    assert r.estado == ATRIB_EXPLICITA_NO_EXTRAIDA
    assert r.nombre == "Juan Pérez"
    assert r.cargo == "CEO"
    assert r.fragmento and "Juan Pérez" in r.fragmento


def test_no_extraida_nombre_por_verbo_declarativo_sin_cargo():
    r = clasificar_atribucion(_ev(
        "María López afirmó que la ronda se cerró en enero",
    ))
    assert r.estado == ATRIB_EXPLICITA_NO_EXTRAIDA
    assert r.nombre == "María López"


def test_no_extraida_patron_segun_minusculas():
    r = clasificar_atribucion(_ev(
        "la ronda se cerró en enero, según María López, fundadora de Acme",
    ))
    assert r.estado == ATRIB_EXPLICITA_NO_EXTRAIDA
    assert r.nombre == "María López"


def test_no_extraida_cita_textual_con_comillas_y_nombre():
    r = clasificar_atribucion(_ev(
        '"Recortamos por la crisis", dijo Carlos Ruiz, director de operaciones',
    ))
    assert r.estado == ATRIB_EXPLICITA_NO_EXTRAIDA
    assert r.nombre == "Carlos Ruiz"


def test_no_extraida_autoidentificacion_primera_persona():
    r = clasificar_atribucion(_ev(
        "Soy fundadora de Acme y decidimos cerrar la empresa tras cinco semanas",
    ))
    assert r.estado == ATRIB_EXPLICITA_NO_EXTRAIDA
    assert r.fragmento is not None


def test_ambiguo_cargo_introducido_por_segun_sin_nombre_propio():
    """Caso real de la auditoría 2026-09-10 (evidencia de producción):
    'según experto' es un marcador de fuente tan válido como un verbo
    declarativo, aunque 'experto' no sea un nombre propio capturable."""
    r = clasificar_atribucion(_ev(
        "Startups y grandes empresas impulsan la innovación en América Latina "
        "desde enfoques distintos, según experto",
    ))
    assert r.estado == ATRIB_AMBIGUA
    assert r.nombre is None
    assert r.cargo == "experto"


def test_sin_atribucion_segun_organizacion_no_cuenta_como_cargo():
    """'según KPMG' atribuye a una organización, no a un cargo/persona: KPMG
    no está en el léxico de cargos, así que no dispara ni ambiguo."""
    r = clasificar_atribucion(_ev(
        "Las 10 startups en Colombia que más inversiones recibieron en 2025, "
        "según KPMG",
    ))
    assert r.estado == ATRIB_SIN_ATRIBUCION


def test_ambiguo_cargo_con_senal_de_habla_sin_nombre_adjunto():
    r = clasificar_atribucion(_ev("El CEO de Kavak anunció recortes de personal"))
    assert r.estado == ATRIB_AMBIGUA
    assert r.nombre is None
    assert r.cargo == "CEO"
    assert r.fragmento == "CEO"


def test_sin_atribucion_titular_sin_cargo_ni_nombre():
    r = clasificar_atribucion(_ev(
        "Kavak anuncia cierre de operaciones en Colombia y Perú",
    ))
    assert r.estado == ATRIB_SIN_ATRIBUCION
    assert r.nombre is None
    assert r.cargo is None
    assert r.fragmento is None


def test_sin_atribucion_cargo_mencionado_como_objeto_no_como_fuente():
    """'Oracle despide a 21 mil empleados' menciona 'empleados' como objeto
    del despido, no como fuente de una declaración: no hay cita que atribuir."""
    r = clasificar_atribucion(_ev(
        "Oracle despide a 21 mil empleados gracias a la IA",
    ))
    assert r.estado == ATRIB_SIN_ATRIBUCION


def test_sin_atribucion_texto_vacio():
    r = clasificar_atribucion(_ev(""))
    assert r.estado == ATRIB_SIN_ATRIBUCION
    assert r.fragmento is None


def test_fragmento_es_siempre_recorte_literal_del_texto_original():
    """Regla de grounding: el fragmento nunca es una paráfrasis, siempre un
    recorte de `cita_textual` (o de las columnas ya declaradas)."""
    texto = "Juan Pérez, CEO de Kavak, dijo que la empresa recortará personal"
    r = clasificar_atribucion(_ev(texto))
    assert r.fragmento in texto  # substring literal, no texto sintetizado


def test_no_inventa_nombre_cuando_el_texto_no_lo_da():
    """Regla 13 (incertidumbre): sin nombre resoluble, nombre=None — nunca
    se completa con la organización o el medio."""
    r = clasificar_atribucion(_ev(
        "El CEO de Kavak anunció recortes de personal", empresa="Kavak", medio="Reuters",
    ))
    assert r.nombre is None
