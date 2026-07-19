"""Motor de filtro y scoring de la Capa 0 — 100% determinista y auditable.

Evalúa un texto (titular, descripción o transcripción de video) contra reglas
booleanas por tipo de señal y asigna un peso. No usa IA: cada match es una cadena
fija comprobable, con un motivo de auditoría en el log. El motor está DESACOPLADO
de la API y de la persistencia (recibe texto, devuelve señales).

Mejoras sobre el esqueleto:
  - id DETERMINISTA (sha1 de url|tipo|kw), no ``hash()`` (que varía por proceso).
  - sin señales duplicadas para el mismo (tipo, keyword).
  - reglas y pesos configurables por el constructor (separados de la lógica).
"""
from __future__ import annotations

import hashlib
import logging
from typing import Optional

from .schemas import SeñalCapa0

logger = logging.getLogger("hd_scraper.rule_engine")

# Reglas booleanas por tipo de señal (vocabulario declarado del laboratorio).
REGLAS_DEFAULT: dict[str, list[str]] = {
    "Operativa": ["vacante senior", "growth", "retention", "head of"],
    "Discursiva": ["educar al mercado", "evangelizar", "tropicalizar"],
    "Rescate": ["bridge round", "expansión lenta", "pivote estético", "down round"],
    # Evento observable en PRENSA (titulares): disparadores de negocio. Señal más
    # débil que el lenguaje de founder, pero es lo que aparece en las noticias, así
    # que "Ingerir noticias" deja de dar 0 resultados.
    "Evento": [
        "ronda de inversión", "ronda de inversion", "levanta capital", "recauda",
        "serie a", "serie b", "serie c", "financiamiento", "capital semilla",
        "despidos", "despido masivo", "recorte de personal", "layoffs",
        "reestructura", "reestructuración", "reestructuracion",
        "pivote", "pivota", "cambia de modelo", "relanza",
        "adquisición", "adquisicion", "adquiere", "fusión", "fusion", "se fusiona",
        "cierre de operaciones", "cierra operaciones", "quiebra", "cesa operaciones",
        "churn", "cancelaciones", "fuga de usuarios", "pérdida de clientes",
        "demanda colectiva", "expansión", "nuevos mercados", "nuevo ceo", "nuevo cto",
    ],
}

# Pesos para el scoring (a mayor peso, mayor evidencia de Deuda).
PESOS_DEFAULT: dict[str, float] = {
    "Operativa": 1.5, "Discursiva": 2.0, "Rescate": 3.0, "Evento": 1.0,
}

UMBRAL_CRITICO_DEFAULT = 5.0

ALERTA_CRITICA = "Crítica"
ALERTA_NORMAL = "Normal"


class RuleEngine:
    def __init__(
        self,
        reglas: Optional[dict[str, list[str]]] = None,
        pesos: Optional[dict[str, float]] = None,
        umbral_critico: float = UMBRAL_CRITICO_DEFAULT,
    ) -> None:
        self.reglas = reglas or {k: list(v) for k, v in REGLAS_DEFAULT.items()}
        self.pesos = pesos or dict(PESOS_DEFAULT)
        self.umbral_critico = umbral_critico

    @staticmethod
    def _id(url: str, tipo: str, kw: str) -> str:
        return hashlib.sha1(f"{url}|{tipo}|{kw}".encode("utf-8")).hexdigest()[:16]

    def evaluar(self, texto_limpio: str, url: str, timestamp: str | None = None) -> list[SeñalCapa0]:
        """Devuelve las señales (SeñalCapa0) que dispara el texto. Determinista."""
        señales: list[SeñalCapa0] = []
        texto_lower = (texto_limpio or "").lower()
        vistos: set[tuple[str, str]] = set()
        for tipo, keywords in self.reglas.items():
            peso = self.pesos.get(tipo, 0.0)
            for kw in keywords:
                if kw in texto_lower and (tipo, kw) not in vistos:
                    vistos.add((tipo, kw))
                    motivo = f"Match determinista: '{kw}' en '{tipo}'"
                    logger.info("AUDITORÍA | %s | URL: %s | TS: %s", motivo, url, timestamp)
                    señales.append(SeñalCapa0(
                        id=self._id(url, tipo, kw),
                        url=url,
                        timestamp_video=timestamp,
                        fragmento_literal=(texto_limpio or "")[:200],  # trunca para almacenamiento
                        tipo_señal=tipo,
                        score_deuda=peso,
                        motivo_match=motivo,
                    ))
        return señales

    def calcular_alerta(self, señales: list[SeñalCapa0]) -> tuple[float, str]:
        """Suma de pesos y nivel de alerta (Crítica si alcanza el umbral)."""
        score_total = round(sum(s.score_deuda for s in señales), 2)
        alerta = ALERTA_CRITICA if score_total >= self.umbral_critico else ALERTA_NORMAL
        return score_total, alerta
