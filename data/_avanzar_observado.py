import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import os.path, sys as _sys

HOME = os.path.expanduser("~")
proj = os.path.join(HOME, "antrosapiens")
_sys.path.insert(0, proj)

from hd_scraper.api.app import _paquete_cientifico
from hd_scraper.db.database import Database
from hd_scraper.candidato import observar, G0Denied

db = Database()
db.init_schema()

filas = db.fetch_all(
    "SELECT DISTINCT empresa_mencionada FROM evidencias WHERE estado='ok' ORDER BY empresa_mencionada"
)
orgs = [r["empresa_mencionada"] for r in filas]

avanzados, denegados, errores = [], [], []
for org in orgs:
    try:
        exp, val, huella = _paquete_cientifico(org)
        exp["validacion_cientifica"] = val["dictamen_cientifico"]
        exp["huella"] = huella["hash"]
        estado = db.fetch_one(
            "SELECT estado FROM candidatos WHERE org_nombre = ?", (org.strip(),))
        if not estado or estado["estado"] != "detectado":
            continue
        res = observar(db, org, exp=exp)
        avanzados.append((org, res.get("estado")))
    except G0Denied:
        denegados.append(org)
    except Exception as e:
        errores.append((org, f"{type(e).__name__}: {e}"))

print("avanzados a observado:", len(avanzados))
for org, st in avanzados:
    print("  ", org, st)
print("denegados por G0:", len(denegados))
print("errores:", len(errores))
for org, err in errores:
    print("  ERR", org, err)
db.close()
