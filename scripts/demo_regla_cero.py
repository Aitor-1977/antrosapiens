#!/usr/bin/env python3
"""Demuestra en la práctica la Regla Cero (G0): ``detectado → observado``.

Regla Cero (``hd_scraper/candidato.py:g0_permitido``): ninguna entidad de BC-II
avanza a ``observado`` sin un peritaje validado originado en BC-I (dictamen con
veredicto ``VALIDADA``/``VALIDADA_PARCIAL`` y sin hipótesis bloqueada). El
candidato NO avanza jamás sin ese candado científico.

Este script simula la transición sobre un entorno de TEST (SQLite en memoria),
nunca toca la base real (``data/hd_scraper.db`` ni Postgres de producción):

    Escenario 1 · sin adjuntar evidencia
        ``observar(exp={})`` ⇒ G0 bloquea (G0Denied). Estado sigue ``detectado``.

    Escenario 2 · adjuntando un objeto de evidencia MOCK
        ``observar(exp={}, evidencia=mock)`` ⇒ G0 vuelve a bloquear: adjuntar
        evidencia NO salta la Regla Cero (el candado es el peritaje, no el
        adjunto). Estado sigue ``detectado``.

    Escenario 3 · control positivo (dictamen validado + evidencia mock)
        ``observar(exp=dictamen VALIDADA, evidencia=mock)`` ⇒ G0 permite, la
        transición se registra y referencia la evidencia mock. Estado ``observado``.

Uso:
    python -m scripts.demo_regla_cero [--org "Nubank"]

El ID es el ``candidato_id`` determinista de la Fase 1 (sha256 del nombre
normalizado): el mismo insumo produce siempre el mismo candidato. Se acepta
cualquier organización del directorio semilla curado (Fase 1).
"""
from __future__ import annotations

import argparse
import hashlib
import sys

from hd_scraper import candidato as cand
from hd_scraper.db.database import Database
from hd_scraper.db.models import ahora_iso
from hd_scraper.seed_prospectos import asegurar_directorio_semilla


def _insertar_evidencia(db, org: str, url: str) -> int:
    """Evidencia determinista de la organización en el entorno de test."""
    h = hashlib.sha256(f"{org}{url}".encode()).hexdigest()
    db.execute(
        """INSERT INTO evidencias
             (cita_textual, fecha_extraccion, fecha_publicacion, url_fuente,
              nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion,
              hash_dedup, connector, keywords, confianza, calidad_captura,
              categoria, estado, creado_en)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (f"{org} señal de expansión", ahora_iso(), "2026-01-01", url, "Medio",
         org, "expansion", "prensa", h, "google_news", '["expansion"]',
         0.9, "Alta", "Startup", "ok", ahora_iso()),
    )
    return db.fetch_one(
        "SELECT id FROM evidencias WHERE url_fuente = ?", (url,))["id"]


def _expediente(org: str, url: str, veredicto: str = "",
                bloqueada: bool = False) -> dict:
    """Expediente de BC-I: sin dictamen (veredicto "") o con dictamen validado."""
    return {
        "nombre": org,
        "huella": f"huella-{org.lower()}",
        "evidencias": [{"url": url, "texto": f"{org} señal", "confianza": 0.9}],
        "validacion_cientifica": {"veredicto": veredicto,
                                  "hipotesis_bloqueada": bloqueada},
    }


def _intento_observar(db, org: str, exp: dict, evidencia: dict | None,
                      etiqueta: str) -> dict:
    """Intenta la transición y captura el resultado (siempre sin lanzar)."""
    antes = cand.obtener_candidato(db, org)
    try:
        r = cand.observar(db, org, exp=exp, evidencia=evidencia)
        return {"escenario": etiqueta, "transicion": "PERMITIDA",
                "g0_permitido": r["g0"]["permitido"], "motivo": ""}
    except cand.G0Denied as e:
        despues = cand.obtener_candidato(db, org)
        return {"escenario": etiqueta, "transicion": "BLOQUEADA",
                "g0_permitido": False, "motivo": str(e),
                "estado_persistido": despues["estado"],
                "transiciones_persistidas": len(despues["transiciones"])}


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo de la Regla Cero (G0).")
    parser.add_argument("--org", default="Nubank",
                        help="organización del directorio semilla Fase 1")
    args = parser.parse_args()

    org = args.org.strip()
    # Entorno de test aislado: SQLite en memoria. La base real NO se abre.
    db = Database(":memory:")
    db.init_schema()
    asegurar_directorio_semilla(db)

    url = f"https://{org.lower()}.example/nota"
    ev_id = _insertar_evidencia(db, org, url)
    evidencia_mock = {"id": ev_id, "url": url, "texto": f"{org} señal (mock)"}

    cand.materializar_candidatos(db, [_expediente(org, url)])
    cid = cand.candidato_id(org)
    c = cand.obtener_candidato(db, org)

    print("=" * 72)
    print("REGLA CERO (G0) — detectado → observado · entorno de TEST (:memory:)")
    print("=" * 72)
    print(f"organización      : {org}")
    print(f"candidato_id (F1) : {cid}")
    print(f"prospecto         : {c['prospecto']['nombre']} "
          f"({c['prospecto']['categoria']})" if c.get("prospecto") else
          f"prospecto         : (sin prospecto)")
    print(f"estado inicial    : {c['estado']} ({c['etiqueta_estado']})")
    print()

    esc1 = _intento_observar(db, org, exp={}, evidencia=None,
                             etiqueta="1 · sin adjuntar evidencia")
    esc2 = _intento_observar(db, org, exp={}, evidencia=evidencia_mock,
                             etiqueta="2 · con evidencia mock (sin peritaje)")
    exp3 = _expediente(org, url, veredicto="VALIDADA")
    esc3 = _intento_observar(db, org, exp=exp3, evidencia=evidencia_mock,
                             etiqueta="3 · peritaje VALIDADA + evidencia mock")

    print(f"{'Escenario':<42} {'Resultado':<10} Detalle")
    print("-" * 72)
    for e in (esc1, esc2, esc3):
        detalle = e.get("motivo") or "transición registrada con evidencia mock"
        print(f"{e['escenario']:<42} {e['transicion']:<10} {detalle}")
        if e["transicion"] == "BLOQUEADA":
            print(f"{'':<42} {'':<10} estado persiste: "
                  f"{e['estado_persistido']} "
                  f"({e['transiciones_persistidas']} transición registrada)")
    print()

    # Verificación final del estado del candidato tras la demo.
    final = cand.obtener_candidato(db, org)
    ultima = final["transiciones"][-1]
    print("Estado final del candidato en el entorno de test:")
    print(f"  estado        : {final['estado']} ({final['etiqueta_estado']})")
    print(f"  transición    : {ultima['estado_desde']} → {ultima['estado_hasta']}")
    print(f"  evidencia_url : {ultima['evidencia_url']}")
    print(f"  evidencia_id  : {ultima['evidencia_id']}")
    print()

    ok = (
        esc1["transicion"] == "BLOQUEADA"
        and esc2["transicion"] == "BLOQUEADA"
        and esc3["transicion"] == "PERMITIDA"
        and final["estado"] == "observado"
    )
    print("RESULTADO:", "G0 FUNCIONA EN LA PRÁCTICA ✔" if ok
          else "G0 NO bloqueó lo que debía ✘")
    db.close()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
