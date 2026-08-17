"""Gobernanza Científica, Auditoría Total y Reproducibilidad — Capa 12.

Último paso del pipeline. NO genera hipótesis, NO toca Dolor Cultural, NO toca
el Motor de Inferencia ni la Validación Científica. Su única función es
garantizar que **toda conclusión sea auditable, reproducible y explicable**:

  Captura → Curaduría → Inferencia → Validación Científica → GOBERNANZA → API

Principios (inviolables en esta capa):
  - Toda afirmación puede reconstruirse.        - Toda evidencia tiene origen.
  - Toda hipótesis puede auditarse.             - Toda transformación se registra.
  - Toda conclusión es trazable.                - Nunca IA, nunca aleatoriedad.

Todo es determinista: mismo insumo ⇒ misma huella, mismo certificado, misma
auditoría (las fechas de emisión son metadatos y NUNCA entran en los hashes).

Contiene 14 funciones puras (sin disco, sin red, sin IA). La persistencia en las
tablas de gobernanza vive en funciones ``persistir_*`` separadas, que solo
almacenan lo que estas funciones puras ya calcularon.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata

from .analisis import (
    COMBINACIONES,
    DEUDA_POR_SENAL,
    SENALES_CAMBIO,
    SENALES_DOLOR,
)

# ── Versiones declaradas (auditables) ─────────────────────────────────────────
# Cada componente del sistema tiene una versión semántica explícita. Cambiar el
# comportamiento de un componente exige subir su versión aquí: así la huella
# digital de todo expediente queda ligada a la versión exacta que lo produjo.
VERSION_MOTOR = "1.0.0"        # Motor de Inferencia Antropológica (analisis.py)
VERSION_TAXONOMIA = "1.0.0"    # Taxonomía de Dolor Cultural (etiquetas y señales)
VERSION_CORPUS = "1.0.0"       # Esquema del corpus de evidencia
VERSION_PIPELINE = "12.0.0"    # Pipeline completo (12 capas)
VERSION_EXPEDIENTE = "1.0.0"   # Esquema del expediente
VERSION_DICTAMEN = "1.0.0"     # Dictamen Científico (Capa 11)
VERSION_DOSSIER = "1.0.0"      # Dossier de inteligencia
VERSION_DOLORMAP = "1.0.0"     # DolorMap consolidado
VERSION_DRIFT = "1.0.0"        # Motor de Drift Narrativo (Capa 6)
VERSION_ONLIFE = "1.0.0"       # Motor Onlife (Capa 7)
VERSION_VALIDACION = "1.0.0"   # Validación Científica (Capa 11)
VERSION_GOBERNANZA = "1.0.0"   # Gobernanza Científica (Capa 12)

MOTOR_NOMBRE = "Antrosapiens Motor A"

# Etapas del pipeline, en orden. Ligadas a la huella para poder reconstruir por
# qué transformaciones pasó una conclusión.
ETAPAS_PIPELINE = (
    "captura", "curaduria", "inferencia_antropologica",
    "validacion_cientifica", "gobernanza_cientifica",
)


# ── Utilidades deterministas ──────────────────────────────────────────────────
def _canonical(obj) -> str:
    """Serialización canónica: claves ordenadas, sin espacios, estable."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), default=str)


def _sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _hash_obj(obj) -> str:
    return _sha256(_canonical(obj))


def _slug(nombre: str) -> str:
    base = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()
    return base or "org"


def _evidencias(expediente: dict) -> list[dict]:
    ev = expediente.get("evidencias", [])
    if isinstance(ev, dict):
        return list(ev.get("items", []))
    return list(ev or [])


def _ev_identidad(ev: dict) -> dict:
    """Identidad estable de una evidencia (sin campos volátiles)."""
    return {
        "url": (ev.get("url") or ev.get("url_fuente") or "").strip(),
        "fuente": (ev.get("fuente") or ev.get("nombre_medio") or "").strip(),
        "fecha": (ev.get("fecha") or ev.get("fecha_publicacion") or "").strip(),
        "tipo_evento": (ev.get("tipo_evento") or "").strip(),
        "texto": (ev.get("texto") or ev.get("cita_textual") or "").strip(),
    }


