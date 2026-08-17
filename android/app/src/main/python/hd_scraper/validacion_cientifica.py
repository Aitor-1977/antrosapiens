"""Validación Científica del Peritaje Antropológico — Capa 11.

Somete cada expediente (hipótesis de Dolor Cultural™ + evidencia capturada por
este mismo motor) a una batería de controles epistémicos DETERMINISTAS antes de
que la hipótesis pueda sostenerse. No inventa datos, no usa IA ni red: audita la
calidad de la evidencia ya extraída y emite un **Dictamen Científico**.

Esta capa NO decide acción comercial (eso es exclusivo de Motor B / RadarHD).
Solo responde una pregunta metodológica: *¿la evidencia disponible sostiene la
hipótesis, o hay que bloquearla por insuficiente, contradictoria o no trazable?*

Encaja en la «Frontera de Interpretación» del repo: interpretación determinista
y auditable sobre datos YA extraídos por este motor (mismo insumo ⇒ mismo
resultado). Es el guardián de rigor de la Capa 10 (Curaduría Antropológica).

Flujo:
  … → Expedientes → Curaduría (Capa 10) → VALIDACIÓN CIENTÍFICA (Capa 11)

Contiene 14 funciones puras de validación científica. Ninguna toca disco, red
ni base de datos; todas reciben un ``expediente`` (dict) y devuelven un dict o
un valor escalar reproducible.
"""
from __future__ import annotations

from urllib.parse import urlparse

from .analisis import SENALES_CAMBIO, SENALES_DOLOR, analizar

# ── Criterios declarados (auditables) ─────────────────────────────────────────
# Umbrales explícitos: cambiar un criterio científico exige cambiar esta tabla,
# nunca esconderlo en la lógica. Todos son deterministas.
MIN_EVIDENCIAS = 3                 # corpus mínimo para sostener una hipótesis
MIN_FUENTES_INDEPENDIENTES = 2     # corroboración: al menos dos fuentes distintas
UMBRAL_SOLIDEZ_BLOQUEO = 40        # solidez por debajo ⇒ hipótesis bloqueada
UMBRAL_SUFICIENCIA_BLOQUEO = 40    # suficiencia por debajo ⇒ hipótesis bloqueada
UMBRAL_SOLIDEZ_VALIDADA = 65       # solidez para veredicto VALIDADA
UMBRAL_SUFICIENCIA_VALIDADA = 60   # suficiencia para veredicto VALIDADA

# Veredictos posibles del Dictamen Científico.
VEREDICTOS = (
    "VALIDADA",          # evidencia suficiente y sólida, sin contradicciones
    "VALIDADA_PARCIAL",  # plausible pero preliminar: ampliar corpus
    "NO_VALIDADA",       # hay evidencia pero contradicciones/vacíos lo impiden
    "BLOQUEADA",         # evidencia insuficiente: hipótesis bloqueada
    "SIN_HIPOTESIS",     # no hay hipótesis de deuda que validar
)


# ── Accesores tolerantes a la forma de la evidencia ───────────────────────────
# Las evidencias llegan en dos formas equivalentes:
#   - expediente (_construir_expedientes): {texto, fuente, fecha, url, tipo_evento, confianza}
#   - fila cruda (dolormap): {cita_textual, nombre_medio, fecha_publicacion, url_fuente, ...}
# Estos accesores leen ambas sin acoplar la validación a una sola forma.

def _ev_url(ev: dict) -> str:
    return (ev.get("url") or ev.get("url_fuente") or "").strip()


def _ev_fuente(ev: dict) -> str:
    return (ev.get("fuente") or ev.get("nombre_medio") or "").strip()


def _ev_fecha(ev: dict) -> str:
    return (ev.get("fecha") or ev.get("fecha_publicacion") or "").strip()


def _ev_tipo(ev: dict) -> str:
    return (ev.get("tipo_evento") or "").strip()


