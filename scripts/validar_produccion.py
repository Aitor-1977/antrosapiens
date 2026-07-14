"""Validación FINAL en PRODUCCIÓN del Motor A (datos reales, auditable).

NO simula nada: ejecuta capturas reales contra la app desplegada en Vercel (que
consulta Google News real) y luego audita el corpus real. Genera evidencia
verificable en docs/evidencia_produccion.json y docs/evidencia_produccion.md,
suficiente para auditar la corrida SIN leer el código fuente.

IMPORTANTE — dónde se ejecuta:
    Debe correrse desde un entorno CON acceso a Internet y al despliegue de
    producción. El sandbox del asistente tiene la salida de red bloqueada por el
    proxy (todo CONNECT externo responde 403), por lo que el asistente NO puede
    generar esta evidencia; la produces tú al correr el script. El script no
    inventa datos: si no alcanza producción, aborta con error explícito.

Requisitos:
    - Python 3.9+ (solo stdlib para red). Importa hd_scraper.relevance/signals/
      db.models del repo para EXPLICAR y VERIFICAR con el mismo código objetivo
      que usó producción (no altera nada en el servidor).
    - Variables de entorno:
        MOTOR_A_URL     (por defecto https://hd-prospector.vercel.app)
        HD_INGEST_TOKEN (X-Ingest-Token del despliegue; requerido salvo --solo-leer)

Uso:
    export MOTOR_A_URL="https://hd-prospector.vercel.app"
    export HD_INGEST_TOKEN="<token>"
    python -m scripts.validar_produccion              # captura real + auditoría
    python -m scripts.validar_produccion --solo-leer  # audita el corpus existente
    python -m scripts.validar_produccion --seed 7     # muestreo reproducible (det.)

Código de salida: 0 si TODAS las verificaciones pasan; 1 si alguna falla.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Mismo código OBJETIVO que usó producción (para explicar/verificar, no para simular).
from hd_scraper.db.models import ORIGENES_DECLARACION, TIPOS_EVENTO  # noqa: E402
from hd_scraper.relevance import detectar_empresa  # noqa: E402
from hd_scraper.signals import detectar_keywords, fuente_confiable  # noqa: E402

BASE = os.getenv("MOTOR_A_URL", "https://hd-prospector.vercel.app").rstrip("/")
TOKEN = os.getenv("HD_INGEST_TOKEN", "")

CONTRATO = "motor_a.corpus.v1"
CLAVES_CORPUS = {"empresa", "fuente", "fecha", "texto", "url",
                 "keywords", "confianza", "calidad_captura",
                 "categoria", "tipo_evento", "hash"}
# Campos obligatorios del contrato /corpus (no pueden ir vacíos/nulos).
OBLIGATORIOS_CORPUS = ("empresa", "fuente", "texto", "url", "tipo_evento", "hash")

# Plan de captura real (mezcla empresa y categoría):
#   - Misma empresa bajo DOS tipos -> mismas notas por consultas distintas => dedup.
#   - Categoría => descubrimiento amplio => filtro de relevancia + variedad calidad.
PLAN_EMPRESAS = [
    ("Nubank", ["ronda", "lanzamiento"]),
    ("Mercado Libre", ["lanzamiento", "queja"]),
    ("Rappi", ["despido", "queja"]),
    ("Kavak", ["ronda", "despido"]),
    ("Bitso", ["ronda", "lanzamiento"]),
    ("Clip", ["ronda", "queja"]),
]
PLAN_CATEGORIAS = [
    {"categoria": "Startup", "tipo_evento": "queja", "vertical": "fintech", "region": "México"},
    {"categoria": "VC", "tipo_evento": "ronda", "vertical": "todas", "region": "México"},
    {"categoria": "Startup", "tipo_evento": "despido", "vertical": "todas", "region": "Colombia"},
]


# ── HTTP (stdlib) ─────────────────────────────────────────────────────────────

def _req(metodo, ruta, cuerpo=None, token=False, intentos=3):
    url = f"{BASE}{ruta}"
    data = json.dumps(cuerpo).encode() if cuerpo is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["X-Ingest-Token"] = TOKEN
    ultimo = None
    for i in range(intentos):
        try:
            r = urllib.request.Request(url, data=data, headers=headers, method=metodo)
            with urllib.request.urlopen(r, timeout=120) as resp:
                raw = resp.read().decode()
                try:
                    return resp.status, json.loads(raw)
                except json.JSONDecodeError:
                    return resp.status, raw
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                pass
            return e.code, body
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            ultimo = e
            time.sleep(2 ** i)
    raise SystemExit(
        f"\nERROR de red irrecuperable contra {url}: {ultimo}\n"
        "Este script debe correrse desde un entorno CON acceso a Internet y a "
        "producción. Abortando SIN generar evidencia (no se simula).")


def _get_paginado(ruta, clave_items="items", limite=200):
    salida, offset = [], 0
    while True:
        sep = "&" if "?" in ruta else "?"
        st, d = _req("GET", f"{ruta}{sep}limite={limite}&offset={offset}")
        if st != 200 or not isinstance(d, dict):
            raise SystemExit(f"GET {ruta} devolvió {st}: {d}")
        items = d.get(clave_items, [])
        salida.extend(items)
        total = d.get("total", len(salida))
        offset += len(items)
        if not items or offset >= total:
            break
    return salida


# ── Explicación / verificación objetiva (mismo criterio que producción) ───────

def _titulo(ev):
    return ev.get("cita_textual") or ev.get("texto") or ""


def explicar_calidad(ev):
    titulo = _titulo(ev)
    empresa_ok = bool(detectar_empresa(titulo))
    evento_ok = bool(detectar_keywords(titulo))
    fuente_ok = fuente_confiable(ev.get("nombre_medio") or ev.get("fuente") or "")
    n = int(empresa_ok) + int(evento_ok) + int(fuente_ok)
    esperada = "Alta" if n == 3 else "Media" if n == 2 else "Baja"
    razon = (f"{n}/3 criterios (empresa={'sí' if empresa_ok else 'no'}, "
             f"evento={'sí' if evento_ok else 'no'}, "
             f"fuente_confiable={'sí' if fuente_ok else 'no'}) -> {esperada}")
    return esperada, razon


def _es_iso(v):
    if v in (None, ""):
        return True  # fecha nula es válida (no_fechado); /corpus solo trae fechados
    try:
        datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def auditar_contrato(corpus, contrato_tag):
    """Verifica contrato, esquema, campos obligatorios y corrupción por item."""
    problemas = []
    for it in corpus:
        h = it.get("hash")
        if set(it.keys()) != CLAVES_CORPUS:
            problemas.append({"hash": h, "tipo": "claves_contrato",
                              "detalle": sorted(it.keys())})
        for campo in OBLIGATORIOS_CORPUS:
            val = it.get(campo)
            if val is None or (isinstance(val, str) and not val.strip()):
                problemas.append({"hash": h, "tipo": "campo_obligatorio_vacio",
                                  "detalle": campo})
        te = it.get("tipo_evento")
        if te not in TIPOS_EVENTO:
            problemas.append({"hash": h, "tipo": "tipo_evento_invalido", "detalle": te})
        cf = it.get("confianza")
        if not isinstance(cf, (int, float)) or not (0.0 <= float(cf) <= 1.0):
            problemas.append({"hash": h, "tipo": "confianza_fuera_de_rango", "detalle": cf})
        if not isinstance(it.get("keywords"), list):
            problemas.append({"hash": h, "tipo": "keywords_no_lista",
                              "detalle": type(it.get("keywords")).__name__})
        if not _es_iso(it.get("fecha")):
            problemas.append({"hash": h, "tipo": "fecha_no_iso8601", "detalle": it.get("fecha")})
    contrato_ok = (contrato_tag == CONTRATO) and not problemas
    return contrato_ok, problemas


# ── Validación ────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-leer", action="store_true")
    ap.add_argument("--muestra", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0, help="Semilla del muestreo (determinista)")
    args = ap.parse_args()
    rnd = random.Random(args.seed)

    print("=" * 72)
    print("VALIDACIÓN FINAL EN PRODUCCIÓN — Motor A (datos reales, auditable)")
    print(f"Base: {BASE}   seed={args.seed}")
    print("=" * 72)

    st, salud = _req("GET", "/health")
    print(f"[health] status={st} -> {salud}")
    if st != 200:
        raise SystemExit("La app no responde /health; abortando (no se simula).")

    capturas = []
    if not args.solo_leer:
        if not TOKEN:
            raise SystemExit("Falta HD_INGEST_TOKEN para ejecutar /scrape.")
        print("\n[captura] Ejecutando scrapes REALES contra Google News…")
        for empresa, tipos in PLAN_EMPRESAS:
            for tipo in tipos:
                st, d = _req("POST", "/scrape", token=True,
                             cuerpo={"empresa": empresa, "tipo_evento": tipo,
                                     "connectors": ["google_news"], "region": "LATAM"})
                print(f"  empresa={empresa!r:16} tipo={tipo:10} -> {st} {_resumen(d)}")
                if st == 200:
                    capturas.append({"consulta": f"{empresa}/{tipo}", "resp": d})
        for pl in PLAN_CATEGORIAS:
            st, d = _req("POST", "/scrape", token=True, cuerpo=pl)
            print(f"  categoria={pl['categoria']:8} tipo={pl['tipo_evento']:8} "
                  f"vert={pl['vertical']:8} -> {st} {_resumen(d)}")
            if st == 200:
                capturas.append({"consulta": json.dumps(pl, ensure_ascii=False), "resp": d})
    else:
        print("\n[captura] --solo-leer: se audita el corpus existente.")

    print("\n[lectura] Descargando corpus, evidencias y stats reales…")
    st, corpus_head = _req("GET", "/corpus?limite=1")
    contrato_tag = corpus_head.get("contrato") if isinstance(corpus_head, dict) else None
    corpus = _get_paginado("/corpus")
    evidencias = _get_paginado("/evidencias")
    st, stats = _req("GET", "/stats")
    if not isinstance(stats, dict):
        stats = {}
    print(f"  corpus={len(corpus)}  evidencias={len(evidencias)}  contrato={contrato_tag!r}")

    # Contrato + esquema + corrupción.
    contrato_ok, problemas = auditar_contrato(corpus, contrato_tag)
    print("\n[contrato] motor_a.corpus.v1 + esquema + campos obligatorios + corrupción")
    print(f"  contrato_tag={contrato_tag!r}  items={len(corpus)}  "
          f"problemas={len(problemas)}  -> {'OK' if contrato_ok else 'FALLA'}")
    for p in problemas[:5]:
        print(f"    - {p}")

    # Deduplicación.
    urls = [it["url"] for it in corpus]
    hashes = [it["hash"] for it in corpus]
    dup_urls = [u for u, c in Counter(urls).items() if c > 1]
    dup_hash = [h for h, c in Counter(hashes).items() if c > 1]
    dups_run = sum(r.get("duplicados", 0)
                   for cap in capturas for r in cap["resp"].get("resultados", []))
    dedup_ok = not dup_urls and not dup_hash
    print("\n[dedup] Unicidad en el corpus real")
    print(f"  urls únicas={len(set(urls))}/{len(urls)}  hash únicos={len(set(hashes))}/{len(hashes)}")
    print(f"  duplicados colapsados al escribir (esta corrida)={dups_run}  -> "
          f"{'OK' if dedup_ok else 'FALLA'}")

    # Métricas (fuente autoritativa: /stats corpus-wide; /scrape para esta corrida).
    consumibles = stats.get("evidencias_consumibles", len(evidencias))
    no_fechadas = stats.get("evidencias_no_fechadas", 0)
    rechazos = stats.get("rechazos", 0)
    motivos = stats.get("rechazos_por_motivo", {})
    calidad_stats = stats.get("calidad_captura", {})
    dist_calidad = Counter((ev.get("calidad_captura") or "sin_calidad") for ev in evidencias)
    empresas = {(ev.get("empresa_mencionada") or "").strip()
                for ev in evidencias if (ev.get("empresa_mencionada") or "").strip()}
    empresas_detectadas = sum(1 for ev in evidencias if detectar_empresa(_titulo(ev)))
    capturados_run = sum(r.get("escritos", 0)
                         for cap in capturas for r in cap["resp"].get("resultados", []))
    filtrados_run = sum(r.get("filtrados", 0)
                        for cap in capturas for r in cap["resp"].get("resultados", []))
    vistos_run = sum(r.get("vistos", 0)
                     for cap in capturas for r in cap["resp"].get("resultados", []))
    descartados_total = rechazos  # incluye contrato + relevancia (rechazos) — corpus-wide
    base_util = consumibles + no_fechadas + rechazos
    pct_utiles = (consumibles / base_util * 100) if base_util else 0.0

    print("\n[métricas] (corpus-wide desde /stats + esta corrida desde /scrape)")
    print(f"  artículos capturados (esta corrida)      : {capturados_run}")
    print(f"  vistos (esta corrida)                    : {vistos_run}")
    print(f"  evidencia consumible (corpus)            : {consumibles}")
    print(f"  evidencia no fechada (corpus)            : {no_fechadas}")
    print(f"  descartados / rechazos (corpus)          : {descartados_total}")
    print(f"  duplicados detectados (esta corrida)     : {dups_run}")
    print(f"  descartados por relevancia (esta corrida): {filtrados_run}")
    print(f"  empresas distintas (corpus)              : {len(empresas)}")
    print(f"  evidencias con empresa detectable        : {empresas_detectadas}/{len(evidencias)}")
    print(f"  distribución calidad (/evidencias)       : {dict(dist_calidad)}")
    print(f"  distribución calidad (/stats)            : {calidad_stats}")
    print(f"  distribución motivos de rechazo (/stats) : {motivos}")
    print(f"  % artículos útiles                       : {pct_utiles:.1f}%")

    # Muestreo determinista ≥ N.
    n = min(args.muestra, len(evidencias))
    muestra = rnd.sample(evidencias, n) if n else []
    print(f"\n[muestra] {n} registros reales (seed={args.seed}). Primeros 12:")
    filas, coincidencias = [], 0
    for i, ev in enumerate(muestra, 1):
        etiqueta = ev.get("calidad_captura") or "sin_calidad"
        esperada, razon = explicar_calidad(ev)
        coincidencias += int(etiqueta == esperada)
        evento = ev.get("keywords") or detectar_keywords(_titulo(ev))
        filas.append({
            "empresa": ev.get("empresa_mencionada"),
            "evento_detectado": evento,
            "calidad": etiqueta, "calidad_recalculada": esperada,
            "coincide": etiqueta == esperada, "explicacion": razon,
            "fuente": ev.get("nombre_medio"), "url": ev.get("url_fuente"),
            "titulo": ev.get("cita_textual"),
        })
        if i <= 12:
            print(f"  {i:2}. [{etiqueta:5}] {ev.get('empresa_mencionada')!r} · "
                  f"evento={evento} · fuente={ev.get('nombre_medio')!r}")
            print(f"      {razon}")
            print(f"      {ev.get('url_fuente')}")
    if muestra:
        print(f"  coincidencia etiqueta producción vs recálculo objetivo: {coincidencias}/{n}")
    if n < args.muestra:
        print(f"  AVISO: solo hay {n} evidencias consumibles (<{args.muestra}). "
              "Corre más capturas o revisa producción.")

    # Volcado de evidencia.
    ts = datetime.now(timezone.utc).isoformat()
    evidencia = {
        "generado_en": ts, "base": BASE, "seed": args.seed,
        "origen": "produccion (Vercel + Google News real)",
        "contrato": contrato_tag, "contrato_ok": contrato_ok,
        "problemas_contrato": problemas,
        "dedup_ok": dedup_ok, "dup_urls": dup_urls, "dup_hash": dup_hash,
        "salud": salud, "stats": stats, "capturas": capturas,
        "metricas": {
            "capturados_esta_corrida": capturados_run, "vistos_esta_corrida": vistos_run,
            "consumibles": consumibles, "no_fechadas": no_fechadas,
            "descartados_rechazos": descartados_total,
            "duplicados_esta_corrida": dups_run, "filtrados_esta_corrida": filtrados_run,
            "empresas_distintas": len(empresas), "evidencias_con_empresa": empresas_detectadas,
            "distribucion_calidad": dict(dist_calidad),
            "distribucion_motivos_rechazo": motivos,
            "pct_utiles": round(pct_utiles, 1),
            "corpus_urls_unicas": [len(set(urls)), len(urls)],
            "corpus_hash_unicos": [len(set(hashes)), len(hashes)],
        },
        "muestra_calidad": filas,
    }
    out = ROOT / "docs" / "evidencia_produccion.json"
    out.write_text(json.dumps(evidencia, ensure_ascii=False, indent=2))
    _md(ROOT / "docs" / "evidencia_produccion.md", evidencia)
    print(f"\n[evidencia] escrita en:\n  {out}\n  {out.with_suffix('.md')}")

    ok = contrato_ok and dedup_ok
    print("\n" + "=" * 72)
    print(f"DICTAMEN: {'✅ Motor A LISTO (evidencia real OK)' if ok else '❌ BLOQUEO — revisar arriba'}")
    print(f"  contrato={'ok' if contrato_ok else 'FALLA'}  "
          f"dedup={'ok' if dedup_ok else 'FALLA'}  "
          f"consumibles={consumibles}  %útiles={pct_utiles:.1f}")
    print("=" * 72)
    sys.exit(0 if ok else 1)


def _resumen(d):
    if not isinstance(d, dict):
        return str(d)[:120]
    rs = d.get("resultados", [])
    g = lambda k: sum(r.get(k, 0) for r in rs)  # noqa: E731
    return f"vistos={g('vistos')} escritos={g('escritos')} dup={g('duplicados')} filtrados={g('filtrados')}"


def _md(path, ev):
    m = ev["metricas"]
    L = [
        "# Evidencia de validación en producción — Motor A",
        "",
        f"- Generado: `{ev['generado_en']}`",
        f"- Origen: **{ev['origen']}**",
        f"- Base (producción): `{ev['base']}`   ·   seed: `{ev['seed']}`",
        f"- Salud: `{ev['salud']}`",
        f"- Contrato `motor_a.corpus.v1`: {'✅ OK' if ev['contrato_ok'] else '❌ FALLA'} "
        f"(problemas: {len(ev['problemas_contrato'])})",
        f"- Deduplicación: {'✅ OK' if ev['dedup_ok'] else '❌ FALLA'} "
        f"(url repetidas: {len(ev['dup_urls'])}, hash repetidos: {len(ev['dup_hash'])})",
        "",
        "## Métricas (datos reales)",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Artículos capturados (esta corrida) | {m['capturados_esta_corrida']} |",
        f"| Vistos (esta corrida) | {m['vistos_esta_corrida']} |",
        f"| Evidencia consumible (corpus) | {m['consumibles']} |",
        f"| Evidencia no fechada (corpus) | {m['no_fechadas']} |",
        f"| Descartados / rechazos (corpus) | {m['descartados_rechazos']} |",
        f"| Duplicados detectados (esta corrida) | {m['duplicados_esta_corrida']} |",
        f"| Descartados por relevancia (esta corrida) | {m['filtrados_esta_corrida']} |",
        f"| Empresas distintas | {m['empresas_distintas']} |",
        f"| Evidencias con empresa detectable | {m['evidencias_con_empresa']} |",
        f"| % artículos útiles | {m['pct_utiles']}% |",
        f"| URLs únicas / total (corpus) | {m['corpus_urls_unicas'][0]}/{m['corpus_urls_unicas'][1]} |",
        f"| Hash únicos / total (corpus) | {m['corpus_hash_unicos'][0]}/{m['corpus_hash_unicos'][1]} |",
        "",
        "### Distribución de calidad_captura",
        "",
        f"`{m['distribucion_calidad']}`",
        "",
        "### Distribución de motivos de rechazo",
        "",
        f"`{m['distribucion_motivos_rechazo']}`",
        "",
    ]
    if ev["problemas_contrato"]:
        L += ["### Problemas de contrato/esquema detectados", "",
              "```json", json.dumps(ev["problemas_contrato"][:50], ensure_ascii=False, indent=2),
              "```", ""]
    L += ["## Muestra de calidad (≥50 registros reales)", "",
          "| # | Calidad | Empresa | Evento detectado | Fuente | Explicación | URL |",
          "|--:|:--|:--|:--|:--|:--|:--|"]
    for i, f in enumerate(ev["muestra_calidad"], 1):
        ev_det = ", ".join(f["evento_detectado"]) if isinstance(f["evento_detectado"], list) else str(f["evento_detectado"])
        url = (f["url"] or "").replace("|", "%7C")
        L.append(f"| {i} | {f['calidad']} | {f['empresa']} | {ev_det} | {f['fuente']} "
                 f"| {f['explicacion']} | {url} |")
    path.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
