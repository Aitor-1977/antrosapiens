"""Concentrador de Evidencia — lectura, sólo por coincidencia exacta de nombre.

Ver CLAUDE.md, sección "Frontera de Interpretación", entrada 2026-09-02, para
la autorización y el alcance exacto de este módulo.

Este módulo es de **solo lectura**: no escribe, no crea tablas, no modifica
`clasificacion_epistemologica.py`, `promocion_candidatos.py` ni
`hd_scraper/candidato.py`. Responde una única pregunta —«¿qué evidencias
existen de la organización X, sin importar qué conector las capturó?»—
uniendo las dos identidades organizacionales que ya existen hoy en el
sistema:

- `evidencias.empresa_mencionada`: nombre real de los cuatro conectores de
  Fase 1 (declarado por el operador o detectado estructuralmente).
- `evidencia_clasificada.organizacion_mencionada`: extracción estructural
  sobre el contenido de Tavily (`busqueda_dinamica_founder`), ver
  `clasificacion_epistemologica._detectar_organizacion_mencionada`.

La coincidencia es EXACTA (`LOWER(TRIM(...))`): no hay resolución de
entidad ni fuzzy-match. "Acme" y "Acme Inc." son, a propósito, dos
organizaciones distintas para este módulo hasta que exista esa pieza
(deliberadamente diferida, ver CLAUDE.md).

`resumen_organizacion` es puramente descriptivo (recuentos): NO es Densidad
Evidencial ni ninguna forma de Deuda Cultural™. Automatizar esa
equivalencia sigue fuera de alcance sin una entrada nueva en CLAUDE.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .db.models import normalizar_empresa

# Tipos epistemológicos que cuentan como "señal primaria" en el resumen
# descriptivo (mismo vocabulario que clasificacion_epistemologica.TIPOS).
_TIPOS_SENAL_PRIMARIA = (
    "senal_primaria_autodeclaracion",
    "senal_primaria_huella_practica",
)


@dataclass
class ResumenOrganizacion:
    """Recuentos puramente descriptivos. No es una decisión ni un score."""

    organizacion: str
    total_evidencias: int = 0
    fuentes_distintas: tuple[str, ...] = field(default_factory=tuple)
    senales_primarias: int = 0

    def to_dict(self) -> dict:
        return {
            "organizacion": self.organizacion,
            "total_evidencias": self.total_evidencias,
            "fuentes_distintas": list(self.fuentes_distintas),
            "num_fuentes_distintas": len(self.fuentes_distintas),
            "senales_primarias": self.senales_primarias,
        }


def evidencias_de_organizacion(db, organizacion: str) -> list[dict]:
    """Todas las evidencias de ``organizacion``, sin importar el conector.

    Unión por coincidencia EXACTA de nombre normalizado entre
    ``evidencias.empresa_mencionada`` y
    ``evidencia_clasificada.organizacion_mencionada``. Orden cronológico de
    captura (``creado_en``).
    """
    nombre = normalizar_empresa(organizacion)
    if not nombre:
        return []
    filas = db.fetch_all(
        """
        SELECT DISTINCT e.*, ec.tipo_epistemologico, ec.organizacion_mencionada
        FROM evidencias e
        LEFT JOIN evidencia_clasificada ec ON ec.evidencia_id = e.id
        WHERE LOWER(TRIM(e.empresa_mencionada)) = ?
           OR LOWER(TRIM(COALESCE(ec.organizacion_mencionada, ''))) = ?
        ORDER BY e.creado_en
        """,
        (nombre, nombre),
    )
    return [dict(f) for f in filas]


def resumen_organizacion(db, organizacion: str) -> ResumenOrganizacion:
    """Recuentos descriptivos sobre ``evidencias_de_organizacion``.

    No interpreta ni prioriza: solo cuenta. Ver docstring del módulo.
    """
    evs = evidencias_de_organizacion(db, organizacion)
    fuentes: list[str] = []
    for ev in evs:
        conn = (ev.get("connector") or "").strip()
        if conn and conn not in fuentes:
            fuentes.append(conn)
    senales_primarias = sum(
        1 for ev in evs if ev.get("tipo_epistemologico") in _TIPOS_SENAL_PRIMARIA
    )
    return ResumenOrganizacion(
        organizacion=organizacion,
        total_evidencias=len(evs),
        fuentes_distintas=tuple(fuentes),
        senales_primarias=senales_primarias,
    )
