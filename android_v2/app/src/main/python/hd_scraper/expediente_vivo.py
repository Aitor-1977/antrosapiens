"""Expediente Vivo — paridad de forma con RadarHD (Cutover Arquitectura 1.0).

Produce EXACTAMENTE las formas que consumen los componentes tipados de RadarHD
para el "Radar de Organizaciones Observadas":

- ``OrganizacionObservada``  → listado (GET /api/radar/organizaciones).
- ``Dossier``                → detalle    (GET /api/radar/organizaciones/{id}).
- ``Drift``                  → drift       (GET /api/radar/drift/{id}).

Todo es DETERMINISTA y reproducible (mismo insumo ⇒ misma salida). No añade
interpretación nueva: reaprovecha el análisis ya producido por este mismo motor
(``analizar``, ``calcular_madurez``, la Validación Científica de la Capa 11 y la
inteligencia ecosistémica del Observatorio). Los campos que Motor A NO estructura
(recomendación estratégica y dictamen pericial — decisión comercial de Motor C;
DolorMap — sin fuente de datos) se emiten VACÍOS, nunca inventados.

Los IDs de organización son enteros deterministas (índice en orden alfabético,
vía ``observatorio._id_map``), de modo que el listado y el detalle comparten un
único espacio de identificadores. Las ``evidencia_ids`` remiten a los ``id`` de
la cadena de evidencia del detalle, para que cada afirmación sea trazable.
"""
from __future__ import annotations

from .analisis import SENALES_CAMBIO, SENALES_DOLOR
from .observatorio import (
    _fecha_primera,
    _id_map,
    _patrones_ecosistemicos,
    _periodo,
    _subtipo,
    detectar_centinelas,
    detectar_clusters,
    detectar_outliers,
    ranking_hd,
)
from .predictivo import calcular_madurez
from .validacion_cientifica import (
    calcular_solidez,
    detectar_contradicciones,
    detectar_vacios,
    nivel_evidencia,
    validar_trazabilidad,
)

# Evento estructural (observable por la empresa) vs. narrativo (relato/prensa).
# La frontera es la MISMA que usa RadarHD para tiene_evidencia_operativa/narrativa.
_EVENTOS_OPERATIVOS = {"contratacion", "cambio_sitio", "ronda"}
_EVENTOS_NARRATIVOS = {"queja", "lanzamiento", "despido"}

# Marco fijo de la taxonomía (un solo término, no tres categorías).
_MARCO_DEUDA = "Deuda Cultural Situacional-Simbólica™"


# ── Helpers de forma ──────────────────────────────────────────────────────────

def _ev_fecha(ev: dict) -> str:
    return (ev.get("fecha") or ev.get("fecha_publicacion") or "").strip()[:10]


def _ev_tipo(ev: dict) -> str:
    return (ev.get("tipo_evento") or "").strip()


def _cadena_evidencia(exp: dict) -> list[dict]:
    """EvidenciaItem[] con id determinista (orden por fecha, fuente, texto).

    El id es el índice estable dentro de la organización: así las evidencia_ids
    de la inferencia remiten siempre al mismo registro (reproducible).
    """
    evs = list(exp.get("evidencias", []) or [])
    ordenadas = sorted(
        evs,
        key=lambda e: (_ev_fecha(e), (e.get("fuente") or ""), (e.get("texto") or "")),
    )
    tipo_deuda = _subtipo(exp.get("tipo_deuda", "")) if exp.get("tipo_deuda") else ""
    items = []
    for i, ev in enumerate(ordenadas):
        tipo_evento = _ev_tipo(ev)
        items.append({
            "id": i,
            "fecha": _ev_fecha(ev) or None,
            "fuente": ev.get("fuente") or "",
            "tipo_fuente": tipo_evento,  # Motor A deriva el tipo de la estructura del evento.
            "tipo_evento": tipo_evento,
            "tipo_deuda": tipo_deuda,
            "cita_textual": ev.get("texto") or "",
            "url": ev.get("url") or "",
            "confianza": float(ev.get("confianza") or 0.0),
        })
    return items


def _fuentes(items: list[dict]) -> list[str]:
    vistos: list[str] = []
    for it in items:
        f = it.get("fuente") or ""
        if f and f not in vistos:
            vistos.append(f)
    return vistos


