"""Genera el reporte en TEXTO PLANO con los 5 Candidatos Comerciales recientes.

Regla estricta de entorno: TMPDIR/TMP/TEMP -> ~/antrosapiens/data/ + parche de
``tempfile`` en runtime. Salida: data/reporte_5_candidatos_recientes.txt

Contenido por candidato: nombre, resumen de evidencias (total, tipos, mejor
evidencia y señales recientes) y trazabilidad (candidato_id, expediente_hash,
prospecto, evidencia_ids, URLs).
"""
from __future__ import annotations

import os
import sys

_HOME = os.path.expanduser("~")
_PROJ = os.path.join(_HOME, "antrosapiens")
_TEMP_DIR = os.path.join(_PROJ, "data")
os.makedirs(_TEMP_DIR, exist_ok=True)
os.environ["TMPDIR"] = _TEMP_DIR
os.environ["TMP"] = _TEMP_DIR
os.environ["TEMP"] = _TEMP_DIR

import tempfile  # noqa: E402

tempfile.tempdir = _TEMP_DIR
try:
    tempfile._tempdir = _TEMP_DIR
except AttributeError:  # pragma: no cover
    pass

if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

import datetime  # noqa: E402

from hd_scraper.api.app import _paquete_cientifico  # noqa: E402
from hd_scraper.candidato import ESTADOS_LABELS, candidato_id, g0_permitido  # noqa: E402
from hd_scraper.db.database import Database  # noqa: E402

db = Database()
db.init_schema()


def resolver_evidencia_id(url: str):
    if not url:
        return None
    fila = db.fetch_one(
        "SELECT id FROM evidencias WHERE url_fuente = ? ORDER BY id LIMIT 1",
        (url,),
    )
    return fila["id"] if fila else None


def truncar(cid: str, n: int = 8) -> str:
    return f"{cid[:n]}...{cid[-6:]}"


rows = []
for _row in db.fetch_all("SELECT * FROM candidatos ORDER BY org_nombre"):
    c = dict(_row)
    org = c["org_nombre"]
    try:
        exp, val, huella = _paquete_cientifico(org)
        exp["validacion_cientifica"] = val["dictamen_cientifico"]
        exp["huella"] = huella["hash"]
    except Exception as e:  # noqa: BLE001
        print(f"WARN {org}: {type(e).__name__}: {e}", file=sys.stderr)
        continue

    dic = val["dictamen_cientifico"]
    g0 = g0_permitido(exp)
    evs = list(exp.get("evidencias") or [])
    con_fecha = sorted(
        (e for e in evs if (e.get("fecha") or "")),
        key=lambda e: e["fecha"],
        reverse=True,
    )
    ultima = con_fecha[0]["fecha"] if con_fecha else ""
    mejor = max(
        (e for e in evs if (e.get("url") or "")),
        key=lambda e: float(e.get("confianza") or 0.0),
        default={},
    )
    tipos: dict[str, int] = {}
    for e in evs:
        t = e.get("tipo_evento") or "?"
        tipos[t] = tipos.get(t, 0) + 1

    prospecto = None
    if c.get("prospecto_id"):
        p = db.fetch_one(
            "SELECT id, nombre, categoria, escala, vertical FROM prospectos WHERE id = ?",
            (c["prospecto_id"],),
        )
        prospecto = dict(p) if p else None

    rows.append({
        "org": org,
        "id": c["id"],
        "candidato_id": c["candidato_id"],
        "expediente_hash": exp.get("huella") or c.get("expediente_hash") or "",
        "estado": c["estado"],
        "categoria": exp.get("categoria") or (prospecto or {}).get("categoria") or "",
        "escala": (prospecto or {}).get("escala") or "",
        "scoring": exp.get("scoring", ""),
        "score_icp": exp.get("score_icp", 0),
        "veredicto": dic.get("veredicto", ""),
        "g0": g0["permitido"],
        "n_ev": len(evs),
        "tipos": tipos,
        "ultima": ultima,
        "mejor": mejor,
        "recientes": con_fecha[:3],
        "prospecto": prospecto,
        "total_transiciones": db.fetch_one(
            "SELECT COUNT(*) n FROM candidato_transiciones WHERE candidato_id = ?",
            (c["candidato_id"],),
        )["n"],
    })

top = sorted(rows, key=lambda r: r["ultima"], reverse=True)[:5]

total_ok = db.fetch_one("SELECT COUNT(*) n FROM evidencias WHERE estado='ok'")["n"]
total_dup = db.fetch_one("SELECT COUNT(*) n FROM evidencias WHERE estado='duplicada'")["n"]
total_rech = db.fetch_one("SELECT COUNT(*) n FROM rechazos")["n"]
por_conector = db.fetch_all(
    "SELECT connector, COUNT(*) n FROM evidencias WHERE estado='ok' GROUP BY connector"
)
fechas_ingesta = db.fetch_all(
    "SELECT MIN(fecha_extraccion) min_, MAX(fecha_extraccion) max_ FROM evidencias WHERE estado='ok'"
)

hoy = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

