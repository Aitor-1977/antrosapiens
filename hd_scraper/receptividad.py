"""Receptividad Epistemológica para Capa 0 — motor de priorización determinista.

Autorizado por el operador (Mario) el 2026-09-12, dentro de la "Frontera de
Interpretación" ya vigente en CLAUDE.md (Scoring A/B/C y aplicación de
criterios ICP por reglas declaradas): este módulo es una AMPLIACIÓN de esas
reglas, no una categoría nueva de interpretación. Sigue las mismas
restricciones inmutables — determinista, sin IA, sin red — y la misma
frontera de fondo:

    Motor A puede clasificar la señal que extrae, pero no puede decidir
    ni ejecutar acción comercial sobre ella.

Reencuadre pedido por el operador ese mismo día (ver conversación): el
objeto de este motor NO es "potencial comercial" ni "capacidad de pago".
La pregunta que responde es:

    ¿Existe evidencia observable de que esta organización tiene margen
    para intervenir (capital, ventana temporal) PERO también suficiente
    fricción empírica (señales de negocio que sus capas de decisión
    actuales no explican) como para que un Sprint Fundacional tenga
    sentido?

Ni "capital alto" ni "capital bajo" son, por sí solos, una conclusión
antropológica. Este módulo NUNCA declara que una organización "tiene
Deuda Cultural™", "es receptiva a Capa 0" o "necesita antropología": eso
es interpretación exclusiva de Mario (RadarHD → Peritaje). Lo único que
hace es clasificar, por reglas declaradas y auditables, en qué BANDA de
condiciones observables cae una organización dado un conjunto de variables
estructurales ya capturadas (capital, etapa, tiempo desde el fondeo,
señales de fricción, barreras estructurales). El resultado es una prioridad
de TRIAGE para que Mario decida dónde mirar primero, no un veredicto.

No hay todavía una fuente de datos estructurada (capital en USD, etapa de
inversión, fecha de la ronda) en el esquema de `evidencias`/`prospectos`:
esa información vive hoy solo como texto libre en `cita_textual`. Este
módulo recibe esas variables como parámetros ya resueltos (no las infiere
del texto) — extraerlas de forma determinista desde el texto es un paso de
extracción aparte, todavía no construido, y deliberadamente fuera de este
módulo para no fabricar montos que no estén ya estructurados en algún lado.
"""
from __future__ import annotations

from typing import Optional

# ── Vocabulario cerrado (declarado por el operador, no inferido) ────────────

# Etapas de inversión elegibles para la Prioridad A. Fuera de este conjunto
# (p. ej. "scaleup", "pre-seed sin ronda formal") no aplica la ventana A.
ETAPAS_ELEGIBLES_A = {"seed", "serie_a"}

# Señales de fricción válidas para Prioridad A. Vocabulario cerrado: solo
# estas cuentan como "asfixia empírica observable"; cualquier otra cosa en el
# texto no promueve a Prioridad A por sí sola.
FRICCION_VALIDA = {
    "retencion",                  # churn / fricción de retención
    "churn",
    "pmf",                        # problema de product-market fit
    "expansion_latam_degradada",  # expansión transfronteriza LATAM con degradación operativa
}

# Barreras estructurales (Variables B): capas que pueden absorber o esconder
# la fricción empírica en vez de que llegue a quien decide. Cada una es un
# HECHO observable (existe el rol, existe el gasto, existe el proceso), no un
# juicio; la interpretación de qué tan bloqueante es cada una sigue siendo de
# Mario.
BARRERAS_ESTRUCTURALES = {
    "vp_ejecutivo",          # capa de VPs entre founder y el problema
    "head_growth",           # Head of Growth/Product/UX como amortiguador
    "research_ux_interno",   # equipo interno de research/UX ya "cubre" la pregunta
    "dependencia_pauta",     # puede comprar CAC/pauta/descuentos para tapar la fractura
    "procurement_largo",     # procurement corporativo que mata la velocidad del Sprint
}

# Ventana de capital de la Prioridad A (Sweet Spot Liminal), en USD.
CAPITAL_MIN_A = 1_500_000
CAPITAL_MAX_A = 10_000_000

