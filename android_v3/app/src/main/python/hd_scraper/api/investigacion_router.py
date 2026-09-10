"""Router FastAPI del flujo de investigación + bootstrap de servidor.

Expone los endpoints del motor real de investigación. Se incluye en la API
existente (``hd_scraper.api.app``) para reutilizar el backend, y también puede
servir la UI de escritorio para pruebas. El puente JS de Android
(``investigacion_bridge``) llama a las MISMAS funciones del motor.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..db.database import get_db
from .. import investigacion as ENG

router = APIRouter(prefix="/investigacion", tags=["investigacion"])

# Ruta de la UI (V4) servida por el servidor de escritorio. En Android la UI se
# carga vía file:// y no necesita este route.
UI_DIR = Path(__file__).resolve().parent.parent.parent / "android" / "app" / "src" / "main" / "assets" / "public"


# --- Modelos -----------------------------------------------------------
class CrearIn(BaseModel):
    foco: str
    pregunta: str
    inv_id: Optional[str] = None


class PreguntaIn(BaseModel):
    inv_id: str
    pregunta: str


class CapturarIn(BaseModel):
    inv_id: str
    consulta: str
    tipo_evento: str
    conectores: list[str]
    slug: Optional[str] = None
    region: Optional[str] = None


class CurarIn(BaseModel):
    inv_id: str
    senal_id: int
    accion: str
    nota: Optional[str] = None
    autor: str = "investigador"


class RelacionarIn(BaseModel):
    inv_id: str
    a: int
    b: int
    tipo: str
    nota: Optional[str] = None


class TensionIn(BaseModel):
    inv_id: str
    a: int
    b: int
    explicacion: str
    estado: str = "abierta"
    autor: str = "investigador"


class HipotesisIn(BaseModel):
    inv_id: str
    usar_ia: bool = False


class CerrarIn(BaseModel):
    inv_id: str
    autor: str = "investigador"


# --- Endpoints ----------------------------------------------------------
@router.post("/crear")
def api_crear(p: CrearIn) -> dict:
    db = get_db()
    inv_id = ENG.crear_investigacion(db, p.foco, p.pregunta, p.inv_id)
    return {"id": inv_id}


@router.post("/pregunta")
def api_pregunta(p: PreguntaIn) -> dict:
    ENG.definir_pregunta(get_db(), p.inv_id, p.pregunta)
    return {"ok": True}


@router.post("/capturar")
def api_capturar(p: CapturarIn) -> dict:
    db = get_db()
    resumen = ENG.capturar(
        db, p.inv_id, p.consulta, p.tipo_evento, p.conectores,
        slug=p.slug, region=p.region,
    )
    return resumen


@router.get("/")
def api_listar() -> list[dict]:
    return ENG.listar_investigaciones(get_db())


@router.get("/{inv_id}")
def api_estado(inv_id: str) -> dict:
    return ENG.obtener_estado(get_db(), inv_id)


@router.post("/curar")
def api_curar(p: CurarIn) -> dict:
    return ENG.curar(get_db(), p.inv_id, p.senal_id, p.accion, p.nota, p.autor)


@router.post("/relacionar")
def api_relacionar(p: RelacionarIn) -> dict:
    rid = ENG.relacionar(get_db(), p.inv_id, p.a, p.b, p.tipo, p.nota)
    return {"id": rid}


@router.post("/tension")
def api_tension(p: TensionIn) -> dict:
    tid = ENG.registrar_tension(get_db(), p.inv_id, p.a, p.b, p.explicacion, p.estado, p.autor)
    return {"id": tid}


@router.get("/{inv_id}/tensiones/sugerir")
def api_sugerir(inv_id: str) -> list[dict]:
    return ENG.sugerir_tensiones(get_db(), inv_id)


@router.post("/hipotesis")
def api_hipotesis(p: HipotesisIn) -> list[dict]:
    return ENG.generar_hipotesis(get_db(), p.inv_id, p.usar_ia)


@router.get("/{inv_id}/triangulacion")
def api_triang(inv_id: str) -> dict:
    return ENG.triangulacion(get_db(), inv_id)


@router.post("/cerrar")
def api_cerrar(p: CerrarIn) -> dict:
    return ENG.cerrar_peritaje(get_db(), p.inv_id, p.autor)


# --- Servidor de escritorio (pruebas de la UI vía HTTP) -----------------
def servir_ui() -> str:
    html = (UI_DIR / "app.html").read_text(encoding="utf-8")
    return html


def build_app():
    """Construye la app de escritorio = API existente + router + UI."""
    from ..api.app import app  # importa la API real (reutiliza motores)
    app.include_router(router)

    @app.get("/app", response_class=HTMLResponse)
    def _app_ui() -> HTMLResponse:
        return HTMLResponse(servir_ui())

    return app