def _nivel_confianza_curaduria(exp: dict) -> str:
    """Curaduria.nivel_confianza (Alto|Medio|Bajo) desde el nivel GRADE."""
    nivel = nivel_evidencia(exp)["nivel"]
    return {"I": "Alto", "II": "Medio", "III": "Bajo", "IV": "Bajo"}.get(nivel, "Bajo")


def _solidez_label(exp: dict) -> str:
    """Inferencia.solidez (Alta|Media|Baja) desde el nivel de solidez de la Capa 11."""
    return {"alta": "Alta", "media": "Media", "baja": "Baja"}.get(
        calcular_solidez(exp)["nivel"], "Baja")


def _viabilidad_hd(exp: dict) -> dict:
    """ViabilidadHd {nivel, razon}: capitaliza la viabilidad determinista del motor."""
    v = (exp.get("viabilidad") or "").strip().lower()
    nivel = {"alta": "Alta", "media": "Media", "baja": "Baja"}.get(v, "No determinada")
    razon = exp.get("deuda_razon") or exp.get("razon") or ""
    return {"nivel": nivel, "razon": razon}


def _intensidad_label(exp: dict) -> str:
    return (exp.get("intensidad") or "Baja").strip() or "Baja"


def _consistencia_label(exp: dict, items: list[dict]) -> str:
    """Cualitativa por número de fuentes independientes (no es probabilidad)."""
    fuentes = len(_fuentes(items))
    if fuentes >= 3:
        return "Sólida"
    if fuentes == 2:
        return "Moderada"
    return "Débil"


def _calidad_evidencia_label(exp: dict, items: list[dict]) -> str:
    confs = [it["confianza"] for it in items]
    c = max(confs) if confs else 0.0
    return "Alta" if c >= 0.8 else ("Media" if c >= 0.5 else "Baja")


def _alerta(exp: dict) -> str | None:
    """NivelAlerta (Crítica|Alta|Media|null): relectura de viabilidad + intensidad."""
    nivel = _viabilidad_hd(exp)["nivel"]
    intensidad = _intensidad_label(exp)
    if nivel == "Alta" and intensidad == "Alta":
        return "Crítica"
    if nivel == "Alta":
        return "Alta"
    if nivel == "Media":
        return "Media"
    return None


def _implicacion_sistemica(exp: dict) -> str:
    """Frase determinista: qué implica la viabilidad HD dada la madurez del corpus."""
    nivel = _viabilidad_hd(exp)["nivel"]
    madurez = calcular_madurez(exp)["nivel"]
    if nivel == "Alta":
        return (f"Fricción estructural con viabilidad alta sobre un corpus {madurez}: "
                "su varianza de capital cultural merece indagación prioritaria.")
    if nivel == "Media":
        return (f"Señal intermedia sobre un corpus {madurez}: la implicación sistémica "
                "depende de que converja evidencia operativa y narrativa.")
    if nivel == "Baja":
        return (f"Implicación sistémica acotada: corpus {madurez} sin fricción "
                "estructural sostenida todavía.")
    return "Sin implicación sistémica determinable con la evidencia disponible."


def _hipotesis_texto(exp: dict) -> str:
    deuda = exp.get("tipo_deuda") or ""
    razon = exp.get("deuda_razon") or ""
    if not deuda:
        return ""
    return f"Posible {deuda}: {razon}".strip().rstrip(":")


def _que_cambio(items: list[dict]) -> list[str]:
    """¿Qué cambió?: eventos estructurales, cronológicos y deterministas."""
    cambios = []
    for it in items:
        if it["tipo_evento"] in _EVENTOS_OPERATIVOS:
            fecha = it["fecha"] or "sin fecha"
            cambios.append(f"{fecha}: {it['tipo_evento']} ({it['fuente']})")
    return cambios


# ── Curaduría (forma Curaduria) ───────────────────────────────────────────────

