"""Capa de persistencia offline-first del flujo de investigación antropológica.

Tablas locales (SQLite) que sobreviven al cierre de la aplicación. Toda la
información del ciclo de investigación vive aquí, nunca en el estado del
WebView/HTML: así la app puede cerrarse y recuperar la investigación.

Reutiliza el ``Database`` existente (mismo wrapper SQLite/Postgres) para no
crear una base paralela.
"""
from __future__ import annotations

from typing import Iterable

from .db.database import Database
from .db.models import ahora_iso

# --- Estados de curaduría (mínimos obligatorios) -------------------------
ESTADO_SENAL = "SEÑAL"          # recién capturada, aún no curada
ESTADO_EVIDENCIA = "EVIDENCIA"  # aceptada por el investigador
ESTADO_DESCARTADA = "DESCARTADA"  # rechazada

ESTADOS_CURADURIA = frozenset({ESTADO_SENAL, ESTADO_EVIDENCIA, ESTADO_DESCARTADA})

# --- Tipos de relación ------------------------------------------------
REL_REFUERZA = "REFUERZA"
REL_CONTRADICE = "CONTRADICE"
REL_MATIZA = "MATIZA"
TIPOS_RELACION = frozenset({REL_REFUERZA, REL_CONTRADICE, REL_MATIZA})

# --- Origen de inferencia ---------------------------------------------
ORIGEN_DETERMINISTA = "determinista"
ORIGEN_IA = "ia"  # toda inferencia de IA queda marcada como INFERENCIA IA


