import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import sqlite3, os.path

HOME = os.path.expanduser("~")
db = os.path.join(HOME, "antrosapiens", "data", "hd_scraper.db")
con = sqlite3.connect(db)
cur = con.cursor()
for t in ["evidencias", "candidatos", "candidato_transiciones", "prospectos"]:
    n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(t, n)
print()
print("candidatos por estado:", cur.execute("SELECT estado, COUNT(*) FROM candidatos GROUP BY estado").fetchall())
print("por g0_permitido:", cur.execute("SELECT g0_permitido, COUNT(*) FROM candidatos GROUP BY g0_permitido").fetchall())
print("por veredicto:", cur.execute("SELECT veredicto, COUNT(*) FROM candidatos GROUP BY veredicto").fetchall())
print("por conector:", cur.execute("SELECT conector, COUNT(*) FROM evidencias GROUP BY conector").fetchall())
print("por tipo_evento:", cur.execute("SELECT tipo_evento, COUNT(*) FROM evidencias GROUP BY tipo_evento").fetchall())
print("evidencias por fecha_publicacion (top 5):", cur.execute("SELECT fecha_publicacion, COUNT(*) FROM evidencias GROUP BY fecha_publicacion ORDER BY fecha_publicacion DESC LIMIT 5").fetchall())
con.close()