def curaduria(exp: dict, items: list[dict]) -> dict:
    patrones = [{
        "patron": p.get("patron", ""),
        "num_senales": len(p.get("senales", []) or []),
        "fuentes": _fuentes(items),
    } for p in (exp.get("patrones", []) or [])]

    contradicciones = [c["descripcion"] for c in detectar_contradicciones(exp)]
    vacios = [v["descripcion"] for v in detectar_vacios(exp)]

    dominante = exp.get("senal_dominante") or ""
    razon = exp.get("deuda_razon") or ""
    narrativa = (f"Señal dominante: {dominante}. {razon}".strip()
                 if dominante else (razon or "Sin narrativa dominante consolidada."))

    return {
        "narrativa_dominante": narrativa,
        "nivel_confianza": _nivel_confianza_curaduria(exp),
        "patrones": patrones,
        "contradicciones": contradicciones,
        "vacios": vacios,
        # Motor A deduplica por hash_dedup en la escritura: dentro del expediente
        # ya no quedan duplicadas por descartar.
        "duplicadas_descartadas": 0,
    }


# ── Inferencia Antropológica (forma InferenciaAntropologica) ──────────────────

def inferencia_antropologica(exp: dict, items: list[dict], cur: dict) -> dict:
    todos_ids = [it["id"] for it in items]
    ids_dolor = [it["id"] for it in items
                 if it["tipo_evento"] in _EVENTOS_NARRATIVOS]

    patrones = exp.get("patrones", []) or []
    patron_dominante = None
    if patrones:
        p = patrones[0]
        patron_dominante = {
            "patron": p.get("patron", ""),
            "num_senales": len(p.get("senales", []) or []),
            "evidencia_ids": todos_ids,
        }

    # Tensiones deterministas: deuda secundaria coexistente y dolor+cambio.
    tensiones = []
    kws = set(exp.get("keywords", []) or [])
    if exp.get("deuda_secundaria"):
        tensiones.append({
            "descripcion": f"Coexisten {exp.get('tipo_deuda')} y "
                           f"{exp.get('deuda_secundaria')} en la misma evidencia.",
            "evidencia_ids": todos_ids,
        })
    if (kws & SENALES_DOLOR) and (kws & SENALES_CAMBIO):
        tensiones.append({
            "descripcion": "Señales de dolor y de crecimiento conviven: la hipótesis "
                           "debe explicar por qué antes de sostenerse.",
            "evidencia_ids": todos_ids,
        })

    trazabilidad = validar_trazabilidad(exp)

    return {
        "patron_dominante": patron_dominante,
        "tensiones": tensiones,
        "contradicciones_estructurales": cur["contradicciones"],
        "vacios_criticos": cur["vacios"],
        "clasificacion_deuda": {
            "subtipo": _subtipo(exp.get("tipo_deuda", "")) if exp.get("tipo_deuda") else "No determinado",
            "evidencia_ids": ids_dolor,
        },
        "hipotesis": {"texto": _hipotesis_texto(exp), "evidencia_ids": todos_ids},
        "explicacion": exp.get("razon") or "",
        "solidez": _solidez_label(exp),
        "trazabilidad_valida": bool(trazabilidad.get("completa", False)),
    }


# ── Organización observada (forma OrganizacionObservada) ──────────────────────

def organizacion_observada(exp: dict, idm: dict[str, int], incluir_cadena: bool = False) -> dict:
    items = _cadena_evidencia(exp)
    cur = curaduria(exp, items)
    inf = inferencia_antropologica(exp, items, cur)
    tipos_evidencia = sorted({it["tipo_evento"] for it in items if it["tipo_evento"]})
    fechas = sorted(it["fecha"] for it in items if it["fecha"])
    tiene_operativa = any(it["tipo_evento"] in _EVENTOS_OPERATIVOS for it in items)
    tiene_narrativa = any(it["tipo_evento"] in _EVENTOS_NARRATIVOS for it in items)

    # cadena_evidencia + fuentes hacen el ítem del listado autosuficiente para la
    # trazabilidad (evidencia_ids) que Motor C reconstruye sin volver al detalle.
    extra = {"cadena_evidencia": items, "fuentes": _fuentes(items)} if incluir_cadena else {}

    return {
        **extra,
        "organizacion_id": idm.get(exp.get("nombre", ""), -1),
        "nombre_display": exp.get("nombre", ""),
        "vertical": exp.get("vertical", "") or "",
        "intensidad_label": _intensidad_label(exp),
        "consistencia_label": _consistencia_label(exp, items),
        "calidad_evidencia_label": _calidad_evidencia_label(exp, items),
        "num_senales": len(items),
        "num_fuentes_distintas": len(_fuentes(items)),
        "tipos_evidencia": tipos_evidencia,
        "madurez": calcular_madurez(exp)["nivel"],
        "patrones_observados": [p.get("patron", "") for p in (exp.get("patrones", []) or [])],
        "que_cambio": _que_cambio(items),
        "hipotesis_deuda": _hipotesis_texto(exp),
        "viabilidad_hd": _viabilidad_hd(exp),
        "taxonomia": {"marco": _MARCO_DEUDA,
                      "subtipo": _subtipo(exp.get("tipo_deuda", "")) if exp.get("tipo_deuda") else "No determinado"},
        "implicacion_sistemica": _implicacion_sistemica(exp),
        "alerta": _alerta(exp),
        "tiene_evidencia_operativa": tiene_operativa,
        "tiene_evidencia_narrativa": tiene_narrativa,
        "fecha_ultima_senal": fechas[-1] if fechas else None,
        "curaduria": cur,
        "inferencia_antropologica": inf,
    }


