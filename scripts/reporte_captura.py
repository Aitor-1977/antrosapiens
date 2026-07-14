"""Reporte comparativo ANTES / DESPUÉS de la Captura Inteligente (Motor A).

Ejecuta un corpus de descubrimiento CONTROLADO (fixture determinista) por el
pipeline ANTES de la mejora (dedup solo por empresa+url, sin filtro de
relevancia) y DESPUÉS (dedup robusto de contenido + filtro de relevancia
objetivo + calidad_captura). Imprime la tabla comparativa pedida.

Es una simulación reproducible: en este entorno no hay salida a Internet, así
que en lugar de golpear Google News en vivo se usa un pool de titulares
representativos (eventos reales, republicaciones, opiniones, tendencias sin
empresa y notas sin evento) surgidos por VARIAS consultas —igual que en
producción, donde el mismo artículo aparece bajo distintas consultas—.

Uso:  python -m scripts.reporte_captura
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hd_scraper.config import settings
from hd_scraper.connectors.google_news import GoogleNewsConnector
from hd_scraper.db.database import Database
from hd_scraper.db.models import (
    ESTADO_NO_FECHADO,
    QuerySpec,
    RawItem,
    calcular_hash_dedup,
)
from hd_scraper.pipeline import run_connector
from hd_scraper.signals import calcular_confianza, detectar_keywords

object.__setattr__(settings, "raw_enabled", False)
object.__setattr__(settings, "min_interval_s", 0.0)

# ── Pool de artículos (titulo, url, medio, fecha) ─────────────────────────────
# `fecha=None` => nota sin fecha (no consumible). Categorías del pool:
#   E = evento con empresa (útil)      R = republicación del mismo evento
#   O = opinión/tendencia              S = sin empresa                N = sin evento
POOL = {
    "E1": ("Nubank adquiere una fintech de pagos - Bloomberg Línea",
           "https://news.google.com/rss/articles/E1", "Bloomberg Línea", "2026-07-01T10:00:00Z"),
    "E1r": ("Nubank adquiere una fintech de pagos - El Financiero",
            "https://news.google.com/rss/articles/E1r", "El Financiero", "2026-07-01T12:00:00Z"),
    "E2": ("Clip anuncia despidos masivos y reestructuración - Expansión",
           "https://news.google.com/rss/articles/E2", "Expansión", "2026-07-02T09:00:00Z"),
    "E3": ("Kavak cierra operaciones en un mercado - Reuters",
           "https://news.google.com/rss/articles/E3", "Reuters", "2026-07-03T09:00:00Z"),
    "E4": ("Bitso firma una alianza estratégica con un banco - El Economista",
           "https://news.google.com/rss/articles/E4", "El Economista", "2026-07-04T09:00:00Z"),
    "E5": ("La fintech Ualá levanta capital serie D - Forbes",
           "https://news.google.com/rss/articles/E5", "Forbes", None),
    "E6": ("Konfío duplica ingresos este año",
           "https://news.google.com/rss/articles/E6", "Google News", "2026-07-05T09:00:00Z"),
    "O1": ("Opinión: por qué las fintech van a fracasar - Columna",
           "https://news.google.com/rss/articles/O1", "Medio X", "2026-07-01T08:00:00Z"),
    "O2": ("5 claves para entender el churn en startups - Blog",
           "https://news.google.com/rss/articles/O2", "Blog Y", "2026-07-01T08:00:00Z"),
    "O3": ("El futuro de la banca digital en 2027 - Análisis",
           "https://news.google.com/rss/articles/O3", "Medio Z", "2026-07-01T08:00:00Z"),
    "S1": ("Las startups enfrentan un año de despidos - Reporte",
           "https://news.google.com/rss/articles/S1", "Medio W", "2026-07-01T08:00:00Z"),
    "S2": ("El sector fintech vive una ola de adquisiciones - Nota",
           "https://news.google.com/rss/articles/S2", "Medio V", "2026-07-01T08:00:00Z"),
    "N1": ("Nubank celebra su aniversario en la ciudad - Prensa",
           "https://news.google.com/rss/articles/N1", "Medio U", "2026-07-01T08:00:00Z"),
    "N2": ("Bitso participa en un foro de tecnología - Prensa",
           "https://news.google.com/rss/articles/N2", "Medio T", "2026-07-01T08:00:00Z"),
}

# Consultas de descubrimiento y qué artículos surge cada una (con solapes, para
# reproducir las republicaciones/duplicados entre consultas).
CONSULTAS = [
    ("startup fintech adquisición", ["E1", "E1r", "O3", "S2", "N1", "N2", "E6"]),
    ("startup fintech despidos",    ["E2", "E3", "O1", "S1", "N1"]),
    ("startup fintech fricción",    ["E1", "O2", "E4", "E5", "S1"]),
]


def _raw(clave: str) -> RawItem:
    titulo, url, medio, fecha = POOL[clave]
    meta = {"titulo": titulo, "link": url, "fuente": medio,
            "fecha_publicacion": fecha, "tipo_evento": "queja"}
    return RawItem(url=url, contenido=json.dumps({"title": titulo}), formato="json", meta=meta)


class _FakeGoogleNews(GoogleNewsConnector):
    """Reusa normalize/validate reales; search devuelve el pool de la consulta.

    Igual que el conector real, marca meta['empresa'] con el término de la
    consulta (en descubrimiento la 'empresa' es el término, no una compañía).
    """
    def __init__(self, claves, **kw):
        super().__init__(**kw)
        self._claves = claves

    def search(self, query):
        items = []
        for c in self._claves:
            it = _raw(c)
            it.meta["empresa"] = query.empresa
            items.append(it)
        return items


def _query(termino: str) -> QuerySpec:
    return QuerySpec(empresa=termino, tipo_evento="queja", exact=False, categoria="Startup")


# ── ANTES: comportamiento previo (dedup solo empresa+url, sin relevancia) ─────

def _correr_antes(db: Database) -> dict:
    vistos = escritos = duplicados = nofechados = 0
    for termino, claves in CONSULTAS:
        for clave in claves:
            vistos += 1
            titulo, url, medio, fecha = POOL[clave]
            empresa = termino  # como antes: la "empresa" era el término del query
            keywords = detectar_keywords(titulo)
            confianza = calcular_confianza(fecha, medio, keywords)
            hash_dedup = calcular_hash_dedup(empresa, url)
            estado = "ok" if fecha else ESTADO_NO_FECHADO
            cur = db.execute(
                """INSERT INTO evidencias (
                     cita_textual, fecha_extraccion, url_fuente, nombre_medio,
                     empresa_mencionada, tipo_evento, origen_declaracion, hash_dedup,
                     fecha_publicacion, connector, estado, confianza, creado_en,
                     keywords)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT (hash_dedup) DO NOTHING""",
                (titulo, "2026-07-14T00:00:00Z", url, medio, empresa, "queja",
                 "prensa", hash_dedup, fecha, "google_news", estado, confianza,
                 "2026-07-14T00:00:00Z", json.dumps(keywords, ensure_ascii=False)),
            )
            if cur.rowcount > 0:
                escritos += 1
                if not fecha:
                    nofechados += 1
            else:
                duplicados += 1
    return {"vistos": vistos, "escritos": escritos, "duplicados": duplicados,
            "no_fechados": nofechados, "filtrados": 0}


# ── DESPUÉS: pipeline real con Captura Inteligente ───────────────────────────

def _correr_despues(db: Database) -> dict:
    tot = {"vistos": 0, "escritos": 0, "duplicados": 0, "no_fechados": 0, "filtrados": 0}
    for termino, claves in CONSULTAS:
        c = _FakeGoogleNews(claves)
        r = run_connector(db, c, _query(termino))
        tot["vistos"] += r.vistos
        tot["escritos"] += r.escritos
        tot["duplicados"] += r.duplicados
        tot["no_fechados"] += r.no_fechados
        tot["filtrados"] += r.filtrados
    return tot


def _distribucion_calidad(db: Database) -> dict:
    filas = db.fetch_all(
        "SELECT calidad_captura AS c, COUNT(*) AS n FROM evidencias "
        "WHERE estado='ok' GROUP BY calidad_captura")
    d = {"Alta": 0, "Media": 0, "Baja": 0}
    for f in filas:
        if f["c"] in d:
            d[f["c"]] = f["n"]
    return d


def main() -> None:
    antes_db = Database(":memory:"); antes_db.init_schema()
    despues_db = Database(":memory:"); despues_db.init_schema()

    antes = _correr_antes(antes_db)
    despues = _correr_despues(despues_db)

    antes_utiles = antes_db.fetch_one(
        "SELECT COUNT(*) AS n FROM evidencias WHERE estado='ok'")["n"]
    despues_utiles = despues_db.fetch_one(
        "SELECT COUNT(*) AS n FROM evidencias WHERE estado='ok'")["n"]
    antes_total = antes_db.fetch_one("SELECT COUNT(*) AS n FROM evidencias")["n"]
    despues_total = despues_db.fetch_one("SELECT COUNT(*) AS n FROM evidencias")["n"]
    dist = _distribucion_calidad(despues_db)

    descartados_despues = despues["duplicados"] + despues["filtrados"]
    ruido_antes = antes_total - despues_utiles       # aprox. de basura que antes entraba
    mejora = (1 - despues_utiles / antes_total) * 100 if antes_total else 0.0

    print("=" * 64)
    print("REPORTE COMPARATIVO — CAPTURA INTELIGENTE (Motor A)")
    print("=" * 64)
    print(f"Consultas de descubrimiento simuladas : {len(CONSULTAS)}")
    print(f"Titulares vistos (con solapes)        : {antes['vistos']}")
    print("-" * 64)
    print(f"{'Métrica':38} {'ANTES':>10} {'DESPUÉS':>12}")
    print("-" * 64)
    print(f"{'Artículos almacenados (total)':38} {antes_total:>10} {despues_total:>12}")
    print(f"{'Artículos útiles (estado=ok)':38} {antes_utiles:>10} {despues_utiles:>12}")
    print(f"{'Duplicados eliminados':38} {antes['duplicados']:>10} {despues['duplicados']:>12}")
    print(f"{'Descartados por relevancia':38} {antes['filtrados']:>10} {despues['filtrados']:>12}")
    print(f"{'Descartados totales (dup+filtro)':38} "
          f"{antes['duplicados']:>10} {descartados_despues:>12}")
    print("-" * 64)
    print(f"Reducción de ruido del corpus         : {mejora:5.1f}%")
    print(f"Distribución de calidad (DESPUÉS)     : "
          f"Alta={dist['Alta']}  Media={dist['Media']}  Baja={dist['Baja']}")
    print("=" * 64)

    antes_db.close()
    despues_db.close()


if __name__ == "__main__":
    main()