def _huella_expediente_contenido(expediente: dict) -> dict:
    """Contenido analítico del expediente que define su identidad reproducible."""
    evs = sorted((_ev_identidad(e) for e in _evidencias(expediente)),
                 key=lambda d: (d["url"], d["fuente"], d["fecha"], d["texto"]))
    patrones = sorted(p.get("patron", "") for p in (expediente.get("patrones") or []))
    return {
        "nombre": expediente.get("nombre", ""),
        "scoring": expediente.get("scoring", ""),
        "score_icp": expediente.get("score_icp", 0),
        "tipo_deuda": expediente.get("tipo_deuda", ""),
        "profundidad_dolor": expediente.get("profundidad_dolor", 0),
        "keywords": sorted(expediente.get("keywords", []) or []),
        "patrones": patrones,
        "evidencias": evs,
    }


# ── 1. Versión del modelo ─────────────────────────────────────────────────────
def registrar_version_modelo() -> dict:
    """Registro de versión del Motor de Inferencia (determinista)."""
    descriptor = {"motor": MOTOR_NOMBRE, "version": VERSION_MOTOR,
                  "taxonomia": VERSION_TAXONOMIA}
    return {"componente": "motor_inferencia", "version": VERSION_MOTOR,
            "hash": _hash_obj(descriptor)}


# ── 2. Versión de la taxonomía ────────────────────────────────────────────────
def registrar_version_taxonomia() -> dict:
    """Registro de versión de la taxonomía de Dolor Cultural.

    El hash se calcula sobre el CONTENIDO real de la taxonomía (señales,
    etiquetas de deuda y combinaciones): si la taxonomía cambia, el hash cambia
    y la integridad lo detecta.
    """
    contenido = {
        "senales_dolor": sorted(SENALES_DOLOR),
        "senales_cambio": sorted(SENALES_CAMBIO),
        "deuda_por_senal": {k: list(v) for k, v in sorted(DEUDA_POR_SENAL.items())},
        "combinaciones": sorted(
            [sorted(list(tags)), label, razon] for tags, label, razon in COMBINACIONES
        ),
    }
    return {"componente": "taxonomia_dolor_cultural", "version": VERSION_TAXONOMIA,
            "hash": _hash_obj(contenido)}


# ── 3. Versión del corpus ─────────────────────────────────────────────────────
def registrar_version_corpus(evidencias: list[dict]) -> dict:
    """Registro de versión del corpus que alimenta un expediente.

    El hash liga la versión a las evidencias exactas usadas (por identidad
    estable), de modo que un corpus distinto produce un hash distinto.
    """
    ids = sorted(_hash_obj(_ev_identidad(e)) for e in (evidencias or []))
    return {"componente": "corpus", "version": VERSION_CORPUS,
            "hash": _sha256("|".join(ids)), "total_evidencias": len(ids)}


# ── 4. Versión del pipeline ───────────────────────────────────────────────────
def registrar_version_pipeline() -> dict:
    """Registro de versión del pipeline completo (orden de etapas incluido)."""
    contenido = {"version": VERSION_PIPELINE, "etapas": list(ETAPAS_PIPELINE)}
    return {"componente": "pipeline", "version": VERSION_PIPELINE,
            "hash": _hash_obj(contenido), "etapas": list(ETAPAS_PIPELINE)}


# ── 5. Versión del expediente ─────────────────────────────────────────────────
def registrar_version_expediente(expediente: dict) -> dict:
    """Registro de versión (hash de contenido) de un expediente concreto."""
    return {"componente": "expediente", "version": VERSION_EXPEDIENTE,
            "hash": _hash_obj(_huella_expediente_contenido(expediente))}


# ── 6. Huella digital ─────────────────────────────────────────────────────────
def generar_huella_digital(expediente: dict, validacion: dict, fecha: str = "") -> dict:
    """Genera la huella digital completa y reproducible de un expediente.

    La ``fecha`` es metadato de emisión y NO entra en el ``hash``: por eso dos
    emisiones del mismo expediente producen el mismo hash y el mismo ID.
    """
    vm = registrar_version_modelo()
    vt = registrar_version_taxonomia()
    vc = registrar_version_corpus(_evidencias(expediente))
    vp = registrar_version_pipeline()
    ve = registrar_version_expediente(expediente)

    veredicto = (validacion.get("dictamen_cientifico", {}) or {}).get("veredicto", "")
    versiones = {
        "motor": vm["version"],
        "taxonomia": vt["version"],
        "corpus": vc["version"],
        "pipeline": vp["version"],
        "expediente": ve["version"],
        "dictamen": VERSION_DICTAMEN,
        "dossier": VERSION_DOSSIER,
        "dolormap": VERSION_DOLORMAP,
        "drift": VERSION_DRIFT,
        "onlife": VERSION_ONLIFE,
        "validacion": VERSION_VALIDACION,
        "gobernanza": VERSION_GOBERNANZA,
    }
    hashes = {"expediente": ve["hash"], "corpus": vc["hash"], "taxonomia": vt["hash"]}
    contenido_hash = _hash_obj({
        "hashes": hashes, "versiones": versiones, "veredicto": veredicto,
        "motor": MOTOR_NOMBRE,
    })

    return {
        "id": f"HD-{_slug(expediente.get('nombre', ''))}-{contenido_hash[:12]}",
        "hash": contenido_hash,
        "version": VERSION_GOBERNANZA,
        "fecha": fecha,
        "motor": MOTOR_NOMBRE,
        "versiones": versiones,
        "hashes": hashes,
    }