def listado(exps: list[dict]) -> dict:
    """{generado_en(lo añade la API), resumen, total, organizaciones[]} — orden de ranking HD."""
    idm = _id_map(exps)
    orgs = [organizacion_observada(e, idm, incluir_cadena=True) for e in exps]
    # Orden por prioridad de ranking HD (mismo criterio que el resto del sistema).
    rank = {r["nombre"]: r["posicion"] for r in ranking_hd(exps, len(exps))}
    orgs.sort(key=lambda o: rank.get(o["nombre_display"], 10_000))
    resumen = {
        "organizaciones": len(orgs),
        "con_alerta": sum(1 for o in orgs if o["alerta"]),
        "con_evidencia_operativa": sum(1 for o in orgs if o["tiene_evidencia_operativa"]),
        "con_evidencia_narrativa": sum(1 for o in orgs if o["tiene_evidencia_narrativa"]),
    }
    return {"resumen": resumen, "total": len(orgs), "organizaciones": orgs}


# ── Contexto Ecosistémico (forma ContextoEcosistemico) ────────────────────────

def _contexto_ecosistemico(nombre: str, exps: list[dict], idm: dict[str, int]) -> dict:
    clusters = detectar_clusters(exps)
    mi_cluster = next((c for c in clusters if nombre in c["organizaciones"]), None)
    cluster_out = None
    relacionadas: list[int] = []
    if mi_cluster:
        ids = sorted(idm.get(n, -1) for n in mi_cluster["organizaciones"])
        relacionadas = [i for i in ids if i != idm.get(nombre, -1)]
        cluster_out = {
            "subtipo": _subtipo(mi_cluster["tipo_deuda"]),
            "num_organizaciones": mi_cluster["tamano"],
            "organizaciones": ids,
            "evidencia_ids": [],
        }

    por_nombre = {e.get("nombre", ""): e for e in exps}
    centinelas = detectar_centinelas(exps)
    outliers = detectar_outliers(exps)
    nombres_cent = {c["nombre"] for c in centinelas}
    nombres_atip = {o["nombre"] for o in outliers}

    # Cercanía = mismo cluster (mismo subtipo+vertical) que la organización.
    en_cluster = set(mi_cluster["organizaciones"]) if mi_cluster else set()
    centinelas_cercanos = [{
        "organizacion_id": idm.get(c["nombre"], -1),
        "nombre_display": c["nombre"],
        "subtipo": _subtipo(c.get("tipo_deuda", "")),
        "fecha_primera_senal": _fecha_primera(por_nombre.get(c["nombre"], {})),
        "motivo": c.get("motivo", ""),
    } for c in centinelas if c["nombre"] in en_cluster and c["nombre"] != nombre]
    atipicos_cercanos = [{
        "organizacion_id": idm.get(o["nombre"], -1),
        "nombre_display": o["nombre"],
        "motivo": "; ".join(o.get("razones", [])),
    } for o in outliers if o["nombre"] in en_cluster and o["nombre"] != nombre]

    patrones_compartidos = [p for p in _patrones_ecosistemicos(exps, idm)
                            if idm.get(nombre, -1) in p["organizaciones"] and p["num_organizaciones"] > 1]

    hipotesis_vinculada = None
    if mi_cluster and cluster_out:
        cant_ev = sum(por_nombre.get(n, {}).get("total_evidencias", 0)
                      for n in mi_cluster["organizaciones"])
        subtipo = _subtipo(mi_cluster["tipo_deuda"])
        hipotesis_vinculada = {
            "texto": f"{mi_cluster['tamano']} organizaciones comparten {subtipo}.",
            "organizaciones": cluster_out["organizaciones"],
            "nivel_confianza": _nivel_confianza_curaduria(por_nombre.get(nombre, {})),
            "cantidad_evidencias": cant_ev,
            "periodo": _periodo([por_nombre[n] for n in mi_cluster["organizaciones"] if n in por_nombre]),
        }

    rank = ranking_hd(exps, len(exps))
    pos = next((r["posicion"] for r in rank if r["nombre"] == nombre), None)
    total = len(exps)
    posicion_relativa = (
        f"Posición {pos} de {total} en el ranking de prioridad HD del ecosistema."
        if pos else f"Sin posición en el ranking (ecosistema de {total} organización(es)).")

    return {
        "posicion_relativa": posicion_relativa,
        "cluster": cluster_out,
        "organizaciones_relacionadas": relacionadas,
        "patrones_compartidos": patrones_compartidos,
        "es_centinela": nombre in nombres_cent,
        "es_atipica": nombre in nombres_atip,
        "centinelas_cercanos": centinelas_cercanos,
        "atipicos_cercanos": atipicos_cercanos,
        "hipotesis_vinculada": hipotesis_vinculada,
    }


