"""Backfill de diagnóstico: extrae el cuerpo completo de 50 evidencias de
google_news y lo guarda en `evidencias.cuerpo_completo`.

NO escribe clasificación (eso lo hace el clasificador, en seco). Solo puebla
la materia prima para el diagnóstico comparativo. No toca producción.
"""
from __future__ import annotations

import httpx
import sqlite3
import sys
import time

sys.path.insert(0, "/data/data/com.termux/files/home/antrosapiens")
from hd_scraper.connectors.google_news import extraer_cuerpo

DB = "/data/data/com.termux/files/home/antrosapiens/data/hd_scraper.db"
OBJETIVO = 50
INTENTOS_MAX = 250
TIMEOUT = 12.0
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")

HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"}


def main() -> int:
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(
        "SELECT id, url_fuente FROM evidencias "
        "WHERE connector='google_news' AND cuerpo_completo IS NULL "
        "AND url_fuente IS NOT NULL AND url_fuente<>'' "
        "ORDER BY id LIMIT ?",
        (INTENTOS_MAX,),
    )
    filas = cur.fetchall()
    print(f"candidatos disponibles: {len(filas)}")

    client = httpx.Client(follow_redirects=True, timeout=TIMEOUT, headers=HEADERS)
    hechos = 0
    fallidos = 0
    for i, (eid, url) in enumerate(filas):
        if hechos >= OBJETIVO:
            break
        try:
            r = client.get(url)
            html = r.text
        except Exception as exc:
            fallidos += 1
            print(f"  [{i}] FETCH_FAIL id={eid}: {exc!r}")
            continue
        cuerpo = extraer_cuerpo(html)
        if not cuerpo:
            fallidos += 1
            print(f"  [{i}] EMPTY id={eid} status={getattr(r,'status_code','?')}")
            continue
        cur.execute(
            "UPDATE evidencias SET cuerpo_completo=? WHERE id=?",
            (cuerpo, eid),
        )
        hechos += 1
        if hechos % 10 == 0:
            print(f"  ... {hechos} cuerpos extraídos")
    con.commit()
    con.close()
    client.close()
    print(f"RESULTADO: extraídos={hechos} fallidos={fallidos}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
