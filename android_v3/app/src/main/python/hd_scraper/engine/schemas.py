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

    def to_json_dict(self) -> dict:
        return {
            'id': self.id,
            'url': self.url,
            'timestamp_video': self.timestamp_video,
            'fragmento_literal': self.fragmento_literal,
            'tipo_señal': self.tipo_señal,
            'score_deuda': self.score_deuda,
            'motivo_match': self.motivo_match,
            'creado_en': self.creado_en.isoformat() if self.creado_en else None,
        }


class Prospecto(BaseModel):
    id: str
    nombre_organizacion: str
    señales: List[SeñalCapa0]
    score_total: float
    nivel_alerta: str          # Normal | Crítica
