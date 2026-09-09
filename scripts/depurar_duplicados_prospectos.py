#!/usr/bin/env python3
"""Depura filas duplicadas de una organización en `prospectos` (mismo `nombre`,
`categoria` distinta) — el bloqueo documentado en
`hd_scraper/promocion_store.py:categoria_de_organizacion`, que impide promover
un expediente mientras exista más de una fila en `prospectos` con categorías
distintas para el mismo nombre.

Por defecto NO escribe: solo muestra, para cada organización pedida, qué filas
hay y cuál se borraría. Solo con --aplicar ejecuta el DELETE, y siempre por
`id` exacto (nunca por categoría a secas), así que no puede afectar otras
organizaciones ni filas que no correspondan.

Uso:
    python -m scripts.depurar_duplicados_prospectos --org "Konfío" --org "Clip" --mantener Corporativo
    python -m scripts.depurar_duplicados_prospectos --org "Konfío" --org "Clip" --mantener Corporativo --aplicar

Reejecutarlo es seguro: si ya no hay duplicado para una organización, esa
organización simplemente no aparece en el informe.
"""
from __future__ import annotations

import argparse

from hd_scraper.db.database import get_db
from hd_scraper.db.models import CATEGORIAS


def _filas(db, nombre: str) -> list[dict]:
    return db.fetch_all(
        "SELECT id, nombre, categoria, creado_en FROM prospectos "
        "WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?)) ORDER BY creado_en",
        (nombre,),
    )


def _informe_y_borrar(db, orgs: list[str], mantener: str, aplicar: bool) -> dict:
    detalle = []
    a_borrar: list[int] = []
    for nombre in orgs:
        filas = [dict(f) for f in _filas(db, nombre)]
        if len(filas) <= 1:
            detalle.append({"organizacion": nombre, "estado": "sin duplicado", "filas": filas})
            continue
        categorias = {f["categoria"] for f in filas}
        if len(categorias) <= 1:
            detalle.append({
                "organizacion": nombre,
                "estado": "duplicado pero misma categoría (no es el conflicto que resuelve este script)",
                "filas": filas,
            })
            continue
        conservar = [f for f in filas if f["categoria"] == mantener]
        sobran = [f for f in filas if f["categoria"] != mantener]
        if not conservar:
            detalle.append({
                "organizacion": nombre,
                "estado": f"ninguna fila tiene categoría {mantener!r}, no se borra nada",
                "filas": filas,
            })
            continue
        a_borrar += [f["id"] for f in sobran]
        detalle.append({
            "organizacion": nombre,
            "estado": "conserva 1, borra el resto" if aplicar else "conservaría 1, borraría el resto (dry-run)",
            "conserva_id": conservar[0]["id"],
            "borra_ids": [f["id"] for f in sobran],
            "filas": filas,
        })

    if aplicar and a_borrar:
        marc = ",".join("?" for _ in a_borrar)
        db.execute(f"DELETE FROM prospectos WHERE id IN ({marc})", tuple(a_borrar))

    return {"aplicado": aplicar, "ids_borrados": a_borrar, "detalle": detalle}


def _texto(rep: dict) -> str:
    lineas = [f"modo: {'APLICADO (borró filas)' if rep['aplicado'] else 'dry-run (no borró nada)'}", ""]
    for d in rep["detalle"]:
        lineas.append(f"— {d['organizacion']}: {d['estado']}")
        for f in d["filas"]:
            marca = ""
            if "conserva_id" in d and f["id"] == d["conserva_id"]:
                marca = "  <- se conserva"
            elif "borra_ids" in d and f["id"] in d["borra_ids"]:
                marca = "  <- se borra" if rep["aplicado"] else "  <- se borraría"
            lineas.append(f"    id={f['id']} categoria={f['categoria']} creado_en={f['creado_en']}{marca}")
        lineas.append("")
    if not rep["aplicado"] and rep["ids_borrados"]:
        lineas.append("Nada se borró todavía. Repite el mismo comando agregando --aplicar para confirmar.")
    return "\n".join(lineas)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--org", action="append", required=True,
                   help="nombre de la organización a depurar (repetir para varias)")
    p.add_argument("--mantener", required=True, choices=sorted(CATEGORIAS),
                   help="categoría que debe quedar (las demás filas de ese nombre se borran)")
    p.add_argument("--aplicar", action="store_true",
                   help="ejecuta el DELETE (sin esta bandera es dry-run)")
    args = p.parse_args()

    db = get_db()
    rep = _informe_y_borrar(db, args.org, args.mantener, args.aplicar)
    print(_texto(rep))


if __name__ == "__main__":
    main()
