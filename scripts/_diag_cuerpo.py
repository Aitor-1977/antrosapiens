"""Diagnóstico comparativo (seco, sin escritura):

Para una muestra de 50 evidencias de google_news que YA tienen
`cuerpo_completo`, clasifica cada una DOS veces con el clasificador real
(hd_scraper.clasificacion_epistemologica.clasificar, sin modificar):

  A) solo titular   -> cita_textual = titular (lo que tenemos hoy)
  B) con cuerpo     -> cita_textual = cuerpo_completo (la nueva materia prima)

Y compara la distribución de `tipo_epistemologico`.

NO escribe ninguna clasificación en la base. Solo diagnóstico.
"""
from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hd_scraper.clasificacion_epistemologica import clasificar
from hd_scraper.db.database import get_db
from hd_scraper.clasificacion_store import orgs_conocidas

# Ruta absoluta y dependiente del script: no importa el cwd desde el que se
# ejecute. Antes era "data/hd_scraper.db" relativo y, al correrlo desde otro
# directorio, sqlite3.connect creaba un archivo vacío sin la tabla `evidencias`,
# el SELECT lanzaba OperationalError y el script no imprimía nada.
DB = str(ROOT / "data" / "hd_scraper.db")
TIPOS = [
    "senal_primaria_autodeclaracion",
    "senal_primaria_huella_practica",
    "corroborante",
    "contextual",
]

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()
cur.execute(
    "SELECT id, cita_textual, empresa_mencionada, nombre_medio, "
    "origen_declaracion, persona_citada, cargo, cuerpo_completo "
    "FROM evidencias "
    "WHERE connector='google_news' AND cuerpo_completo IS NOT NULL "
    "ORDER BY id LIMIT 50"
)
rows = cur.fetchall()
con.close()

db = get_db()
orgs = orgs_conocidas(db)

countA, countB = Counter(), Counter()
cambios = Counter()
flip_ejemplos = []

for r in rows:
    base = dict(
        empresa_mencionada=r["empresa_mencionada"],
        nombre_medio=r["nombre_medio"],
        origen_declaracion=r["origen_declaracion"],
        persona_citada=r["persona_citada"],
        cargo=r["cargo"],
    )
    evA = dict(base)
    evA["cita_textual"] = r["cita_textual"] or ""
    evB = dict(base)
    evB["cita_textual"] = r["cuerpo_completo"] or ""
    tA = clasificar(evA, orgs).tipo
    tB = clasificar(evB, orgs).tipo
    countA[tA] += 1
    countB[tB] += 1
    cambios[(tA, tB)] += 1
    if tA != tB:
        flip_ejemplos.append((r["id"], tA, tB))

n = len(rows)
print(f"Muestra: {n} evidencias google_news con cuerpo_completo\n")
print(f"{'tipo_epistemologico':34} | solo_titular | con_cuerpo_completo")
print("-" * 72)
for t in TIPOS:
    a, b = countA[t], countB[t]
    print(f"{t:34} | {a:>4} ({a*100/n:4.1f}%) | {b:>4} ({b*100/n:4.1f}%)")
print("-" * 72)
print(f"{'TOTAL':34} | {n:>4}        | {n:>4}")
print()
print("Transiciones (titular -> cuerpo):")
for (a, b), c in cambios.most_common():
    print(f"  {a} -> {b}: {c}")
print()
print(f"Filas que CAMBIARON de tipo: {len(flip_ejemplos)} / {n} "
      f"({len(flip_ejemplos)*100/n:.1f}%)")
print("Ejemplos de cambio (id, antes, despues):")
for e in flip_ejemplos[:15]:
    print(f"  {e}")
