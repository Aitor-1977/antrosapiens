#!/usr/bin/env python3
"""Sincroniza los instrumentos de campo HTML de la raíz del repo hacia los
assets de la app (`hd_scraper/api/static/instrumentos/`).

La carpeta `hd_scraper/**` viaja en el bundle de la función serverless de
Vercel (`vercel.json` → `includeFiles`), y la API los sirve en `/instrumentos`
con `Cache-Control: no-store`: basta commit + push (deploy Vercel) para que
cualquier edición a un instrumento de la raíz se refleje en producción al
instante, sin reconstruir la arquitectura.

    python -m scripts.sync_instrumentos      # copia y lista las URLs de producción

Idempotente: re-copiar no duplica; sobrescribe el destino con la versión nueva.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIGEN = ROOT
DESTINO = ROOT / "hd_scraper" / "api" / "static" / "instrumentos"

URL_BASE = "https://lemures-66.vercel.app/instrumentos"


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    htmls = sorted(ORIGEN.glob("*.html"))
    copiados = 0
    for origen in htmls:
        shutil.copy2(origen, DESTINO / origen.name)
        copiados += 1
    print(f"instrumentos sincronizados: {copiados} -> {DESTINO}")
    print(f"índice: {URL_BASE}")
    for nombre in sorted(p.name for p in DESTINO.glob("*.html")):
        print(f"  {URL_BASE}/{nombre}")


if __name__ == "__main__":
    sys.exit(main())
