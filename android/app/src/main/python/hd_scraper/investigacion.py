"""Motor real de investigación antropológica — capa de aplicación.

Orquesta el ciclo completo sobre motores YA existentes (no duplica reglas
científicas): captura vía conectores (GDELT/RSS/Google News/job boards),
deduplicación, curaduría, relaciones, tensiones, hipótesis y peritaje. Toda
decisión queda persistida en SQLite (offline-first) a través de
``investigacion_store``.

Ciclo:
  FOCO → PREGUNTA → CAPTURA → NORMALIZACIÓN → DEDUP → CURADURÍA
       → EVIDENCIA → TRIANGULACIÓN → RELACIONES → TENSIONES
       → HIPÓTESIS → PERITAJE

Principio: una señal NO se vuelve evidencia automáticamente; la decisión es
humana y se registra (decisor + timestamp). La IA, si está disponible, solo
asiste y queda marcada como INFERENCIA IA; no cierra peritajes.
"""
from __future__ import annotations

import json
import uuid
from typing import Iterable, Optional

from .config import settings
from .connectors import REGISTRY
from .connectors.base import Connector
from .db.database import Database
from .db.models import (
    QuerySpec,
    ahora_iso,
    calcular_hash_dedup,
    hash_contenido,
    normalizar_url,
)
from . import investigacion_store as S
from . import nvidia_parser as nv
from . import validacion_cientifica as vc

_TIPOS_FUENTE_VALIDOS = frozenset(REGISTRY.keys())


def _nuevo_id() -> str:
    return uuid.uuid4().hex


def _hash_senal(url: str, titulo: str, empresa: str) -> str:
    """Identidad de contenido determinista para dedup dentro de una investigación.

    Combina URL normalizada + hash de título, de modo que la MISMA noticia
    capturada desde distintas consultas o incluso distintas URLs (mismo título)
    colapsa en una sola señal.
    """
    norm = normalizar_url(url)
    contenido = hash_contenido(titulo)
    if norm:
        return f"url:{norm}|{contenido}"
    if contenido:
        return f"txt:{contenido}"
    return "dup:" + calcular_hash_dedup(empresa, url or titulo)


def _resolver_conector(especificacion) -> Connector:
    """Acepta un nombre del REGISTRY o una instancia ya construida (tests)."""
    if isinstance(especificacion, Connector):
        return especificacion
    nombre = str(especificacion)
    if nombre not in REGISTRY:
        raise ValueError(f"conector desconocido: {nombre}")
    return REGISTRY[nombre]()


# --- 1. Investigación --------------------------------------------------
def crear_investigacion(db: Database, foco: str, pregunta: str, inv_id: Optional[str] = None) -> str:
    inv_id = inv_id or _nuevo_id()
    S.init_investigacion_schema(db)
    S.crear_investigacion(db, inv_id, foco, pregunta)
    S.registrar_decision(db, inv_id, "crear_investigacion", "investigador",
                         detalle=json.dumps({"foco": foco, "pregunta": pregunta}, ensure_ascii=False))
    return inv_id


def definir_pregunta(db: Database, inv_id: str, pregunta: str) -> None:
    S.actualizar_investigacion(db, inv_id, pregunta=pregunta)
    S.registrar_decision(db, inv_id, "definir_pregunta", "investigador", detalle=pregunta)


