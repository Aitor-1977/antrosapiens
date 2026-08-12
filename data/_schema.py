import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import sqlite3, os.path

HOME = os.path.expanduser("~")
db = os.path.join(HOME, "antrosapiens", "data", "hd_scraper.db")
con = sqlite3.connect(db)
cur = con.cursor()
print("== candidatos schema")
print(cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='candidatos'").fetchone()[0])
print()
print("== columnas candidatos")
cols = [r[1] for r in cur.execute("PRAGMA table_info(candidatos)").fetchall()]
print(cols)
print()
print("== filas candidatos (limit 3)")
for r in cur.execute("SELECT * FROM candidatos LIMIT 3").fetchall():
    print(r)
print()
print("== candidato_transiciones schema")
print(cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='candidato_transiciones'").fetchone()[0])
con.close()
