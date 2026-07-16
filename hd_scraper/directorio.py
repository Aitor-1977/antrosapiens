"""Directorio de empresas reales (Wikidata) — VOLUMEN sin depender de noticias.

Google News encuentra empresas CON un evento de prensa; muchas empresas reales no
tienen noticia fresca y quedaban fuera. Este módulo trae empresas de una BASE
PÚBLICA y gratuita (Wikidata, sin clave ni pago): por país e (opcional) vertical,
con su sitio web y descripción. Alimenta la tabla de prospectos con volumen real
y accionable (dominio → contacto; descripción → vertical/ICP).

Sigue siendo captura de HECHOS: se guarda lo que Wikidata publica (nombre, web,
descripción), sin interpretar. La red se inyecta (``http_get_json``) para testear
con fixtures. Nunca lanza: ante fallo devuelve lista vacía + nota.

Cobertura honesta: Wikidata cubre mejor empresas notables/medianas que micro-
startups. Da volumen real, no exhaustividad. Para cobertura total de startups
haría falta una base de pago (Crunchbase/Apollo); este es el camino gratuito.
"""
from __future__ import annotations

import logging
from typing import Callable
from urllib.parse import quote_plus

from .enrich import sugerir_vertical
from .relevance import GIGANTES, _norm

log = logging.getLogger("hd_scraper.directorio")

WDQS = "https://query.wikidata.org/sparql"

# País → identificador Wikidata (QID). Zona LATAM del laboratorio.
PAIS_QID: dict[str, str] = {
    "México": "Q96", "Colombia": "Q739", "Chile": "Q298", "Perú": "Q419",
    "Argentina": "Q414", "Brasil": "Q155", "Costa Rica": "Q800", "Panamá": "Q804",
}

HttpGetJson = Callable[[str], dict]


def _sparql(pais_qid: str, limite: int) -> str:
    # Empresas (instancia de "empresa" o subclase) del país, con sitio web y,
    # si existe, descripción en español. Requerir el sitio asegura dominio para
    # el contacto y filtra a entidades reales/establecidas.
    return (
        "SELECT ?empresa ?empresaLabel ?sitio ?descripcion WHERE { "
        "?empresa wdt:P31/wdt:P279* wd:Q4830453 . "
        f"?empresa wdt:P17 wd:{pais_qid} . "
        "?empresa wdt:P856 ?sitio . "
        "OPTIONAL { ?empresa schema:description ?descripcion . "
        "FILTER(LANG(?descripcion) = \"es\") } "
        "SERVICE wikibase:label { bd:serviceParam wikibase:language \"es,en\". } "
        f"}} LIMIT {int(limite)}"
    )


def url_consulta(pais: str, limite: int = 50) -> str:
    """URL de la consulta SPARQL a Wikidata para un país. '' si el país no está."""
    qid = PAIS_QID.get(pais)
    if not qid:
        return ""
    return f"{WDQS}?format=json&query={quote_plus(_sparql(qid, limite))}"


def _es_qid(texto: str) -> bool:
    """True si el 'label' es en realidad un QID sin etiqueta (Q12345)."""
    t = (texto or "").strip()
    return len(t) > 1 and t[0] == "Q" and t[1:].isdigit()


def _coincide_vertical(nombre: str, descripcion: str, vertical: str) -> bool:
    if not vertical or vertical == "todas":
        return True
    texto = f"{nombre} {descripcion}"
    sug = sugerir_vertical(texto)
    if sug == vertical:
        return True
    return _norm(vertical) in _norm(texto)


def parse_empresas(data: dict, vertical: str = "todas") -> list[dict]:
    """Convierte la respuesta SPARQL en empresas. Filtra gigantes y por vertical."""
    filas = ((data or {}).get("results") or {}).get("bindings") or []
    vistos: set[str] = set()
    salida: list[dict] = []
    for b in filas:
        nombre = ((b.get("empresaLabel") or {}).get("value") or "").strip()
        if not nombre or _es_qid(nombre):
            continue
        clave = nombre.lower()
        if clave in vistos:
            continue
        n = _norm(nombre)
        if any(g in n for g in GIGANTES):     # gigantes no son ICP de HD
            continue
        descripcion = ((b.get("descripcion") or {}).get("value") or "").strip()
        if not _coincide_vertical(nombre, descripcion, vertical):
            continue
        vistos.add(clave)
        salida.append({
            "nombre": nombre,
            "sitio_web": ((b.get("sitio") or {}).get("value") or "").strip(),
            "descripcion": descripcion,
            "vertical_sugerida": sugerir_vertical(f"{nombre} {descripcion}") or "",
            "fuente": "Wikidata",
        })
    return salida


def buscar_empresas(pais: str, vertical: str, http_get_json: HttpGetJson,
                    limite: int = 50) -> list[dict]:
    """Busca empresas reales del país (y vertical) en Wikidata. Nunca lanza."""
    url = url_consulta(pais, limite)
    if not url:
        return []
    try:
        data = http_get_json(url)
    except Exception as exc:
        log.debug("directorio: consulta Wikidata falló: %s", exc)
        return []
    return parse_empresas(data, vertical)