# ── 7. Validación de integridad ───────────────────────────────────────────────
def validar_integridad(expediente: dict, huella: dict) -> dict:
    """Recalcula los hashes de contenido y los compara con la huella emitida.

    Si el expediente o la taxonomía cambiaron respecto a la huella, la
    integridad falla — la conclusión ya no corresponde a lo que se firmó.
    """
    hashes = huella.get("hashes", {}) or {}
    exp_actual = registrar_version_expediente(expediente)["hash"]
    tax_actual = registrar_version_taxonomia()["hash"]
    corpus_actual = registrar_version_corpus(_evidencias(expediente))["hash"]

    exp_ok = hashes.get("expediente") == exp_actual
    tax_ok = hashes.get("taxonomia") == tax_actual
    corpus_ok = hashes.get("corpus") == corpus_actual

    detalle = []
    if not exp_ok:
        detalle.append("El contenido del expediente no coincide con la huella.")
    if not tax_ok:
        detalle.append("La taxonomía cambió respecto a la huella emitida.")
    if not corpus_ok:
        detalle.append("El corpus cambió respecto a la huella emitida.")

    return {
        "integra": exp_ok and tax_ok and corpus_ok,
        "expediente_ok": exp_ok,
        "taxonomia_ok": tax_ok,
        "corpus_ok": corpus_ok,
        "detalle": detalle,
    }


# ── 8. Verificación de consistencia ───────────────────────────────────────────
def verificar_consistencia(expediente: dict, validacion: dict) -> dict:
    """Comprueba la coherencia interna entre inferencia y validación.

    No reinterpreta: solo verifica que los campos declarados no se contradigan
    entre sí (reproducibilidad, bloqueo, veredicto conocido).
    """
    from .validacion_cientifica import VEREDICTOS

    dictamen = validacion.get("dictamen_cientifico", {}) or {}
    bloqueo = validacion.get("bloqueo", {}) or {}
    repro = validacion.get("reproducibilidad", {}) or {}

    checks: list[dict] = []

    c_repro = bool(repro.get("reproducible"))
    checks.append({"check": "reproducibilidad_declarada", "ok": c_repro})

    c_bloqueo = dictamen.get("hipotesis_bloqueada") == bloqueo.get("bloqueada")
    checks.append({"check": "bloqueo_coherente", "ok": bool(c_bloqueo)})

    c_veredicto = dictamen.get("veredicto") in VEREDICTOS
    checks.append({"check": "veredicto_conocido", "ok": bool(c_veredicto)})

    incoherencias = [c["check"] for c in checks if not c["ok"]]
    return {
        "consistente": len(incoherencias) == 0,
        "checks": checks,
        "incoherencias": incoherencias,
    }


# ── 9. Comparación de versiones ───────────────────────────────────────────────
def comparar_versiones(huella_a: dict, huella_b: dict) -> list[dict]:
    """Diferencias de versión/hash entre dos huellas (para historial de cambios).

    Si ``huella_a`` es vacía (no había huella previa), devuelve lista vacía.
    """
    if not huella_a:
        return []
    cambios: list[dict] = []

    va = (huella_a.get("versiones", {}) or {})
    vb = (huella_b.get("versiones", {}) or {})
    for comp in sorted(set(va) | set(vb)):
        if va.get(comp) != vb.get(comp):
            cambios.append({"campo": f"version.{comp}",
                            "antes": va.get(comp), "despues": vb.get(comp)})

    if huella_a.get("hash") != huella_b.get("hash"):
        cambios.append({"campo": "hash", "antes": huella_a.get("hash"),
                        "despues": huella_b.get("hash")})
    return cambios


