"""Síntesis Estructural por organización (Capa 19 · alerta estructural).

Reordenamiento determinista de las señales Nivel 1 que ESTE motor ya extrajo,
para que el consumidor (la app Radar) deje de recibir noticias crudas y reciba
una estructura mínima:

    [patrón de comportamiento, señal de tensión/dolor, actores involucrados,
     sustancia/métrica] + [evidencia_urls]

Autorizado por el operador el 2026-08-04 (ver CLAUDE.md → «Frontera de
Interpretación»). Reglas inmutables:

- 100% determinista y grounded: mismo insumo ⇒ mismo JSON; cada campo cita su
  evidencia (marcador textual literal o metadata de captura).
- Sin IA, sin juicio libre, sin red. NUNCA inventa: sin marcador ⇒ estado
  ``sin_marcador``; corpus insuficiente ⇒ ``insuficiente``.
- Patrón y tensión usan la taxonomía GENÉRICA/pública de Motor A
  (``signals.SENALES`` y ``tipo_evento``), NO la taxonomía propietaria de
  Deuda Cultural™ (eso es Motor B / ``lectura_estructural``).
- No decide ni ejecuta acción comercial.
"""
from __future__ import annotations

from collections import Counter

from .signals import SENALES, detectar_keywords

ESTADO_SINTETIZADO = "sintetizado"
ESTADO_INSUFICIENTE = "insuficiente"
ESTADO_SIN_MARCADOR = "sin_marcador"

MIN_EVIDENCIAS = 3

NOTA_PRELIMINAR = (
    "Síntesis determinista preliminar del corpus ya extraído por Motor A; "
    "verificar en campo."
)

# Orden de la taxonomía Nivel 1 (genérica/pública) para desempates deterministas.
ORDEN_KEYWORDS = list(SENALES.keys())

# Etiqueta pública de cada tipo de evento del contrato (taxonomía Motor A).
ETIQUETA_EVENTO = {
    "ronda": "levantamiento de capital (ronda)",
    "contratacion": "crecimiento de plantilla (contratación)",
    "despido": "contracción de plantilla (despidos)",
    "lanzamiento": "lanzamiento de producto o servicio",
    "queja": "fricción con clientes (quejas públicas)",
    "cambio_sitio": "cambio de sede u operaciones",
}

# Patrón de comportamiento público que denota cada señal Nivel 1.
PATRON_POR_KEYWORD = {
    "ronda_inversion": "levantamiento de capital (ronda de financiamiento)",
    "reduccion_personal": "reestructura con recorte de personal",
    "friccion_retencion": "fricción de retención de clientes",
    "expansion": "expansión a nuevos mercados o plazas",
    "cambio_liderazgo": "renovación del liderazgo ejecutivo",
    "lanzamiento": "lanzamiento de producto o servicio",
    "adquisicion": "adquisición o fusión",
    "alianza": "alianza estratégica o colaboración",
    "contratacion_masiva": "contratación masiva / crecimiento de plantilla",
    "cierre_operaciones": "cierre o contracción de operaciones",
    "crecimiento": "crecimiento acelerado (ingresos o ventas)",
    "regulacion": "presión regulatoria o de cumplimiento",
}

# Señales Nivel 1 de connotación negativa pública (base de la tensión/dolor).
# No es Deuda Cultural™: es vocabulario estándar de negocio ya extraído.
TENSION_KEYWORDS = (
    "reduccion_personal",
    "friccion_retencion",
    "cierre_operaciones",
    "regulacion",
)
TENSION_EVENTOS = {"despido", "queja"}


def _orden_patron() -> list[str]:
    orden: list[str] = []
    for k in ORDEN_KEYWORDS:
        p = PATRON_POR_KEYWORD[k]
        if p not in orden:
            orden.append(p)
    for v in ETIQUETA_EVENTO.values():
        if v not in orden:
            orden.append(v)
    return orden


ORDEN_PATRONES = _orden_patron()


def _normalizar_evidencias(evidencias: list[dict]) -> list[dict]:
    """Normaliza las filas del contrato a la forma interna, sin texto vacío."""
    out: list[dict] = []
    for e in evidencias or []:
        cita = (e.get("cita_textual") or "").strip()
        if not cita:
            continue
        keywords = e.get("keywords") or []
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]
        conocidos = [k for k in keywords if k in SENALES]
        if not conocidos:
            conocidos = detectar_keywords(cita)
        out.append({
            "cita": cita,
            "url": (e.get("url_fuente") or "").strip(),
            "medio": (e.get("nombre_medio") or "").strip(),
            "empresa": (e.get("empresa_mencionada") or "").strip(),
            "persona": (e.get("persona_citada") or "").strip(),
            "cargo": (e.get("cargo") or "").strip(),
            "tipo_evento": (e.get("tipo_evento") or "").strip(),
            "fecha": (e.get("fecha_publicacion") or "").strip(),
            "confianza": float(e.get("confianza") or 0.0),
            "keywords": conocidos,
        })
    return out


def _ordenar(evs: list[dict]) -> list[dict]:
    """Orden estable (confianza desc, cita asc) para salida reproducible."""
    return sorted(evs, key=lambda e: (-e["confianza"], e["cita"]))


def _patron(evs: list[dict]) -> str | None:
    """Patrón de comportamiento dominante; None si no hay señales reconocidas."""
    pesos: Counter = Counter()
    for e in evs:
        for k in e["keywords"]:
            p = PATRON_POR_KEYWORD.get(k)
            if p:
                pesos[p] += 1.0
        etiqueta = ETIQUETA_EVENTO.get(e["tipo_evento"])
        if etiqueta:
            pesos[etiqueta] += 0.5
    if not pesos:
        return None
    return max(pesos, key=lambda p: (pesos[p], -ORDEN_PATRONES.index(p)))


