"""Promoción de expedientes candidatos — Entrega 3.

Confirmado por el operador (Mario, 2026-08-22) que esto NO amplía la
«Frontera de Interpretación» de CLAUDE.md: no interpreta contenido nuevo, solo
transiciona el `estado` de un expediente a partir de datos ya estructurales
producidos por Entrega 2 (`tipo_epistemologico`) y por el intake de prospectos
(`categoria`). Es bookkeeping determinista, del mismo tipo que
`validacion_cientifica.py` o `gobernanza.py`: no añade lectura de texto.

REGLA (doctrina de HD, no negociable):
- Un expediente pasa de 'abierto' a 'candidato' cuando tiene AL MENOS una fila
  en `evidencia_clasificada` con `tipo_epistemologico` en
  ('senal_primaria_autodeclaracion', 'senal_primaria_huella_practica'). Sin
  ninguna de esas dos, permanece 'abierto' sin importar cuánta evidencia
  `corroborante` o `contextual` tenga acumulada.
- Cualquier organización con `categoria='Corporativo'` en `prospectos` queda
  EXCLUIDA explícitamente: nunca promueve, sin importar la evidencia. Es un
  filtro explícito (no confianza en que esas organizaciones ya no aparezcan).
- Si `categoria` no se pudo resolver (la organización del expediente no
  matchea ninguna fila de `prospectos`, p. ej. una variante de nombre), la
  exclusión de Corporativo NO aplica: sin categoría confirmada, no se asume
  que lo sea. La promoción sigue el criterio normal de evidencia.

Naturaleza (INVIOLABLE, igual que Entrega 2):
- **Determinista y reproducible**: mismos datos ⇒ misma decisión. Sin IA.
- **Solo una dirección**: `abierto` → `candidato`. Nunca degrada un
  `candidato` de vuelta a `abierto`, y nunca toca un `descartado`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

CATEGORIA_EXCLUIDA = "Corporativo"

TIPOS_QUE_PROMUEVEN: tuple[str, ...] = (
    "senal_primaria_autodeclaracion",
    "senal_primaria_huella_practica",
)
_TIPOS_QUE_PROMUEVEN = frozenset(TIPOS_QUE_PROMUEVEN)


@dataclass(frozen=True)
class DecisionPromocion:
    promover: bool
    razon: str


def decidir_promocion(categoria: str | None, tipos: Iterable[str]) -> DecisionPromocion:
    """Decide si un expediente debe promoverse. Función pura: sin BD.

    ``categoria`` es la de `prospectos` para la organización del expediente
    (o ``None`` si no se pudo resolver). ``tipos`` son los
    `tipo_epistemologico` ya registrados en `evidencia_clasificada` para ese
    expediente — puede repetirse, se trata como conjunto.
    """
    if categoria == CATEGORIA_EXCLUIDA:
        return DecisionPromocion(
            False,
            f"organización con categoria='{CATEGORIA_EXCLUIDA}': excluida "
            "explícitamente, sin importar la evidencia acumulada",
        )

    coincidencias = sorted(set(tipos) & _TIPOS_QUE_PROMUEVEN)
    if coincidencias:
        return DecisionPromocion(
            True, f"tiene evidencia con tipo_epistemologico en {coincidencias}")

    return DecisionPromocion(
        False,
        "sin ninguna fila con tipo_epistemologico en "
        f"{sorted(TIPOS_QUE_PROMUEVEN)} (regla dura: corroborante/contextual "
        "no bastan)",
    )
