"""Logging para Vercel: JSON a stdout, con request_id por petición.

Vercel captura stdout/stderr de la función y los muestra en su panel de
"Logs" — no hay archivo de log persistente en serverless (el disco es
efímero), así que emitir a stdout en un formato parseable (JSON, una línea
por evento) es lo único que sirve ahí. Mismo criterio que ya usa
`pipeline._log_evento` para SCRAPER_START/PROGRESS/END/ERROR.

`request_id` identifica todas las líneas de log de UNA petición HTTP. Se
usa el propio ``x-vercel-id`` que Vercel ya pone en la respuesta cuando
existe (así el id del log coincide con el que ves en el panel de Vercel);
si no está (desarrollo local), se genera un UUID.
"""
from __future__ import annotations

import contextvars
import json
import logging
import sys
import uuid

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


def nuevo_request_id(id_externo: str | None = None) -> str:
    """Fija el request_id para el resto de logs de esta petición y lo
    devuelve. ``id_externo`` es el ``x-vercel-id`` de la petición, si Vercel
    ya lo mandó; si no, se genera uno nuevo."""
    rid = id_externo or uuid.uuid4().hex[:16]
    _request_id_var.set(rid)
    return rid


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "nivel": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "mensaje": record.getMessage(),
        }
        if record.exc_info:
            base["excepcion"] = self.formatException(record.exc_info)
        # Si el mensaje ya es un JSON de una línea (p. ej. SCRAPER_START de
        # pipeline._log_evento), se incrusta como objeto en vez de como texto
        # escapado, para que quede plano y fácil de filtrar en el panel de Vercel.
        try:
            parsed = json.loads(record.getMessage())
            if isinstance(parsed, dict):
                base["mensaje"] = parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return json.dumps(base, ensure_ascii=False, default=str)


def configure_logging(nivel: int = logging.INFO) -> None:
    """Configura el logger raíz UNA vez por proceso: stdout, JSON, con
    request_id. Reentrante: si ya se configuró (mismo proceso/cold start),
    no duplica handlers."""
    root = logging.getLogger()
    ya_configurado = any(isinstance(h, logging.StreamHandler)
                         and isinstance(getattr(h, "formatter", None), _JsonFormatter)
                         for h in root.handlers)
    if ya_configurado:
        root.setLevel(nivel)
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(_JsonFormatter())
    handler.addFilter(_RequestIdFilter())
    root.handlers = [handler]
    root.setLevel(nivel)