# --- 2-5. Captura + normalización + dedup ------------------------------
def capturar(
    db: Database, inv_id: str, consulta: str, tipo_evento: str,
    conectores: Iterable, *, slug: Optional[str] = None,
    region: Optional[str] = None, autor: str = "investigador",
) -> dict:
    """Ejecuta búsquedas reales en los conectores y guarda cada ítem como SEÑAL.

    Deduplica por identidad de contenido: la misma noticia capturada por varias
    consultas/conectores aparece una sola vez. Devuelve un resumen de conteos.
    """
    if S.obtener_investigacion(db, inv_id) is None:
        raise ValueError(f"investigación inexistente: {inv_id}")

    resumen = {"vistos": 0, "escritos": 0, "duplicados": 0, "errores": []}
    query = QuerySpec(
        empresa=consulta, tipo_evento=tipo_evento, slug=slug,
        region=region, exact=True,
    )

    for espec in conectores:
        conector = _resolver_conector(espec)
        try:
            for raw in conector.search(query):
                resumen["vistos"] += 1
                try:
                    record = conector.normalize(raw)
                    record.tipo_evento = tipo_evento
                    url = record.url_fuente
                    titulo = record.cita_textual
                    if not titulo or not url:
                        continue
                    hash_ = _hash_senal(url, titulo, record.empresa_mencionada or consulta)
                    contenido = hash_contenido(titulo)
                    if (S.senal_existe(db, inv_id, hash_)
                            or (contenido and S.senal_existe_por_contenido(db, inv_id, contenido))):
                        resumen["duplicados"] += 1
                        continue
                    senal = {
                        "organizacion": record.empresa_mencionada or consulta,
                        "titulo": titulo,
                        "fuente": record.nombre_medio or conector.name,
                        "url": url,
                        "fecha_publicacion": record.fecha_publicacion,
                        "fecha_captura": ahora_iso(),
                        "texto": titulo,
                        "tipo_fuente": conector.name,
                        "hash": hash_,
                        "id_interno": _nuevo_id()[:12],
                    }
                    sid = S.insertar_senal(db, inv_id, senal)
                    S.registrar_decision(
                        db, inv_id, "captura", autor, senal_id=sid,
                        detalle=json.dumps({"fuente": senal["fuente"],
                                            "titulo": titulo}, ensure_ascii=False),
                    )
                    resumen["escritos"] += 1
                except Exception as exc:  # una señal falla, no tumba la corrida
                    resumen["errores"].append(f"normalize: {exc}")
        except Exception as exc:
            resumen["errores"].append(f"search({conector.name}): {exc}")
        finally:
            try:
                conector.close()
            except Exception:
                pass

    S.actualizar_investigacion(db, inv_id)
    return resumen


# --- 6. Curaduría ------------------------------------------------------
def curar(
    db: Database, inv_id: str, senal_id: int, accion: str,
    nota: Optional[str] = None, autor: str = "investigador",
) -> dict:
    """Aplica una decisión de curaduría humana sobre una señal.

    acciones: 'aceptar' (→ EVIDENCIA), 'descartar' (→ DESCARTADA), 'nota' (solo anota).
    """
    senal = S.obtener_senal(db, senal_id)
    if senal is None or senal["inv_id"] != inv_id:
        raise ValueError(f"señal inexistente o fuera de la investigación: {senal_id}")

    if accion == "aceptar":
        S.curar_senal(db, senal_id, S.ESTADO_EVIDENCIA, nota=nota, autor=autor)
        S.registrar_decision(db, inv_id, "aceptar_evidencia", autor, senal_id=senal_id)
    elif accion == "descartar":
        S.curar_senal(db, senal_id, S.ESTADO_DESCARTADA, nota=nota, autor=autor)
        S.registrar_decision(db, inv_id, "descartar_senal", autor, senal_id=senal_id)
    elif accion == "nota":
        S.curar_senal(db, senal_id, senal["estado_curaduria"], nota=nota, autor=autor)
        S.registrar_decision(db, inv_id, "anotar_senal", autor, senal_id=senal_id, detalle=nota)
    else:
        raise ValueError(f"acción de curaduría desconocida: {accion}")
    return S.obtener_senal(db, senal_id)


# --- 7. Relaciones -----------------------------------------------------
def relacionar(
    db: Database, inv_id: str, a: int, b: int, tipo: str,
    nota: Optional[str] = None, autor: str = "investigador",
) -> int:
    if tipo not in S.TIPOS_RELACION:
        raise ValueError(f"tipo de relación inválido: {tipo}")
    sa, sb = S.obtener_senal(db, a), S.obtener_senal(db, b)
    if sa is None or sb is None or sa["inv_id"] != inv_id or sb["inv_id"] != inv_id:
        raise ValueError("ambas evidencias deben existir en la investigación")
    rid = S.insertar_relacion(db, inv_id, a, b, tipo, nota)
    S.registrar_decision(db, inv_id, f"relacion_{tipo}", autor, senal_id=a,
                         detalle=json.dumps({"a": a, "b": b}, ensure_ascii=False))
    return rid


# --- 8. Tensiones ------------------------------------------------------
def registrar_tension(
    db: Database, inv_id: str, a: int, b: int, explicacion: str,
    estado: str = "abierta", autor: str = "investigador",
) -> int:
    sa, sb = S.obtener_senal(db, a), S.obtener_senal(db, b)
    if sa is None or sb is None or sa["inv_id"] != inv_id or sb["inv_id"] != inv_id:
        raise ValueError("ambas evidencias deben existir en la investigación")
    tid = S.insertar_tension(db, inv_id, a, b, explicacion, estado, decisor=autor)
    S.registrar_decision(db, inv_id, "registrar_tension", autor, senal_id=a, detalle=explicacion)
    return tid


