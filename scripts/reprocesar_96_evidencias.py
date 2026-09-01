#!/usr/bin/env python3
"""Reprocesa la evidencia ya capturada de `busqueda_dinamica_founder`
(las evidencias de Tavily que nunca se persistieron mientras
`expediente_id` era `NOT NULL`), ahora que el esquema lo admite nullable.

No dispara ninguna búsqueda nueva contra Tavily: lee `evidencias` (tabla que
ya existe, ya capturada) y reutiliza `clasificacion_store.clasificar_lote`
tal cual — no reimplementa la cascada de clasificación ni la lógica de
persistencia (`expediente_id`/`organizacion_mencionada` en NULL cuando no
hay organización identificable ya se resuelve ahí). No importa ni llama a
`promocion_candidatos` en ningún punto: la promoción queda fuera de alcance
de este script a propósito, ver `siguiente_paso_optimo.md`.

Uso:
    python -m scripts.reprocesar_96_evidencias --dry-run
    python -m scripts.reprocesar_96_evidencias --host-esperado "ep-xxx-pooler.c-1.region.aws.neon.tech"

Sin `--host-esperado`, igual pide confirmación interactiva del host antes de
escribir (se omite en `--dry-run`, que no escribe nada).
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import urlparse

from hd_scraper.clasificacion_store import clasificar_lote
from hd_scraper.config import settings
from hd_scraper.db.database import get_db

_CONECTOR = "busqueda_dinamica_founder"


def _host_de(dsn: str) -> str:
    try:
        return urlparse(dsn).hostname or "(desconocido)"
    except Exception:
        return "(desconocido)"


def _confirmar(host: str, host_esperado: str | None) -> None:
    print(f"Host detectado (resuelto por hd_scraper.config.settings.database_url): {host}")
    if host_esperado and host != host_esperado:
        print(f"ABORTADO: el host detectado ({host}) no coincide con "
              f"--host-esperado ({host_esperado}). No se escribe nada.")
        sys.exit(1)
    respuesta = input(
        "¿Confirmas que este es el host de PRODUCCIÓN correcto? "
        "Escribe 'SI' (mayúsculas, sin comillas) para continuar: "
    ).strip()
    if respuesta != "SI":
        print("Cancelado: la respuesta no fue exactamente 'SI'. No se escribió nada.")
        sys.exit(1)


def _snapshot(db) -> dict:
    """Foto del estado de la evidencia del conector Tavily: totales,
    clasificadas, con/sin expediente, distribución por tipo. Se usa igual
    ANTES y DESPUÉS para poder comparar."""
    total = dict(db.fetch_one(
        "SELECT count(*) AS n FROM evidencias WHERE connector = ?",
        (_CONECTOR,)))["n"]
    clasificadas = dict(db.fetch_one(
        "SELECT count(*) AS n FROM evidencias e "
        "JOIN evidencia_clasificada ec ON ec.evidencia_id = e.id "
        "WHERE e.connector = ?", (_CONECTOR,)))["n"]
    con_expediente = dict(db.fetch_one(
        "SELECT count(*) AS n FROM evidencias e "
        "JOIN evidencia_clasificada ec ON ec.evidencia_id = e.id "
        "WHERE e.connector = ? AND ec.expediente_id IS NOT NULL",
        (_CONECTOR,)))["n"]
    con_org_pero_sin_expediente = dict(db.fetch_one(
        "SELECT count(*) AS n FROM evidencias e "
        "JOIN evidencia_clasificada ec ON ec.evidencia_id = e.id "
        "WHERE e.connector = ? AND ec.expediente_id IS NULL "
        "AND ec.organizacion_mencionada IS NOT NULL",
        (_CONECTOR,)))["n"]
    distribucion = {
        dict(f)["tipo_epistemologico"]: dict(f)["n"]
        for f in db.fetch_all(
            "SELECT ec.tipo_epistemologico, count(*) AS n FROM evidencias e "
            "JOIN evidencia_clasificada ec ON ec.evidencia_id = e.id "
            "WHERE e.connector = ? GROUP BY ec.tipo_epistemologico",
            (_CONECTOR,))
    }
    return {
        "evidencias_del_conector": total,
        "ya_clasificadas": clasificadas,
        "con_expediente_id": con_expediente,
        "sin_expediente_id": clasificadas - con_expediente,
        # Caso que NUNCA debería aparecer: organización detectada sin
        # expediente creado. Si aparece, es una regresión real.
        "con_organizacion_pero_sin_expediente_ANOMALO": con_org_pero_sin_expediente,
        "distribucion_tipo_epistemologico": distribucion,
    }


def _preguntas_de_validacion(antes: dict, despues: dict, rep: dict) -> list[dict]:
    perdidas = antes["evidencias_del_conector"] - despues["ya_clasificadas"]
    return [
        {"pregunta": "¿Cuántas evidencias del conector Tavily existen en total?",
         "respuesta": despues["evidencias_del_conector"]},
        {"pregunta": "¿Cuántas quedaron con fila en evidencia_clasificada tras esta corrida?",
         "respuesta": despues["ya_clasificadas"]},
        {"pregunta": "¿Coincide la distribución con la esperada "
                     "(5 autodeclaracion, 3 corroborante, 88 contextual)? "
                     "Si no coincide exactamente, explicar por qué antes de continuar.",
         "respuesta": despues["distribucion_tipo_epistemologico"]},
        {"pregunta": "¿Cuántas filas tienen expediente_id NULL vs NOT NULL?",
         "respuesta": {"NULL": despues["sin_expediente_id"],
                       "NOT NULL": despues["con_expediente_id"]}},
        {"pregunta": "¿Hay alguna fila con organizacion_mencionada NOT NULL pero "
                     "expediente_id NULL? (nunca debería pasar — ver REGLA DURA)",
         "respuesta": despues["con_organizacion_pero_sin_expediente_ANOMALO"],
         "criterio": "DEBE SER 0"},
        {"pregunta": "¿Se perdió alguna evidencia de las que existían antes de correr esto "
                     "(evidencias_del_conector - ya_clasificadas > 0 después de la corrida)?",
         "respuesta": perdidas,
         "criterio": "DEBE SER 0"},
        {"pregunta": "¿Cuántos expedientes nuevos se crearon en esta corrida?",
         "respuesta": rep.get("expedientes_creados")},
        {"pregunta": "¿Cuántas filas se escribieron en evidencia_clasificada en esta corrida?",
         "respuesta": rep.get("escritas")},
        {"pregunta": "¿Este script tocó expedientes_candidatos.estado en algún punto? "
                     "(promocion_candidatos.py no se importa ni se llama aquí)",
         "respuesta": "No — no se importa promocion_candidatos en este módulo."},
        {"pregunta": "¿El conteo total después = conteo antes + filas escritas en esta corrida, "
                     "sin duplicados?",
         "respuesta": {
             "antes": antes["ya_clasificadas"],
             "escritas_ahora": rep.get("escritas"),
             "despues": despues["ya_clasificadas"],
             "cuadra": antes["ya_clasificadas"] + (rep.get("escritas") or 0) == despues["ya_clasificadas"],
         }},
    ]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true",
                   help="no escribe nada; solo muestra la foto antes/después y el plan")
    p.add_argument("--host-esperado",
                   help="si se pasa, aborta si el host resuelto no coincide exactamente")
    args = p.parse_args()

    host = _host_de(settings.database_url)
    if not args.dry_run:
        _confirmar(host, args.host_esperado)
    else:
        print(f"Host detectado: {host} (dry-run: no se pide confirmación, no se escribe nada)")

    db = get_db()

    antes = _snapshot(db)
    print("\n=== Estado ANTES ===")
    print(json.dumps(antes, ensure_ascii=False, indent=2))

    rep = clasificar_lote(db, aplicar=not args.dry_run)
    print("\n=== Reporte de clasificar_lote ===")
    print(json.dumps({k: v for k, v in rep.items() if k != "muestra"},
                     ensure_ascii=False, indent=2))

    despues = _snapshot(db)
    print("\n=== Estado DESPUÉS ===")
    print(json.dumps(despues, ensure_ascii=False, indent=2))

    print("\n=== 10 preguntas de validación ===")
    for i, q in enumerate(_preguntas_de_validacion(antes, despues, rep), 1):
        print(f"{i}. {q['pregunta']}")
        print(f"   -> {q['respuesta']}"
              + (f"  [criterio: {q['criterio']}]" if "criterio" in q else ""))

    if args.dry_run:
        print("\n(dry-run: no se escribió nada en la base)")


if __name__ == "__main__":
    main()
