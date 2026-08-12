import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import os.path, sys as _sys

HOME = os.path.expanduser("~")
proj = os.path.join(HOME, "antrosapiens")
_sys.path.insert(0, proj)

from hd_scraper.api.app import _paquete_cientifico
from hd_scraper.candidato import g0_permitido

for org in ["Nubank", "Rappi", "Clara", "Mercado Libre", "Cobre", "Cometa"]:
    try:
        exp, val, huella = _paquete_cientifico(org)
        dic = val.get("dictamen_cientifico") or val
        ver = (dic or {}).get("veredicto", "")
        g0 = g0_permitido(exp)
        n_hip = len(exp.get("hipotesis") or [])
        n_ev = len(exp.get("evidencias") or [])
        fuentes = sorted({e.get("nombre_medio") or e.get("conector") or "" for e in (exp.get("evidencias") or [])})
        print(f"{org:15s} veredicto={ver:20s} hipotesis={n_hip} evidencias={n_ev} g0.permitido={g0['permitido']} fuentes={fuentes}")
    except Exception as e:
        print(f"{org:15s} ERR {type(e).__name__}: {e}")
