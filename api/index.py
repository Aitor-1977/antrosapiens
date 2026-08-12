"""Entrypoint serverless de Vercel.

Vercel usa el runtime @vercel/python y busca la variable ``app`` (ASGI) en este
archivo. Reexportamos la app FastAPI de solo lectura.

Nota importante: en Vercel solo corre la API de LECTURA. El scraper (scheduler
cada 12 h + escritura en la base) NO puede correr en serverless: no hay proceso
de larga vida y el disco es efímero. Ver README ("Despliegue") para el plan de
extracción en un host always-on + base persistente.
"""
import mimetypes
import sys
from pathlib import Path

# Asegura que el paquete hd_scraper (en la raíz del repo) sea importable.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hd_scraper.api.app import app as _app  # noqa: E402

# ── Instrumentos de campo (assets de la app) ─────────────────────────────────
# Los instrumentos HTML de la raíz del repo se sincronizan aquí (script
# `scripts/sync_instrumentos.py`) y viajan dentro del bundle de la función
# serverless (`vercel.json` → `includeFiles: hd_scraper/**`). Se sirven con
# `Cache-Control: no-store` para que la edición de un instrumento se refleje en
# producción inmediatamente tras el deploy, sin cachés intermedias que sirvan
# una versión vieja. Capa aditiva: no toca la arquitectura de la API.
_INSTRUMENTOS = ROOT / "hd_scraper" / "api" / "static" / "instrumentos"
_NO_CACHE = [
    (b"cache-control", b"no-cache, no-store, must-revalidate"),
    (b"pragma", b"no-cache"),
    (b"expires", b"0"),
]


async def _respuesta(send, status, cuerpo, tipo="text/plain; charset=utf-8"):
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            (b"content-type", tipo.encode("latin-1")),
            (b"content-length", str(len(cuerpo)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": cuerpo})


async def _servir_instrumentos(send, ruta) -> bool:
    """Sirve `/instrumentos` y `/instrumentos/{nombre}` sin caché. Solo lectura."""
    if ruta == "/instrumentos":
        nombres = sorted(p.name for p in _INSTRUMENTOS.glob("*.html"))
        enlaces = "".join(
            f'<li><a href="/instrumentos/{n}">{n}</a></li>' for n in nombres)
        html = (
            "<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>Instrumentos de campo</title></head><body><h1>"
            "Instrumentos de campo</h1><ul>" + enlaces + "</ul></body></html>"
        )
        await _respuesta(send, 200, html.encode("utf-8"), "text/html; charset=utf-8")
        return True
    if ruta.startswith("/instrumentos/"):
        nombre = ruta[len("/instrumentos/"):]
        if "/" in nombre or ".." in nombre or not nombre.endswith(".html"):
            await _respuesta(send, 404, b'{"detail":"Not Found"}')
            return True
        archivo = (_INSTRUMENTOS / nombre).resolve()
        if archivo.parent != _INSTRUMENTOS.resolve() or not archivo.is_file():
            await _respuesta(send, 404, b'{"detail":"Not Found"}')
            return True
        tipo, _ = mimetypes.guess_type(nombre)
        cuerpo = archivo.read_bytes()
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", (tipo or "text/html").encode("latin-1")),
                (b"content-length", str(len(cuerpo)).encode()),
                *_NO_CACHE,
            ],
        })
        await send({"type": "http.response.body", "body": cuerpo})
        return True
    return False

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
            ruta = nueva
    if scope.get("type") == "http" and ruta.startswith("/instrumentos"):
        if await _servir_instrumentos(send, ruta):
            return
    await _app(scope, receive, send)


# Vercel toma esta variable como la aplicación ASGI a servir.
__all__ = ["app"]