def init_investigacion_schema(db: Database) -> None:
    """Crea las tablas del flujo de investigación (idempotente)."""
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS investigaciones (
            id              TEXT PRIMARY KEY,
            foco            TEXT NOT NULL,
            pregunta        TEXT NOT NULL,
            estado          TEXT NOT NULL DEFAULT 'abierta',
            creado_en       TEXT NOT NULL,
            actualizado_en  TEXT NOT NULL,
            cerrada_en      TEXT
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS senales (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            inv_id            TEXT NOT NULL,
            organizacion      TEXT NOT NULL,
            titulo            TEXT NOT NULL,
            fuente            TEXT NOT NULL,
            url               TEXT NOT NULL,
            fecha_publicacion TEXT,
            fecha_captura     TEXT NOT NULL,
            texto             TEXT NOT NULL DEFAULT '',
            tipo_fuente       TEXT NOT NULL,
            hash              TEXT NOT NULL UNIQUE,
            id_interno        TEXT NOT NULL,
            estado_curaduria  TEXT NOT NULL DEFAULT 'SEÑAL',
            nota              TEXT,
            decisor           TEXT,
            decision_en       TEXT,
            FOREIGN KEY (inv_id) REFERENCES investigaciones(id)
        )
        """
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_senales_inv ON senales (inv_id)"
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS relaciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            inv_id      TEXT NOT NULL,
            evidencia_a INTEGER NOT NULL,
            evidencia_b INTEGER NOT NULL,
            tipo        TEXT NOT NULL,
            nota        TEXT,
            creado_en   TEXT NOT NULL,
            FOREIGN KEY (inv_id) REFERENCES investigaciones(id)
        )
        """
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_rel_inv ON relaciones (inv_id)"
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS tensiones (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            inv_id       TEXT NOT NULL,
            evidencia_a  INTEGER NOT NULL,
            evidencia_b  INTEGER NOT NULL,
            explicacion  TEXT NOT NULL,
            estado       TEXT NOT NULL DEFAULT 'abierta',
            decisor      TEXT,
            creado_en    TEXT NOT NULL,
            FOREIGN KEY (inv_id) REFERENCES investigaciones(id)
        )
        """
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_tension_inv ON tensiones (inv_id)"
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS hipotesis (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            inv_id         TEXT NOT NULL,
            texto          TEXT NOT NULL,
            origen         TEXT NOT NULL,
            estado         TEXT NOT NULL DEFAULT 'preliminar',
            evidencias_ids TEXT NOT NULL DEFAULT '[]',
            creado_en      TEXT NOT NULL,
            FOREIGN KEY (inv_id) REFERENCES investigaciones(id)
        )
        """
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_hip_inv ON hipotesis (inv_id)"
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS decisiones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            inv_id      TEXT NOT NULL,
            senal_id    INTEGER,
            accion      TEXT NOT NULL,
            autor       TEXT NOT NULL,
            detalle     TEXT,
            fecha       TEXT NOT NULL,
            FOREIGN KEY (inv_id) REFERENCES investigaciones(id)
        )
        """
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_dec_inv ON decisiones (inv_id)"
    )


def _row_to_dict(row) -> dict:
    if row is None:
        return {}
    return {k: row[k] for k in row.keys()}


# --- Investigaciones ---------------------------------------------------
def crear_investigacion(db: Database, inv_id: str, foco: str, pregunta: str) -> None:
    ahora = ahora_iso()
    db.execute(
        """INSERT INTO investigaciones (id, foco, pregunta, estado, creado_en, actualizado_en)
           VALUES (?, ?, ?, 'abierta', ?, ?)""",
        (inv_id, foco, pregunta, ahora, ahora),
    )


def actualizar_investigacion(db: Database, inv_id: str, **campos) -> None:
    permitidos = {"foco", "pregunta", "estado", "cerrada_en"}
    cols = [c for c in campos if c in permitidos and campos[c] is not None]
    if not cols:
        return
    sets = ", ".join(f"{c} = ?" for c in cols) + ", actualizado_en = ?"
    vals = [campos[c] for c in cols] + [ahora_iso()]
    db.execute(f"UPDATE investigaciones SET {sets} WHERE id = ?", (*vals, inv_id))


def obtener_investigacion(db: Database, inv_id: str) -> dict | None:
    row = db.fetch_one("SELECT * FROM investigaciones WHERE id = ?", (inv_id,))
    return _row_to_dict(row) or None


def listar_investigaciones(db: Database) -> list[dict]:
    rows = db.fetch_all(
        "SELECT * FROM investigaciones ORDER BY actualizado_en DESC"
    )
    return [_row_to_dict(r) for r in rows]


# --- Señales / evidencias ---------------------------------------------
def insertar_senal(db: Database, inv_id: str, senal: dict) -> int:
    """Inserta una señal. El hash es UNIQUE: si ya existe, lanza IntegrityError."""
    cur = db.execute(
        """
        INSERT INTO senales (
            inv_id, organizacion, titulo, fuente, url, fecha_publicacion,
            fecha_captura, texto, tipo_fuente, hash, id_interno,
            estado_curaduria, nota, decisor, decision_en
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SEÑAL', NULL, NULL, NULL)
        """,
        (
            inv_id, senal["organizacion"], senal["titulo"], senal["fuente"],
            senal["url"], senal.get("fecha_publicacion"),
            senal["fecha_captura"], senal.get("texto", ""), senal["tipo_fuente"],
            senal["hash"], senal["id_interno"],
        ),
    )
    return cur.lastrowid


def senal_existe(db: Database, inv_id: str, hash_: str) -> bool:
    row = db.fetch_one(
        "SELECT 1 AS x FROM senales WHERE inv_id = ? AND hash = ?",
        (inv_id, hash_),
    )
    return row is not None


def senal_existe_por_contenido(db: Database, inv_id: str, contenido: str) -> bool:
    """Dedup por hash de contenido (título) aunque la URL difiera."""
    row = db.fetch_one(
        "SELECT 1 AS x FROM senales WHERE inv_id = ? AND hash LIKE ?",
        (inv_id, f"%{contenido}"),
    )
    return row is not None


def obtener_senal(db: Database, senal_id: int) -> dict | None:
    row = db.fetch_one("SELECT * FROM senales WHERE id = ?", (senal_id,))
    return _row_to_dict(row) or None


def listar_senales(db: Database, inv_id: str, estado: str | None = None) -> list[dict]:
    if estado:
        rows = db.fetch_all(
            "SELECT * FROM senales WHERE inv_id = ? AND estado_curaduria = ? ORDER BY id",
            (inv_id, estado),
        )
    else:
        rows = db.fetch_all("SELECT * FROM senales WHERE inv_id = ? ORDER BY id", (inv_id,))
    return [_row_to_dict(r) for r in rows]


def curar_senal(
    db: Database, senal_id: int, estado: str, nota: str | None = None,
    autor: str = "investigador",
) -> None:
    db.execute(
        """UPDATE senales
           SET estado_curaduria = ?, nota = COALESCE(?, nota),
               decisor = ?, decision_en = ?
           WHERE id = ?""",
        (estado, nota, autor, ahora_iso(), senal_id),
    )


def registrar_decision(
    db: Database, inv_id: str, accion: str, autor: str,
    senal_id: int | None = None, detalle: str | None = None,
) -> None:
    db.execute(
        """INSERT INTO decisiones (inv_id, senal_id, accion, autor, detalle, fecha)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (inv_id, senal_id, accion, autor, detalle, ahora_iso()),
    )


