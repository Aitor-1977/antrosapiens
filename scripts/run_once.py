#!/usr/bin/env python3
"""Corre el pipeline una vez para una o varias empresas (verificación punta a punta).

Operación autónoma: ``empresa`` es opcional. Si se omite, se barre la lista de
objetivos por defecto (``HD_TRACKED_EMPRESAS`` o el directorio semilla curado).
Los conectores que requieren slug (job_boards) siguen exigiendo ``--slug``.

Uso:
    python -m scripts.run_once                          # autónomo: objetivos por defecto
    python -m scripts.run_once "Nombre Empresa" --tipo ronda --connector google_news

Sirve para verificar el flujo completo del conector: extracción -> normalización
-> validación -> escritura en SQLite.
"""
from __future__ import annotations

import argparse
import logging

from hd_scraper.connectors import REGISTRY
from hd_scraper.db.database import Database
from hd_scraper.db.models import TIPOS_EVENTO, QuerySpec
from hd_scraper.filtros import (
    ESCALAS,
    CATEGORIAS_FILTRO,
    REGIONES,
    descripcion,
    objetivos_por_filtros,
)
from hd_scraper.pipeline import run_connector


def main() -> None:
    parser = argparse.ArgumentParser(description="Corrida única de un conector.")
    parser.add_argument("empresa", nargs="?", default=None,
                        help="Nombre de la empresa a buscar (si se omite: objetivos por defecto)")
    parser.add_argument("--tipo", default="ronda", choices=sorted(TIPOS_EVENTO),
                        help="tipo_evento declarado para la consulta")
    parser.add_argument("--connector", default="google_news", choices=sorted(REGISTRY),
                        help="conector a usar")
    parser.add_argument("--terminos", default=None, help="términos extra de búsqueda")
    parser.add_argument("--slug", default=None,
                        help="slug de empresa (requerido por job_boards)")
    parser.add_argument("--region", default="Toda LATAM", choices=sorted(REGIONES),
                        help="región del radar (gl/hl/ceid o sourcecountry)")
    parser.add_argument("--enfoque", action="append", dest="categorias",
                        choices=sorted(CATEGORIAS_FILTRO),
                        help="filtrar objetivos por ecosistema (VC|Startup|Incubadora|Corporativo)")
    parser.add_argument("--tamano", action="append", dest="escalas",
                        choices=sorted(ESCALAS),
                        help="filtrar objetivos por banda de tamaño")
    parser.add_argument("--keyword", default=None,
                        help="palabra clave agregada a la búsqueda")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    db = Database()
    db.init_schema()

    connector_cls = REGISTRY[args.connector]
    if connector_cls.requires_slug and not args.slug:
        parser.error(f"el conector {args.connector} requiere --slug")

    empresas: list[str] = [args.empresa] if args.empresa \
        else list(objetivos_por_filtros(filtros_desde_args(args)))
    if not empresas:
        parser.error("no hay objetivos por defecto (HD_TRACKED_EMPRESAS vacío y sin semilla)")

    # La palabra clave explícita de la CLI se suma a la de los filtros.
    terminos = " ".join(t for t in (args.terminos, args.keyword) if t) or None
    print(descripcion(filtros_desde_args(args)))
    for empresa in empresas:
        query = QuerySpec(empresa=empresa, tipo_evento=args.tipo,
                          terminos=terminos, slug=args.slug, region=args.region)
        with connector_cls() as connector:
            res = run_connector(db, connector, query)
        print(res.resumen())

    db.close()


def filtros_desde_args(args) -> "object":
    """Filtros construidos desde los flags de la CLI (mismo vocabulario que env)."""
    from hd_scraper.filtros import FiltrosRadar

    return FiltrosRadar(
        region=args.region,
        categorias=tuple(args.categorias or ()),
        escalas=tuple(args.escalas or ()),
        palabra_clave=args.keyword or "",
    )


if __name__ == "__main__":
    main()