# ── 10. Línea de tiempo ───────────────────────────────────────────────────────
def construir_linea_tiempo(expediente: dict) -> list[dict]:
    """Ordena cronológicamente los hechos con origen fechado del expediente."""
    eventos: list[dict] = []
    for ev in _evidencias(expediente):
        idv = _ev_identidad(ev)
        eventos.append({
            "fecha": idv["fecha"] or "sin_fecha",
            "tipo": idv["tipo_evento"] or "evidencia",
            "fuente": idv["fuente"],
            "url": idv["url"],
        })
    # Orden determinista: fecha, luego fuente, luego url. 'sin_fecha' al final.
    eventos.sort(key=lambda e: (e["fecha"] == "sin_fecha", e["fecha"],
                                e["fuente"], e["url"]))
    return eventos


# ── 11. Registro de decisión ──────────────────────────────────────────────────
def registrar_decision(tipo: str, regla: str, resultado: str,
                       detalle: str = "", version_algoritmo: str = VERSION_MOTOR) -> dict:
    """Construye un registro de decisión trazable (entrada de bitácora)."""
    return {
        "tipo": tipo,
        "regla": regla,
        "resultado": resultado,
        "detalle": detalle,
        "version_algoritmo": version_algoritmo,
    }


# ── 12. Bitácora ──────────────────────────────────────────────────────────────
def generar_bitacora(expediente: dict, validacion: dict) -> dict:
    """Reconstruye qué pasó con la evidencia y qué reglas se ejecutaron.

    Registra: evidencia recibida, aceptada (trazable+fechada) y descartada
    (no consumible), reglas de validación ejecutadas con su resultado, y las
    reglas que bloquearon la hipótesis. Todo con la versión del algoritmo.
    """
    evs = _evidencias(expediente)
    traza = validacion.get("trazabilidad", {}) or {}
    fechado = validacion.get("fechado", {}) or {}
    suf = validacion.get("suficiencia_corpus", {}) or {}
    sol = validacion.get("solidez", {}) or {}
    contra = validacion.get("contradicciones", []) or []
    vacios = validacion.get("vacios", []) or []
    bloqueo = validacion.get("bloqueo", {}) or {}

    decisiones: list[dict] = []

    # Evidencia recibida (origen de cada afirmación).
    for ev in evs:
        idv = _ev_identidad(ev)
        decisiones.append(registrar_decision(
            "evidencia_recibida", "captura",
            "recibida", f"{idv['fuente']} · {idv['url']}",
            VERSION_CORPUS,
        ))

    # Aceptadas vs descartadas por consumibilidad (trazable + fechada).
    aceptadas = min(traza.get("trazables", 0), fechado.get("fechadas", 0))
    descartadas = len(evs) - aceptadas
    decisiones.append(registrar_decision(
        "evidencia_aceptada", "consumibilidad",
        str(aceptadas), "evidencias trazables y fechadas", VERSION_VALIDACION))
    if descartadas > 0:
        decisiones.append(registrar_decision(
            "evidencia_descartada", "consumibilidad",
            str(descartadas),
            "no consumibles (sin fecha o sin trazabilidad)", VERSION_VALIDACION))

    # Reglas de validación ejecutadas (Capa 11).
    reglas = [
        ("trazabilidad", "completa" if traza.get("completa") else "incompleta"),
        ("suficiencia_corpus", suf.get("nivel", "")),
        ("solidez", sol.get("nivel", "")),
        ("contradicciones", str(len(contra))),
        ("vacios", str(len(vacios))),
        ("reproducibilidad",
         "reproducible" if (validacion.get("reproducibilidad", {}) or {}).get("reproducible")
         else "no_reproducible"),
    ]
    for regla, resultado in reglas:
        decisiones.append(registrar_decision(
            "regla_ejecutada", regla, resultado, "", VERSION_VALIDACION))

    # Reglas que bloquearon la hipótesis.
    reglas_bloqueo = 0
    if bloqueo.get("bloqueada"):
        for motivo in bloqueo.get("motivos", []):
            reglas_bloqueo += 1
            decisiones.append(registrar_decision(
                "regla_bloqueo", "bloqueo_hipotesis", "bloqueada", motivo,
                VERSION_VALIDACION))

    return {
        "org": expediente.get("nombre", ""),
        "total": len(decisiones),
        "resumen": {
            "recibidas": len(evs),
            "aceptadas": aceptadas,
            "descartadas": descartadas,
            "reglas_ejecutadas": len(reglas),
            "reglas_bloqueo": reglas_bloqueo,
        },
        "decisiones": decisiones,
    }