def sugerir_tensiones(db: Database, inv_id: str) -> list[dict]:
    """Sugiere pares de evidencias en posible contradicción (solo con evidencia).

    Determinista: usa ``validacion_cientifica.detectar_contradicciones`` sobre el
    corpus de evidencias. La decisión final de marcar la tensión es humana.
    """
    evidencias = S.listar_senales(db, inv_id, S.ESTADO_EVIDENCIA)
    if len(evidencias) < 2:
        return []
    expediente = {"evidencias": [_a_evidencia_para_vc(e) for e in evidencias]}
    contradicciones = vc.detectar_contradicciones(expediente)
    sugerencias = []
    for c in contradicciones:
        sugerencias.append({
            "evidencia_a": c.get("a"),
            "evidencia_b": c.get("b"),
            "razon": c.get("razon", ""),
            "tipo": "CONTRADICCION_DETECTADA",
        })
    return sugerencias


# --- 9. Hipótesis (asistida, nunca automática) -------------------------
def generar_hipotesis(
    db: Database, inv_id: str, usar_ia: bool = False, autor: str = "investigador",
) -> list[dict]:
    """Genera hipótesis preliminares a partir de las evidencias curadas.

    Determinista por defecto (triangulación + validación científica). Si
    ``usar_ia`` y NVIDIA está disponible, enriquece la síntesis pero queda
    marcada como INFERENCIA IA y SIEMPRE con fallback determinista.
    """
    evidencias = S.listar_senales(db, inv_id, S.ESTADO_EVIDENCIA)
    if not evidencias:
        return []

    expediente = {"evidencias": [_a_evidencia_para_vc(e) for e in evidencias]}
    dictamen = vc.validar_expediente(expediente)
    dc = dictamen.get("dictamen_cientifico", {})
    triang = triangulacion(db, inv_id)

    lineas = [
        f"Hipótesis preliminar construida sobre {triang['n_evidencias']} evidencias "
        f"de {triang['fuentes_independientes']} fuentes independientes.",
    ]
    if triang["contradicciones"]:
        lineas.append(
            f"Existen {triang['contradicciones']} tensión(es)/contradicción(es) "
            f"registrada(s) que la hipótesis debe explicar, no ignorar.")
    if triang["evidencia_faltante"]:
        lineas.append(
            "Evidencia faltante: " + "; ".join(triang["evidencia_faltante"][:3]) + ".")
    lineas.append(f"Dictamen científico preliminar: {dc.get('veredicto', 'SIN_HIPOTESIS')} "
                  f"(solidez {dc.get('solidez', 0)}, suficiencia {dc.get('suficiencia', 0)}).")
    lineas.append("Esta hipótesis es preliminar y requiere corroboración cualitativa.")

    texto_det = "\n".join(lineas)
    hid = S.insertar_hipotesis(db, inv_id, texto_det, S.ORIGEN_DETERMINISTA,
                               [e["id"] for e in evidencias])
    S.registrar_decision(db, inv_id, "generar_hipotesis_determinista", autor,
                         detalle=f"hipotesis_id={hid}")

    insertadas = [S.listar_hipotesis(db, inv_id)[-1]]

    # Asistencia IA (opcional, etiquetada, con fallback).
    if usar_ia and nv.disponible():
        try:
            sintesis = nv.sintetizar(
                [{"texto": e["titulo"], "fuente": e["fuente"], "url": e["url"],
                  "fecha": e.get("fecha_publicacion")} for e in evidencias],
                organizacion=evidencias[0]["organizacion"],
            )
            cuerpo = sintesis.get("sintesis", "") if isinstance(sintesis, dict) else str(sintesis)
            texto_ia = "INFERENCIA IA: " + (cuerpo or texto_det)
            hid2 = S.insertar_hipotesis(db, inv_id, texto_ia, S.ORIGEN_IA,
                                        [e["id"] for e in evidencias])
            S.registrar_decision(db, inv_id, "generar_hipotesis_ia", autor,
                                 detalle=f"hipotesis_id={hid2}")
            insertadas.append(S.listar_hipotesis(db, inv_id)[-1])
        except Exception as exc:
            # Fallback determinista ya insertado; no falla la operación.
            S.registrar_decision(db, inv_id, "generar_hipotesis_ia_fallback", autor,
                                 detalle=str(exc))

    return insertadas


