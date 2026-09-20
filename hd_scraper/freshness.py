"""score_freshness — antigüedad de la evidencia PRIMARIA, gate de VISIBILIDAD
para /verificados (autorizado por el operador —Mario—, 2026-09-20, ver
CLAUDE.md "Frontera de Interpretación" / Visibilidad del Radar condicionada a
fricción documentada). Aritmética pura sobre `fecha_publicacion`: no lee ni
interpreta el contenido de la evidencia, mismo criterio que
`perfil_fundacional.py` con hechos estructurales ya declarados (no activa la
Regla de ampliación por sí sola).

SIEMPRE se calcula sobre la evidencia PRIMARIA ya seleccionada por
`candidatos_verificados.py` (autodeclaración o huella práctica) — NUNCA sobre
la evidencia más reciente de la organización. Una nota nueva pero irrelevante
para la promoción no debe "rejuvenecer" un expediente cuya evidencia primaria
es vieja.
"""
from __future__ import annotations

import datetime as _dt
from typing import Optional

VENTANA_DIAS = 180


def score_freshness(fecha_publicacion: Optional[str], hoy: Optional[_dt.date] = None) -> int:
    """0-100: max(0, 100 - (días_desde_publicación / 180 * 100)).

    Una evidencia sin fecha (`no_fechado`) vale 0, nunca 100: la ausencia de
    dato no es evidencia de frescura.
    """
    if not fecha_publicacion:
        return 0
    try:
        fecha = _dt.date.fromisoformat(fecha_publicacion[:10])
    except ValueError:
        return 0
    hoy = hoy or _dt.date.today()
    dias = (hoy - fecha).days
    return max(0, min(100, round(100 - (dias / VENTANA_DIAS * 100))))
