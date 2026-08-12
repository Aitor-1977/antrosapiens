import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import sqlite3, os.path
from urllib.parse import urlparse

HOME = os.path.expanduser("~")
db = os.path.join(HOME, "antrosapiens", "data", "hd_scraper.db")
con = sqlite3.connect(db)
cur = con.cursor()

def dominio(u):
    try:
        return urlparse(u if "://" in u else "http://" + u).netloc.lower().replace("www.", "")
    except Exception:
        return ""

print("evidencias totales:", cur.execute("SELECT COUNT(*) FROM evidencias").fetchone()[0])
print("por conector:", cur.execute("SELECT connector, COUNT(*) FROM evidencias GROUP BY connector").fetchall())

print()
print("== orgs con >=2 fuentes independientes (por dominio real):")
rows = cur.execute("""
    SELECT empresa_mencionada, COUNT(*) n, COUNT(DISTINCT url_fuente) u, COUNT(DISTINCT connector) c
    FROM evidencias WHERE estado='ok' GROUP BY empresa_mencionada
""").fetchall()
multi = [r for r in rows if r[2] >= 2]
print(f"total orgs con evidencia: {len(rows)}, con >=2 URL distintas: {len(multi)}")
for r in rows:
    doms = set()
    for (u,) in cur.execute("SELECT url_fuente FROM evidencias WHERE empresa_mencionada=? AND estado='ok'", (r[0],)).fetchall():
        doms.add(dominio(u))
    if len(doms) >= 2:
        print(f"  {r[0]:25s} n={r[1]:3d} dominios={len(doms)} conns={r[3]} doms={sorted(doms)[:4]}")
con.close()
