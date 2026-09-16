"""FIXTURE CONGELADO — contrato CANÓNICO confirmado en Fase 1.5.

Creado ANTES de `schema_expediente.py`, a partir ÚNICAMENTE de la decisión
explícita de Mario (Fase 1.5, 2026-09-16):

1. El contrato incorpora ``enunciador_nombre``/``enunciador_cargo`` (datos
   producidos y persistidos por la clasificación epistemológica).
2. ``categoria`` queda restringida a los 4 literales estructurales
   (VC | Startup | Incubadora | Corporativo); cualquier otro valor de origen
   se normaliza a ``""``.
3. ``persona_citada``/``cargo`` (estructurales, de ``evidencias``) NUNCA se
   fusionan con ``enunciador_nombre``/``enunciador_cargo`` (de la
   clasificación epistemológica): son campos conceptualmente distintos y
   ambos pares viajan por separado.

Distinto de `fixture_contrato_verificados.py` (Fase 1): aquel es la
referencia HISTÓRICA del contrato tal como se observó antes de esta
decisión (9 campos) y NO se modifica. Este es el contrato VIGENTE (11
campos) contra el que se valida la prueba de extremo a extremo (Fase 4).

REGLA DE CONGELAMIENTO: este fixture no se deriva de `schema_expediente.py`
ni de ningún código de implementación — es al revés. No modificar este
archivo para hacer pasar una prueba.
"""
from __future__ import annotations

# Item único con los 11 campos del contrato canónico confirmado. Valores
# explícitos: la organización cita a su propia fundadora/CEO (autodeclaración,
# tipo de máxima autoridad), la fuente NO declara persona_citada/cargo de
# forma estructural (como ocurre siempre en los 5 conectores reales), pero la
# clasificación epistemológica SÍ extrajo quién habla del propio texto — de
# ahí que persona_citada/cargo sean None mientras enunciador_nombre/
# enunciador_cargo tienen valor: son la prueba viva de que no se fusionan.
FIXTURE_ITEM_EXPEDIENTE_CANONICO: dict = {
    "organizacion": "Fixture Org SA",
    "categoria": "Startup",
    "tipo_epistemologico": "senal_primaria_autodeclaracion",
    "cita_textual": "Ana Torres, CEO de Fixture Org SA, anunció una ronda "
                     "de inversión de 12 millones de dólares para su "
                     "expansión en México",
    "url_fuente": "https://ejemplo.test/fixture-org-ronda",
    "nombre_medio": "Medio de Prueba",
    "fecha_publicacion": "2026-09-01T09:00:00+00:00",
    "persona_citada": None,
    "cargo": None,
    "enunciador_nombre": "Ana Torres",
    "enunciador_cargo": "CEO",
}

# Respuesta COMPLETA esperada del endpoint (wrapper "total"/"items").
FIXTURE_RESPUESTA_VERIFICADOS_CANONICA: dict = {
    "total": 1,
    "items": [FIXTURE_ITEM_EXPEDIENTE_CANONICO],
}

# Segundo caso explícito: categoria de origen NO canónica -> "" (decisión 2).
# El resto de campos se mantiene mínimo pero completo, para aislar solo la
# regla de normalización de categoria.
FIXTURE_ITEM_CATEGORIA_NO_CANONICA: dict = {
    "organizacion": "Otra Org SA",
    "categoria": "",  # origen real: "vertical_fintech" (no es uno de los 4)
    "tipo_epistemologico": "senal_primaria_huella_practica",
    "cita_textual": "Otra Org SA publica una vacante de ingeniería en México",
    "url_fuente": "https://ejemplo.test/otra-org-vacante",
    "nombre_medio": "Medio de Prueba 2",
    "fecha_publicacion": None,
    "persona_citada": None,
    "cargo": None,
    "enunciador_nombre": None,
    "enunciador_cargo": None,
}

CLAVES_ITEM_EXPEDIENTE_CANONICO = frozenset(FIXTURE_ITEM_EXPEDIENTE_CANONICO.keys())
