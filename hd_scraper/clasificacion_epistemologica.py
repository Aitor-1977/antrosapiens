"""Clasificación epistemológica de la evidencia capturada — Entrega 2.

Autorizado por el operador (Mario) el 2026-08-21 (ver «Frontera de
Interpretación» en CLAUDE.md). Responde UNA sola pregunta sobre una evidencia
ya extraída por este mismo motor: **qué peso epistemológico tiene**, es decir,
quién enuncia y desde qué posición, no si lo enunciado es bueno o malo.

Naturaleza y frontera (INVIOLABLE):
- **Determinista y reproducible**: mismo texto ⇒ misma clasificación. Sin IA,
  sin red, sin modelo. Léxico cerrado y patrones de atribución declarados aquí.
- **No nombra Deuda Cultural™**: este módulo NO produce, sugiere ni etiqueta
  ningún tipo de Deuda (Ontológica/Moral/Temporal/Relacional/Epistémica). Su
  única salida es una de las cuatro categorías de ``TIPOS``. La lectura de Deuda
  sigue siendo de ``lectura_estructural`` (discurso) y de RadarHD.
- **No decide ni ejecuta acción comercial.** Tampoco promueve expedientes: el
  paso de ``abierto`` a ``candidato`` es Entrega 3, fuera de este módulo.

REGLA DURA (doctrina de HD, no negociable): ante información insuficiente para
distinguir con confianza razonable, se clasifica ``contextual``. Nunca se fuerza
una categoría de mayor peso epistemológico sobre evidencia ambigua. Todas las
ramas de la cascada están escritas para caer hacia ``contextual``, jamás al revés.

Nota sobre el corpus real: los cuatro conectores de Fase 1 guardan en
``cita_textual`` únicamente el TITULAR, y escriben ``persona_citada = NULL`` y
``cargo = NULL``. Sobre un titular de 10–15 palabras la atribución rara vez es
identificable, así que la REGLA DURA manda la mayoría de las filas a
``contextual`` o a ``senal_primaria_huella_practica``. Eso es fidelidad al
corpus, no una limitación del clasificador.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

VERSION_REGLAS = "clasificacion_epistemologica.v1"

# Literales del CHECK `chk_tipo` de `evidencia_clasificada`. No añadir valores
# sin migrar antes la restricción en la base.
TIPO_AUTODECLARACION = "senal_primaria_autodeclaracion"
TIPO_HUELLA_PRACTICA = "senal_primaria_huella_practica"
TIPO_CORROBORANTE = "corroborante"
TIPO_CONTEXTUAL = "contextual"

TIPOS: tuple[str, ...] = (
    TIPO_AUTODECLARACION,
    TIPO_HUELLA_PRACTICA,
    TIPO_CORROBORANTE,
    TIPO_CONTEXTUAL,
)

# Niveles de autoridad del enunciador. No se persisten: son el estado interno
# de la cascada.
NIVEL_MAXIMA = "maxima_autoridad"   # founder/CEO: autoridad sobre cualquier dominio
NIVEL_FUNCIONAL = "funcional"       # CFO/CTO/…: autoridad SOLO sobre su dominio
NIVEL_TENSION = "tension"           # empleado/exempleado/inversionista/cliente
NIVEL_EXTERNO = "externo"           # analista/consultor: no pertenece a la org
NIVEL_NINGUNO = "ninguno"           # no se identificó posición


# ── Normalización determinista ──────────────────────────────────────────────

def normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, espacios colapsados. Para pertenencia a léxico."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t.lower()).strip()


def _plano(texto: str) -> str:
    """Como ``normalizar`` pero PRESERVANDO los índices del texto original.

    La cascada compara posiciones entre el texto plano (donde se buscan cargos)
    y el original (donde se buscan nombres propios, que necesitan mayúsculas).
    Si ambas cadenas no midieran lo mismo, esas posiciones no serían
    comparables. Por eso se normaliza carácter a carácter y se conserva el
    original cuando la descomposición no devuelve exactamente un carácter.
    """
    salida = []
    for ch in texto or "":
        d = unicodedata.normalize("NFKD", ch)
        d = "".join(c for c in d if not unicodedata.combining(c))
        salida.append(d.lower() if len(d) == 1 else ch.lower())
    return "".join(salida)


# ── Léxico de dominios ──────────────────────────────────────────────────────
# El dominio es el TEMA de la afirmación, no el cargo de quien la hace. Léxico
# cerrado: si nada coincide, el dominio es 'indeterminado' (y entonces un cargo
# funcional nunca alcanza autodeclaración).

DOMINIOS: dict[str, tuple[str, ...]] = {
    "retencion_talento": (
        "talento", "retencion", "rotacion", "renuncia", "despido", "despidos",
        "recorte", "layoff", "plantilla", "headcount", "contratacion", "vacante",
        "recursos humanos", "clima laboral", "cultura laboral", "salario",
        "sueldo", "empleo", "equipo", "fuga de talento",
    ),
    "finanzas": (
        "ronda", "inversion", "capital", "valuacion", "valoracion", "ingresos",
        "rentabilidad", "perdidas", "financiamiento", "deuda", "ebitda",
        "runway", "serie a", "serie b", "serie c", "semilla", "seed",
        "levanta", "levanto", "recauda", "recaudo", "utilidades", "margen",
    ),
    "producto": (
        "producto", "lanzamiento", "lanza", "funcionalidad", "feature",
        "roadmap", "version", "beta", "rediseno", "app", "aplicacion",
    ),
    "operaciones": (
        "operaciones", "logistica", "cadena de suministro", "almacen",
        "entrega", "planta", "sucursal", "cierre", "expansion",
        "reestructuracion", "fusion", "adquisicion", "escala",
    ),
    "tecnologia": (
        "tecnologia", "infraestructura", "ingenieria", "datos",
        "inteligencia artificial", "ciberseguridad", "sistema", "plataforma",
        "software", "nube",
    ),
    "mercado_clientes": (
        "clientes", "usuarios", "mercado", "competencia", "demanda", "churn",
        "adopcion", "ventas", "marketing", "marca",
    ),
    "legal_regulatorio": (
        "regulacion", "regulador", "ley", "corte", "juez", "multa", "sancion",
        "cofece", "condusef", "banxico", "cnbv", "profeco", "licencia",
        "permiso", "cumplimiento", "compliance",
    ),
    "cultura": (
        "cultura", "valores", "proposito", "mision", "diversidad", "inclusion",
        "liderazgo", "clima", "bienestar",
    ),
}

DOMINIO_INDETERMINADO = "indeterminado"


def detectar_dominio(texto: str) -> str:
    """Dominio del que trata el texto. Primer dominio con más coincidencias.

    El desempate es por orden declarado en ``DOMINIOS`` (determinista), no por
    orden de aparición en el texto.
    """
    plano = normalizar(texto)
    if not plano:
        return DOMINIO_INDETERMINADO
    mejor, mejor_n = DOMINIO_INDETERMINADO, 0
    for dominio, marcadores in DOMINIOS.items():
        n = sum(1 for m in marcadores if m in plano)
        if n > mejor_n:
            mejor, mejor_n = dominio, n
    return mejor


# ── Léxico de cargos ────────────────────────────────────────────────────────
# (patrón sobre texto plano, nivel, dominio de autoridad o None).
# `None` en un cargo funcional significa "dominio no declarado por el cargo":
# ese cargo no alcanza autodeclaración por sí solo.

_CARGOS: tuple[tuple[str, str, str | None], ...] = (
    # Tensión ANTES que máxima autoridad: 'ex-ceo' debe ganarle a 'ceo'. La
    # selección es por longitud de coincidencia, así que el orden aquí solo
    # documenta la intención.
    (r"\bex-?\s?ceo\b", NIVEL_TENSION, None),
    (r"\bex-?\s?fundador(?:a|es|as)?\b", NIVEL_TENSION, None),
    (r"\bex-?\s?emplead[oa]s?\b", NIVEL_TENSION, None),
    (r"\bex-?\s?trabajador(?:a|es|as)?\b", NIVEL_TENSION, None),
    (r"\bex-?\s?director(?:a|es)?\b", NIVEL_TENSION, None),
    (r"\bemplead[oa]s?\b", NIVEL_TENSION, None),
    (r"\btrabajador(?:a|es|as)?\b", NIVEL_TENSION, None),
    (r"\bsindicato\b", NIVEL_TENSION, None),
    (r"\binversionista\b", NIVEL_TENSION, None),
    (r"\binversor(?:a|es)?\b", NIVEL_TENSION, None),
    (r"\baccionista\b", NIVEL_TENSION, None),
    (r"\bclientes?\b", NIVEL_TENSION, None),
    (r"\busuari[oa]s?\b", NIVEL_TENSION, None),
    # Máxima autoridad
    (r"\bceo\b", NIVEL_MAXIMA, None),
    (r"\bco-?fundador(?:a|es|as)?\b", NIVEL_MAXIMA, None),
    (r"\bfundador(?:a|es|as)?\b", NIVEL_MAXIMA, None),
    (r"\bco-?founder\b", NIVEL_MAXIMA, None),
    (r"\bfounder\b", NIVEL_MAXIMA, None),
    (r"\bpresident[ae]\b", NIVEL_MAXIMA, None),
    (r"\bdirector(?:a)? general\b", NIVEL_MAXIMA, None),
    (r"\bdirector(?:a)? ejecutiv[oa]\b", NIVEL_MAXIMA, None),
    # Funcional con dominio declarado por el propio cargo
    (r"\bcfo\b", NIVEL_FUNCIONAL, "finanzas"),
    (r"\bdirector(?:a)? financier[oa]\b", NIVEL_FUNCIONAL, "finanzas"),
    (r"\bcto\b", NIVEL_FUNCIONAL, "tecnologia"),
    (r"\bcoo\b", NIVEL_FUNCIONAL, "operaciones"),
    (r"\bcmo\b", NIVEL_FUNCIONAL, "mercado_clientes"),
    (r"\bchro\b", NIVEL_FUNCIONAL, "retencion_talento"),
    # Funcional genérico: el dominio sale del complemento ('director de X').
    (r"\bdirector(?:a)? de ((?:[a-z]+)(?: [a-z]+){0,2})\b", NIVEL_FUNCIONAL, None),
    (r"\bgerente de ((?:[a-z]+)(?: [a-z]+){0,2})\b", NIVEL_FUNCIONAL, None),
    (r"\bhead of ((?:[a-z]+)(?: [a-z]+){0,2})\b", NIVEL_FUNCIONAL, None),
    (r"\bvicepresident[ae]\b", NIVEL_FUNCIONAL, None),
    (r"\bvp\b", NIVEL_FUNCIONAL, None),
    (r"\bdirectiv[oa]s?\b", NIVEL_FUNCIONAL, None),
    # Externos a la organización
    (r"\banalista\b", NIVEL_EXTERNO, None),
    (r"\bconsultor(?:a|es)?\b", NIVEL_EXTERNO, None),
    (r"\bexpert[oa]s?\b", NIVEL_EXTERNO, None),
    (r"\bacademic[oa]s?\b", NIVEL_EXTERNO, None),
    (r"\bperiodista\b", NIVEL_EXTERNO, None),
)

_CARGOS_COMPILADOS = tuple(
    (re.compile(p), nivel, dominio) for p, nivel, dominio in _CARGOS
)

# Marcadores de fricción: una declaración solo es `corroborante` si además de
# venir de una posición de tensión revela desacuerdo. Sin marcador, la posición
# por sí sola no basta (REGLA DURA).
_FRICCION: tuple[str, ...] = (
    "denunci", "acus", "demand", "queja", "quejas", "renunci", "protest",
    "huelga", "paro", "desacuerdo", "critic", "discrep", "tension", "conflicto",
    "disputa", "reclam", "inconformidad", "malestar", "descontento", "exig",
    "advierte", "alerta", "fricci", "molestia", "desmiente", "contradice",
)


# ── Nombres propios y atribución ────────────────────────────────────────────

_TOKEN = r"[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ'’\-]+"
_CONECTOR = r"(?:de|del|la|las|los|van|von|da|di)"
# Exige AL MENOS dos tokens capitalizados: un solo token es indistinguible del
# arranque de un titular. Los acrónimos en mayúsculas (CEO, GDELT) no encajan
# en _TOKEN, así que quedan excluidos por construcción.
_NOMBRE = re.compile(rf"{_TOKEN}(?:\s+(?:{_CONECTOR}\s+)?{_TOKEN}){{1,3}}")

_VERBOS = (
    r"(?:dijo|afirm[oó]|declar[oó]|asegur[oó]|advirti[oó]|se[ñn]al[oó]|"
    r"explic[oó]|coment[oó]|sostuvo|reconoci[oó]|admiti[oó]|anunci[oó])"
)

_ATRIBUCION = tuple(
    re.compile(p) for p in (
        rf"(?:seg[uú]n|de acuerdo con)\s+({_NOMBRE.pattern})",
        rf"({_NOMBRE.pattern})\s*,?\s+{_VERBOS}\b",
        rf"{_VERBOS}\s+({_NOMBRE.pattern})",
    )
)

# Ventana alrededor del cargo dentro de la cual un nombre propio se considera
# atribuido a él. 80 caracteres cubre «Juan Pérez, director de operaciones de
# Acme» en ambos sentidos sin cruzar a otra oración de un titular.
_VENTANA = 80


@dataclass(frozen=True)
class Enunciador:
    """Quién habla, desde qué posición y sobre qué. Todo puede ser vacío."""
    nombre: str | None
    cargo: str | None
    nivel: str
    # Dominio del que TRATA el texto. Puede ser 'indeterminado'.
    dominio: str
    # Dominio sobre el que el CARGO da autoridad (None si el cargo no lo
    # declara). Se mantiene separado de `dominio` a propósito: confundirlos
    # concedería autoridad sobre un tema que el texto nunca identificó.
    dominio_cargo: str | None
    # El cargo está ligado a la organización de la evidencia (y no a otra que
    # el texto mencione más cerca).
    vinculado: bool


@dataclass(frozen=True)
class Clasificacion:
    tipo: str
    enunciador_nombre: str | None
    enunciador_cargo: str | None
    enunciador_dominio: str | None
    # Razón legible de la rama tomada. Se usa en el informe del dry-run; la
    # tabla no tiene columna para guardarla.
    razon: str
    version_reglas: str = VERSION_REGLAS


def _buscar_cargo(plano: str) -> tuple[re.Match, str, str | None] | None:
    """Cargo con la coincidencia MÁS LARGA (desempate: la más temprana)."""
    mejor: tuple[re.Match, str, str | None] | None = None
    for patron, nivel, dominio in _CARGOS_COMPILADOS:
        m = patron.search(plano)
        if not m:
            continue
        if mejor is None:
            mejor = (m, nivel, dominio)
            continue
        largo_actual = len(m.group(0))
        largo_mejor = len(mejor[0].group(0))
        if largo_actual > largo_mejor or (
            largo_actual == largo_mejor and m.start() < mejor[0].start()
        ):
            mejor = (m, nivel, dominio)
    return mejor


def _dominio_del_cargo(hallazgo: tuple[re.Match, str, str | None]) -> str | None:
    """Dominio sobre el que el cargo da autoridad, o None si no lo declara.

    Los cargos genéricos ('director de X', 'head of X') lo declaran en el grupo
    capturado; si ese complemento no cae en el léxico de dominios, el cargo no
    concede autoridad sobre nada y la cascada no podrá llegar a autodeclaración.
    """
    m, _, dominio = hallazgo
    if dominio is not None:
        return dominio
    if not m.groups():
        return None
    d = detectar_dominio(m.group(1))
    return None if d == DOMINIO_INDETERMINADO else d


def _es_nombre_valido(candidato: str, vetados: tuple[str, ...]) -> bool:
    plano = normalizar(candidato)
    if len(plano) < 5:
        return False
    for veto in vetados:
        if not veto:
            continue
        if veto in plano or plano in veto:
            return False
    return True


def _nombre_cerca(texto: str, centro: int, vetados: tuple[str, ...]) -> str | None:
    """Nombre propio más cercano al cargo, dentro de ``_VENTANA``."""
    ini, fin = max(0, centro - _VENTANA), centro + _VENTANA
    mejor, mejor_d = None, None
    for m in _NOMBRE.finditer(texto):
        if m.end() < ini or m.start() > fin:
            continue
        if not _es_nombre_valido(m.group(0), vetados):
            continue
        d = abs(m.start() - centro)
        if mejor_d is None or d < mejor_d:
            mejor, mejor_d = m.group(0).strip(), d
    return mejor


def _nombre_por_atribucion(texto: str, vetados: tuple[str, ...]) -> str | None:
    for patron in _ATRIBUCION:
        for m in patron.finditer(texto):
            candidato = (m.group(1) or "").strip()
            if _es_nombre_valido(candidato, vetados):
                return candidato
    return None


def _vinculado_a_org(plano: str, pos_cargo: int, org: str,
                     otras_orgs: tuple[str, ...]) -> bool:
    """El cargo pertenece a la organización de la evidencia.

    Se exige que la organización aparezca en el texto y que ninguna OTRA
    organización conocida esté más cerca del cargo. Un CEO de otra empresa
    hablando sobre esta no es autodeclaración de esta.
    """
    org_plano = normalizar(org)
    if not org_plano or org_plano not in plano:
        return False
    d_org = min(abs(m.start() - pos_cargo)
                for m in re.finditer(re.escape(org_plano), plano))
    for otra in otras_orgs:
        otra_plano = normalizar(otra)
        if not otra_plano or otra_plano == org_plano or otra_plano not in plano:
            continue
        d_otra = min(abs(m.start() - pos_cargo)
                     for m in re.finditer(re.escape(otra_plano), plano))
        if d_otra < d_org:
            return False
    return True


def identificar_enunciador(evidencia: dict,
                           orgs_conocidas: tuple[str, ...] = ()) -> Enunciador:
    """Quién habla en esta evidencia y desde qué posición.

    Las columnas ``persona_citada`` y ``cargo`` son parte del contrato de datos
    y tienen prioridad sobre el texto: si un conector las declara, se respetan
    en lugar de reinterpretar el titular. Hoy los cuatro conectores de Fase 1
    las dejan en NULL, así que en la práctica se cae al texto.
    """
    texto = (evidencia.get("cita_textual") or "")
    org = (evidencia.get("empresa_mencionada") or "")
    medio = (evidencia.get("nombre_medio") or "")
    plano = _plano(texto)

    vetados = tuple(
        v for v in (normalizar(org), normalizar(medio),
                    *(normalizar(o) for o in orgs_conocidas)) if v
    )
    otras_orgs = tuple(o for o in orgs_conocidas if normalizar(o) != normalizar(org))

    cargo_declarado = (evidencia.get("cargo") or "").strip()
    persona_declarada = (evidencia.get("persona_citada") or "").strip()

    if cargo_declarado:
        hallazgo = _buscar_cargo(_plano(cargo_declarado))
        nivel = hallazgo[1] if hallazgo else NIVEL_NINGUNO
        dominio_cargo = _dominio_del_cargo(hallazgo) if hallazgo else None
        return Enunciador(
            nombre=persona_declarada or None,
            cargo=cargo_declarado,
            nivel=nivel,
            dominio=detectar_dominio(texto),
            dominio_cargo=dominio_cargo,
            # El conector declaró el cargo como dato estructural de la fila: el
            # vínculo con la organización de esa misma fila no se pone en duda.
            vinculado=True,
        )

    hallazgo = _buscar_cargo(plano)
    dominio = detectar_dominio(texto)

    if hallazgo is None:
        nombre = persona_declarada or _nombre_por_atribucion(texto, vetados)
        return Enunciador(nombre=nombre, cargo=None, nivel=NIVEL_NINGUNO,
                          dominio=dominio, dominio_cargo=None, vinculado=False)

    m, nivel, _ = hallazgo
    dominio_cargo = _dominio_del_cargo(hallazgo)

    nombre = persona_declarada or _nombre_cerca(texto, m.start(), vetados)
    return Enunciador(
        nombre=nombre,
        # Se guarda el fragmento tal como aparece en el texto original.
        cargo=texto[m.start():m.end()].strip() or m.group(0),
        nivel=nivel,
        dominio=dominio,
        dominio_cargo=dominio_cargo,
        vinculado=_vinculado_a_org(plano, m.start(), org, otras_orgs),
    )


def _dominio_bajo_autoridad(enunciador: Enunciador) -> bool:
    """¿El dominio del que habla cae dentro de su autoridad razonable?

    Máxima autoridad: cualquier dominio de su organización. Cargo funcional:
    solo el dominio del propio cargo. Cualquier otra combinación es ambigua y,
    por la REGLA DURA, no alcanza autodeclaración.
    """
    if enunciador.nivel == NIVEL_MAXIMA:
        return True
    if enunciador.nivel != NIVEL_FUNCIONAL:
        return False
    if not enunciador.dominio_cargo or enunciador.dominio == DOMINIO_INDETERMINADO:
        return False
    return enunciador.dominio == enunciador.dominio_cargo


def _hay_friccion(texto: str, desde: int = 0) -> bool:
    """¿El texto revela fricción a partir de ``desde``?

    Se exige que el marcador aparezca DESPUÉS de la posición de tensión porque
    en español el enunciador precede al verbo: «Clientes de Acme se quejan» es
    fricción de un cliente; «Acme demanda más clientes» no lo es, aunque ambas
    contengan las mismas dos palabras. Sin este orden, la segunda ascendería a
    `corroborante` sobre evidencia ambigua, justo lo que la REGLA DURA prohíbe.
    """
    plano = _plano(texto)[desde:]
    return any(marcador in plano for marcador in _FRICCION)


def clasificar(evidencia: dict,
               orgs_conocidas: tuple[str, ...] = ()) -> Clasificacion:
    """Clasifica UNA evidencia ya extraída. Función pura: no toca la base.

    ``evidencia`` es una fila de ``evidencias`` como dict. Se leen
    ``cita_textual``, ``empresa_mencionada``, ``nombre_medio``,
    ``origen_declaracion``, ``persona_citada`` y ``cargo``.
    """
    texto = evidencia.get("cita_textual") or ""
    enunciador = identificar_enunciador(evidencia, orgs_conocidas)

    # Posición del cargo en el texto: la fricción solo cuenta a partir de ahí.
    # Con el cargo declarado por el conector (columna del contrato) no hay
    # posición que respetar, así que se mira el texto completo.
    hallazgo_pos = _buscar_cargo(_plano(texto))
    pos_tension = (0 if (evidencia.get("cargo") or "").strip()
                   else (hallazgo_pos[0].start() if hallazgo_pos else 0))

    dominio_salida = (
        enunciador.dominio if enunciador.dominio != DOMINIO_INDETERMINADO else None
    )

    def salida(tipo: str, razon: str) -> Clasificacion:
        return Clasificacion(
            tipo=tipo,
            enunciador_nombre=enunciador.nombre,
            enunciador_cargo=enunciador.cargo,
            enunciador_dominio=dominio_salida,
            razon=razon,
        )

    # 1 · Autodeclaración: la persona pertenece a la organización con autoridad
    #     sobre el dominio del que habla.
    if enunciador.nivel in (NIVEL_MAXIMA, NIVEL_FUNCIONAL) and enunciador.vinculado:
        if _dominio_bajo_autoridad(enunciador):
            return salida(
                TIPO_AUTODECLARACION,
                f"cargo '{enunciador.cargo}' ({enunciador.nivel}) de la propia "
                f"organización, hablando de '{enunciador.dominio}'",
            )

    # 2 · Corroborante: posición de tensión con la organización Y fricción
    #     explícita en el texto. Faltando cualquiera de las dos, no basta.
    if enunciador.nivel == NIVEL_TENSION and _hay_friccion(texto, pos_tension):
        return salida(
            TIPO_CORROBORANTE,
            f"posición de tensión ('{enunciador.cargo}') con marcador de "
            f"fricción en el texto",
        )

    # 3 · Huella práctica: sin declaración de persona, pero la organización
    #     MISMA publicó el acto. Es estructura de la fuente (origen_declaracion
    #     == 'operador': vacante, comunicado propio), no lectura del contenido.
    if enunciador.nombre is None and enunciador.nivel == NIVEL_NINGUNO:
        if (evidencia.get("origen_declaracion") or "").strip() == "operador":
            return salida(
                TIPO_HUELLA_PRACTICA,
                "acto publicado por la propia organización "
                "(origen_declaracion='operador'), sin declaración de persona",
            )

    # 4 · REGLA DURA: todo lo demás es contextual.
    return salida(
        TIPO_CONTEXTUAL,
        "sin atribución identificable o sin autoridad/fricción demostrable "
        "(regla dura)",
    )