def _ev_confianza(ev: dict) -> float:
    try:
        return max(0.0, min(float(ev.get("confianza") or 0.0), 1.0))
    except (TypeError, ValueError):
        return 0.0


def _dominio(url: str) -> str:
    """Dominio normalizado de una URL (sin www). Puro, sin red."""
    if not url:
        return ""
    try:
        neto = urlparse(url if "://" in url else "http://" + url).netloc.lower()
    except (ValueError, TypeError):
        return ""
    return neto[4:] if neto.startswith("www.") else neto


def _fecha_valida(f: str) -> bool:
    """ISO 8601 mínimamente plausible y distinta del marcador ``no_fechado``."""
    if not f or f == "no_fechado":
        return False
    return len(f) >= 8 and f[:4].isdigit() and f[4:5] == "-"


def _evidencias(expediente: dict) -> list[dict]:
    ev = expediente.get("evidencias", [])
    # ``dolormap`` anida en {"total": n, "items": [...]}; el expediente da lista.
    if isinstance(ev, dict):
        return list(ev.get("items", []))
    return list(ev or [])


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> int:
    return int(round(max(lo, min(x, hi))))


# ── 1. Fuentes independientes ─────────────────────────────────────────────────
def contar_fuentes_independientes(evidencias: list[dict]) -> int:
    """Número de fuentes DISTINTAS que sostienen la evidencia.

    Corrobora por dominio de URL; si no hay URL, cae al nombre del medio. Dos
    notas del mismo medio no cuentan como corroboración independiente.
    """
    claves: set[str] = set()
    for ev in evidencias or []:
        dom = _dominio(_ev_url(ev))
        clave = dom or _ev_fuente(ev).lower()
        if clave:
            claves.add(clave)
    return len(claves)


# ── 2. Confianza agregada ─────────────────────────────────────────────────────
def calcular_confianza_agregada(evidencias: list[dict]) -> float:
    """Confianza agregada (0–1) por corroboración entre fuentes independientes.

    Combina la mejor confianza de cada fuente con un OR-ruidoso: fuentes
    independientes que apuntan a lo mismo elevan la confianza sin superar 1.0.
    Varias notas del mismo medio no se acumulan (se toma su mejor confianza).
    """
    if not evidencias:
        return 0.0
    mejor_por_fuente: dict[str, float] = {}
    for ev in evidencias:
        dom = _dominio(_ev_url(ev))
        clave = dom or _ev_fuente(ev).lower() or id(ev)
        c = _ev_confianza(ev)
        if c > mejor_por_fuente.get(clave, 0.0):
            mejor_por_fuente[clave] = c
    prod = 1.0
    for c in mejor_por_fuente.values():
        prod *= (1.0 - c)
    return round(1.0 - prod, 4)


# ── 3. Trazabilidad ───────────────────────────────────────────────────────────
def validar_trazabilidad(expediente: dict) -> dict:
    """Cada evidencia debe poder rastrearse a su fuente (URL + medio).

    Sin trazabilidad la hipótesis no es auditable. Devuelve el conteo de
    evidencias trazables/no trazables y el detalle de las que fallan.
    """
    evs = _evidencias(expediente)
    total = len(evs)
    no_trazables: list[dict] = []
    for i, ev in enumerate(evs):
        url = _ev_url(ev)
        fuente = _ev_fuente(ev)
        faltan = []
        if not url:
            faltan.append("url_fuente")
        if not fuente:
            faltan.append("nombre_medio")
        if faltan:
            no_trazables.append({"indice": i, "faltan": faltan,
                                 "fuente": fuente or "(desconocida)"})
    trazables = total - len(no_trazables)
    ratio = round(trazables / total, 4) if total else 0.0
    return {
        "total": total,
        "trazables": trazables,
        "no_trazables": len(no_trazables),
        "ratio": ratio,
        "completa": total > 0 and len(no_trazables) == 0,
        "detalle": no_trazables,
    }


