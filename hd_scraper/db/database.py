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
import threading
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
        # Lock usado SOLO para SQLite (self.conn persistente, una única
        # conexión). Postgres usa un pool (ver _connect_postgres): cada hilo
        # toma su propia conexión física, así que no comparte estado que haya
        # que serializar con un candado propio (el pool ya es thread-safe).
        #
        # Historia (2026-09-11): la causa raíz real del timeout intermitente
        # en producción no fue Neon ni vercel.json (ambos se investigaron y
        # corrigieron primero) sino que los endpoints de app.py son `def`
        # síncronos — Starlette los corre en hilos del threadpool — y TODOS
        # compartían una única conexión psycopg sin candado. psycopg no es
        # seguro para uso concurrente de la misma conexión desde varios
        # hilos: dos `execute()` simultáneos entrelazaban el protocolo de
        # wire y la dejaban en un estado del que nunca volvía a responder
        # (200/503/504 mezclados en la misma ráfaga). Un Lock por instancia
        # arregló la corrupción, pero como _construir_expedientes hace varios
        # round-trips secuenciales por petición, serializar TODO detrás de un
        # único candado bajo 4+ peticiones concurrentes empujaba el tiempo
        # total más allá del maxDuration de 60s. Un pool de conexiones reales
        # (varias conexiones físicas, una por hilo concurrente) resuelve
        # ambos problemas a la vez: sin compartir conexión, no hay
        # entrelazado de protocolo que temer, y varias peticiones progresan
        # en paralelo de verdad en vez de hacer cola una detrás de otra.
        self._lock = threading.Lock()

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
        import time

        import psycopg
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool, PoolTimeout

        # psycopg acepta el prefijo postgres:// directamente. Neon/Vercel ya
        # incluyen sslmode=require en la cadena.
        #
        # Neon (plan serverless) suspende el cómputo tras inactividad; la
        # PRIMERA conexión tras la suspensión reactiva la base y puede tardar
        # bastante más que una conexión normal (evidencia real, 2026-09-10:
        # /health y /expedientes sin respuesta 55s+ tras un rato sin tráfico).
        #
        # Pool de conexiones (2026-09-11, reemplaza una única self.conn
        # compartida): los endpoints de app.py son `def` síncronos — Starlette
        # los corre en hilos concurrentes del threadpool —, así que varias
        # peticiones concurrentes necesitan cada una su propia conexión física,
        # no turnarse una sola tras otra. `min_size=1` mantiene una conexión
        # lista sin esperar cold-start en el caso común; `max_size=5` acota
        # cuántas conexiones físicas abre esta instancia cálida (la cadena
        # pooled de Neon, ver `config._resolve_database_url`, multiplexa esto
        # más arriba con PgBouncer, así que 5 no agota el límite real de
        # Postgres). `autocommit=True`: cada `execute()` es su propia
        # transacción — necesario porque el pool puede entregar la MISMA
        # conexión física a peticiones distintas en momentos distintos, y
        # dejar una transacción a medias abierta entre préstamos sería
        # incorrecto. `check=ConnectionPool.check_connection` valida la
        # conexión al prestarla (Neon cierra conexiones ociosas).
        self._pool = ConnectionPool(
            dsn,
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row, "autocommit": True, "connect_timeout": 10},
            open=False,
            timeout=20,
            check=ConnectionPool.check_connection,
        )
        # Abre con un reintento corto: cubre el mismo cold-start de Neon que
        # antes cubría el reintento de conexión directa, ahora aplicado a
        # poblar el pool. Presupuesto total (10s + 1s + 20s = 31s) deja
        # margen real dentro de los 60s de maxDuration configurados en
        # vercel.json para el resto del request.
        ultimo_error: Exception | None = None
        for intento, espera in enumerate((0, 1)):
            if espera:
                time.sleep(espera)
            try:
                self._pool.open(wait=True, timeout=10 if intento == 0 else 20)
                return
            except PoolTimeout as exc:
                ultimo_error = exc
        raise ultimo_error

    # -- Traducción de marcadores --------------------------------------
    def _q(self, sql: str) -> str:
        # El SQL de la app no contiene '?' literales ni '%' literales, así que la
        # sustitución es segura para el paramstyle de psycopg.
        return sql if self.dialect == "sqlite" else sql.replace("?", "%s")

    # -- Inicialización -------------------------------------------------
    def init_schema(self) -> None:
        if self.dialect == "sqlite":
            self.conn.executescript(SCHEMA_SQLITE.read_text(encoding="utf-8"))
            self._migrar_pipeline_candidato()
            self._migrar_organizacion_mencionada()
            self._migrar_expediente_id_nullable()
            self._migrar_resumen_fuente()
            self._migrar_pais_prospecto()
            self.conn.commit()
            return
        # Postgres: se corre una sola vez por proceso, dentro del lock del
        # singleton en get_db() (antes de compartir el objeto con peticiones
        # concurrentes), así que basta con UNA conexión prestada del pool. Los
        # métodos `_migrar_*` siguen escritos contra `self.conn` tal cual
        # (no se tocan, ya están bien probados); se les presta la conexión
        # temporalmente en ese atributo mientras dura la inicialización.
        with self._pool.connection() as conn:
            self.conn = conn
            try:
                # psycopg admite múltiples sentencias en un execute sin parámetros.
                conn.execute(SCHEMA_POSTGRES.read_text(encoding="utf-8"))
                self._migrar_pipeline_candidato()
                self._migrar_organizacion_mencionada()
                self._migrar_expediente_id_nullable()
                self._migrar_resumen_fuente()
                self._migrar_pais_prospecto()
            finally:
                del self.conn

    def _migrar_pais_prospecto(self) -> None:
        """Migración idempotente: añade ``prospectos.pais`` a bases persistentes
        previas a esta ampliación (FASE territorial). ``CREATE TABLE IF NOT
        EXISTS`` no altera una tabla ya existente (protocolo Capa 0, CLAUDE.md);
        el ALTER es un no-op cuando la columna ya existe. No borra datos: solo
        agrega la columna, con NULL para las filas ya sembradas hasta que
        ``asegurar_directorio_semilla`` (o una captura futura) la rellene.
        """
        try:
            self.conn.execute("ALTER TABLE prospectos ADD COLUMN pais TEXT")
        except Exception:
            pass

    def _migrar_resumen_fuente(self) -> None:
        """Migración idempotente (auditoría 2026-09-10, autorización P0):
        añade ``evidencias.resumen_fuente`` a bases persistentes previas a
        esta corrección. ``CREATE TABLE IF NOT EXISTS`` no altera una tabla
        ya existente (ver protocolo Capa 0 en CLAUDE.md); el ALTER es un
        no-op cuando la columna ya existe.
        """
        try:
            self.conn.execute("ALTER TABLE evidencias ADD COLUMN resumen_fuente TEXT")
        except Exception:
            pass

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
    # SQLite: self._lock serializa el acceso a self.conn (única conexión).
    # Postgres: cada llamada toma su propia conexión física del pool — sin
    # candado propio, el pool ya resuelve la concurrencia entre hilos (ver
    # comentario en __init__).
    def execute(self, sql: str, params: Iterable[Any] = ()):
        if self.dialect == "postgres":
            with self._pool.connection() as conn:
                return conn.execute(self._q(sql), tuple(params))
        with self._lock:
            cur = self.conn.execute(self._q(sql), tuple(params))
            self.conn.commit()
            return cur

    def fetch_one(self, sql: str, params: Iterable[Any] = ()) -> Optional[Any]:
        if self.dialect == "postgres":
            with self._pool.connection() as conn:
                return conn.execute(self._q(sql), tuple(params)).fetchone()
        with self._lock:
            return self.conn.execute(self._q(sql), tuple(params)).fetchone()

    def fetch_all(self, sql: str, params: Iterable[Any] = ()) -> list[Any]:
        if self.dialect == "postgres":
            with self._pool.connection() as conn:
                return conn.execute(self._q(sql), tuple(params)).fetchall()
        with self._lock:
            return self.conn.execute(self._q(sql), tuple(params)).fetchall()

    def insert_returning_id(self, sql: str, params: Iterable[Any] = ()) -> int:
        """INSERT que devuelve el id generado, portable entre motores."""
        if self.dialect == "postgres":
            with self._pool.connection() as conn:
                cur = conn.execute(self._q(sql) + " RETURNING id", tuple(params))
                return cur.fetchone()["id"]
        with self._lock:
            cur = self.conn.execute(sql, tuple(params))
            self.conn.commit()
            return cur.lastrowid

    def reconectar(self) -> None:
        """Cierra la conexión/pool actual (si sigue vivo) y abre uno nuevo.

        Para recuperarse de una red inestable (p. ej. datos móviles en Termux)
        que tumba el socket a media ejecución de un batch largo: la conexión en
        sí es lo que murió, no hay nada que reparar en la sesión SQL. Reusa el
        DSN original.
        """
        with self._lock:
            if self.dialect == "postgres":
                try:
                    self._pool.close()
                except Exception:
                    pass
                self._connect_postgres(self._dsn)
                return
            try:
                self.conn.close()
            except Exception:
                pass
            self._connect_sqlite(self._dsn)

    def close(self) -> None:
        with self._lock:
            if self.dialect == "postgres":
                self._pool.close()
            else:
                self.conn.close()

    def rollback_seguro(self) -> None:
        """Deshace una transacción fallida, cuando aplica.

        En Postgres las conexiones del pool usan ``autocommit=True`` (cada
        `execute()` es su propia transacción independiente — necesario porque
        el pool puede prestar la misma conexión física a peticiones
        distintas), así que un INSERT fallido nunca deja la conexión en
        estado "transaction aborted": no hay nada que revertir. En SQLite
        (``self.conn`` persistente, sin autocommit) sí puede quedar una
        transacción implícita abierta tras un error; se revierte para poder
        seguir usando la conexión (ver `hd_scraper/seed_prospectos.py`).
        """
        if self.dialect != "sqlite":
            return
        with self._lock:
            try:
                self.conn.rollback()
            except Exception:
                pass

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


