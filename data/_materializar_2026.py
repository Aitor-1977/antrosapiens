"""Materializa los Candidatos Comerciales tras la corrida run_once (2026-08-11).

Regla estricta de entorno: TMPDIR/TMP/TEMP → ~/antrosapiens/data/ y parche de
``tempfile`` en runtime (mismo contrato que ``_ingesta_run_once_2026.py``).

Construye los expedientes científicos de cada organización con evidencia
(Inferencia → Validación Científica → Gobernanza vía ``_paquete_cientifico``)
y materializa un Candidato Comercial por organización (UPSERT idempotente por
``candidato_id`` determinista).
"""
import os
import sys

_HOME = os.path.expanduser("~")
_PROJ = os.path.join(_HOME, "antrosapiens")
_TEMP_DIR = os.path.join(_PROJ, "data")
os.makedirs(_TEMP_DIR, exist_ok=True)
os.environ["TMPDIR"] = _TEMP_DIR
os.environ["TMP"] = _TEMP_DIR
os.environ["TEMP"] = _TEMP_DIR

import tempfile  # noqa: E402

tempfile.tempdir = _TEMP_DIR
try:
    tempfile._tempdir = _TEMP_DIR
except AttributeError:  # pragma: no cover
    pass

if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

from hd_scraper.api.app import _paquete_cientifico  # noqa: E402
from hd_scraper.candidato import materializar_candidatos  # noqa: E402
from hd_scraper.db.database import Database  # noqa: E402

db = Database()
db.init_schema()

filas = db.fetch_all(
    "SELECT DISTINCT empresa_mencionada FROM evidencias WHERE estado='ok' "
    "ORDER BY empresa_mencionada"
)
orgs = [r["empresa_mencionada"] for r in filas]
print(f"orgs con evidencia: {len(orgs)}")

exps = []
errores = []
for org in orgs:
    try:
        exp, val, huella = _paquete_cientifico(org)
        exp["validacion_cientifica"] = val["dictamen_cientifico"]
        exp["huella"] = huella["hash"]
        exps.append(exp)
    except Exception as e:  # noqa: BLE001 - nunca tumba la materialización
        errores.append((org, f"{type(e).__name__}: {e}"))

print(f"expedientes construidos: {len(exps)} | errores: {len(errores)}")
for org, err in errores:
    print(f"  ERR {org} {err}")

res = materializar_candidatos(db, exps)
print("RESULTADO:", {k: v for k, v in res.items() if k != "candidatos"})
db.close()
