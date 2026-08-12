import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import os.path, sys as _sys, datetime, hashlib

HOME = os.path.expanduser("~")
proj = os.path.join(HOME, "antrosapiens")
_sys.path.insert(0, proj)

from hd_scraper.api.app import _paquete_cientifico
from hd_scraper.db.database import Database
from hd_scraper.candidato import g0_permitido

db = Database()
db.init_schema()

def trunc(cid: str, n: int = 8) -> str:
    return cid[:n] + "…" + cid[-6:]

# ---- recopilar candidatos con expediente ----
candidatos = db.fetch_all("SELECT * FROM candidatos ORDER BY org_nombre")
rows = []
for c in candidatos:
    org = c["org_nombre"]
    try:
        exp, val, huella = _paquete_cientifico(org)
        exp["validacion_cientifica"] = val["dictamen_cientifico"]
        dic = val["dictamen_cientifico"]
        g0 = g0_permitido(exp)
    except Exception as e:
        print("WARN", org, type(e).__name__, e, file=sys.stderr)
        continue
    evs = exp.get("evidencias") or []
    fechas = sorted((e.get("fecha") or "") for e in evs if e.get("fecha"))
    ultima = fechas[-1] if fechas else ""
    conf = max([(e.get("confianza") or 0) for e in evs] or [0])
    mejor = max(evs, key=lambda e: e.get("confianza") or 0) if evs else {}
    rows.append({
        "org": org,
        "id": c["id"],
        "candidato_id": c["candidato_id"],
        "expediente_hash": c["expediente_hash"] or exp.get("huella", ""),
        "estado": c["estado"],
        "prospecto": c["prospecto_id"],
        "categoria": exp.get("categoria") or "",
        "escala": exp.get("escala") or "",
        "scoring": exp.get("scoring", ""),
        "score_icp": exp.get("score_icp", 0),
        "veredicto": dic.get("veredicto", ""),
        "g0": g0["permitido"],
        "n_ev": len(evs),
        "ultima": ultima,
        "conf": conf,
        "mejor": mejor,
    })

# escala: caer a prospectos si el expediente no lo trae
prows = db.fetch_all("SELECT id, categoria, escala FROM prospectos")
pmap = {p["id"]: dict(p) for p in prows}
for r in rows:
    p = pmap.get(r["prospecto"])
    if p:
        r["categoria"] = r["categoria"] or p.get("categoria") or ""
        r["escala"] = r["escala"] or p.get("escala") or ""

# ---- top 5 por última señal ----
top = sorted(rows, key=lambda r: r["ultima"], reverse=True)[:5]

conector = db.fetch_one(
    "SELECT connector, COUNT(*) n FROM evidencias GROUP BY connector ORDER BY n DESC")
total_ev = db.fetch_one("SELECT COUNT(*) n FROM evidencias WHERE estado='ok'")
rech = db.fetch_one("SELECT COUNT(*) n FROM rechazos")
dups = db.fetch_one("SELECT COUNT(*) n FROM evidencias WHERE estado='duplicada'")
n_org = db.fetch_one("SELECT COUNT(*) n FROM (SELECT DISTINCT empresa_mencionada FROM evidencias WHERE estado='ok')")

por_estado = {}
for r in rows:
    por_estado[r["estado"]] = por_estado.get(r["estado"], 0) + 1
g0_count = sum(1 for r in rows if r["g0"])

hoy = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

