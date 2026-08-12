import os, sys
sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

import os.path, sys as _sys

HOME = os.path.expanduser("~")
proj = os.path.join(HOME, "antrosapiens")
_sys.path.insert(0, proj)

from hd_scraper.api.app import _paquete_cientifico
from hd_scraper.candidato import g0_permitido

for org in ["Nubank", "Rappi", "Clara", "Mercado Libre", "Cobre", "Cometa",
            "Endeavor", "Mundi", "Ualá", "500 Global LATAM"]:
    try:
        exp, val, huella = _paquete_cientifico(org)
        exp["validacion_cientifica"] = val["dictamen_cientifico"]
        exp["huella"] = huella["hash"]
        dic = val["dictamen_cientifico"]
        ver = dic.get("veredicto", "")
        g0 = g0_permitido(exp)
        n_ev = len(exp.get("evidencias") or [])
        print(f"{org:18s} veredicto={ver:18s} ev={n_ev:3d} bloqueada={dic.get('hipotesis_bloqueada')} g0={g0['permitido']}")
    except Exception as e:
        print(f"{org:18s} ERR {type(e).__name__}: {e}")
