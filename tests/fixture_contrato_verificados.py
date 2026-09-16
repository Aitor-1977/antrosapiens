"""FIXTURE DE REFERENCIA CONGELADO — contrato REAL de GET /verificados.

Creado en FASE 1 (inspección, 2026-09-16) ANTES de escribir
`schema_expediente.py`. Representa el contrato tal como lo produce HOY
`hd_scraper.candidatos_verificados.listar_candidatos_verificados` (código) y
tal como lo devolvió el endpoint real en producción el mismo día (ver
diagnóstico de Fase 1 para la respuesta cruda observada).

REGLA DE CONGELAMIENTO (instrucción explícita de Mario): este fixture NO se
deriva de `schema_expediente.py` ni de ningún schema futuro — es al revés,
el schema futuro debe adaptarse a esto. NO modificar este archivo para hacer
pasar una prueba; si una prueba falla contra este fixture, el error está en
la implementación o en el fixture está mal fechado, nunca se ajusta el
fixture para acomodar el código.

Un solo expediente sintético, con las 9 columnas EXACTAS que hoy expone el
endpoint (ver candidatos_verificados.py líneas 80-90), tipos reales
observados (str | null) y un valor explícito para cada campo — no genérico.
"""
from __future__ import annotations

# Item único, tal como aparece dentro de la lista `items` de GET /verificados.
FIXTURE_ITEM_VERIFICADO: dict = {
    "organizacion": "Fixture Org SA",
    "categoria": "Startup",
    "tipo_epistemologico": "senal_primaria_autodeclaracion",
    "cita_textual": "Ana Torres, fundadora y CEO de Fixture Org, anunció una "
                     "ronda de inversión de 12 millones de dólares para su "
                     "expansión en México",
    "url_fuente": "https://ejemplo.test/fixture-org-ronda",
    "nombre_medio": "Medio de Prueba",
    "fecha_publicacion": "2026-09-01T09:00:00+00:00",
    "persona_citada": None,
    "cargo": None,
}

# Respuesta COMPLETA del endpoint (wrapper "total"/"items"), tal como la
# arma `verificados_listar` en hd_scraper/api/app.py.
FIXTURE_RESPUESTA_VERIFICADOS: dict = {
    "total": 1,
    "items": [FIXTURE_ITEM_VERIFICADO],
}

# Claves EXACTAS esperadas por cada item (orden no relevante, presencia sí).
# Cualquier clave de más o de menos respecto a este conjunto es, por
# definición, una discrepancia respecto al contrato congelado.
CLAVES_ITEM_VERIFICADO = frozenset(FIXTURE_ITEM_VERIFICADO.keys())
