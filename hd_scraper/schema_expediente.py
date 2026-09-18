"""Declaración CANÓNICA del expediente expuesto por GET /verificados.

Contrato confirmado por Mario en Fase 1.5 (2026-09-16), a partir del
diagnóstico de Fase 1 (ver `tests/fixture_contrato_verificados.py`, contrato
REAL observado, 9 campos) y la evolución explícitamente autorizada (2 campos
nuevos). Ver `tests/fixture_contrato_canonico_expediente.py` para el fixture
congelado contra el que se valida este contrato.

No reproducir esta declaración en otro módulo: cualquier componente que
construya el diccionario de un expediente verificado debe usar
`ExpedienteVerificado` (o `normalizar_categoria`), nunca reconstruirlo con
sus propias claves.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

# Decisión 2 (Fase 1.5): únicos valores admitidos para `categoria`. Idéntico
# al CHECK de `prospectos.categoria` en el esquema de base de datos — no se
# amplía ni se reduce aquí, solo se declara para poder normalizar el
# fallback a `evidencias.categoria` (TEXT libre, sin CHECK).
CATEGORIAS_CANONICAS: tuple[str, ...] = ("VC", "Startup", "Incubadora", "Corporativo")


def normalizar_categoria(categoria: str | None) -> str:
    """Restringe `categoria` a los 4 literales estructurales.

    Cualquier valor que no sea exactamente uno de `CATEGORIAS_CANONICAS`
    (incluido `None`, `""` o una etiqueta de captura libre de
    `evidencias.categoria`) se normaliza a `""` — nunca se inventa ni se
    aproxima a la categoría más parecida.
    """
    return categoria if categoria in CATEGORIAS_CANONICAS else ""


@dataclass(frozen=True)
class ExpedienteVerificado:
    """Un expediente tal como lo expone GET /verificados. 11 campos, ninguno
    opcional en la declaración (los que pueden faltar en el dato real se
    tipan `str | None`, nunca se omiten de la estructura).

    `persona_citada`/`cargo` (estructurales, declarados por la fuente en
    `evidencias`) y `enunciador_nombre`/`enunciador_cargo` (extraídos por la
    clasificación epistemológica del propio texto) son conceptualmente
    distintos y NUNCA se fusionan (decisión 3, Fase 1.5): ambos pares
    viajan siempre por separado, incluso cuando describen a la misma
    persona.
    """
    organizacion: str
    categoria: str
    tipo_epistemologico: str
    cita_textual: str
    url_fuente: str
    nombre_medio: str
    fecha_publicacion: str | None
    persona_citada: str | None
    cargo: str | None
    enunciador_nombre: str | None
    enunciador_cargo: str | None

    def to_dict(self) -> dict:
        return asdict(self)
