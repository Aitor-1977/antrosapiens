"""Puente JS ↔ Python para Android (Chaquopy).

El WebView de la app llama ``AntroBridge.call(method, argsJson, callbackId)``.
Kotlin invoca ``investigacion_bridge.dispatch(method, argsJson)`` y devuelve el
resultado JSON al JS. Reutiliza EXACTAMENTE el mismo motor que la API HTTP, de
modo que no hay lógica duplicada: una sola fuente de verdad.
"""
from __future__ import annotations

import json
import os

from .db.database import get_db
from . import investigacion as ENG


def init(db_path: str) -> str:
    """Configura la base offline-first local (ruta en almacenamiento interno).

    Se invoca una sola vez desde Android (Chaquopy) antes de cualquier ``dispatch``.
    Apunta el motor a un SQLite del dispositivo y desactiva la retención de crudo
    (el disco móvil es efímero respecto a la red).
    """
    from .config import settings
    os.environ.setdefault("HD_RAW_ENABLED", "0")
    try:
        object.__setattr__(settings, "database_url", f"sqlite:///{db_path}")
        object.__setattr__(settings, "raw_enabled", False)
    except Exception:
        pass
    return json.dumps({"ok": True})


def dispatch(method: str, args_json: str) -> str:
    """Ejecuta ``method`` con ``args_json`` y devuelve un JSON string.

    Siempre devuelve ``{"ok": bool, "data"|"error": ...}`` para que el JS lo
    maneje de forma uniforme.
    """
    try:
        args = json.loads(args_json or "{}")
        db = get_db()
        if method == "crear":
            inv_id = ENG.crear_investigacion(db, args["foco"], args["pregunta"], args.get("inv_id"))
            return _ok({"id": inv_id})
        if method == "pregunta":
            ENG.definir_pregunta(db, args["inv_id"], args["pregunta"])
            return _ok({"ok": True})
        if method == "capturar":
            resumen = ENG.capturar(
                db, args["inv_id"], args["consulta"], args["tipo_evento"],
                args["conectores"], slug=args.get("slug"), region=args.get("region"),
            )
            return _ok(resumen)
        if method == "listar":
            return _ok(ENG.listar_investigaciones(db))
        if method == "estado":
            return _ok(ENG.obtener_estado(db, args["inv_id"]))
        if method == "curar":
            return _ok(ENG.curar(db, args["inv_id"], int(args["senal_id"]),
                                 args["accion"], args.get("nota"), args.get("autor", "investigador")))
        if method == "relacionar":
            rid = ENG.relacionar(db, args["inv_id"], int(args["a"]), int(args["b"]),
                                 args["tipo"], args.get("nota"))
            return _ok({"id": rid})
        if method == "tension":
            tid = ENG.registrar_tension(db, args["inv_id"], int(args["a"]), int(args["b"]),
                                        args["explicacion"], args.get("estado", "abierta"),
                                        args.get("autor", "investigador"))
            return _ok({"id": tid})
        if method == "sugerir_tensiones":
            return _ok(ENG.sugerir_tensiones(db, args["inv_id"]))
        if method == "hipotesis":
            return _ok(ENG.generar_hipotesis(db, args["inv_id"], bool(args.get("usar_ia", False))))
        if method == "triangulacion":
            return _ok(ENG.triangulacion(db, args["inv_id"]))
        if method == "cerrar":
            return _ok(ENG.cerrar_peritaje(db, args["inv_id"], args.get("autor", "investigador")))
        return _err(f"método desconocido: {method}")
    except Exception as exc:  # nunca romper el puente: devolver el error al JS
        return _err(f"{type(exc).__name__}: {exc}")


def _ok(data) -> str:
    return json.dumps({"ok": True, "data": data}, ensure_ascii=False, default=str)


def _err(msg: str) -> str:
    return json.dumps({"ok": False, "error": msg}, ensure_ascii=False)