# ── 4. Fechado (consumibilidad) ───────────────────────────────────────────────
def validar_fechado(expediente: dict) -> dict:
    """Cuántas evidencias tienen fecha ISO válida (consumibles por la API).

    Coherente con el contrato del repo: ``fecha_publicacion`` ausente ⇒
    ``no_fechado`` ⇒ no consumible por la API (pero no se rechaza).
    """
    evs = _evidencias(expediente)
    total = len(evs)
    fechadas = sum(1 for ev in evs if _fecha_valida(_ev_fecha(ev)))
    ratio = round(fechadas / total, 4) if total else 0.0
    return {
        "total": total,
        "fechadas": fechadas,
        "no_fechadas": total - fechadas,
        "ratio": ratio,
        "todas_consumibles": total > 0 and fechadas == total,
    }


# ── 5. Suficiencia del corpus ─────────────────────────────────────────────────
def calcular_suficiencia_corpus(expediente: dict) -> dict:
    """¿Hay evidencia suficiente para siquiera plantear la hipótesis? (0–100).

    Cruza volumen de evidencia, fuentes independientes, fechado y diversidad de
    señales. Es la puerta de entrada: sin suficiencia, la hipótesis se bloquea.
    """
    evs = _evidencias(expediente)
    n_ev = len(evs)
    fuentes = contar_fuentes_independientes(evs)
    fechado = validar_fechado(expediente)["ratio"]
    n_senales = len(set(expediente.get("keywords", []) or []))

    comp_ev = min(n_ev, MIN_EVIDENCIAS) / MIN_EVIDENCIAS * 40
    comp_fuentes = min(fuentes, MIN_FUENTES_INDEPENDIENTES) / MIN_FUENTES_INDEPENDIENTES * 30
    comp_fechado = fechado * 20
    comp_diversidad = min(n_senales, 3) / 3 * 10
    score = _clamp(comp_ev + comp_fuentes + comp_fechado + comp_diversidad)

    suficiente = (
        n_ev >= MIN_EVIDENCIAS
        and fuentes >= MIN_FUENTES_INDEPENDIENTES
        and score >= UMBRAL_SUFICIENCIA_VALIDADA
    )
    if score >= UMBRAL_SUFICIENCIA_VALIDADA:
        nivel = "suficiente"
    elif score >= UMBRAL_SUFICIENCIA_BLOQUEO:
        nivel = "parcial"
    else:
        nivel = "insuficiente"

    return {
        "score": score,
        "nivel": nivel,
        "suficiente": suficiente,
        "evidencias": n_ev,
        "fuentes_independientes": fuentes,
        "ratio_fechado": fechado,
        "senales_distintas": n_senales,
    }


# ── 6. Solidez de la hipótesis ────────────────────────────────────────────────
def calcular_solidez(expediente: dict) -> dict:
    """Solidez de la hipótesis (0–100): qué tanto la sostiene la evidencia.

    Suma volumen, corroboración independiente, convergencia (patrones),
    profundidad del dolor y confianza agregada; resta por contradicciones y
    vacíos detectados. Determinista y acotado a [0, 100].
    """
    evs = _evidencias(expediente)
    n_ev = len(evs)
    fuentes = contar_fuentes_independientes(evs)
    n_patrones = len(expediente.get("patrones", []) or [])
    profundidad = float(expediente.get("profundidad_dolor", 0) or 0)
    conf = calcular_confianza_agregada(evs)

    n_contra = len(detectar_contradicciones(expediente))
    n_vacios = len(detectar_vacios(expediente))

    positivo = (
        min(n_ev, 6) / 6 * 25
        + min(fuentes, 3) / 3 * 20
        + min(n_patrones, 2) / 2 * 15
        + profundidad / 100 * 20
        + conf * 20
    )
    penalizacion = min(n_contra * 10, 30) + min(n_vacios * 3, 15)
    score = _clamp(positivo - penalizacion)

    if score >= UMBRAL_SOLIDEZ_VALIDADA:
        nivel = "alta"
    elif score >= UMBRAL_SOLIDEZ_BLOQUEO:
        nivel = "media"
    else:
        nivel = "baja"

    return {
        "score": score,
        "nivel": nivel,
        "evidencias": n_ev,
        "fuentes_independientes": fuentes,
        "patrones": n_patrones,
        "profundidad_dolor": int(profundidad),
        "confianza_agregada": conf,
        "penalizacion": penalizacion,
    }