def _marcadores_literal(cita: str, tags: list[str]) -> list[str]:
    """Frases literales de la taxonomía presentes en la cita (grounding)."""
    t = cita.lower()
    marcadores: list[str] = []
    for tag in tags:
        for frase in SENALES.get(tag, ()):
            if frase in t:
                marcadores.append(frase)
    return marcadores


def _tension(evs: list[dict]) -> dict:
    """Señal de tensión/dolor grounded: primera evidencia con marcador negativo."""
    for e in evs:
        tags = [t for t in e["keywords"] if t in TENSION_KEYWORDS]
        if tags or e["tipo_evento"] in TENSION_EVENTOS:
            senal = ", ".join(PATRON_POR_KEYWORD[t] for t in tags)
            if not senal:
                senal = ETIQUETA_EVENTO.get(e["tipo_evento"], e["tipo_evento"])
            return {
                "presente": True,
                "señal": senal,
                "marcadores_textuales": _marcadores_literal(e["cita"], tags),
                "cita_textual": e["cita"][:280],
                "confianza": e["confianza"],
            }
    return {
        "presente": False,
        "señal": "sin marcador de tensión explícito en el corpus",
        "marcadores_textuales": [],
        "cita_textual": "",
        "confianza": 0.0,
    }


def _actores(evs: list[dict], org: str) -> list[dict]:
    actores: list[dict] = []
    vistos: set[tuple[str, str]] = set()

    def agregar(nombre: str, rol: str) -> None:
        clave = (nombre.lower(), rol)
        if nombre and clave not in vistos:
            vistos.add(clave)
            actores.append({"nombre": nombre, "rol": rol})

    agregar(org, "organización observada")
    for e in evs:
        if e["persona"]:
            rol = f"persona citada — {e['cargo']}" if e["cargo"] else "persona citada"
            agregar(e["persona"], rol)
        if e["empresa"] and e["empresa"].lower() != org.lower():
            agregar(e["empresa"], "organización mencionada")
    return actores


def _meses_cobertura(fechas: list[str]) -> int:
    meses: list[int] = []
    for f in fechas:
        if len(f) >= 7 and f[4:5] == "-":
            try:
                meses.append(int(f[:4]) * 12 + int(f[5:7]))
            except ValueError:
                continue
    if not meses:
        return 0
    return max(0, max(meses) - min(meses) + 1)


def _sustancia(evs: list[dict]) -> dict:
    n = len(evs)
    fuentes = sorted({e["medio"] for e in evs if e["medio"]})
    meses = _meses_cobertura([e["fecha"] for e in evs])
    confianza = round(sum(e["confianza"] for e in evs) / n, 2) if n else 0.0
    volumen = min(n / 10.0, 1.0)
    fuentes_norm = min(len(fuentes) / 6.0, 1.0)
    cobertura = min(meses / 6.0, 1.0)
    indice = round(
        0.40 * volumen + 0.30 * fuentes_norm + 0.20 * cobertura + 0.10 * confianza,
        2,
    )
    return {
        "evidencias": n,
        "fuentes_distintas": len(fuentes),
        "meses_cobertura": meses,
        "confianza_media": confianza,
        "indice_sustancia": min(indice, 1.0),
        "umbral": "conforme" if n >= MIN_EVIDENCIAS else "insuficiente",
    }


def _evidencia_urls(evs: list[dict]) -> list[str]:
    urls: list[str] = []
    vistos: set[str] = set()
    for e in evs:
        u = e["url"]
        if u and u not in vistos:
            vistos.add(u)
            urls.append(u)
    return urls


def sintetizar(evidencias: list[dict], org: str, *, minimo_evidencias: int = MIN_EVIDENCIAS) -> dict:
    """Síntesis estructural de una organización (determinista, grounded).

    ``evidencias`` es una lista de filas del contrato (forma de
    ``_row_a_evidencia``): ``cita_textual``, ``url_fuente``, ``nombre_medio``,
    ``empresa_mencionada``, ``persona_citada``, ``cargo``, ``tipo_evento``,
    ``fecha_publicacion``, ``confianza``, ``keywords``.
    """
    org = (org or "").strip()
    evs = _ordenar(_normalizar_evidencias(evidencias))
    n = len(evs)
    patron = _patron(evs)
    tension = _tension(evs)

    if n < minimo_evidencias:
        estado = ESTADO_INSUFICIENTE
        motivo = (
            f"corpus con {n} evidencia(s); se requieren {minimo_evidencias} "
            "para una síntesis mínima."
        )
    elif patron is None:
        estado = ESTADO_SIN_MARCADOR
        motivo = "sin señales Nivel 1 ni tipo de evento reconocido en el corpus."
    else:
        estado = ESTADO_SINTETIZADO
        motivo = ""

    return {
        "org": org,
        "version_esquema": "sintesis_estructural.v1",
        "estado": estado,
        "motivo": motivo,
        "patron_comportamiento": patron,
        "senal_tension_dolor": tension["señal"],
        "tension_presente": tension["presente"],
        "marcadores_textuales": tension["marcadores_textuales"],
        "cita_tension": tension["cita_textual"],
        "actores_involucrados": _actores(evs, org),
        "sustancia_metrica": _sustancia(evs),
        "evidencia_urls": _evidencia_urls(evs),
        "nota": NOTA_PRELIMINAR,
    }
