"""Motor de Colisión Estructural (Capa 21) — gate ADITIVO para /verificados.

Autorizado por el operador —Mario— el 2026-09-22, con alcance recortado el
mismo día tras verificación técnica (ver CLAUDE.md → "Frontera de
Interpretación"): sin `VECTOR_FATIGA` (exige transcripciones de podcast, sin
conector), sin `VECTOR_SILENCIO` (tratar ausencia de evidencia como señal
positiva contradice la Regla Dura de Capa 20: "no encontré evidencia" y "no
pude evaluar la fuente" no pueden significar lo mismo), sin umbral de capital
nuevo (reutiliza `receptividad.CAPITAL_TECHO`, ya vigente).

Clasifica evidencia YA extraída en dos vectores estructurales, por metadato,
nunca por juicio de contenido:

- `VECTOR_NARRATIVA`: `origen_declaracion == "prensa"` — discurso público ya
  capturado por Google News/GDELT/RSS fijos. Grupo de control, costo 0.
- `VECTOR_OPERATIVO`: `connector == "job_boards"` Y `cita_textual` contiene al
  menos una palabra del vocabulario cerrado (vacante correctiva real).

Colisión: existe un par (narrativa, operativo) cuyas fechas de publicación
distan 9 meses o menos. Evidencia sin fecha (`no_fechado`) nunca participa del
cálculo de ventana — la ausencia de fecha no inventa una colisión, mismo
criterio que `freshness.py`.

Determinista, sin IA, sin red, booleano puro sobre metadatos ya existentes.
NUNCA nombra Deuda Cultural™ ni decide ni ejecuta acción comercial. No toca
`clasificacion_epistemologica.py` ni `friccion.py` (ambos congelados por el
operador el 2026-09-22).
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

VECTOR_NARRATIVA = "narrativa"
VECTOR_OPERATIVO = "operativo"

ESTADO_COLISION_DETECTADA = "COLISION_DETECTADA"
ESTADO_SENAL_AISLADA = "SENAL_AISLADA"
ESTADO_SIN_SENAL = "SIN_SENAL"

VENTANA_MESES = 9

# Vocabulario cerrado: vacante correctiva real, no boilerplate genérico de
# "buscamos crecer" (mismo espíritu que Capa 20, léxico distinto y acotado al
# encargo del operador).
KEYWORDS_OPERATIVO: tuple[str, ...] = (
    "retention", "onboarding", "customer success", "behavioral",
)


def es_vector_narrativa(fila: dict) -> bool:
    return (fila.get("origen_declaracion") or "") == "prensa"


def es_vector_operativo(fila: dict) -> bool:
    if (fila.get("connector") or "") != "job_boards":
        return False
    texto = (fila.get("cita_textual") or "").lower()
    return any(kw in texto for kw in KEYWORDS_OPERATIVO)


def _fecha(fila: dict) -> _dt.date | None:
    valor = fila.get("fecha_publicacion")
    if not valor:
        return None
    try:
        return _dt.date.fromisoformat(valor[:10])
    except ValueError:
        return None


def _meses_entre(a: _dt.date, b: _dt.date) -> int:
    return abs((a.year - b.year) * 12 + (a.month - b.month))


@dataclass(frozen=True)
class Colision:
    estado: str
    vectores_presentes: tuple[str, ...] = field(default_factory=tuple)
    par_narrativa: dict | None = None
    par_operativo: dict | None = None


def detectar_colision(filas: list[dict], *, ventana_meses: int = VENTANA_MESES) -> Colision:
    """Clasifica evidencia YA extraída de una organización y busca colisión.

    ``filas`` es una lista de dicts con al menos ``origen_declaracion``,
    ``connector``, ``cita_textual`` y ``fecha_publicacion``. Función pura: no
    toca la base de datos.
    """
    narrativas = [f for f in filas if es_vector_narrativa(f)]
    operativos = [f for f in filas if es_vector_operativo(f)]

    vectores = tuple(
        v for v, presentes in (
            (VECTOR_NARRATIVA, narrativas), (VECTOR_OPERATIVO, operativos),
        ) if presentes
    )

    if not vectores:
        return Colision(ESTADO_SIN_SENAL, vectores)

    mejor: tuple[int, dict, dict] | None = None
    for n in narrativas:
        fecha_n = _fecha(n)
        if fecha_n is None:
            continue
        for o in operativos:
            fecha_o = _fecha(o)
            if fecha_o is None:
                continue
            distancia = _meses_entre(fecha_n, fecha_o)
            if distancia <= ventana_meses and (mejor is None or distancia < mejor[0]):
                mejor = (distancia, n, o)

    if mejor is not None:
        _, par_n, par_o = mejor
        return Colision(ESTADO_COLISION_DETECTADA, vectores, par_n, par_o)

    return Colision(ESTADO_SENAL_AISLADA, vectores)
