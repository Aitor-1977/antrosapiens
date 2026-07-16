"""Verificación de correo del decisor vía Hunter.io (opcional, bajo demanda).

Cierra el paso que faltaba: pasar de un correo HIPÓTESIS (patrón sin verificar) a
un correo VERIFICADO. Requiere ``HUNTER_API_KEY`` (se agrega en Vercel). Sin la
clave, todo el sistema sigue funcionando con las hipótesis deterministas de
``contacto.py``; con la clave, este módulo:

  1. BUSCA el correo del decisor (email-finder si hay nombre; si no, domain-search).
  2. lo VERIFICA (email-verifier: valid | accept_all | invalid | unknown…).

Diseño:
  - Las llamadas de red se inyectan (``http_get_json``) para testear con fixtures
    y controlar timeouts desde el endpoint.
  - NUNCA lanza: ante cualquier fallo (cuota, red, respuesta rara) devuelve un
    resultado con ``verificado=False`` y una nota; el operador nunca se queda sin
    respuesta.
  - Se usa BAJO DEMANDA (un decisor a la vez), no en el informe masivo, para no
    gastar la cuota de pago ni agotar el tiempo de la función serverless.
"""
from __future__ import annotations

import logging
import unicodedata
from typing import Callable, Optional
from urllib.parse import quote_plus

log = logging.getLogger("hd_scraper.hunter")

API = "https://api.hunter.io/v2"

# Estados de Hunter que consideramos "correo utilizable".
ESTADOS_OK = {"valid", "accept_all", "webmail"}

# Tipo de la función de red inyectable: url -> dict (JSON ya parseado).
HttpGetJson = Callable[[str], dict]


def disponible(api_key: str) -> bool:
    """True si hay clave de Hunter configurada."""
    return bool((api_key or "").strip())


def _sin_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _nombre_apellido(nombre_decisor: str) -> tuple[str, str]:
    toks = [t for t in _sin_acentos(nombre_decisor or "").split() if t]
    if len(toks) >= 2:
        return toks[0], toks[-1]
    if len(toks) == 1:
        return toks[0], ""
    return "", ""


def email_finder_url(dominio: str, nombre: str, apellido: str, api_key: str) -> str:
    q = f"domain={quote_plus(dominio)}&api_key={quote_plus(api_key)}"
    if nombre:
        q += f"&first_name={quote_plus(nombre)}"
    if apellido:
        q += f"&last_name={quote_plus(apellido)}"
    return f"{API}/email-finder?{q}"


def domain_search_url(dominio: str, api_key: str, limite: int = 10) -> str:
    return f"{API}/domain-search?domain={quote_plus(dominio)}&limit={limite}&api_key={quote_plus(api_key)}"


def email_verifier_url(email: str, api_key: str) -> str:
    return f"{API}/email-verifier?email={quote_plus(email)}&api_key={quote_plus(api_key)}"


def _elegir_de_domain_search(data: dict) -> tuple[str, Optional[int]]:
    """Del domain-search, elige el correo del contacto más 'decisor' (senior)."""
    emails = ((data or {}).get("data") or {}).get("emails") or []
    if not emails:
        return "", None
    # Prioriza posiciones senior si vienen; si no, el de mayor confianza.
    def rango(e: dict) -> tuple[int, int]:
        pos = (e.get("position") or "").lower()
        senior = 0 if any(k in pos for k in ("founder", "ceo", "director", "head", "chief", "vp")) else 1
        return (senior, -(e.get("confidence") or 0))
    mejor = sorted(emails, key=rango)[0]
    return mejor.get("value", ""), mejor.get("confidence")


def buscar_email(dominio: str, nombre_decisor: str, api_key: str,
                 http_get_json: HttpGetJson) -> dict:
    """Busca el correo del decisor. Devuelve {email, score, fuente}. No lanza."""
    nombre, apellido = _nombre_apellido(nombre_decisor)
    try:
        if nombre and apellido:
            data = http_get_json(email_finder_url(dominio, nombre, apellido, api_key))
            d = (data or {}).get("data") or {}
            return {"email": d.get("email", "") or "", "score": d.get("score"),
                    "fuente": "email-finder"}
        data = http_get_json(domain_search_url(dominio, api_key))
        email, conf = _elegir_de_domain_search(data)
        return {"email": email, "score": conf, "fuente": "domain-search"}
    except Exception as exc:  # cuota/red/respuesta rara
        log.debug("hunter buscar_email falló: %s", exc)
        return {"email": "", "score": None, "fuente": "error", "error": str(exc)}


def verificar_email(email: str, api_key: str, http_get_json: HttpGetJson) -> dict:
    """Verifica un correo con Hunter. Devuelve {status, score, verificado}. No lanza."""
    try:
        data = http_get_json(email_verifier_url(email, api_key))
        d = (data or {}).get("data") or {}
        status = (d.get("status") or d.get("result") or "unknown").lower()
        return {"status": status, "score": d.get("score"),
                "verificado": status in ESTADOS_OK}
    except Exception as exc:
        log.debug("hunter verificar_email falló: %s", exc)
        return {"status": "error", "score": None, "verificado": False, "error": str(exc)}


def enriquecer_contacto(dominio: str, nombre_decisor: str, api_key: str,
                        http_get_json: HttpGetJson) -> dict:
    """Busca + verifica el correo del decisor. Best-effort; nunca lanza.

    Devuelve un dict de contacto con ``verificado`` real. Si no hay email o falla,
    ``verificado=False`` y una nota explicativa (el llamador puede caer a la
    hipótesis determinista de contacto.py).
    """
    if not disponible(api_key):
        return {"dominio": dominio, "email_verificado": "", "status": "sin_clave",
                "verificado": False, "score": None,
                "nota": "configura HUNTER_API_KEY en Vercel para verificar correos"}
    if not dominio or "." not in dominio:
        return {"dominio": "", "email_verificado": "", "status": "sin_dominio",
                "verificado": False, "score": None,
                "nota": "sin dominio válido para consultar Hunter"}

    hallado = buscar_email(dominio, nombre_decisor, api_key, http_get_json)
    email = hallado.get("email", "")
    if not email:
        return {"dominio": dominio, "email_verificado": "", "status": "no_encontrado",
                "verificado": False, "score": None, "fuente": hallado.get("fuente"),
                "nota": "Hunter no encontró un correo para este dominio/decisor"}

    ver = verificar_email(email, api_key, http_get_json)
    return {
        "dominio": dominio,
        "email_verificado": email if ver["verificado"] else "",
        "email_encontrado": email,
        "status": ver["status"],
        "verificado": ver["verificado"],
        "score": ver.get("score"),
        "fuente": hallado.get("fuente"),
        "nota": "correo verificado por Hunter" if ver["verificado"]
                else f"Hunter marcó el correo como '{ver['status']}' (revisa antes de usar)",
    }
