"""Fixture congelado del E2E del Observatorio (Fase 6.3 del encargo
2026-09-18). Definido contra la forma PÚBLICA y documentada de la respuesta
de Apple Podcasts Search API (developer.apple.com/library/archive/
documentation/AudioVideo/Conceptual/iTuneSearchAPI/), no derivado del código
del conector: un episodio crudo de ejemplo y el resultado normalizado que
`GET /observatorio` debe devolver para él.
"""
from __future__ import annotations

ACTOR_PRUEBA = "Fixture Org SA"

EPISODIO_CRUDO = {
    "trackViewUrl": "https://podcasts.apple.com/us/podcast/fixture-episode/id1?i=1",
    "episodeUrl": "https://cdn.example.test/fixture-episode.mp3",
    "collectionName": "El Podcast de Prueba",
    "releaseDate": "2026-01-15T10:00:00Z",
    "trackTimeMillis": 1800000,  # 30 minutos exactos
    "description": (
        "En este episodio, la fundadora de Fixture Org SA cuenta cómo "
        "construyó la empresa desde cero y qué aprendió en el camino."
    ),
    "shortDescription": "La fundadora de Fixture Org SA cuenta su historia.",
    "genres": [{"name": "Business", "id": "1321"}],
}

# Lo que se espera que produzca normalize() a partir de EPISODIO_CRUDO.
FUENTE_ESPERADA = {
    "tipo_fuente": "podcast",
    "url": "https://podcasts.apple.com/us/podcast/fixture-episode/id1?i=1",
    "plataforma": "Apple Podcasts",
    "actor_principal": ACTOR_PRUEBA,
    "fecha_publicacion": "2026-01-15T10:00:00Z",
    "duracion_aprox": "30 min",
}

FRAGMENTO_ESPERADO = {
    "texto_citable": (
        "En este episodio, la fundadora de Fixture Org SA cuenta cómo "
        "construyó la empresa desde cero y qué aprendió en el camino."
    ),
    "minuto_aproximado": None,
    "tema_libre": "Business",
    "tipo_registro": "dato",
    "estado": "capturado",
}
