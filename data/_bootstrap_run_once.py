import os, sys

sys.stdout = os.fdopen(os.dup(1), "w", encoding="utf-8", buffering=1)
sys.stderr = os.fdopen(os.dup(2), "w", encoding="utf-8", buffering=1)

HOME = os.path.expanduser("~")
sys.path.insert(0, os.path.join(HOME, "antrosapiens"))

import runpy

runpy.run_module("scripts.run_once", run_name="__main__")
