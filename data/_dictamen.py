import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import sqlite3, os.path

HOME = os.path.expanduser("~")
db = os.path.join(HOME, "antrosapiens", "data", "hd_scraper.db")
con = sqlite3.connect(db)
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print("TABLES:", tables)
print()
# find columns named veredicto or dictamen
for t in tables:
    cols = [r[1] for r in cur.execute(f"PRAGMA table_info({t})").fetchall()]
    hits = [c for c in cols if 'vered' in c.lower() or 'dictamen' in c.lower() or 'validacion' in c.lower()]
    if hits:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: cols={cols}")
        print(f"  count={n}, hits={hits}")
con.close()