L: list[str] = []
L.append("REPORTE · 5 CANDIDATOS COMERCIALES RECIENTES")
L.append("=" * 60)
L.append(f"Fecha de corrida    : {hoy}")
L.append(f"Entorno             : local (Termux · Linux)")
L.append(f"Base de datos       : ~/antrosapiens/data/hd_scraper.db (SQLite)")
L.append(f"Directorio temporal : {_TEMP_DIR}  (regla de entorno: prohibido /tmp; TMPDIR/TMP/TEMP redirigidos + parche tempfile en runtime)")
L.append(f"Ingesta             : scripts.run_once (modo autónomo, Google News RSS · region=Toda LATAM)")
L.append("")
L.append("1. RESUMEN DE LA INGESTA")
L.append("-" * 60)
L.append(f"  - Objetivos barridos por defecto: {len(rows)} organizaciones del directorio semilla curado (VC · Startup · Incubadora · Corporativo).")
L.append(f"  - Evidencias con estado=ok      : {total_ok}")
L.append(f"  - Duplicadas (dedup hash_dedup) : {total_dup}")
L.append(f"  - Rechazadas (contrato Motor A) : {total_rech}")
_por_conector = ", ".join(
    f"{fila['connector']}={fila['n']}" for fila in por_conector
)
L.append(f"  - Evidencias por conector       : {_por_conector}")
if fechas_ingesta and fechas_ingesta[0]["min_"]:
    L.append(f"  - Ventana de captura            : {fechas_ingesta[0]['min_']} -> {fechas_ingesta[0]['max_']}")
L.append("")
L.append("2. MATERIALIZACION DE CANDIDATOS COMERCIALES (BC-I -> BC-II)")
L.append("-" * 60)
por_estado: dict[str, int] = {}
for r in rows:
    por_estado[r["estado"]] = por_estado.get(r["estado"], 0) + 1
g0_count = sum(1 for r in rows if r["g0"])
L.append(f"  - Candidatos materializados: {len(rows)} (uno por organizacion detectada con evidencia).")
L.append(f"  - Estados: {', '.join(f'{ESTADOS_LABELS.get(k,k)}={v}' for k, v in sorted(por_estado.items()))}.")
L.append(f"  - Regla Cero (G0): g0_permitido = {g0_count} (solo dictamen VALIDADA/VALIDADA_PARCIAL habilita avanzar a 'observado').")
L.append("")
L.append("3. LOS 5 CANDIDATOS COMERCIALES RECIENTES")
L.append("-" * 60)
L.append("Ordenados por la senal mas reciente capturada (fecha_publicacion maxima de la evidencia).")
L.append("")
for i, r in enumerate(top, 1):
    mejor = r["mejor"] or {}
    L.append(f"[{i}] {r['org']}")
    L.append(f"    Categoria   : {r['categoria'] or '—'} | Escala: {r['escala'] or '—'} | Scoring: {r['scoring'] or '—'} | Score ICP: {r['score_icp']}")
    L.append(f"    Estado      : {ESTADOS_LABELS.get(r['estado'], r['estado'])} | Dictamen: {r['veredicto']} | G0 permitido: {r['g0']}")
    L.append(f"    Evidencias  : {r['n_ev']} total | ultima senal: {r['ultima'] or '—'}")
    if r["tipos"]:
        detalle_tipos = ", ".join(f"{t}={n}" for t, n in sorted(r["tipos"].items()))
        L.append(f"    Por tipo    : {detalle_tipos}")
    if mejor.get("texto"):
        L.append(f"    Mejor evidencia (confianza {mejor.get('confianza') or '—'}):")
        L.append(f"      Texto   : {mejor['texto']}")
        L.append(f"      Fuente  : {mejor.get('fuente') or '—'} | fecha: {mejor.get('fecha') or '—'}")
        L.append(f"      URL     : {mejor.get('url')}")
    if r["recientes"]:
        L.append("    Senales mas recientes (evidencia_id -> fecha -> fuente):")
        for e in r["recientes"]:
            eid = resolver_evidencia_id(e.get("url"))
            L.append(f"      id={eid} | {e.get('fecha')} | {e.get('fuente') or '—'} | {e.get('url')}")
    p = r["prospecto"]
    L.append("    Trazabilidad:")
    L.append(f"      candidato_id    : {r['candidato_id']}")
    L.append(f"      expediente_hash : {r['expediente_hash']}")
    L.append(f"      prospecto       : id={p['id'] if p else '—'} ({p['nombre'] if p else '—'} · {p['categoria'] if p else '—'})")
    L.append(f"      transiciones    : {r['total_transiciones']}")
    L.append("")

L.append("4. NOTAS DE TRAZABILIDAD Y CALIDAD")
L.append("-" * 60)
L.append("  - Regla Cero activa: los candidatos con dictamen distinto de VALIDADA/VALIDADA_PARCIAL")
L.append("    permanecen en 'detectado'. La decision de avanzar/descartar corresponde al operador vía")
L.append("    RadarHD (Motor B); Motor A solo registra deteccion y observacion.")
L.append("  - Determinismo: candidato_id (sha256 del nombre normalizado) y expediente_hash son")
L.append("    reproducibles (mismo insumo => mismo resultado). Re-materializar no duplica filas ni transiciones.")
L.append("  - Cadena referencial verificable: organizacion -> candidato -> prospecto -> expediente -> evidencia")
L.append("    (scripts.trazabilidad, solo lectura).")
L.append("  - Dedup por hash_dedup: re-capturar la misma URL/empresa cuenta como 'duplicada', no como escrito nuevo.")
L.append("")
L.append("*Fin del reporte*")

out = os.path.join(_TEMP_DIR, "reporte_5_candidatos_recientes.txt")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print("reporte escrito:", out)
db.close()
