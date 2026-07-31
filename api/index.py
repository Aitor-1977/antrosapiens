"""Entrypoint serverless de Vercel.

Vercel usa el runtime @vercel/python y busca la variable ``app`` (ASGI) en este
archivo. Reexportamos la app FastAPI de solo lectura.

Nota importante: en Vercel solo corre la API de LECTURA. El scraper (scheduler
cada 12 h + escritura en la base) NO puede correr en serverless: no hay proceso
de larga vida y el disco es efímero. Ver README ("Despliegue") para el plan de
extracción en un host always-on + base persistente.
"""
import sys
from pathlib import Path

# Asegura que el paquete hd_scraper (en la raíz del repo) sea importable.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hd_scraper.api.app import app as _app  # noqa: E402

# ── Normalización de ruta para el rewrite de Vercel ─────────────────────────
# vercel.json reescribe `/(.*)` -> `/api/index`. Según la configuración, el
# runtime puede entregarle a la app ASGI la ruta ORIGINAL (correcto) o la ruta
# de DESTINO (`/api/index[...]`). En el segundo caso FastAPI no encuentra ruta y
# responde `{"detail":"Not Found"}` para TODO. Este envoltorio quita ese prefijo
# si aparece, dejando la ruta real (`/prospectos`, `/health`, `/` …). Es inocuo
# cuando la ruta ya llega bien (no empieza por `/api/index`).
_PREFIJO = "/api/index"


async def app(scope, receive, send):  # noqa: D401 - envoltorio ASGI
    if scope.get("type") in ("http", "websocket"):
        ruta = scope.get("path", "") or ""
        if ruta == _PREFIJO or ruta.startswith(_PREFIJO + "/"):
            nueva = ruta[len(_PREFIJO):] or "/"
            scope = {**scope, "path": nueva, "raw_path": nueva.encode("utf-8")}
    await _app(scope, receive, send)


# Vercel toma esta variable como la aplicación ASGI a servir.
__all__ = ["app"]
