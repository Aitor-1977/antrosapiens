"""Lectura estructural del discurso corporativo — pre-peritaje de Capa 0.

Autorizado por el operador (Mario) el 2026-08-02 (ver «Frontera de
Interpretación» en CLAUDE.md). Convierte el DIRECTORIO (identidad) en algo que
permite DECIDIR: qué Deuda Cultural™ SUGIERE el discurso que la propia
organización declara, con qué síntoma citable, contra qué compite realmente y
qué pregunta cultural queda abierta.

Naturaleza y frontera (INVIOLABLE):
- **Determinista y reproducible**: mismo discurso ⇒ misma lectura. Sin IA.
- **Grounded, jamás fabrica**: sólo afirma una Deuda si un marcador aparece
  LITERALMENTE en el discurso; se cita el fragmento. Sin marcador ⇒ estado
  ``requiere_campo`` (el diagnóstico real es DolorMap®, trabajo de campo).
- **Siempre PRELIMINAR**: es una hipótesis estructural sobre el discurso, no un
  juicio de comportamiento de usuarios (eso exige etnografía). No decide ni
  ejecuta acción comercial: eso es de Mario vía RadarHD/Motor C.

Los cinco tipos de Deuda Cultural™ y sus marcadores discursivos provienen del
marco de Hamaca Digital (skill hamaca-digital-anthropology).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

# ── Normalización determinista (minúsculas, sin acentos) ────────────────────

def normalizar(texto: str) -> str:
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t.lower()).strip()


# ── Marco de Deuda Cultural™: marcadores discursivos por tipo ────────────────
# Cada marcador es una subcadena SIN acentos que, si aparece en el discurso,
# sugiere (preliminarmente) el supuesto cultural correspondiente. Curado desde
# el skill de HD; ampliable con autorización del operador.

@dataclass(frozen=True)
class TipoDeuda:
    tipo: str
    marcadores: tuple[str, ...]
    # Supuesto que el discurso sugiere (lectura estructural, no juicio).
    supuesto: str
    # La pregunta que las métricas NO responden (Paso 2 del protocolo HD).
    pregunta_cultural: str
    # Contra qué compite realmente el producto (nunca otro producto).
    compite_contra: str
    # Varianza no modelada / categoría de decisión sin información cultural.
    implicacion: str


MARCO_DEUDA: tuple[TipoDeuda, ...] = (
    TipoDeuda(
        tipo="Ontológica",
        marcadores=(
            # ES
            "tu decides", "tu eliges", "tu tienes el control", "control total",
            "empodera", "empoderar", "cada persona", "cada usuario", "el individuo",
            "hazlo tu mismo", "sin depender de nadie", "toma el control", "tu dinero tus reglas",
            "libertad individual", "autonomia", "se tu propio",
            # PT
            "voce decide", "voce escolhe", "controle total", "cada pessoa",
            "faca voce mesmo", "sem depender", "liberdade individual", "seja seu proprio",
        ),
        supuesto="asume un usuario-individuo autónomo donde puede operar una personería relacional (el usuario decide en red de obligaciones y pertenencias).",
        pregunta_cultural="¿Quién decide realmente en la red de obligaciones del usuario, aunque él sea el comprador?",
        compite_contra="la estructura de decisión colectiva/familiar del usuario, no otra app.",
        implicacion="varianza no modelada en la unidad de decisión: el funnel asume un decisor autónomo que quizá no lo es.",
    ),
    TipoDeuda(
        tipo="Temporal",
        marcadores=(
            # ES
            "a largo plazo", "planea tu futuro", "planifica", "roadmap", "metas anuales",
            "ahorra para", "para el retiro", "constancia", "habitos diarios", "todos los meses",
            "proyecta", "cada mes", "disciplina", "tu futuro financiero", "planeacion",
            # PT
            "a longo prazo", "planeje seu futuro", "planeje", "poupe para", "aposentadoria",
            "todo mes", "seu futuro financeiro", "planejamento",
        ),
        supuesto="opera con temporalidad lineal y proyectable (roadmaps, metas mensuales) en contextos que pueden ser cíclicos o estructuralmente precarios.",
        pregunta_cultural="¿Qué configuración temporal (cíclica, situacional, precaria) compite con la planeación lineal que el producto exige?",
        compite_contra="la temporalidad situacional/precaria del usuario, no la falta de features.",
        implicacion="varianza no modelada en la retención: caídas que no correlacionan con ningún evento del producto.",
    ),
    TipoDeuda(
        tipo="Relacional",
        marcadores=(
            # ES
            "sin intermediarios", "directo", "en un clic", "un solo clic", "100% digital",
            "sin contacto", "autoservicio", "sin filas", "sin papeleo", "sin sucursales",
            "confia en la app", "todo desde tu celular", "sin asesores", "self-service", "sin agentes",
            # PT
            "sem intermediarios", "em um clique", "sem contato", "autoatendimento",
            "sem filas", "sem papelada", "sem agencias", "tudo pelo celular", "sem agentes",
        ),
        supuesto="ignora que la confianza y el compromiso se construyen por mediación social, no por transacción directa.",
        pregunta_cultural="¿Qué mediación social (recomendación, aval, presencia) reemplaza la confianza que el producto pide dar directamente?",
        compite_contra="la arquitectura de confianza mediada del territorio, no el canal digital.",
        implicacion="varianza no modelada en el CAC: el canal directo no escala aunque el referido rinda 10x.",
    ),
    TipoDeuda(
        tipo="Epistémica",
        marcadores=(
            # ES
            "es facil", "es simple", "es intuitivo", "cualquiera puede", "sin conocimientos",
            "sin ser experto", "solo tienes que", "es obvio", "en minutos", "sin complicaciones",
            "educacion financiera", "aprende a", "te explicamos", "sencillo", "facil de usar",
            # PT
            "e facil", "e simples", "e intuitivo", "qualquer um pode", "sem ser especialista",
            "voce so precisa", "e obvio", "sem complicacoes", "educacao financeira", "facil de usar",
        ),
        supuesto="asume que el usuario comparte la relación del founder con el conocimiento, la evidencia y la decisión.",
        pregunta_cultural="¿Qué relación con el conocimiento y la evidencia tiene el usuario, distinta a la que el equipo da por obvia?",
        compite_contra="la epistemología cotidiana del usuario, no la claridad del mensaje.",
        implicacion="varianza no modelada en la activación: se explica el beneficio con claridad y el usuario no actúa.",
    ),
    TipoDeuda(
        tipo="Moral",
        marcadores=(
            # ES
            "sin tabu", "sin tabus", "rompe el estigma", "habla abiertamente", "sin verguenza",
            "sin pena", "sin miedo", "sin juicios", "libre de estigma", "normaliza",
            "sin culpa", "atrevete a", "sin secretos",
            # PT
            "sem tabu", "quebre o estigma", "fale abertamente", "sem vergonha",
            "sem medo", "sem julgamentos", "sem culpa", "sem segredos",
        ),
        supuesto="activa un tabú o transgresión simbólica que el usuario no articula pero que gobierna su comportamiento.",
        pregunta_cultural="¿Qué tabú o vergüenza simbólica gobierna el comportamiento que el usuario no articula?",
        compite_contra="el tabú/vergüenza del territorio, no la conveniencia del producto.",
        implicacion="varianza no modelada en el uso: el usuario dice que le gusta pero no lo usa.",
    ),
)


# ── Lectura (pura, determinista, testeable) ─────────────────────────────────

@dataclass
class SenalDeuda:
    tipo: str
    fragmentos: list[str] = field(default_factory=list)  # marcadores hallados (citables)


def _buscar_marcadores(disc_norm: str) -> list[SenalDeuda]:
    """Detecta marcadores por tipo. Reproducible; sólo cuenta lo que aparece."""
    hallazgos: list[SenalDeuda] = []
    for td in MARCO_DEUDA:
        encontrados = [m for m in td.marcadores if m in disc_norm]
        if encontrados:
            hallazgos.append(SenalDeuda(tipo=td.tipo, fragmentos=encontrados))
    # Orden determinista: más marcadores primero; empate por orden del marco.
    orden = {td.tipo: i for i, td in enumerate(MARCO_DEUDA)}
    hallazgos.sort(key=lambda s: (-len(s.fragmentos), orden[s.tipo]))
    return hallazgos


def _por_tipo(tipo: str) -> TipoDeuda:
    return next(td for td in MARCO_DEUDA if td.tipo == tipo)


# Nota de preliminaridad que acompaña SIEMPRE la lectura (disciplina HD).
NOTA_PRELIMINAR = (
    "Hipótesis estructural PRELIMINAR sobre el discurso declarado, no un juicio "
    "de comportamiento de usuarios. El diagnóstico se confirma con DolorMap® "
    "(trabajo de campo etnográfico)."
)


def leer_discurso(discurso: Optional[str], empresa: str = "") -> dict:
    """Pre-peritaje determinista del discurso. Devuelve la lectura estructural.

    ``estado``:
      - ``requiere_campo``: sin discurso o sin marcador ⇒ no se afirma Deuda.
      - ``grounded``: al menos un marcador presente; se cita el fragmento.
    """
    disc_norm = normalizar(discurso or "")
    if not disc_norm:
        return {
            "empresa": empresa,
            "estado": "requiere_campo",
            "motivo": "sin discurso corporativo extraído todavía",
            "tipo_deuda_preliminar": None,
            "nota": NOTA_PRELIMINAR,
        }

    hallazgos = _buscar_marcadores(disc_norm)
    if not hallazgos:
        return {
            "empresa": empresa,
            "estado": "requiere_campo",
            "motivo": "el discurso no exhibe marcadores de Deuda Cultural; requiere campo",
            "tipo_deuda_preliminar": None,
            "nota": NOTA_PRELIMINAR,
        }

    principal = hallazgos[0]
    td = _por_tipo(principal.tipo)
    secundaria = hallazgos[1].tipo if len(hallazgos) > 1 else None
    return {
        "empresa": empresa,
        "estado": "grounded",
        "tipo_deuda_preliminar": td.tipo,
        "tipo_deuda_secundaria": secundaria,
        "supuesto": td.supuesto,
        "sintoma_observable": principal.fragmentos,  # marcadores citables del discurso
        "pregunta_cultural": td.pregunta_cultural,
        "compite_contra": td.compite_contra,
        "implicacion_vc": td.implicacion,
        "senales": [{"tipo": h.tipo, "marcadores": h.fragmentos} for h in hallazgos],
        "nota": NOTA_PRELIMINAR,
    }