# Techo rígido: por encima de este monto, la organización típicamente ya
# tiene margen para subsidiar el error y blindaje ejecutivo — el capital deja
# de ser habilitador y pasa a ser barrera para la agilidad del Sprint
# Fundacional. Aplica SIEMPRE, incluso si hay fricción observable.
CAPITAL_TECHO = 15_000_000

# Ventana temporal post-fondeo de la Prioridad A, en meses.
MESES_MIN_A = 6
MESES_MAX_A = 12

PRIORIDAD_A = "A"
PRIORIDAD_TECHO = "techo"
PRIORIDAD_INSUFICIENTE = ""


def _friccion_declarada(senales_friccion) -> set[str]:
    """Solo cuenta el vocabulario cerrado; ignora cualquier otra cadena para
    no dejar que texto libre no clasificado infle la fricción observada."""
    return set(senales_friccion or ()) & FRICCION_VALIDA


def _barreras_declaradas(barreras_estructurales) -> set[str]:
    return set(barreras_estructurales or ()) & BARRERAS_ESTRUCTURALES


def evaluar_receptividad_organizacion(
    capital_usd: Optional[float],
    etapa: str = "",
    meses_post_fondeo: Optional[int] = None,
    senales_friccion=(),
    barreras_estructurales=(),
) -> dict:
    """Clasifica condiciones OBSERVABLES de una organización en una banda de
    prioridad de triage. Determinista: mismo insumo, mismo resultado siempre.

    Parámetros (todos declarados por quien llama, ninguno inferido de texto
    libre por este módulo):
      capital_usd            monto de la última ronda conocida, en USD.
      etapa                  "seed" | "serie_a" | cualquier otro string
                             (p. ej. "scaleup"); se compara tal cual, en
                             minúsculas.
      meses_post_fondeo      meses transcurridos desde esa ronda.
      senales_friccion       iterable de tags de FRICCION_VALIDA presentes
                             en la evidencia ya capturada.
      barreras_estructurales iterable de tags de BARRERAS_ESTRUCTURALES
                             presentes en la evidencia ya capturada.

    Devuelve un dict con la banda (`prioridad`), las condiciones evaluadas
    (para auditoría) y una `razon` legible que cita exactamente qué regla
    aplicó. NUNCA incluye una etiqueta de Deuda Cultural™ ni una afirmación
    de que la organización "es receptiva": solo la banda de condiciones.
    """
    etapa_norm = (etapa or "").strip().lower()
    friccion = _friccion_declarada(senales_friccion)
    barreras = _barreras_declaradas(barreras_estructurales)

    capital_en_ventana_a = (
        capital_usd is not None and CAPITAL_MIN_A <= capital_usd <= CAPITAL_MAX_A
    )
    etapa_elegible_a = etapa_norm in ETAPAS_ELEGIBLES_A
    tiempo_en_ventana_a = (
        meses_post_fondeo is not None and MESES_MIN_A <= meses_post_fondeo <= MESES_MAX_A
    )
    hay_friccion = bool(friccion)
    supera_techo = capital_usd is not None and capital_usd > CAPITAL_TECHO

    condiciones = {
        "capital_en_ventana_a": capital_en_ventana_a,
        "etapa_elegible_a": etapa_elegible_a,
        "tiempo_en_ventana_a": tiempo_en_ventana_a,
        "friccion_observada": hay_friccion,
        "friccion_detectada": sorted(friccion),
        "supera_techo_capital": supera_techo,
        "barreras_detectadas": sorted(barreras),
    }

    # Regla de techo rígido: por encima del monto, prioridad baja SIEMPRE,
    # sin importar si hay fricción — el capital ya no es el habilitador que
    # es en la ventana A, es la barrera. Las barreras estructurales detectadas
    # (si las hay) se citan como refuerzo de la razón, no como condición
    # necesaria: el techo aplica por capital solo.
    #
    # Hipótesis de diseño de ESTA regla (por qué el operador la declaró así),
    # documentada aquí como comentario interno, NUNCA como conclusión en un
    # campo que consuma Mario (auditoría 2026-09-12): por encima del techo, la
    # organización PODRÍA tener margen para subsidiar el error y blindaje
    # ejecutivo que vuelva la fricción menos visible. Es la razón de ser de
    # la regla, no una observación — el motor no tiene evidencia de que eso
    # esté ocurriendo en un caso concreto, así que `razon` no debe afirmarlo.
    if supera_techo:
        razon = (
            f"capital (${capital_usd:,.0f}) supera el techo declarado de "
            f"${CAPITAL_TECHO:,.0f}; se aplica la regla de techo "
            "independientemente de las señales de fricción recibidas"
        )
        if barreras:
            razon += f"; barreras estructurales detectadas: {', '.join(sorted(barreras))}"
        return {
            "prioridad": PRIORIDAD_TECHO,
            "puntaje_liminal": max(0, 20 - 5 * len(barreras)),
            "condiciones": condiciones,
            "razon": razon,
        }

    if capital_en_ventana_a and etapa_elegible_a and tiempo_en_ventana_a and hay_friccion:
        return {
            "prioridad": PRIORIDAD_A,
            "puntaje_liminal": 100,
            "condiciones": condiciones,
            "razon": (
                f"capital (${capital_usd:,.0f}) dentro de la ventana liminal "
                f"(${CAPITAL_MIN_A:,.0f}-${CAPITAL_MAX_A:,.0f}), etapa "
                f"'{etapa_norm}' elegible, {meses_post_fondeo} meses "
                f"post-fondeo dentro de la ventana ({MESES_MIN_A}-{MESES_MAX_A}) "
                f"y fricción observada: {', '.join(sorted(friccion))}"
            ),
        }

    # Ninguna banda declarada aplica: se listan las condiciones que faltaron,
    # sin inventar una prioridad intermedia no declarada por el operador.
    faltantes = [
        nombre for nombre, cumplida in (
            ("capital en ventana", capital_en_ventana_a),
            ("etapa elegible", etapa_elegible_a),
            ("tiempo post-fondeo en ventana", tiempo_en_ventana_a),
            ("fricción observada", hay_friccion),
        ) if not cumplida
    ]
    return {
        "prioridad": PRIORIDAD_INSUFICIENTE,
        "puntaje_liminal": 0,
        "condiciones": condiciones,
        "razon": "no cumple la Prioridad A liminal; falta: " + ", ".join(faltantes),
    }