# --- Relaciones --------------------------------------------------------
def insertar_relacion(
    db: Database, inv_id: str, a: int, b: int, tipo: str, nota: str | None = None,
) -> int:
    cur = db.execute(
        """INSERT INTO relaciones (inv_id, evidencia_a, evidencia_b, tipo, nota, creado_en)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (inv_id, a, b, tipo, nota, ahora_iso()),
    )
    return cur.lastrowid


def listar_relaciones(db: Database, inv_id: str) -> list[dict]:
    rows = db.fetch_all("SELECT * FROM relaciones WHERE inv_id = ? ORDER BY id", (inv_id,))
    return [_row_to_dict(r) for r in rows]


# --- Tensiones ---------------------------------------------------------
def insertar_tension(
    db: Database, inv_id: str, a: int, b: int, explicacion: str,
    estado: str = "abierta", decisor: str | None = None,
) -> int:
    cur = db.execute(
        """INSERT INTO tensiones (inv_id, evidencia_a, evidencia_b, explicacion, estado, decisor, creado_en)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (inv_id, a, b, explicacion, estado, decisor, ahora_iso()),
    )
    return cur.lastrowid


def listar_tensiones(db: Database, inv_id: str) -> list[dict]:
    rows = db.fetch_all("SELECT * FROM tensiones WHERE inv_id = ? ORDER BY id", (inv_id,))
    return [_row_to_dict(r) for r in rows]


# --- Hipótesis ---------------------------------------------------------
def insertar_hipotesis(db: Database, inv_id: str, texto: str, origen: str,
                     evidencias_ids: list[int], estado: str = "preliminar") -> int:
    cur = db.execute(
        """INSERT INTO hipotesis (inv_id, texto, origen, estado, evidencias_ids, creado_en)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (inv_id, texto, origen, estado, _json(evidencias_ids), ahora_iso()),
    )
    return cur.lastrowid


def listar_hipotesis(db: Database, inv_id: str) -> list[dict]:
    rows = db.fetch_all("SELECT * FROM hipotesis WHERE inv_id = ? ORDER BY id", (inv_id,))
    out = []
    for r in rows:
        d = _row_to_dict(r)
        d["evidencias_ids"] = _unjson(d.get("evidencias_ids", "[]"))
        out.append(d)
    return out


def _json(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


def _unjson(s: str):
    import json
    try:
        return json.loads(s)
    except Exception:
        return []


def contar_estado(db: Database, inv_id: str, estado: str) -> int:
    row = db.fetch_one(
        "SELECT COUNT(*) AS n FROM senales WHERE inv_id = ? AND estado_curaduria = ?",
        (inv_id, estado),
    )
    return row["n"] if row else 0
