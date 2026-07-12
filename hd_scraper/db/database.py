"""Acceso a la base de datos: SQLite (local/tests) o PostgreSQL (producción).

Un único wrapper habla los dos motores. El dialecto se decide por la URL:

    postgres://... | postgresql://...  -> PostgreSQL vía psycopg (v3)
    sqlite:///ruta | ruta | :memory:   -> SQLite

El código de la app escribe SQL con marcador ``?`` (estilo SQLite); para
Postgres se traduce a ``%s`` de forma transparente. El SQL compartido usa solo
sintaxis válida en ambos motores (``ON CONFLICT ... DO NOTHING/UPDATE``). El DDL,
que sí difiere (autoincremento), vive en dos archivos: ``schema.sql`` (SQLite) y
``schema_postgres.sql`` (Postgres).

psycopg se importa de forma perezosa: los entornos que solo usan SQLite (tests,
dev) no necesitan tenerlo instalado.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

from ..config import settings

_DIR = Path(__file__).resolve().parent
SCHEMA_SQLITE = _DIR / "schema.sql"
SCHEMA_POSTGRES = _DIR / "schema_postgres.sql"


def _es_postgres(dsn: str) -> bool:
    return dsn.startswith("postgres://") or dsn.startswith("postgresql://")


class Database:
    def __init__(self, dsn: str | Path | None = None) -> None:
        if dsn is None:
            dsn = settings.database_url
        dsn = str(dsn)

        if _es_postgres(dsn):
            self.dialect = "postgres"
            self._connect_postgres(dsn)
        else:
            self.dialect = "sqlite"
            self._connect_sqlite(dsn)

    # -- Conexión -------------------------------------------------------
    def _connect_sqlite(self, dsn: str) -> None:
        if dsn.startswith("sqlite:///"):
            dsn = dsn[len("sqlite:///"):]
        self.path = Path(dsn)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def _connect_postgres(self, dsn: str) -> None:
        import psycopg
        from psycopg.rows import dict_row

        # psycopg acepta el prefijo postgres:// directamente. Neon/Vercel ya
        # incluyen sslmode=require en la cadena.
        self.conn = psycopg.connect(dsn, row_factory=dict_row)

    # -- Traducción de marcadores --------------------------------------
    def _q(self, sql: str) -> str:
        # El SQL de la app no contiene '?' literales ni '%' literales, así que la
        # sustitución es segura para el paramstyle de psycopg.
        return sql if self.dialect == "sqlite" else sql.replace("?", "%s")

    # -- Inicialización -------------------------------------------------
    def init_schema(self) -> None:
        if self.dialect == "sqlite":
            self.conn.executescript(SCHEMA_SQLITE.read_text(encoding="utf-8"))
        else:
            # psycopg admite múltiples sentencias en un execute sin parámetros.
            self.conn.execute(SCHEMA_POSTGRES.read_text(encoding="utf-8"))
        self.conn.commit()

    # -- Operaciones ----------------------------------------------------
    def execute(self, sql: str, params: Iterable[Any] = ()):
        cur = self.conn.execute(self._q(sql), tuple(params))
        self.conn.commit()
        return cur

    def fetch_one(self, sql: str, params: Iterable[Any] = ()) -> Optional[Any]:
        return self.conn.execute(self._q(sql), tuple(params)).fetchone()

    def fetch_all(self, sql: str, params: Iterable[Any] = ()) -> list[Any]:
        return self.conn.execute(self._q(sql), tuple(params)).fetchall()

    def insert_returning_id(self, sql: str, params: Iterable[Any] = ()) -> int:
        """INSERT que devuelve el id generado, portable entre motores."""
        if self.dialect == "sqlite":
            cur = self.conn.execute(sql, tuple(params))
            self.conn.commit()
            return cur.lastrowid
        cur = self.conn.execute(self._q(sql) + " RETURNING id", tuple(params))
        rid = cur.fetchone()["id"]
        self.conn.commit()
        return rid

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


_db_singleton: Database | None = None


def get_db() -> Database:
    """Instancia compartida (para API/scheduler). Crea el esquema si falta."""
    global _db_singleton
    if _db_singleton is None:
        _db_singleton = Database()
        _db_singleton.init_schema()
    return _db_singleton