# ── 7. Contradicciones ────────────────────────────────────────────────────────
def detectar_contradicciones(expediente: dict) -> list[dict]:
    """Detecta conflictos observables en la evidencia del expediente.

    No juzga el contenido: contrasta señales y campos estructurales entre sí.
    """
    contradicciones: list[dict] = []
    kws = set(expediente.get("keywords", []) or [])
    patrones = expediente.get("patrones", []) or []
    evs = _evidencias(expediente)

    # 1) Dolor y crecimiento coexisten sin patrón que los concilie.
    if (kws & SENALES_DOLOR) and (kws & SENALES_CAMBIO) and not patrones:
        contradicciones.append({
            "tipo": "dolor_y_crecimiento_sin_patron",
            "descripcion": "Coexisten señales de dolor y de crecimiento sin un "
                           "patrón que las concilie: la hipótesis debe explicar "
                           "por qué conviven antes de sostenerse.",
            "severidad": "alta",
        })

    # 2) Eventos estructuralmente opuestos en la misma evidencia agregada.
    tipos = {_ev_tipo(ev) for ev in evs}
    if "despido" in tipos and "contratacion" in tipos:
        contradicciones.append({
            "tipo": "eventos_opuestos",
            "descripcion": "La evidencia reporta despidos y contrataciones a la "
                           "vez: puede ser reestructura real, pero exige "
                           "desambiguación temporal antes de concluir.",
            "severidad": "media",
        })

    # 3) Clasificada como prioritaria pero declarada no viable.
    if expediente.get("scoring") == "A" and expediente.get("viabilidad") == "descartable":
        contradicciones.append({
            "tipo": "prioridad_vs_viabilidad",
            "descripcion": "Scoring A (dolor explícito) junto a viabilidad "
                           "descartable: la clasificación es internamente "
                           "inconsistente.",
            "severidad": "media",
        })

    return contradicciones


# ── 8. Vacíos ─────────────────────────────────────────────────────────────────
def detectar_vacios(expediente: dict) -> list[dict]:
    """Detecta huecos de evidencia que debilitan la hipótesis (sin inventar)."""
    vacios: list[dict] = []
    evs = _evidencias(expediente)
    n_ev = len(evs)
    fuentes = contar_fuentes_independientes(evs)
    kws = set(expediente.get("keywords", []) or [])
    patrones = expediente.get("patrones", []) or []
    fechado = validar_fechado(expediente)
    profundidad = float(expediente.get("profundidad_dolor", 0) or 0)

    if not (expediente.get("vertical") or "").strip():
        vacios.append({"tipo": "sin_vertical",
                       "descripcion": "Sin vertical declarada: falta el contexto "
                                      "sectorial que matiza la lectura."})
    if fuentes < MIN_FUENTES_INDEPENDIENTES:
        vacios.append({"tipo": "fuente_unica",
                       "descripcion": f"Solo {fuentes} fuente(s) independiente(s): "
                                      "sin corroboración cruzada."})
    if n_ev < MIN_EVIDENCIAS:
        vacios.append({"tipo": "corpus_escaso",
                       "descripcion": f"Corpus escaso ({n_ev} evidencia(s), "
                                      f"mínimo {MIN_EVIDENCIAS})."})
    if fechado["no_fechadas"] > 0:
        vacios.append({"tipo": "evidencia_sin_fecha",
                       "descripcion": f"{fechado['no_fechadas']} evidencia(s) sin "
                                      "fecha: no consumibles por la API."})
    if len(kws) <= 1:
        vacios.append({"tipo": "senal_unica",
                       "descripcion": "Hipótesis apoyada en una sola señal: base "
                                      "demasiado estrecha."})
    if not patrones:
        vacios.append({"tipo": "sin_convergencia",
                       "descripcion": "Sin patrones de convergencia entre señales."})
    if profundidad >= 70 and n_ev <= 1:
        vacios.append({"tipo": "profundidad_sin_volumen",
                       "descripcion": "Profundidad de dolor alta sostenida por una "
                                      "sola evidencia: falta volumen."})
    return vacios


