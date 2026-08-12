#!/usr/bin/env python3
"""Cadena de trazabilidad de organizaciones aleatorias (SOLO LECTURA, sin COMMIT).

Toma ``--cantidad`` (por defecto 3) organizaciones aleatorias de la base de
datos (producción/staging según ``HD_DATABASE_URL`` / ``DATABASE_URL`` /
``POSTGRES_URL``) e imprime para cada una la cadena de trazabilidad exacta:

    Nombre de Organización -> ID Estable -> ID Prospecto -> ID Expediente

La cadena vive en la tabla ``candidatos`` (reparación BC-I ↔ BC-II):

    org_nombre      -> nombre de la organización observada (BC-I)
    candidato_id    -> ID estable por organización/candidato (sha256 determinista)
    prospecto_id    -> ID del prospecto (BC-II), FK a ``prospectos.id``
    expediente_hash -> huella/identidad del expediente (BC-I)

Solo lectura:
    Usa ``Database()`` únicamente con ``fetch_one`` / ``fetch_all``. NUNCA llama
    a ``init_schema()`` (que ejecuta DDL + COMMIT y siembra el directorio) ni a
    ``execute`` / ``insert_*``. La cadena exacta es la que ya está persistida.

Fallos explícitos (código de salida 1):
    * Dos organizaciones DISTINTAS comparten el mismo ID de expediente
      (integridad de trazabilidad comprometida). El chequeo se hace sobre TODA
      la tabla ``candidatos``, no solo sobre la muestra.
    * La tabla ``candidatos`` está vacía o no existe (no se materializa nada:
      la materialización la hace la ingesta/API, no un script de lectura).

Uso:
    python -m scripts.trazabilidad                   # 3 orgs, muestreo aleatorio
    python -m scripts.trazabilidad --cantidad 5
    python -m scripts.trazabilidad --seed 7          # muestreo reproducible
"""
from __future__ import annotations

import argparse
import random
import sys
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

from hd_scraper.db.database import Database

HEADER = "Nombre de Organización -> ID Estable -> ID Prospecto -> ID Expediente"


def _dsn_desc(dsn: str) -> str:
    """DSN legible sin credenciales (nunca imprime el password)."""
    if dsn.startswith(("postgres://", "postgresql://")):
        partes = urlsplit(dsn)
        netloc = partes.hostname or ""
        if partes.port:
            netloc = f"{netloc}:{partes.port}"
        return urlunsplit((partes.scheme, netloc, partes.path, "", ""))
    if dsn.startswith("sqlite:///"):
        return f"sqlite:///{dsn[len('sqlite:///'):]}"
    return dsn


def _leer_candidatos(db: Database) -> list[dict]:
    """Lee SOLO la cadena persistida en ``candidatos`` (fetch, sin escritura)."""
    try:
        filas = db.fetch_all(
            "SELECT id, candidato_id, org_nombre, prospecto_id, expediente_hash "
            "FROM candidatos ORDER BY id ASC"
        )
    except Exception as e:
        raise SystemExit(
            f"ERROR: no se pudo leer la tabla `candidatos` en la base "
            f"{_dsn_desc(settings_dsn())}: {e}")
    return [dict(f) for f in filas]


def _duplicados_expediente(candidatos: list[dict]) -> list[tuple[str, list[str]]]:
    """Organizaciones distintas que comparten el mismo ID de expediente.

    Devuelve [(expediente_hash, [org_nombre...])] para cada hash compartido por
    2+ nombres de organización distintos. Los hashes vacíos se ignoran: una
    organización sin expediente NO comparte ID (simplemente no tiene).
    """
    por_hash: dict[str, set[str]] = {}
    for c in candidatos:
        h = (c.get("expediente_hash") or "").strip()
        if not h:
            continue
        por_hash.setdefault(h, set()).add((c.get("org_nombre") or "").strip())
    return sorted(
        (h, sorted(orgs)) for h, orgs in por_hash.items() if len(orgs) > 1
    )


def _cadena(c: dict) -> str:
    nombre = (c.get("org_nombre") or "").strip()
    estable = (c.get("candidato_id") or "").strip()
    prospecto = c.get("prospecto_id")
    prospecto = prospecto if prospecto is not None else "(sin prospecto)"
    expediente = (c.get("expediente_hash") or "").strip()
    expediente = expediente or "(sin expediente)"
    return f"{nombre} -> {estable} -> {prospecto} -> {expediente}"


def _verificar_y_muestrear(db: Database, cantidad: int, rnd: random.Random) -> list[dict]:
    candidatos = _leer_candidatos(db)
    if not candidatos:
        raise SystemExit(
            "ERROR: la tabla `candidatos` está vacía en la base leída. "
            "La cadena de trazabilidad se materializa por la ingesta "
            "(`materializar_candidatos` / POST /candidatos/materializar), no por "
            "un script de lectura; corre primero esa materialización en la base "
            "objetivo (producción/staging)."
        )

    duplicados = _duplicados_expediente(candidatos)
    if duplicados:
        lineas = [
            "ERROR: dos organizaciones DISTINTAS comparten el mismo ID de expediente "
            "(integridad de trazabilidad comprometida):",
        ]
        for h, orgs in duplicados:
            lineas.append(f"  ID de expediente: {h}")
            for o in orgs:
                lineas.append(f"    -> {o}")
        lineas.append("Bloqueando la lectura de la cadena.")
        raise SystemExit("\n".join(lineas))

    if cantidad > len(candidatos):
        print(f"[aviso] --cantidad={cantidad} > {len(candidatos)} "
              f"candidatos disponibles; se muestrean {len(candidatos)}.")
        cantidad = len(candidatos)
    return rnd.sample(candidatos, cantidad)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Cadena de trazabilidad exacta de organizaciones aleatorias "
                    "(solo lectura, sin COMMIT).")
    ap.add_argument("--cantidad", type=int, default=3,
                    help="número de organizaciones a muestrear (por defecto 3)")
    ap.add_argument("--seed", type=int, default=0,
                    help="semilla del muestreo aleatorio (determinista)")
    args = ap.parse_args()

    if args.cantidad < 1:
        ap.error("--cantidad debe ser >= 1")

    rnd = random.Random(args.seed)

    try:
        db = Database()
        dsn = settings_dsn()
    except Exception as e:
        raise SystemExit(
            f"ERROR: no se pudo conectar a la base de datos "
            f"({_dsn_desc(settings_dsn())}): {e}")
    try:
        muestra = _verificar_y_muestrear(db, args.cantidad, rnd)
    finally:
        db.close()

    print("=" * 72)
    print("CADENA DE TRAZABILIDAD — solo lectura, sin COMMIT")
    print(f"Base: {_dsn_desc(dsn)}   seed={args.seed}   muestra={len(muestra)}")
    print("=" * 72)
    print(HEADER)
    for c in muestra:
        print(_cadena(c))
    print("=" * 72)
    print(f"OK: {len(muestra)} organizaciones trazadas, sin IDs de expediente "
          f"compartidos entre organizaciones distintas.")
    sys.exit(0)


def settings_dsn() -> str:
    """DSN resuelto por la config (para mensajes de error de conexión)."""
    from hd_scraper.config import settings
    return settings.database_url


if __name__ == "__main__":
    main()
