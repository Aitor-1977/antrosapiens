"""Filtro de Situación Observable (Capa 20).

Autorizado por el operador —Mario— el 2026-09-22 (ver CLAUDE.md → «Frontera
de Interpretación»), tras validar en Clara/Greenhouse que "texto completo de
job boards → evidencia real de fricción → clasificación epistemológica
determinista" produce señal útil.

Sobre evidencia YA clasificada por Entrega 2 (`tipo_epistemologico`), este
módulo distingue si el TEXTO describe una situación observable concreta
orientada al cliente/usuario (fricción, retención, adopción, onboarding,
cuellos de botella manuales, implementación compleja, quejas) frente a
huella práctica genérica (misma señal primaria estructural, sin ese
marcador) o ruido (sin señal primaria en absoluto — la REGLA DURA de
Entrega 2 ya lo descartó).

Determinista, léxico cerrado, sin IA, sin red: mismo texto ⇒ mismo
resultado. NO nombra Deuda Cultural™, NO decide acción comercial.
"""
from __future__ import annotations

from dataclasses import dataclass

TIPO_SITUACION_UTIL = "situacion_util"
TIPO_HUELLA_GENERICA = "huella_generica"
TIPO_RUIDO = "ruido"

_TIPOS_SENAL_PRIMARIA = frozenset((
    "senal_primaria_autodeclaracion",
    "senal_primaria_huella_practica",
))

# Léxico cerrado de marcadores de situación observable, orientados al
# cliente/usuario (no a eficiencia interna genérica). Variantes con y sin
# acento incluidas explícitamente (sin normalización Unicode) para que las
# posiciones encontradas coincidan exactamente con `cita_textual` original y
# permitan recortar un fragmento grounded sin desalinear offsets.
MARCADORES_SITUACION: tuple[str, ...] = (
    "user friction", "fricción de usuario", "friccion de usuario",
    "fricción del usuario", "friccion del usuario",
    "root causes of user", "root cause of user",
    "causa raíz de", "causa raiz de",
    "churn",
    "retention", "retención de clientes", "retencion de clientes",
    "retención del cliente", "retencion del cliente",
    "onboarding", "time-to-onboard",
    "adoption", "adopción de producto", "adopcion de producto",
    "adopción del producto", "adopcion del producto",
    "recurring pain points", "problemas recurrentes",
    "manual bottleneck", "cuello de botella manual",
    "cuellos de botella manuales",
    "complex integration", "integración compleja", "integracion compleja",
    "implementación compleja", "implementacion compleja",
    "customer complain", "queja de cliente", "queja de clientes",
    "quejas de clientes",
    "support-intensive", "soporte intensivo",
    "customer health scoring", "salud del cliente",
    "customers abandon", "clientes abandonan", "usuarios abandonan",
)


@dataclass(frozen=True)
class Situacion:
    tipo: str
    marcador: str | None
    razon: str


def clasificar_situacion(evidencia_clasificada: dict) -> Situacion:
    """Clasifica UNA fila ya clasificada epistemológicamente. Función pura.

    ``evidencia_clasificada`` es un dict con al menos ``tipo_epistemologico``
    y ``cita_textual``.
    """
    tipo_epistemologico = evidencia_clasificada.get("tipo_epistemologico")
    if tipo_epistemologico not in _TIPOS_SENAL_PRIMARIA:
        return Situacion(
            TIPO_RUIDO, None,
            "sin señal epistemológica primaria (REGLA DURA de Entrega 2, "
            "no reinterpretada aquí)",
        )

    texto = (evidencia_clasificada.get("cita_textual") or "").lower()
    for marcador in MARCADORES_SITUACION:
        if marcador in texto:
            return Situacion(
                TIPO_SITUACION_UTIL, marcador,
                f"marcador de situación observable: '{marcador}'",
            )

    return Situacion(
        TIPO_HUELLA_GENERICA, None,
        "señal primaria sin marcador de situación observable orientado al "
        "cliente/usuario (huella práctica genérica)",
    )