# --- 10. Peritaje (cierre humano) --------------------------------------
def cerrar_peritaje(db: Database, inv_id: str, autor: str = "investigador") -> dict:
    """Cierra el peritaje: valida científicamente y lo marca cerrado.

    El veredicto lo emite la validación científica (determinista), no la IA.
    """
    evidencias = S.listar_senales(db, inv_id, S.ESTADO_EVIDENCIA)
    expediente = {"evidencias": [_a_evidencia_para_vc(e) for e in evidencias]}
    dictamen = vc.validar_expediente(expediente)
    S.actualizar_investigacion(db, inv_id, estado="cerrada", cerrada_en=ahora_iso())
    dc = dictamen.get("dictamen_cientifico", {})
    S.registrar_decision(db, inv_id, "cerrar_peritaje", autor,
                         detalle=json.dumps(dc, ensure_ascii=False, default=str))
    return dc


# --- Triangulación (reutiliza validación científica) --------------------
def triangulacion(db: Database, inv_id: str) -> dict:
    evidencias = S.listar_senales(db, inv_id, S.ESTADO_EVIDENCIA)
    if not evidencias:
        return {
            "n_evidencias": 0, "fuentes_independientes": 0, "relaciones": 0,
            "contradicciones": 0, "evidencia_faltante": [],
            "veredicto": "SIN_HIPOTESIS", "solidez": 0, "suficiencia": 0,
        }
    exp_vc = [_a_evidencia_para_vc(e) for e in evidencias]
    expediente = {"evidencias": exp_vc}
    n_fuentes = vc.contar_fuentes_independientes(exp_vc)
    dictamen = vc.validar_expediente(expediente)
    dc = dictamen.get("dictamen_cientifico", {})
    relaciones = S.listar_relaciones(db, inv_id)
    tensiones = S.listar_tensiones(db, inv_id)
    contradicciones = sum(1 for r in relaciones if r["tipo"] == S.REL_CONTRADICE) + len(tensiones)
    faltante = [v.get("razon", "") for v in vc.detectar_vacios(expediente)]
    return {
        "n_evidencias": len(evidencias),
        "fuentes_independientes": n_fuentes,
        "relaciones": len(relaciones),
        "contradicciones": contradicciones,
        "evidencia_faltante": faltante,
        "veredicto": dc.get("veredicto", "SIN_HIPOTESIS"),
        "solidez": dc.get("solidez", 0),
        "suficiencia": dc.get("suficiencia", 0),
    }


# --- Estado completo (para la UI / trazabilidad) ------------------------
def obtener_estado(db: Database, inv_id: str) -> dict:
    inv = S.obtener_investigacion(db, inv_id)
    if inv is None:
        return {}
    senales = S.listar_senales(db, inv_id)
    return {
        "investigacion": inv,
        "conteos": {
            "senales": len(senales),
            "evidencias": S.contar_estado(db, inv_id, S.ESTADO_EVIDENCIA),
            "descartadas": S.contar_estado(db, inv_id, S.ESTADO_DESCARTADA),
        },
        "senales": senales,
        "relaciones": S.listar_relaciones(db, inv_id),
        "tensiones": S.listar_tensiones(db, inv_id),
        "hipotesis": S.listar_hipotesis(db, inv_id),
        "triangulacion": triangulacion(db, inv_id),
        "decisiones": [S._row_to_dict(r) for r in db.fetch_all(
            "SELECT * FROM decisiones WHERE inv_id = ? ORDER BY id", (inv_id,))],
    }


def listar_investigaciones(db: Database) -> list[dict]:
    S.init_investigacion_schema(db)
    return S.listar_investigaciones(db)


def _a_evidencia_para_vc(e: dict) -> dict:
    """Mapea una señal al shape que espera validacion_cientifica."""
    return {
        "texto": e.get("titulo", ""),
        "fuente": e.get("fuente", ""),
        "fecha": e.get("fecha_publicacion") or e.get("fecha_captura", ""),
        "url": e.get("url", ""),
        "tipo_evento": e.get("tipo_fuente", ""),
        "confianza": 1.0,
    }