def nombre_de(exps: list[dict], org_id: int) -> str | None:
    """Resuelve el id numérico determinista → nombre de organización, o None."""
    return {v: k for k, v in _id_map(exps).items()}.get(org_id)


def detalle(exps: list[dict], org_id: int, tiene_analisis_onlife: bool = False) -> dict | None:
    """Dossier de una organización por id numérico determinista, o None si no existe.

    Los campos comerciales (recomendación estratégica, dictamen pericial) son de
    Motor C y se emiten null: Motor A no decide ni ejecuta acción comercial.
    DolorMap se emite null (sin fuente de datos). El resto es paridad total.
    """
    idm = _id_map(exps)
    inv = {v: k for k, v in idm.items()}
    nombre = inv.get(org_id)
    if nombre is None:
        return None
    exp = next((e for e in exps if e.get("nombre", "") == nombre), None)
    if exp is None:
        return None

    base = organizacion_observada(exp, idm)
    items = _cadena_evidencia(exp)
    return {
        **base,
        "cadena_evidencia": items,
        "fuentes": _fuentes(items),
        "contexto_ecosistemico": _contexto_ecosistemico(nombre, exps, idm),
        # Motor C (comercial): fuera del alcance de Motor A (ADR-0001).
        "recomendacion_estrategica": None,
        "dictamen_pericial": None,
        "tiene_analisis_onlife": bool(tiene_analisis_onlife),
        "dolormap": None,
    }


# ── Drift narrativo (forma Drift) ─────────────────────────────────────────────

def drift(exps: list[dict], org_id: int) -> dict | None:
    """{organizacion_id, drift:{detectado, resumen, ultima_fecha, num_observaciones}}.

    Determinista a partir de la evidencia narrativa ya extraída — no reinterpreta.
    """
    idm = _id_map(exps)
    inv = {v: k for k, v in idm.items()}
    nombre = inv.get(org_id)
    if nombre is None:
        return None
    exp = next((e for e in exps if e.get("nombre", "") == nombre), None)
    if exp is None:
        return None

    items = _cadena_evidencia(exp)
    narrativas = [it for it in items if it["tipo_evento"] in _EVENTOS_NARRATIVOS]
    fechas = sorted(it["fecha"] for it in narrativas if it["fecha"])
    resumen = [f"{(it['fecha'] or 'sin fecha')} · {it['tipo_evento']}: {it['cita_textual']}"
               for it in narrativas]
    return {
        "organizacion_id": org_id,
        "drift": {
            "detectado": len(narrativas) > 0,
            "resumen": resumen,
            "ultima_fecha": fechas[-1] if fechas else None,
            "num_observaciones": len(narrativas),
        },
    }