# ── 9. Reproducibilidad ───────────────────────────────────────────────────────
def validar_reproducibilidad(expediente: dict) -> dict:
    """Confirma que la inferencia es determinista y coincide con lo declarado.

    Reejecuta el análisis (``analizar``) sobre las mismas señales dos veces y
    comprueba: (a) que ambas corridas son idénticas (determinismo) y (b) que el
    ``scoring`` y ``tipo_deuda`` declarados en el expediente se reproducen desde
    las señales. ``scoring`` y ``tipo_deuda`` dependen solo de las keywords, así
    que la comprobación es exacta y offline.
    """
    keywords = list(expediente.get("keywords", []) or [])
    vertical = (expediente.get("vertical") or "")

    r1 = analizar(keywords, vertical=vertical)
    r2 = analizar(keywords, vertical=vertical)
    determinista = r1 == r2

    discrepancias: list[dict] = []
    for campo in ("scoring", "tipo_deuda"):
        if campo in expediente:
            esperado = r1.get(campo, "")
            declarado = expediente.get(campo, "")
            if declarado != esperado:
                discrepancias.append({
                    "campo": campo,
                    "declarado": declarado,
                    "reproducido": esperado,
                })

    return {
        "determinista": determinista,
        "consistente": len(discrepancias) == 0,
        "reproducible": determinista and len(discrepancias) == 0,
        "discrepancias": discrepancias,
    }


# ── 10. Nivel de evidencia ────────────────────────────────────────────────────
def nivel_evidencia(expediente: dict) -> dict:
    """Gradúa la fuerza de la evidencia (I–IV), estilo escala GRADE.

    I = alta, II = moderada, III = baja, IV = insuficiente.
    """
    solidez = calcular_solidez(expediente)["score"]
    suf = calcular_suficiencia_corpus(expediente)
    n_contra = len(detectar_contradicciones(expediente))
    fuentes = suf["fuentes_independientes"]
    suficiencia = suf["score"]

    if (solidez >= UMBRAL_SOLIDEZ_VALIDADA and suficiencia >= UMBRAL_SUFICIENCIA_VALIDADA
            and n_contra == 0 and fuentes >= MIN_FUENTES_INDEPENDIENTES):
        nivel, etiqueta = "I", "alta"
        desc = "Evidencia corroborada por múltiples fuentes, sólida y sin contradicciones."
    elif solidez >= 45 and suficiencia >= 45 and n_contra == 0:
        nivel, etiqueta = "II", "moderada"
        desc = "Evidencia razonable pero mejorable: ampliar corroboración."
    elif solidez >= 25 or suficiencia >= 25:
        nivel, etiqueta = "III", "baja"
        desc = "Evidencia débil o preliminar: la hipótesis es tentativa."
    else:
        nivel, etiqueta = "IV", "insuficiente"
        desc = "Evidencia insuficiente para sostener cualquier hipótesis."

    return {"nivel": nivel, "etiqueta": etiqueta, "descripcion": desc}


