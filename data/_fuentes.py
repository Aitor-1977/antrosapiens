import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import sqlite3, os.path
from urllib.parse import urlparse

HOME = os.path.expanduser("~")
db = os.path.join(HOME, "antrosapiens", "data", "hd_scraper.db")
con = sqlite3.connect(db)
cur = con.cursor()
print("== dominios de url_fuente")
for r in cur.execute("SELECT url_fuente, COUNT(*) c FROM evidencias GROUP BY url_fuente ORDER BY c DESC LIMIT 8").fetchall():
    d = urlparse(r[0]).netloc if r[0] else ""
    print(f"  {d:40s} {r[1]}")
print("== nombre_medio top")
for r in cur.execute("SELECT nombre_medio, COUNT(*) c FROM evidencias GROUP BY nombre_medio ORDER BY c DESC LIMIT 8").fetchall():
    print(f"  {str(r[0])[:50]:50s} {r[1]}")
print("== por empresa_mencionada (top 10)")
for r in cur.execute("SELECT empresa_mencionada, COUNT(*) c FROM evidencias GROUP BY empresa_mencionada ORDER BY c DESC LIMIT 10").fetchall():
    print(f"  {str(r[0])[:30]:30s} {r[1]}")
print("== connces: contar dominios distintos por empresa (muestra)")
for r in cur.execute("""
  SELECT empresa_mencionada, COUNT(DISTINCT substr(url_fuente, 1, 8)) d
  FROM evidencias GROUP BY empresa_mencionada LIMIT 5""").fetchall():
    print("  ", r)
con.close()
