#!/usr/bin/env python3
"""Clasifica epistemológicamente la evidencia ya capturada (modo batch).

Por defecto NO escribe: imprime la distribución y una muestra razonada del lote
pendiente. Solo con ``--aplicar`` inserta en `evidencia_clasificada` y crea los
`expedientes_candidatos` que falten (siempre en estado 'abierto').

Uso:
    python -m scripts.clasificar_evidencia                      # dry-run completo
    python -m scripts.clasificar_evidencia --limite 50          # dry-run acotado
    python -m scripts.clasificar_evidencia --org "Nubank"
    python -m scripts.clasificar_evidencia --aplicar

Reejecutarlo es seguro: el lote excluye lo ya clasificado y cada escritura
reverifica antes de insertar.
"""
from __future__ import annotations

import argparse
import json

from hd_scraper.clasificacion_store import clasificar_lote
from hd_scraper.db.database import get_db


def _informe(rep: dict) -> str:
    lineas = [
        f"reglas: {rep['version_reglas']}",
        f"modo:   {'APLICADO (escribe)' if rep['aplicado'] else 'dry-run (no escribe)'}",
        f"lote pendiente: {rep['pendientes']}",
        "",
        "distribución:",
    ]
    total = max(rep["procesadas"], 1)
    for tipo, n in sorted(rep["distribucion"].items(), key=lambda kv: -kv[1]):
        lineas.append(f"  {tipo:<32} {n:>6}  ({100 * n / total:.1f} %)")
    lineas += [
        "",
        f"clasificaciones escritas: {rep['escritas']}",
        f"expedientes creados:      {rep['expedientes_creados']}"
        + ("" if rep["aplicado"] else "  (proyección)"),
    ]
    if rep.get("saltadas"):
        lineas.append(f"saltadas (fallo de conexión persistente): {rep['saltadas']}"
                      "  — re-correr el mismo comando las recoge")
    if rep["muestra"]:
        lineas += ["", "muestra:"]
        for m in rep["muestra"]:
            lineas.append(f"  [{m['evidencia_id']}] {m['organizacion']} -> "
                          f"{m['tipo_epistemologico']}")
            lineas.append(f"      cita:  {m['cita_textual']}")
            lineas.append(f"      razón: {m['razon']}")
    return "\n".join(lineas)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--aplicar", action="store_true",
                   help="escribe en la base (sin esta bandera es dry-run)")
    p.add_argument("--desde", help="fecha ISO mínima de CAPTURA (evidencias.creado_en)")
    p.add_argument("--org", help="acota a una organización (empresa_mencionada)")
    p.add_argument("--limite", type=int, help="máximo de evidencias a procesar")
    p.add_argument("--solo-ok", action="store_true",
                   help="omite las evidencias en estado no_fechado")
    p.add_argument("--muestra", type=int, default=10,
                   help="cuántos ejemplos razonados imprimir (por defecto 10)")
    p.add_argument("--json", action="store_true", help="salida en JSON")
    args = p.parse_args()

    db = get_db()
    rep = clasificar_lote(db, desde=args.desde, org=args.org, limite=args.limite,
                          solo_ok=args.solo_ok, aplicar=args.aplicar,
                          muestra=args.muestra)
    print(json.dumps(rep, ensure_ascii=False, indent=2) if args.json
          else _informe(rep))


if __name__ == "__main__":
    main()
