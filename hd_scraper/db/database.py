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
        self._dsn = dsn

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
        self._migrar_pipeline_candidato()
        self._migrar_organizacion_mencionada()
        self._migrar_expediente_id_nullable()
        self.conn.commit()

    def _migrar_expediente_id_nullable(self) -> None:
        """Migración idempotente (2026-08-29, ver §8.3 del documento maestro):
        ``evidencia_clasificada.expediente_id`` pasa a admitir NULL.

        Antes, una evidencia sin organización identificable no podía
        persistirse en absoluto (la columna era NOT NULL) — se perdía en
        silencio, confirmado empíricamente con las 96 evidencias de
        `busqueda_dinamica_founder`: 0 quedaron guardadas en
        `evidencia_clasificada`, ni siquiera las 5 con
        `senal_primaria_autodeclaracion`. Ahora se conserva con
        `expediente_id = NULL`: sin fila en `expedientes_candidatos` que
        referencie esa clasificación, no hay caso organizacional ni
        promoción posible (`promocion_store.py` solo evalúa expedientes que
        SÍ existen en `expedientes_candidatos`, así que una fila con
        `expediente_id` NULL nunca entra en ese universo) — pero la
        evidencia y su clasificación ya no se pierden.

        Solo aplica en Postgres: SQLite no soporta
        ``ALTER TABLE ... ALTER COLUMN ... DROP NOT NULL``, y las bases
        SQLite (dev/tests) siempre se crean desde cero con ``schema.sql``,
        que ya declara la columna nullable.
        """
        if self.dialect != "postgres":
            return
        try:
            self.conn.execute(
                "ALTER TABLE evidencia_clasificada "
                "ALTER COLUMN expediente_id DROP NOT NULL")
        except Exception:
            pass

    def _migrar_organizacion_mencionada(self) -> None:
        """Migración idempotente: añade ``organizacion_mencionada`` a
        ``evidencia_clasificada`` (bases persistentes previas a esta
        ampliación del clasificador epistemológico). El ALTER es un no-op
        cuando la columna ya existe. Ver CLAUDE.md "Frontera de
        Interpretación" (entrada 2026-08-28).
        """
        try:
            self.conn.execute(
                "ALTER TABLE evidencia_clasificada "
                "ADD COLUMN organizacion_mencionada TEXT")
        except Exception:
            pass

    def _migrar_pipeline_candidato(self) -> None:
        """Migración idempotente: añade ``candidato_id`` a ``pipeline_comercial``.

        ``CREATE TABLE IF NOT EXISTS`` no añade columnas a una tabla ya
        existente (bases persistentes previas a la reparación BC-I↔BC-II).
        El ALTER es un no-op cuando la columna ya existe (SQLite y Postgres
        lanzan el mismo tipo de error de columna duplicada). El índice de la
        columna se crea AQUÍ (y no en el DDL) porque en una base legacy la
        columna aún no existe cuando ``executescript`` corre.
        """
        try:
            self.conn.execute(
                "ALTER TABLE pipeline_comercial ADD COLUMN candidato_id TEXT")
        except Exception:
            pass
        try:
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pipeline_candidato "
                "ON pipeline_comercial (candidato_id)")
            self.conn.commit()
        except Exception:  # pragma: no cover - defensivo, nunca tumba el arranque
            pass

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

    def reconectar(self) -> None:
        """Cierra la conexión actual (si sigue viva) y abre una nueva.

        Para recuperarse de una red inestable (p. ej. datos móviles en Termux)
        que tumba el socket a media ejecución de un batch largo: la conexión en
        sí es lo que murió, no hay nada que reparar en la sesión SQL. Reusa el
        DSN original.
        """
        try:
            self.conn.close()
        except Exception:
            pass
        if self.dialect == "postgres":
            self._connect_postgres(self._dsn)
        else:
            self._connect_sqlite(self._dsn)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


_db_singleton: Database | None = None
_schema_ready: bool = False


def get_db() -> Database:
    """Instancia compartida con reconexión (segura en serverless).

    En Vercel el proceso se reutiliza entre invocaciones y la conexión a Postgres
    puede cerrarse por inactividad (Neon cierra conexiones ociosas). Antes de
    reutilizar la conexión se hace un ping; si falló, se reconecta. El esquema se
    aplica una sola vez por proceso (es idempotente de todos modos).
    """
    global _db_singleton, _schema_ready
    if _db_singleton is not None:
        try:
            _db_singleton.fetch_one("SELECT 1")
            return _db_singleton
        except Exception:
            try:
                _db_singleton.close()
            except Exception:
                pass
            _db_singleton = None
    _db_singleton = Database()
    if not _schema_ready:
        _db_singleton.init_schema()
        # Directorio semilla: asegura organizaciones reales de LATAM en
        # `prospectos` para que Motor A entregue datos desde el primer arranque
        # (sin ingesta ni credenciales). Idempotente (ON CONFLICT), se ejecuta
        # SIEMPRE —no sólo con la tabla vacía— para poblar también una base
        # persistente que ya tuviera filas. Sin red; nunca tumba el arranque.
        # Ver `hd_scraper/seed_prospectos.py`.
        try:
            from ..seed_prospectos import asegurar_directorio_semilla
            asegurar_directorio_semilla(_db_singleton)
        except Exception:  # pragma: no cover - la siembra jamás bloquea la API
            pass
        _schema_ready = True
    return _db_singleton
