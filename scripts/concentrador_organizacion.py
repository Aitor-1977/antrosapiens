#!/usr/bin/env python3
"""Concentra la evidencia de una organización y muestra su densidad (Entrega 4).

Solo lectura: no escribe nada, no promueve nada. Muestra, para la organización
pedida, todas sus evidencias clasificadas (con su fuente y su peso
epistemológico) y la métrica de densidad aritmética.

Uso:
    python -m scripts.concentrador_organizacion "Nubank"
    python -m scripts.concentrador_organizacion "Nubank" --json
    python -m scripts.concentrador_organizacion --sin-organizacion   # lista la
        evidencia conservada que aún no tiene organización identificada
"""
from __future__ import annotations

import argparse
import json

from hd_scraper.concentrador import (
    densidad_evidencial,
    evidencia_sin_organizacion,
    evidencias_de_organizacion,
)
from hd_scraper.db.database import get_db


def _informe_org(concentrado: dict | None, densidad: dict) -> str:
    if concentrado is None:
        return (
            f"organización '{densidad['organizacion']}': sin expediente "
            "(no identificada). Su evidencia, si la hay, se lista con "
            "--sin-organizacion."
        )
    lineas = [
        f"organización: {concentrado['organizacion']}",
        f"expediente: {concentrado['expediente_id']} (estado={concentrado['estado']})",
        f"evidencias: {concentrado['total_evidencias']}",
        "",
        "densidad evidencial (recuento, no veredicto):",
        f"  evidencias .............. {densidad['n_evidencias']}",
        f"  fuentes independientes .. {densidad['n_fuentes_independientes']}",
        f"  señales primarias ....... {densidad['n_senales_primarias']}",
        f"  corroborantes ........... {densidad['n_corroborantes']}",
        f"  contextuales ............ {densidad['n_contextuales']}",
        f"  persistencia (días) ..... {densidad['persistencia_dias']}",
        "",
        "evidencia:",
    ]
    for e in concentrado["evidencias"]:
        lineas.append(
            f"  [{e['evidencia_id']}] {e['fuente'] or '—'} · "
            f"{e['tipo_epistemologico']} · {e['fecha_publicacion'] or 'no_fechado'}"
        )
        lineas.append(f"      {(e['cita_textual'] or '').strip()}")
        lineas.append(f"      {e['url_fuente']}")
    return "\n".join(lineas)


def _informe_sin_org(filas: list[dict]) -> str:
    if not filas:
        return "no hay evidencia sin organización identificada."
    lineas = [f"evidencia conservada sin organización identificada: {len(filas)}", ""]
    for e in filas:
        lineas.append(
            f"  [{e['evidencia_id']}] {e['fuente'] or '—'} · "
            f"empresa_mencionada='{e['empresa_mencionada']}' · "
            f"{e['fecha_publicacion'] or 'no_fechado'}"
        )
        lineas.append(f"      {(e['cita_textual'] or '').strip()}")
    return "\n".join(lineas)


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("organizacion", nargs="?", help="nombre de la organización")
    p.add_argument("--sin-organizacion", action="store_true",
                   help="lista la evidencia conservada sin organización identificada")
    p.add_argument("--limite", type=int, help="máximo de filas con --sin-organizacion")
    p.add_argument("--json", action="store_true", help="salida en JSON")
    args = p.parse_args()

    db = get_db()

    if args.sin_organizacion:
        filas = evidencia_sin_organizacion(db, limite=args.limite)
        print(json.dumps(filas, ensure_ascii=False, indent=2) if args.json
              else _informe_sin_org(filas))
        return

    if not args.organizacion:
        p.error("indica una organización o usa --sin-organizacion")

    concentrado = evidencias_de_organizacion(db, args.organizacion)
    densidad = densidad_evidencial(db, args.organizacion)
    if args.json:
        print(json.dumps({"concentrado": concentrado, "densidad": densidad},
                         ensure_ascii=False, indent=2))
    else:
        print(_informe_org(concentrado, densidad))


if __name__ == "__main__":
    main()
