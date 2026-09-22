"""Ficha de Prospección HD (Capa 20).

Autorizado por el operador —Mario— el 2026-09-22 (ver CLAUDE.md → «Frontera
de Interpretación»). La unidad de salida de AntroLabsHD deja de ser "un
documento clasificado" y pasa a ser una FICHA: organización, situación
observable, evidencia textual grounded, fuente(s), fecha(s), persona/cargo,
tipo epistemológico, origen, corroboración, recurrencia, contexto
organizacional, estado de evaluación y `fit_comercial` (score_icp) como
campo separado y aditivo, nunca como filtro.

REGLA DURA propia de esta capa: **si no existe una situación observable, no
hay ficha de prospección.** Puede existir evidencia clasificada (huella
práctica genérica, corroborante, contextual) y aun así no pasar a
prospección — se conserva en la base como evidencia secundaria, pero nunca
genera ficha.

Función pura: no toca la base de datos, no decide acción comercial, NUNCA
nombra Deuda Cultural™. Determinista: mismo insumo ⇒ misma(s) ficha(s).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .clasificacion_epistemologica import _fragmento_alrededor
from .estado_evidencia import estado_de
from .situacion_observable import Situacion, TIPO_SITUACION_UTIL, clasificar_situacion

# Margen (caracteres) alrededor del marcador para el fragmento grounded de
# "qué está ocurriendo". Mayor que el de `clasificacion_epistemologica`
# (pensado para nombres propios cortos) porque aquí el fragmento debe
# transmitir contexto de negocio legible por un humano en segundos.
MARGEN_FRAGMENTO_FICHA = 160

# Longitud máxima de la evidencia textual completa citada en la ficha.
MAX_EVIDENCIA_TEXTUAL = 600


@dataclass(frozen=True)
class FichaProspeccion:
    organizacion: str
    situacion_observable: str
    que_esta_ocurriendo: str
    evidencia_textual: str
    fuentes: list[str]
    fechas: list[str]
    persona_cargo: str | None
    tipo_epistemologico: str
    origen_declaracion: str
    corroboracion: str
    recurrencia: int
    contexto_organizacional: str
    estado_evaluacion: str
    fit_comercial: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "organizacion": self.organizacion,
            "situacion_observable": self.situacion_observable,
            "que_esta_ocurriendo": self.que_esta_ocurriendo,
            "evidencia_textual": self.evidencia_textual,
            "fuentes": self.fuentes,
            "fechas": self.fechas,
            "persona_cargo": self.persona_cargo,
            "tipo_epistemologico": self.tipo_epistemologico,
            "origen_declaracion": self.origen_declaracion,
            "corroboracion": self.corroboracion,
            "recurrencia": self.recurrencia,
            "contexto_organizacional": self.contexto_organizacional,
            "estado_evaluacion": self.estado_evaluacion,
            "fit_comercial": self.fit_comercial,
        }


def _persona_cargo(fila: dict) -> str | None:
    persona = (fila.get("enunciador_nombre") or fila.get("persona_citada") or "").strip()
    cargo = (fila.get("enunciador_cargo") or fila.get("cargo") or "").strip()
    if persona and cargo:
        return f"{persona}, {cargo}"
    return persona or cargo or None


def _fragmento(cita: str, marcador: str) -> str:
    pos = cita.lower().find(marcador)
    if pos < 0:
        return cita[:MAX_EVIDENCIA_TEXTUAL]
    return _fragmento_alrededor(cita, pos, pos + len(marcador), MARGEN_FRAGMENTO_FICHA)


def generar_fichas(
    organizacion: str,
    filas: list[dict],
    *,
    contexto_organizacional: str = "",
    score_icp: float | None = None,
) -> list[FichaProspeccion]:
    """Genera las fichas de una organización a partir de evidencia YA
    clasificada epistemológicamente. Función pura: no toca la base.

    ``filas`` es una lista de dicts, cada uno la unión de una fila de
    `evidencias` con su fila de `evidencia_clasificada` (``cita_textual``,
    ``url_fuente``, ``nombre_medio``, ``fecha_publicacion``,
    ``persona_citada``, ``cargo``, ``origen_declaracion``,
    ``tipo_epistemologico``, ``enunciador_nombre``, ``enunciador_cargo``).

    Agrupa por marcador de situación: documentos distintos que describen la
    MISMA situación (mismo marcador) producen UNA sola ficha, con
    ``recurrencia`` = número de documentos — nunca una ficha por documento
    (ver CLAUDE.md, "no sobregenerar resultados").
    """
    grupos: dict[str, list[dict]] = {}
    situaciones: dict[str, Situacion] = {}
    for fila in filas:
        s = clasificar_situacion(fila)
        if s.tipo != TIPO_SITUACION_UTIL:
            continue
        grupos.setdefault(s.marcador, []).append(fila)
        situaciones[s.marcador] = s

    fichas: list[FichaProspeccion] = []
    for marcador in sorted(grupos):
        grupo = sorted(
            grupos[marcador],
            key=lambda f: (f.get("fecha_publicacion") or "", f.get("url_fuente") or ""),
        )
        principal = grupo[0]
        recurrencia = len(grupo)
        cita = principal.get("cita_textual") or ""
        fichas.append(FichaProspeccion(
            organizacion=organizacion,
            situacion_observable=marcador,
            que_esta_ocurriendo=_fragmento(cita, marcador),
            evidencia_textual=cita[:MAX_EVIDENCIA_TEXTUAL],
            fuentes=sorted({f.get("nombre_medio") or "" for f in grupo if f.get("nombre_medio")}),
            fechas=sorted({f.get("fecha_publicacion") or "" for f in grupo if f.get("fecha_publicacion")}),
            persona_cargo=_persona_cargo(principal),
            tipo_epistemologico=principal.get("tipo_epistemologico") or "",
            origen_declaracion=principal.get("origen_declaracion") or "",
            corroboracion=(f"{recurrencia} documentos" if recurrencia > 1 else "ninguna"),
            recurrencia=recurrencia,
            contexto_organizacional=contexto_organizacional,
            estado_evaluacion=estado_de(situaciones[marcador], recurrencia),
            fit_comercial={"score_icp": score_icp},
        ))
    return fichas
