"""Bootstrap de la corrida run_once (2026-08-11).

Regla estricta de entorno: prohibido /tmp/ y no se piden permisos externos.
Se sobrescribe TMPDIR/TMP/TEMP a ~/antrosapiens/data/ ANTES de importar
hd_scraper y se aplica un parche en tiempo de ejecución sobre ``tempfile``
(tempfile.tempdir / tempfile._tempdir) para que cualquier lectura de
``gettempdir()`` resuelva dentro del proyecto.
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
except AttributeError:  # pragma: no cover - variantes de la stdlib
    pass

if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

import runpy  # noqa: E402

runpy.run_module("scripts.run_once", run_name="__main__")
