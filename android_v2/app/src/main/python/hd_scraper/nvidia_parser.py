"""Síntesis estructural con LLM NVIDIA (infraestructura de pensamiento).

Capa 19 extendida: cuando ``NVIDIA_API_KEY`` está configurada, la síntesis por
organización puede enriquecerse invocando un LLM vía NVIDIA NIM (endpoint
compatible con OpenAI). Autorizado por el operador el 2026-08-04 (ver
CLAUDE.md → «Frontera de Interpretación»).

Reglas inmutables:
- El LLM SOLO reordena/sintetiza evidencia que ESTE motor ya extrajo; nunca
  escribe ni decide acción comercial.
- Salida SIEMPRE preliminar, etiquetada y grounded: `evidencia_urls` y la
  métrica de sustancia son las deterministas (jamás inventadas por el LLM).
- Vocabulario público/genérico de la taxonomía Motor A: NO clasifica Deuda
  Cultural™ ni emite juicios de valor (eso sigue siendo RadarHD).
- Fallback determinista garantizado: sin clave, ante fallo de red, timeout o
  JSON inválido, se lanza ``NvidiaError`` para que el endpoint degrade a
  ``sintetizar``; Motor A nunca colapsa.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .config import settings
from .sintesis import sintetizar as sintetizar_determinista

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres la infraestructura de síntesis estructural de Hamaca \
Digital. Tu función es analizar texto crudo ya extraído por el motor de \
evidencia y detectar fricciones, tensiones y patrones de comportamiento \
públicos y verificables. Usa vocabulario público y genérico; NO clasifiques \
Deuda Cultural™, NO emitas juicios de valor ni evalúes moral o culturalmente \
a las organizaciones.

Devuelve EXCLUSIVAMENTE un objeto JSON con estas claves:
- "patron_comportamiento": str
- "senal_tension": str
- "actores_involucrados": [{"nombre": str, "rol": str}]
- "metrica_relevancia": {"evidencias": int, "fuentes": int, "resumen": str}
- "evidencia_urls": [str, ...]
- "estado": "sintetizado" | "sin_marcador"
- "motivo": str

Reglas:
- Grounded: cada afirmación debe estar sostenida por las citas recibidas; NO \
inventes hechos, fechas, cifras ni URLs.
- Los actores son SOLO los presentes en la evidencia: la organización \
observada, las personas citadas y otras organizaciones mencionadas.
- Si la evidencia no sostiene ningún patrón ni tensión, devuelve estado \
"sin_marcador" con un motivo breve."""

NOTA_LLM = "Síntesis estructural preliminar generada con LLM (NVIDIA NIM); verificar en campo."


