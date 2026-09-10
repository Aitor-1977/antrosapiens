"""Publicador Científico — Capa 17.

Genera documentación científica (peritajes, informes, dossiers) en múltiples
formatos (JSON, CSV, HTML, HTML imprimible/PDF) a partir ÚNICAMENTE de evidencia
validada. Nunca inventa información: todo campo proviene del expediente, su
validación (Capa 11) y su gobernanza (Capa 12). Cada documento lleva firma
determinista del Motor. Sin IA, sin red.

Un peritaje sobre una hipótesis no validada se marca ``publicable=False`` y
declara sus limitaciones: se publica el estado real, nunca una conclusión que la
evidencia no sostiene.
"""
from __future__ import annotations

import csv
import io

from .dictamen import generar_dictamen
from .gobernanza import VERSION_GOBERNANZA, _hash_obj, firmar_motor


def _esc(s: str) -> str:
    return (str(s) or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _evidencias(expediente: dict) -> list[dict]:
    ev = expediente.get("evidencias", [])
    if isinstance(ev, dict):
        return list(ev.get("items", []))
    return list(ev or [])


def _ev_norm(ev: dict) -> dict:
    return {
        "texto": ev.get("texto") or ev.get("cita_textual") or "",
        "fuente": ev.get("fuente") or ev.get("nombre_medio") or "",
        "fecha": ev.get("fecha") or ev.get("fecha_publicacion") or "",
        "url": ev.get("url") or ev.get("url_fuente") or "",
    }


# ── 7. Firmar documento ───────────────────────────────────────────────────────
def firmar_documento(doc: dict, excluir: tuple[str, ...] = ("firma",)) -> str:
    """Firma determinista de un documento.

    Excluye la propia firma y cualquier campo volátil indicado (p. ej. la fecha
    de emisión y el certificado derivado), para que la firma sea reproducible:
    solo depende del contenido científico, no del momento de emisión.
    """
    contenido = {k: v for k, v in doc.items() if k not in excluir}
    h = _hash_obj(contenido)
    return firmar_motor(h, VERSION_GOBERNANZA, doc.get("veredicto", ""))


# ── 1. Generar peritaje ───────────────────────────────────────────────────────
def generar_peritaje(expediente: dict, validacion: dict, huella: dict,
                     certificado: dict) -> dict:
    """Peritaje antropológico completo, trazable y firmado (evidencia validada)."""
    dic = validacion.get("dictamen_cientifico", {}) or {}
    publicable = dic.get("veredicto") in ("VALIDADA", "VALIDADA_PARCIAL")
    doc = {
        "tipo": "peritaje_antropologico",
        "org": expediente.get("nombre", ""),
        "fecha": huella.get("fecha", ""),
        "id": huella.get("id", ""),
        "hash": huella.get("hash", ""),
        "publicable": publicable,
        "veredicto": dic.get("veredicto", ""),
        "hipotesis": expediente.get("tipo_deuda", ""),
        "razon": expediente.get("deuda_razon", ""),
        "resumen": dic.get("resumen", ""),
        "recomendacion": dic.get("recomendacion", ""),
        "solidez": dic.get("solidez", 0),
        "suficiencia": dic.get("suficiencia", 0),
        "nivel_evidencia": dic.get("nivel_evidencia", ""),
        "limitaciones": dic.get("limitaciones", []),
        "evidencias": [_ev_norm(e) for e in _evidencias(expediente)],
        "certificado": certificado,
        "anexo_metodologico": {
            "trazabilidad": validacion.get("trazabilidad", {}),
            "fechado": validacion.get("fechado", {}),
            "reproducibilidad": validacion.get("reproducibilidad", {}),
            "versiones": huella.get("versiones", {}),
        },
    }
    # La firma cubre el contenido científico, no la fecha ni el certificado
    # derivado (que llevan la fecha de emisión): así es reproducible.
    doc["firma"] = firmar_documento(doc, excluir=("firma", "fecha", "certificado"))
    return doc


# ── 2. Generar informe ────────────────────────────────────────────────────────
def generar_informe(expedientes: list[dict], titulo: str = "Informe",
                    region: str = "", vertical: str = "") -> dict:
    """Informe agregado a partir del Dictamen Antropológico (reutilizado)."""
    dictamen = generar_dictamen(expedientes, query=titulo, region=region, vertical=vertical)
    doc = {
        "tipo": "informe_cientifico",
        "titulo": titulo,
        "total_organizaciones": len(expedientes),
        "veredicto": "informe",
        "dictamen": dictamen,
    }
    doc["firma"] = firmar_documento(doc)
    return doc


# ── 3-4. Cuerpo y documentos HTML ─────────────────────────────────────────────
def _cuerpo_html(peritaje: dict) -> str:
    ev_rows = "".join(
        f"<div class='ev'>{_esc(e['texto'][:200])}<br><small>{_esc(e['fuente'])} · "
        f"{_esc(e['fecha'])}</small></div>"
        for e in peritaje.get("evidencias", []))
    lims = "".join(f"<li>{_esc(l)}</li>" for l in peritaje.get("limitaciones", []))
    return f"""<h1>Peritaje Antropológico · {_esc(peritaje['org'])}</h1>
<p><b>Veredicto:</b> {_esc(peritaje['veredicto'])} · <b>Publicable:</b>
{'sí' if peritaje['publicable'] else 'no'}</p>
<p><b>Hipótesis:</b> {_esc(peritaje['hipotesis'])}</p>
<p>{_esc(peritaje['resumen'])}</p>
<p><b>Solidez:</b> {peritaje['solidez']}/100 · <b>Suficiencia:</b>
{peritaje['suficiencia']}/100 · <b>Nivel evidencia:</b> {_esc(peritaje['nivel_evidencia'])}</p>
<h2>Evidencia ({len(peritaje.get('evidencias', []))})</h2>{ev_rows}
{('<h2>Limitaciones</h2><ul>' + lims + '</ul>') if lims else ''}
<h2>Firma</h2><code>{_esc(peritaje.get('firma', ''))}</code>"""


def generar_html(peritaje: dict) -> str:
    """Documento HTML para pantalla."""
    return (f"<!doctype html><html lang='es'><head><meta charset='utf-8'>"
            f"<title>Peritaje · {_esc(peritaje['org'])}</title></head>"
            f"<body>{_cuerpo_html(peritaje)}</body></html>")


def generar_pdf(peritaje: dict) -> str:
    """Documento HTML imprimible como PDF (convención del repo para dossiers)."""
    return (f"<!doctype html><html lang='es'><head><meta charset='utf-8'>"
            f"<title>Peritaje · {_esc(peritaje['org'])}</title>"
            f"<style>@media print{{@page{{margin:1.5cm}}}} "
            f"body{{font-family:system-ui;max-width:800px;margin:auto}}"
            f".ev{{border-left:2px solid #ccc;padding:.3rem .6rem;margin:.4rem 0}}"
            f"</style></head><body>{_cuerpo_html(peritaje)}</body></html>")


# ── 5. Generar JSON ───────────────────────────────────────────────────────────
def generar_json(peritaje: dict) -> dict:
    """Representación JSON del documento (serializable, sin pérdida)."""
    return dict(peritaje)


# ── 6. Generar CSV ────────────────────────────────────────────────────────────
def generar_csv(peritaje: dict) -> str:
    """CSV de la evidencia trazable del peritaje."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["org", "fuente", "fecha", "url", "texto"])
    org = peritaje.get("org", "")
    for e in peritaje.get("evidencias", []):
        w.writerow([org, e["fuente"], e["fecha"], e["url"], e["texto"]])
    return buf.getvalue()
