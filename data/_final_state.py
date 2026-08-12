import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import sqlite3, os.path

HOME = os.path.expanduser("~")
db = os.path.join(HOME, "antrosapiens", "data", "hd_scraper.db")
con = sqlite3.connect(db)
cur = con.cursor()
print("evidencias:", cur.execute("SELECT COUNT(*) FROM evidencias WHERE estado='ok'").fetchone()[0])
print("por conector:", cur.execute("SELECT connector, COUNT(*) FROM evidencias WHERE estado='ok' GROUP BY connector").fetchall())
print()
print("candidatos por estado:")
for r in cur.execute("SELECT estado, COUNT(*) FROM candidatos GROUP BY estado").fetchall():
    print("  ", r)
print()
print("candidatos observados:")
for r in cur.execute("SELECT org_nombre FROM candidatos WHERE estado='observado' ORDER BY org_nombre").fetchall():
    print("  ", r[0])
print()
print("transiciones por estado_hasta:")
for r in cur.execute("SELECT estado_hasta, COUNT(*) FROM candidato_transiciones GROUP BY estado_hasta").fetchall():
    print("  ", r)
con.close()
