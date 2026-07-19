"""Esquemas de datos de la Capa 0 (señales de Deuda observadas).

Una SeñalCapa0 es un HECHO observado en una fuente (texto/transcripción de video):
un fragmento literal que hizo match con una regla determinista, con su tipo, su
peso y un motivo auditable. Un Prospecto agrupa las señales de una organización y
su nivel de alerta. Capa 0 SOLO observa y registra; no interpreta cualitativamente
(eso es del Motor B), solo puntúa por reglas transparentes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class SeñalCapa0(BaseModel):
    id: str
    url: str
    timestamp_video: Optional[str] = None
    fragmento_literal: str
    tipo_señal: str            # Operativa | Discursiva | Rescate
    score_deuda: float
    motivo_match: str          # log de auditoría (por qué hizo match)
    creado_en: datetime = Field(default_factory=_ahora)


class Prospecto(BaseModel):
    id: str
    nombre_organizacion: str
    señales: List[SeñalCapa0]
    score_total: float
    nivel_alerta: str          # Normal | Crítica
