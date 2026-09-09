#!/usr/bin/env python3
"""Verifica en un solo comando el estado real del backend en Vercel.

Llama a /health, /audit/scraper, /audit/database y /api/dashboard y
resume el resultado en consola, en español, sin necesitar Neon SQL Editor
ni curl a mano. Solo lectura: no escribe nada, no requiere HD_INGEST_TOKEN.

Uso:
    python -m scripts.audit_backend
    python -m scripts.audit_backend --url https://antrosapiens-api-pro.vercel.app
"""
from __future__ import annotations

import argparse
import sys

import httpx

URL_DEFAULT = "https://antrosapiens-api-pro.vercel.app"


def _get(base: str, path: str) -> tuple[bool, dict | str, str | None]:
    """Devuelve (ok, cuerpo, request_id). request_id viene de la cabecera
    X-Request-Id (ver logging_config.py) — con ese id se busca la línea
    exacta en el panel de Logs de Vercel, sin tener que pegar todo el log."""
    try:
        r = httpx.get(f"{base}{path}", timeout=20.0)
        rid = r.headers.get("x-request-id")
        r.raise_for_status()
        return True, r.json(), rid
    except Exception as exc:  # noqa: BLE001 — se reporta, no se propaga
        return False, str(exc), None


def _marca_error(cuerpo: dict, rid: str | None) -> str:
    """Si el cuerpo trae error específico (ok: False), lo muestra junto al
    request_id para poder buscarlo en Vercel."""
    if isinstance(cuerpo, dict) and cuerpo.get("error"):
        sufijo = f" (request_id={rid})" if rid else ""
        return f"  ✗ error específico: {cuerpo['error']}{sufijo}"
    return ""


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default=URL_DEFAULT, help="URL base del backend")
    args = p.parse_args()

    fallo_general = False
    print(f"Auditando: {args.url}\n")

    ok, health, rid = _get(args.url, "/health")
    if not ok:
        print(f"✗ /health no respondió: {health}")
        print("\nEl backend está caído o inalcanzable. Nada más que auditar.")
        sys.exit(1)
    print(f"✓ /health: vivo, base de datos = {health.get('db')} (request_id={rid})")
    if health.get("db") == "sqlite":
        print("  ⚠ ADVERTENCIA: en producción esto debería decir 'postgres'. "
              "'sqlite' significa que la base es temporal y se borra sola.")
        fallo_general = True

    ok, scraper, rid = _get(args.url, "/audit/scraper")
    if ok:
        print(f"\n✓ /audit/scraper:")
        err = _marca_error(scraper, rid)
        if err:
            print(err)
            fallo_general = True
        print(f"  última evidencia escrita: {scraper.get('ultima_evidencia_escrita_en') or '(nunca)'}")
        print(f"  jobs pendientes: {scraper.get('jobs_pendientes')} | con error: {scraper.get('jobs_con_error')}")
        for f in scraper.get("fuentes", []):
            marca = "⚠" if f.get("alerta") else "✓"
            print(f"  {marca} {f.get('fuente')}: {f.get('ultimo_estado')} "
                  f"(fallos seguidos: {f.get('fallos_consecutivos')}, última corrida: {f.get('ultima_corrida')})")
        if scraper.get("alguna_fuente_en_alerta"):
            fallo_general = True
    else:
        print(f"\n✗ /audit/scraper falló: {scraper}")
        fallo_general = True

    ok, database, rid = _get(args.url, "/audit/database")
    if ok:
        cal = database.get("calidad_de_datos", {})
        print(f"\n✓ /audit/database:")
        for seccion in (database.get("base_de_datos"), cal, database.get("scraper")):
            err = _marca_error(seccion or {}, rid)
            if err:
                print(err)
                fallo_general = True
        print(f"  evidencias OK: {cal.get('total_evidencias_ok')} "
              f"(sin empresa identificada: {cal.get('evidencias_sin_empresa_identificada')}, "
              f"no fechadas: {cal.get('evidencias_no_fechadas')})")
        conflictos = cal.get("prospectos_con_categoria_en_conflicto", 0)
        if conflictos:
            print(f"  ⚠ {conflictos} organización(es) con categoría en conflicto: "
                  f"{', '.join(cal.get('nombres_en_conflicto', []))}")
    else:
        print(f"\n✗ /audit/database falló: {database}")
        fallo_general = True

    ok, dash, rid = _get(args.url, "/api/dashboard")
    if ok:
        print(f"\n✓ /api/dashboard:")
        err = _marca_error(dash, rid)
        if err:
            print(err)
            fallo_general = True
        print(f"  candidatos a prospecto ({dash.get('categoria_icp')}): {dash.get('candidatos_prospecto')}")
        print(f"  confirmados por el propio founder/CEO: {dash.get('candidatos_confirmados_por_founder')}")
        print(f"  vertical: {dash.get('vertical')}")
        print(f"  escala: {dash.get('escala')}")
        print(f"  último escaneo: {dash.get('last_scan') or '(nunca)'}")
        if not dash.get("candidatos_prospecto"):
            fallo_general = True
    else:
        print(f"\n✗ /api/dashboard falló: {dash}")
        fallo_general = True

    print("\n" + ("⚠ HAY ALGO QUE REVISAR (ver advertencias arriba)" if fallo_general
                  else "✓ Todo en orden: base real, sin conflictos, con candidatos."))
    sys.exit(1 if fallo_general else 0)


if __name__ == "__main__":
    main()
