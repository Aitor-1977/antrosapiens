#!/usr/bin/env python3
"""Crea el esquema en la base configurada (SQLite o PostgreSQL).

Idempotente (CREATE TABLE IF NOT EXISTS). Úsalo tras conectar la base Postgres:

    HD_DATABASE_URL="postgres://..." python -m scripts.migrate

Sin variables, usa la base por defecto (SQLite local). En Vercel, la API
también crea el esquema al primer acceso, así que este script es opcional.
"""
from __future__ import annotations

from hd_scraper.config import settings
from hd_scraper.db.database import Database


def main() -> None:
    db = Database()
    db.init_schema()
    print(f"esquema aplicado ({db.dialect}) en: {settings.database_url.split('@')[-1]}")
    # Recuento rápido de tablas para confirmar.
    if db.dialect == "sqlite":
        filas = db.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tablas = [f["name"] for f in filas]
    else:
        filas = db.fetch_all(
            "SELECT tablename AS name FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        tablas = [f["name"] for f in filas]
    print("tablas:", ", ".join(tablas))
    db.close()


if __name__ == "__main__":
    main()