# ── Prioridad B: GPs de VC, nivel portafolio ─────────────────────────────────
#
# El objeto de inteligencia aquí NO es el fondo (no es "tiene dinero para
# contratar"), es que el PORTAFOLIO completo puede tener un problema
# epistemológico distinto: alto consumo de capital sin retención, sostenido
# por una narrativa de crecimiento que ya no explica los resultados. Variables
# declaradas por quien llama (no inferidas de texto libre por este módulo).

PRIORIDAD_B = "B"


def evaluar_receptividad_portafolio(
    alto_burn_rate: bool,
    baja_retencion: bool,
    disonancia_narrativa_resultados: bool,
) -> dict:
    """Clasifica un fondo/GP como candidato de Prioridad B (nivel portafolio).

    Las tres condiciones son observables y declaradas por quien llama (p. ej.
    a partir de evidencia ya capturada sobre el portafolio): alto burn rate,
    baja retención agregada, y una disonancia entre la narrativa de
    crecimiento que el fondo/portafolio comunica y los resultados empíricos
    ya observados. Solo cuando las tres están presentes se marca Prioridad B;
    ninguna combinación parcial la alcanza.
    """
    cumple = alto_burn_rate and baja_retencion and disonancia_narrativa_resultados
    condiciones = {
        "alto_burn_rate": bool(alto_burn_rate),
        "baja_retencion": bool(baja_retencion),
        "disonancia_narrativa_resultados": bool(disonancia_narrativa_resultados),
    }
    if cumple:
        return {
            "prioridad": PRIORIDAD_B,
            "condiciones": condiciones,
            "razon": (
                "portafolio con alto consumo de capital, baja retención y "
                "disonancia entre narrativa de crecimiento y resultados "
                "empíricos: el objeto de inteligencia es el portafolio, no "
                "el fondo como comprador"
            ),
        }
    faltantes = [
        nombre for nombre, cumplida in condiciones.items() if not cumplida
    ]
    return {
        "prioridad": PRIORIDAD_INSUFICIENTE,
        "condiciones": condiciones,
        "razon": "no cumple la Prioridad B a nivel portafolio; falta: " + ", ".join(faltantes),
    }
