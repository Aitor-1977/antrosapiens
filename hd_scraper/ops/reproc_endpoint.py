from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter(prefix="/ops", tags=["ops"])

class ReproRequest(BaseModel):
    dry_run: bool = True

@router.post("/reproc-4bf45f8085f14016e440d7845b67dd0d")
async def repro_evidencias(req: ReproRequest, auth: str = Depends(lambda: os.getenv("HD_INGEST_TOKEN"))):
    if auth != os.getenv("HD_INGEST_TOKEN"):
        raise HTTPException(401, "Token inválido")
    
    # Aquí iría la lógica de reprocesamiento
    return {"status": "ok", "dry_run": req.dry_run, "message": "Endpoint temporal funcionando"}