# ── 13. Certificado científico ────────────────────────────────────────────────
def _nivel_confianza(confianza_agregada: float) -> str:
    if confianza_agregada >= 0.8:
        return "Alta"
    if confianza_agregada >= 0.5:
        return "Media"
    return "Baja"


_ESTADO_POR_VEREDICTO = {
    "VALIDADA": "CERTIFICADO",
    "VALIDADA_PARCIAL": "CERTIFICADO_PRELIMINAR",
    "NO_VALIDADA": "NO_CERTIFICADO",
    "BLOQUEADA": "BLOQUEADO",
    "SIN_HIPOTESIS": "SIN_HIPOTESIS",
}


def firmar_motor(hash_huella: str, version: str, veredicto: str) -> str:
    """Firma determinista del Motor sobre una conclusión (no es aleatoria)."""
    firma = _sha256(f"{MOTOR_NOMBRE}|{version}|{hash_huella}|{veredicto}")
    return f"AS-MOTORA::{firma[:32]}"


def emitir_certificado(expediente: dict, validacion: dict, huella: dict,
                       fecha: str = "") -> dict:
    """Emite el certificado científico del expediente (determinista salvo fecha)."""
    dictamen = validacion.get("dictamen_cientifico", {}) or {}
    solidez = (validacion.get("solidez", {}) or {})
    suficiencia = (validacion.get("suficiencia_corpus", {}) or {})
    nivel_ev = (validacion.get("nivel_evidencia", {}) or {})
    veredicto = dictamen.get("veredicto", "")

    return {
        "certificado_id": f"CERT-{huella.get('id', '')}",
        "fecha": fecha,
        "id": huella.get("id", ""),
        "hash": huella.get("hash", ""),
        "version": huella.get("version", VERSION_GOBERNANZA),
        "estado": _ESTADO_POR_VEREDICTO.get(veredicto, "DESCONOCIDO"),
        "veredicto": veredicto,
        "nivel_evidencia": nivel_ev.get("nivel", ""),
        "nivel_confianza": _nivel_confianza(solidez.get("confianza_agregada", 0.0)),
        "solidez": solidez.get("score", 0),
        "suficiencia": suficiencia.get("score", 0),
        "firma_motor": firmar_motor(huella.get("hash", ""),
                                    huella.get("version", VERSION_GOBERNANZA), veredicto),
        "motor": MOTOR_NOMBRE,
    }


# ── 14. Auditoría completa (orquestador) ──────────────────────────────────────
def auditar_expediente(expediente: dict, validacion: dict, fecha: str = "",
                       huella_previa: dict | None = None) -> dict:
    """Ensambla la auditoría total y reproducible de un expediente.

    Devuelve todas las secciones exigidas: resumen, historial, versionado,
    bitácora, cambios, huellas digitales, trazabilidad, integridad,
    consistencia, reproducibilidad y certificado.
    """
    huella = generar_huella_digital(expediente, validacion, fecha)
    integridad = validar_integridad(expediente, huella)
    consistencia = verificar_consistencia(expediente, validacion)
    bitacora = generar_bitacora(expediente, validacion)
    linea_tiempo = construir_linea_tiempo(expediente)
    certificado = emitir_certificado(expediente, validacion, huella, fecha)
    cambios = comparar_versiones(huella_previa or {}, huella)

    versionado = [
        registrar_version_modelo(),
        registrar_version_taxonomia(),
        registrar_version_corpus(_evidencias(expediente)),
        registrar_version_pipeline(),
        registrar_version_expediente(expediente),
    ]

    dictamen = validacion.get("dictamen_cientifico", {}) or {}
    repro = validacion.get("reproducibilidad", {}) or {}
    resumen = {
        "org": expediente.get("nombre", ""),
        "veredicto": dictamen.get("veredicto", ""),
        "hash": huella["hash"],
        "id": huella["id"],
        "integra": integridad["integra"],
        "consistente": consistencia["consistente"],
        "reproducible": bool(repro.get("reproducible")),
        "total_evidencias": len(_evidencias(expediente)),
    }

    return {
        "resumen": resumen,
        "historial": linea_tiempo,
        "versionado": versionado,
        "bitacora": bitacora,
        "cambios": cambios,
        "huellas_digitales": [huella],
        "trazabilidad": validacion.get("trazabilidad", {}),
        "integridad": integridad,
        "consistencia": consistencia,
        "reproducibilidad": repro,
        "certificado": certificado,
    }