# ── 11. Bloqueo automático de hipótesis ───────────────────────────────────────
def evaluar_bloqueo_hipotesis(expediente: dict) -> dict:
    """Bloquea automáticamente la hipótesis si la evidencia es insuficiente.

    Este es el candado de rigor: una hipótesis de Dolor Cultural sin corpus,
    sin corroboración independiente o con solidez/suficiencia bajo umbral queda
    BLOQUEADA — Motor B no debe escalarla hasta ampliar la evidencia.
    """
    motivos: list[str] = []
    hipotesis = (expediente.get("tipo_deuda") or "").strip()

    if not hipotesis:
        return {
            "bloqueada": True,
            "hipotesis": "",
            "motivos": ["No hay hipótesis de Dolor Cultural declarada para validar."],
        }

    evs = _evidencias(expediente)
    n_ev = len(evs)
    fuentes = contar_fuentes_independientes(evs)
    suf = calcular_suficiencia_corpus(expediente)["score"]
    sol = calcular_solidez(expediente)["score"]

    if n_ev < MIN_EVIDENCIAS:
        motivos.append(f"Corpus insuficiente: {n_ev} evidencia(s) (mínimo {MIN_EVIDENCIAS}).")
    if fuentes < MIN_FUENTES_INDEPENDIENTES:
        motivos.append(f"Corroboración insuficiente: {fuentes} fuente(s) "
                       f"independiente(s) (mínimo {MIN_FUENTES_INDEPENDIENTES}).")
    if suf < UMBRAL_SUFICIENCIA_BLOQUEO:
        motivos.append(f"Suficiencia de corpus bajo umbral ({suf} < {UMBRAL_SUFICIENCIA_BLOQUEO}).")
    if sol < UMBRAL_SOLIDEZ_BLOQUEO:
        motivos.append(f"Solidez bajo umbral ({sol} < {UMBRAL_SOLIDEZ_BLOQUEO}).")

    return {
        "bloqueada": bool(motivos),
        "hipotesis": hipotesis,
        "motivos": motivos,
    }


# ── 12. Clasificación del veredicto ───────────────────────────────────────────
def clasificar_veredicto(
    solidez: int,
    suficiencia: int,
    n_contradicciones: int,
    bloqueada: bool,
    tiene_hipotesis: bool,
) -> str:
    """Traduce las métricas de validación al veredicto del Dictamen Científico."""
    if not tiene_hipotesis:
        return "SIN_HIPOTESIS"
    if bloqueada:
        return "BLOQUEADA"
    if n_contradicciones > 0:
        return "NO_VALIDADA"
    if solidez >= UMBRAL_SOLIDEZ_VALIDADA and suficiencia >= UMBRAL_SUFICIENCIA_VALIDADA:
        return "VALIDADA"
    if solidez >= UMBRAL_SOLIDEZ_BLOQUEO and suficiencia >= UMBRAL_SUFICIENCIA_BLOQUEO:
        return "VALIDADA_PARCIAL"
    return "NO_VALIDADA"


_RECOMENDACION = {
    "VALIDADA": "Hipótesis con soporte suficiente para escalar a peritaje "
                "cualitativo en Motor B (RadarHD). La decisión y ejecución "
                "comercial es exclusiva de Motor B.",
    "VALIDADA_PARCIAL": "Hipótesis plausible pero preliminar: ampliar el corpus "
                        "y la corroboración antes de escalar.",
    "NO_VALIDADA": "Resolver contradicciones y vacíos antes de sostener la "
                   "hipótesis; no escalar en su estado actual.",
    "BLOQUEADA": "Evidencia insuficiente: hipótesis bloqueada hasta ampliar la "
                 "captura (más evidencias y fuentes independientes).",
    "SIN_HIPOTESIS": "No hay hipótesis que validar; ampliar la captura de "
                     "evidencia antes de inferir Dolor Cultural.",
}