class NvidiaError(Exception):
    """Fallo controlado del enriquecimiento LLM (red, timeout, HTTP, formato).

    Se lanza para que el endpoint degrade a la síntesis determinista con un
    motivo estructurado, sin colapsar el servidor.
    """

    def __init__(self, mensaje: str, *, causa: BaseException | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.causa = causa


def disponible() -> bool:
    """True si hay credencial NVIDIA configurada para activar el LLM."""
    return bool((settings.nvidia_api_key or "").strip())


def _evidencias_a_insumo(evidencias: list[dict]) -> list[dict]:
    """Recorta las filas del contrato a lo que el LLM necesita (nada privado)."""
    out: list[dict] = []
    for e in evidencias or []:
        cita = (e.get("cita_textual") or "").strip()
        if not cita:
            continue
        out.append({
            "fecha": (e.get("fecha_publicacion") or "")[:10],
            "medio": (e.get("nombre_medio") or "").strip(),
            "url": (e.get("url_fuente") or "").strip(),
            "cita": cita,
        })
    return out


def _mensaje_usuario(org: str, insumo: list[dict]) -> str:
    lineas = [f"Organización: {org}", "", "Evidencia ya extraída por Motor A:"]
    for i, fila in enumerate(insumo, start=1):
        url = f" · {fila['url']}" if fila["url"] else ""
        fecha = f"({fila['fecha']}) " if fila["fecha"] else ""
        lineas.append(f"{i}. {fecha}{fila['medio']}{url}\n   «{fila['cita']}»")
    lineas.append("")
    lineas.append("Devuelve el JSON del esquema indicado, grounded en esa evidencia.")
    return "\n".join(lineas)


def _pedir_json(*, org: str, insumo: list[dict], http: httpx.Client) -> dict:
    """Invoca al LLM y devuelve el JSON crudo; levanta NvidiaError en fallos."""
    if not disponible():
        raise NvidiaError("NVIDIA_API_KEY no configurada")
    try:
        respuesta = http.post(
            f"{settings.nvidia_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.nvidia_api_key}"},
            json={
                "model": settings.nvidia_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _mensaje_usuario(org, insumo)},
                ],
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
            },
        )
    except httpx.TimeoutException as error:
        raise NvidiaError(
            f"timeout al consultar el LLM NVIDIA (>{settings.nvidia_timeout_s}s)",
            causa=error,
        ) from error
    except httpx.HTTPError as error:
        raise NvidiaError(f"error de red al consultar el LLM NVIDIA: {error}", causa=error) from error

    if respuesta.status_code != 200:
        raise NvidiaError(
            f"NVIDIA respondió HTTP {respuesta.status_code}: {respuesta.text[:200]}"
        )
    try:
        datos = respuesta.json()
    except ValueError as error:
        raise NvidiaError("NVIDIA devolvió un cuerpo no JSON", causa=error) from error

    try:
        contenido = datos["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise NvidiaError("respuesta del LLM sin `choices[0].message.content`", causa=error) from error

    try:
        parsed = json.loads(contenido)
    except (ValueError, TypeError) as error:
        raise NvidiaError("el LLM devolvió JSON malformado", causa=error) from error
    if not isinstance(parsed, dict):
        raise NvidiaError("el LLM no devolvió un objeto JSON")
    return parsed


def _actores_llm(llm: dict) -> list[dict]:
    actores: list[dict] = []
    vistos: set[str] = set()
    for item in llm.get("actores_involucrados") or []:
        if isinstance(item, dict):
            nombre = str(item.get("nombre") or "").strip()
            rol = str(item.get("rol") or "involucrado").strip()
        else:
            nombre = str(item).strip()
            rol = "involucrado"
        if not nombre or nombre.lower() in vistos:
            continue
        vistos.add(nombre.lower())
        actores.append({"nombre": nombre, "rol": rol})
    return actores


def _normalizar(base: dict, llm: dict) -> dict:
    """Superpone la interpretación del LLM sobre la base determinista.

    La base determina estado, evidencia_urls y sustancia_metrica (grounding);
    el LLM solo puede matizar patrón, tensión, actores y citas, y solo con
    valores no vacíos (nunca borra ni fabrica).
    """
    resultado = dict(base)
    for clave in ("patron_comportamiento", "senal_tension_dolor", "cita_tension"):
        valor_llm = str(
            llm.get("senal_tension" if clave == "senal_tension_dolor" else clave) or ""
        ).strip()
        if valor_llm:
            resultado[clave] = valor_llm
    if "marcadores_textuales" in llm and isinstance(llm["marcadores_textuales"], list):
        marcadores = [str(m) for m in llm["marcadores_textuales"] if str(m).strip()]
        if marcadores:
            resultado["marcadores_textuales"] = marcadores
    actores = _actores_llm(llm)
    if actores:
        resultado["actores_involucrados"] = actores
    resultado["nota"] = NOTA_LLM
    return resultado


def sintetizar(evidencias: list[dict], org: str, *, http: httpx.Client | None = None) -> dict:
    """Síntesis estructural enriquecida con el LLM de NVIDIA.

    Devuelve el esquema ``sintesis_estructural.v1`` (la base determinista con
    la interpretación del LLM superpuesta). Levanta ``NvidiaError`` ante
    cualquier fallo; el llamador debe degradar a ``sintetizar_determinista``.
    """
    base = sintetizar_determinista(evidencias, org)
    insumo = _evidencias_a_insumo(evidencias)
    timeout = settings.nvidia_timeout_s
    with http or httpx.Client(timeout=httpx.Timeout(timeout)) as cliente:
        llm = _pedir_json(org=org, insumo=insumo, http=cliente)
    return _normalizar(base, llm)


__all__ = [
    "NvidiaError",
    "SYSTEM_PROMPT",
    "NOTA_LLM",
    "disponible",
    "sintetizar",
    "sintetizar_determinista",
    "_normalizar",
    "_mensaje_usuario",
    "_evidencias_a_insumo",
    "_pedir_json",
]
