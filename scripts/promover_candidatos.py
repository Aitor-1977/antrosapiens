#!/usr/bin/env python3
"""Promueve expedientes 'abierto' a 'candidato' (Entrega 3, modo batch).

Por defecto NO escribe: imprime, para cada expediente 'abierto', si
promovería o no y por qué. Solo con ``--aplicar`` ejecuta el UPDATE.

Uso:
    python -m scripts.promover_candidatos                # dry-run completo
    python -m scripts.promover_candidatos --org "Nubank"
    python -m scripts.promover_candidatos --aplicar

Reejecutarlo es seguro: el UPDATE lleva WHERE estado='abierto', así que un
expediente ya promovido no se vuelve a escribir.
"""
from __future__ import annotations

import argparse
import json

from hd_scraper.db.database import get_db
from hd_scraper.promocion_store import promover_lote


def _informe(rep: dict) -> str:
    lineas = [
        f"modo: {'APLICADO (escribe)' if rep['aplicado'] else 'dry-run (no escribe)'}",
        f"expedientes 'abierto' evaluados: {rep['evaluados']}",
        f"promovidos: {rep['promovidos']}"
        + ("" if rep["aplicado"] else "  (proyección)"),
        "",
        "detalle:",
    ]
    for d in rep["detalle"]:
        marca = "PROMUEVE" if d["promovido"] else "queda abierto"
        lineas.append(
            f"  [{d['expediente_id']}] {d['organizacion']} "
            f"(categoria={d['categoria'] or '—'}) -> {marca}")
        lineas.append(f"      tipos: {d['tipos_encontrados'] or '(ninguno)'}")
        lineas.append(f"      razón: {d['razon']}")
    return "\n".join(lineas)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--aplicar", action="store_true",
                   help="escribe el cambio de estado (sin esta bandera es dry-run)")
    p.add_argument("--org", help="acota a una organización (organizacion)")
    p.add_argument("--limite", type=int, help="máximo de expedientes a evaluar")
    p.add_argument("--json", action="store_true", help="salida en JSON")
    args = p.parse_args()

    db = get_db()
    rep = promover_lote(db, org=args.org, limite=args.limite, aplicar=args.aplicar)
    print(json.dumps(rep, ensure_ascii=False, indent=2) if args.json
          else _informe(rep))


if __name__ == "__main__":
    main()