_db_singleton: Database | None = None
_schema_ready: bool = False
# Serializa la creación/reemplazo del singleton entre hilos (ver el Lock por
# instancia en Database.__init__): sin esto, dos hilos podrían ver
# `_db_singleton is not None` a la vez, uno cerrarlo tras un ping fallido
# mientras el otro sigue usando la conexión ya cerrada.
_singleton_lock = threading.Lock()


def get_db() -> Database:
    """Instancia compartida con reconexión (segura en serverless).

    En Vercel el proceso se reutiliza entre invocaciones y la conexión a Postgres
    puede cerrarse por inactividad (Neon cierra conexiones ociosas). Antes de
    reutilizar la conexión se hace un ping; si falló, se reconecta. El esquema se
    aplica una sola vez por proceso (es idempotente de todos modos).
    """
    global _db_singleton, _schema_ready
    with _singleton_lock:
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
            # `prospectos` para que Motor A entregue datos desde el primer
            # arranque (sin ingesta ni credenciales). Idempotente (ON
            # CONFLICT), se ejecuta SIEMPRE —no sólo con la tabla vacía— para
            # poblar también una base persistente que ya tuviera filas. Sin
            # red; nunca tumba el arranque. Ver `hd_scraper/seed_prospectos.py`.
            try:
                from ..seed_prospectos import asegurar_directorio_semilla
                asegurar_directorio_semilla(_db_singleton)
            except Exception:  # pragma: no cover - la siembra jamás bloquea la API
                pass
            _schema_ready = True
        return _db_singleton