# ── 13. Emisión del Dictamen Científico ───────────────────────────────────────
def emitir_dictamen_cientifico(expediente: dict) -> dict:
    """Emite el Dictamen Científico compacto de un expediente.

    Reúne solidez, suficiencia, contradicciones, vacíos, reproducibilidad,
    nivel de evidencia y bloqueo en un veredicto único con recomendación
    metodológica (no comercial) y limitaciones declaradas.
    """
    hipotesis = (expediente.get("tipo_deuda") or "").strip()
    solidez = calcular_solidez(expediente)
    suficiencia = calcular_suficiencia_corpus(expediente)
    contradicciones = detectar_contradicciones(expediente)
    vacios = detectar_vacios(expediente)
    reproducibilidad = validar_reproducibilidad(expediente)
    nivel = nivel_evidencia(expediente)
    bloqueo = evaluar_bloqueo_hipotesis(expediente)

    veredicto = clasificar_veredicto(
        solidez["score"], suficiencia["score"], len(contradicciones),
        bloqueo["bloqueada"], bool(hipotesis),
    )

    nombre = expediente.get("nombre", "la organización")
    if veredicto == "VALIDADA":
        resumen = (f"La hipótesis de {hipotesis} sobre {nombre} está VALIDADA: "
                   f"solidez {solidez['score']}/100, suficiencia "
                   f"{suficiencia['score']}/100, evidencia nivel {nivel['nivel']}, "
                   "sin contradicciones.")
    elif veredicto == "VALIDADA_PARCIAL":
        resumen = (f"La hipótesis de {hipotesis} sobre {nombre} es plausible pero "
                   f"PRELIMINAR (solidez {solidez['score']}, suficiencia "
                   f"{suficiencia['score']}). Requiere más corroboración.")
    elif veredicto == "NO_VALIDADA":
        resumen = (f"La hipótesis de {hipotesis} sobre {nombre} NO se valida: "
                   f"{len(contradicciones)} contradicción(es) y "
                   f"{len(vacios)} vacío(s) sin resolver.")
    elif veredicto == "BLOQUEADA":
        resumen = (f"La hipótesis de {hipotesis} sobre {nombre} queda BLOQUEADA por "
                   "evidencia insuficiente. " + " ".join(bloqueo["motivos"]))
    else:  # SIN_HIPOTESIS
        resumen = (f"No hay hipótesis de Dolor Cultural que validar para {nombre}: "
                   "la evidencia disponible no permite inferir una deuda.")

    limitaciones = [v["descripcion"] for v in vacios]
    if not reproducibilidad["consistente"]:
        limitaciones.append("La inferencia declarada no se reproduce exactamente "
                            "desde las señales (revisar pipeline).")

    return {
        "org": expediente.get("nombre", ""),
        "hipotesis": hipotesis,
        "veredicto": veredicto,
        "hipotesis_bloqueada": bloqueo["bloqueada"],
        "solidez": solidez["score"],
        "suficiencia": suficiencia["score"],
        "nivel_evidencia": nivel["nivel"],
        "contradicciones": len(contradicciones),
        "vacios": len(vacios),
        "reproducible": reproducibilidad["reproducible"],
        "resumen": resumen,
        "recomendacion": _RECOMENDACION[veredicto],
        "limitaciones": limitaciones,
    }


# ── 14. Validación completa del expediente (orquestador) ──────────────────────
def validar_expediente(expediente: dict) -> dict:
    """Corre la batería completa de validación científica sobre un expediente.

    Devuelve el informe detallado (todas las secciones) con el Dictamen
    Científico embebido. Punto de entrada del endpoint ``GET /validacion/{org}``.
    """
    return {
        "org": expediente.get("nombre", ""),
        "hipotesis": (expediente.get("tipo_deuda") or "").strip(),
        "trazabilidad": validar_trazabilidad(expediente),
        "fechado": validar_fechado(expediente),
        "suficiencia_corpus": calcular_suficiencia_corpus(expediente),
        "solidez": calcular_solidez(expediente),
        "contradicciones": detectar_contradicciones(expediente),
        "vacios": detectar_vacios(expediente),
        "reproducibilidad": validar_reproducibilidad(expediente),
        "nivel_evidencia": nivel_evidencia(expediente),
        "bloqueo": evaluar_bloqueo_hipotesis(expediente),
        "dictamen_cientifico": emitir_dictamen_cientifico(expediente),
    }
