"""Indagación profunda bajo demanda — Fase B (scraping inteligente por eventos).

Corre los conectores de Motor A (Google News, GDELT) en modo LECTURA para una
organización, extrae EVENTOS reales, fechados y citables, y los pasa por el
cerebro determinista (`analizar` → Deuda Cultural™, scoring, ICP). Combina el
resultado con la lectura estructural del discurso (Capa 0).

Naturaleza y frontera:
- **Read-only**: NO escribe evidencia. Encaja en serverless bajo demanda (una
  petición = una investigación, sin scheduler).
- **Grounded, jamás fabrica**: cada evento se cita con su titular, medio, fecha y
  URL. Sin eventos y sin marcadores de discurso ⇒ estado ``requiere_campo``.
- **Degrada con elegancia**: si una fuente falla, usa lo que consiguió y reporta
  la salud por fuente. Nunca queda peor que la lectura del discurso sola.
- **Determinista**: la síntesis (Deuda dominante, scoring) es reproducible.

`tipo_evento` en la QuerySpec es metadato estructural; la búsqueda es por el
NOMBRE de la organización y los eventos se detectan de los titulares reales por
`detectar_keywords` (determinista), no se infieren leyendo con criterio.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from .analisis import analizar
from .connectors import REGISTRY
from .db.models import QuerySpec
from .lectura_estructural import leer_discurso
from .perfil_fundacional import construir_perfil
from .signals import detectar_keywords

log = logging.getLogger("hd_scraper.indagacion")

# Conectores de prensa/eventos que corren en modo lectura bajo demanda.
CONECTORES_INDAGACION = ("google_news", "gdelt")

# Prioridad de scoring para agregar (A es la mayor).
_ORDEN_SCORING = {"A": 3, "B": 2, "C": 1, "": 0}


def _analizar_titular(titulo: str, vertical: str = "") -> dict:
    kws = detectar_keywords(titulo or "")
    a = analizar(kws, vertical=vertical)
    return {"keywords": kws, **a}


def buscar_eventos(empresa: str, connectors: tuple[str, ...] = CONECTORES_INDAGACION,
                   limite: int = 8, vertical: str = "") -> tuple[list[dict], list[tuple]]:
    """Corre los conectores en modo LECTURA (search + normalize, sin escribir).

    Devuelve ``(eventos, salud)``. Nunca lanza: una fuente caída se reporta en
    ``salud`` y no interrumpe a las demás.
    """
    eventos: list[dict] = []
    salud: list[tuple] = []
    for cname in connectors:
        cls = REGISTRY.get(cname)
        if cls is None or getattr(cls, "requires_slug", False):
            continue
        try:
            with cls() as conn:
                query = QuerySpec(empresa=empresa, tipo_evento="lanzamiento", exact=True)
                raws = list(conn.search(query))[:limite]
                for raw in raws:
                    rec = conn.normalize(raw)
                    a = _analizar_titular(rec.cita_textual, vertical)
                    eventos.append({
                        "titulo": rec.cita_textual,
                        "url": rec.url_fuente,
                        "medio": rec.nombre_medio,
                        "fecha": rec.fecha_publicacion,
                        "keywords": a["keywords"],
                        "tipo_deuda": a.get("tipo_deuda") or None,
                        "deuda_razon": a.get("deuda_razon") or None,
                        "scoring": a.get("scoring") or "",
                        "score_icp": a.get("score_icp"),
                        "fuente": cname,
                    })
            salud.append((cname, True, f"{len(raws)} resultados"))
        except Exception as e:  # pragma: no cover - la red no corre en tests
            salud.append((cname, False, str(e)[:160]))
            log.warning("indagación: fuente %s falló: %s", cname, e)
    return eventos, salud


def _deuda_dominante(eventos: list[dict]) -> Optional[str]:
    """Tipo de Deuda más frecuente entre los eventos con señal. Determinista:
    desempata por el primer evento (orden de llegada) que la exhibe."""
    conteo: dict[str, int] = {}
    primer_indice: dict[str, int] = {}
    for i, e in enumerate(eventos):
        d = e.get("tipo_deuda")
        if d:
            conteo[d] = conteo.get(d, 0) + 1
            primer_indice.setdefault(d, i)
    if not conteo:
        return None
    return sorted(conteo, key=lambda d: (-conteo[d], primer_indice[d]))[0]


def sintetizar(empresa: str, eventos: list[dict], lectura_discurso: dict) -> dict:
    """Pura y determinista: agrega eventos + lectura del discurso en un peritaje
    preliminar. Sin red."""
    # Eventos ordenados por fecha desc (los sin fecha, al final); citables.
    ordenados = sorted(eventos, key=lambda e: (e.get("fecha") or ""), reverse=True)
    deuda_eventos = _deuda_dominante(eventos)
    scoring = max((e.get("scoring") or "" for e in eventos),
                  key=lambda s: _ORDEN_SCORING.get(s, 0), default="")
    icps = [e["score_icp"] for e in eventos if isinstance(e.get("score_icp"), (int, float))]
    score_icp = max(icps) if icps else None

    # La Deuda dominante: la de los eventos si existe; si no, la del discurso.
    deuda_discurso = lectura_discurso.get("tipo_deuda_preliminar")
    deuda_dominante = deuda_eventos or deuda_discurso

    tiene_senal = bool(eventos) or lectura_discurso.get("estado") == "grounded"
    return {
        "empresa": empresa,
        "estado": "grounded" if tiene_senal else "requiere_campo",
        "total_eventos": len(eventos),
        "deuda_dominante_preliminar": deuda_dominante,
        "deuda_por_eventos": deuda_eventos,
        "scoring": scoring or None,
        "score_icp": score_icp,
        "eventos": ordenados,
        "lectura_discurso": lectura_discurso,
        "nota": (
            "Peritaje PRELIMINAR: eventos públicos observables + lectura del "
            "discurso, sin juicio de campo. El diagnóstico se confirma con "
            "DolorMap® (etnografía). Grounded: cada evento es citable."
        ),
    }


def indagar_profundo(empresa: str, dominio: Optional[str] = None, vertical: str = "",
                     buscar_fn: Callable[..., tuple[list[dict], list[tuple]]] = buscar_eventos) -> dict:
    """Orquesta la indagación profunda de una organización (read-only).

    ``buscar_fn`` es inyectable para pruebas (por defecto corre los conectores
    reales). ``dominio`` habilita la lectura del discurso propio.
    """
    eventos, salud = buscar_fn(empresa, vertical=vertical)

    discurso: Optional[str] = None
    if dominio:
        try:
            discurso = construir_perfil(empresa, dominio).discurso_corporativo
        except Exception:  # pragma: no cover - la red no corre en tests
            discurso = None
    lectura = leer_discurso(discurso, empresa=empresa)

    out = sintetizar(empresa, eventos, lectura)
    out["salud_fuentes"] = [{"fuente": f, "ok": ok, "detalle": det} for (f, ok, det) in salud]
    return out
