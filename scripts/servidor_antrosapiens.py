"""Servidor de escritorio de AntroSapiens (pruebas de la UI vía HTTP).

Arranca la API real de hd-scraper (con el router de investigación incluido) y
sirve la UI V4 en ``/app``. En Android la UI corre en el WebView con el puente
JS; este script solo facilita la validación en escritorio.

Uso:
    python -m scripts.servidor_antrosapiens [--port 8080] [--db ruta.db]
"""
from __future__ import annotations

import argparse

import uvicorn

from hd_scraper.api.investigacion_router import build_app


def main() -> None:
    ap = argparse.ArgumentParser(description="Servidor AntroSapiens (escritorio)")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--db", default=None, help="Ruta de la base SQLite local (offline-first)")
    args = ap.parse_args()

    if args.db:
        from hd_scraper.config import settings
        object.__setattr__(settings, "database_url", f"sqlite:///{args.db}")

    app = build_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