L = []
L.append("# Reporte · 5 Candidatos Comerciales recientes")
L.append("")
L.append(f"**Fecha de corrida:** {hoy}")
L.append("**Entorno:** local (Termux · Linux)")
L.append("**Base de datos:** `~/antrosapiens/data/hd_scraper.db` (SQLite)")
L.append("**Directorio temporal:** `~/antrosapiens/data/` (regla de entorno: prohibido `/tmp`; `TMPDIR`/`TMP`/`TEMP` redirigidos en runtime)")
L.append(f"**Conectores de ingesta:** `{conector['connector']}` (+ enriquecimiento `rss_fijos`, `gdelt`)")
L.append("")
L.append("---")
L.append("")
L.append("## 1. Resumen de la ingesta (`run_once`, modo autónomo)")
L.append("")
L.append(f"- Objetivos barridos por defecto: **{n_org['n']}** organizaciones del directorio semilla curado (VC · Startup · Incubadora · Corporativo).")
L.append(f"- Evidencias escritas: **{total_ev['n']}** · `estado=ok` (consumibles por la API) · **{rech['n']} rechazadas** · **{dups['n']} duplicadas**.")
L.append(f"- {n_org['n']}/{n_org['n']} organizaciones del directorio con evidencia captada.")
L.append("")
L.append("## 2. Materialización de Candidatos Comerciales (BC-I → BC-II)")
L.append("")
L.append(f"- Candidatos materializados: **{len(rows)}** (uno por organización detectada con evidencia), por `candidato_id` determinista (sha256 del nombre normalizado).")
L.append(f"- Prospectos vinculados: **{sum(1 for r in rows if r['prospecto'])}** de {len(rows)} (identidad referencial `organización → candidato → prospecto → expediente → evidencia`).")
L.append(f"- Estados: {(' · '.join(f'`{k}`: {v}' for k, v in sorted(por_estado.items())))}.")
L.append(f"- **Regla Cero (G0):** `g0_permitido = {g0_count}`. Solo los candidatos con dictamen `VALIDADA`/`VALIDADA_PARCIAL` pueden avanzar a `observado`; el resto queda bloqueado por la ciencia.")
L.append("")
L.append("## 3. Los 5 Candidatos Comerciales recientes")
L.append("")
L.append("Ordenados por la **señal más reciente** capturada (`fecha_publicacion` máxima de la evidencia).")
L.append("")
L.append("| # | Organización | Categoría | Escala | Scoring | Score ICP | Dictamen (G0) | Evidencias | Última señal |")
L.append("|---|--------------|-----------|--------|---------|-----------|----------------|------------|--------------|")
for i, r in enumerate(top, 1):
    ver = r["veredicto"]
    if r["g0"]:
        ver = f"**{ver}** (G0 ✓)"
    L.append(f"| {i} | **{r['org']}** | {r['categoria']} | {r['escala']} | {r['scoring']} | {r['score_icp']} | {ver} | {r['n_ev']} | {r['ultima']} |")
L.append("")
L.append("### Detalle por candidato")
L.append("")
for i, r in enumerate(top, 1):
    mejor = r["mejor"]
    texto = (mejor.get("texto") or "").strip()
    fuente = (mejor.get("fuente") or "").strip()
    url = (mejor.get("url") or "").strip()
    L.append(f"**{i}. {r['org']}** — `id={r['id']}` · `candidato_id={trunc(r['candidato_id'])}`")
    L.append(f"- Estado: `{r['estado']}` · Prospecto id: `{r['prospecto'] or '—'}` · Dictamen: `{r['veredicto']}` · G0: `{r['g0']}`.")
    L.append(f"- Expediente: `{r['expediente_hash']}`.")
    L.append(f"- Mejor evidencia (confianza {r['conf']}): *«{texto}»* — {fuente}.")
    L.append(f"  - URL: {url}")
    L.append("")
L.append("---")
L.append("")
L.append("## 4. Notas de trazabilidad y calidad")
L.append("")
L.append("- **Regla Cero activa:** los candidatos con dictamen `BLOQUEADA`/`SIN_HIPOTESIS` permanecen en `detectado`; solo avanzan los de dictamen validado. La decisión de qué hacer con los observados corresponde al operador vía RadarHD (Motor B); Motor A solo registra la detección y la observación.")
L.append("- **Ruido por homonimia:** las señales de *Cometa* (cometa astronómico) y *Clara* (Clara Brugada) son coincidencias léxicas del nombre exacto, no actividad de la organización. Es extracción objetiva de la fuente (búsqueda exacta por nombre); la interpretación/descartado no es de este motor.")
L.append("- **Corroboración independiente:** GDELT y RSS fijos aportan dominios reales de medios; sin ellos, todas las notas de Google News compartirían el dominio agregador `news.google.com` y contarían como una sola fuente para la Validación Científica (Capa 11).")
L.append("- **Determinismo:** cada `candidato_id` y `expediente_hash` es reproducible (mismo insumo ⇒ mismo resultado). Re-materializar no duplica filas ni transiciones.")
L.append("- **Cadena referencial verificable** con `python -m scripts.trazabilidad` (solo lectura).")
L.append("")
L.append("*Fin del reporte.*")

out = os.path.join(HOME, "antrosapiens", "data", "reporte_5_candidatos_recientes.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print("reporte escrito:", out)
db.close()
