"""Contacto del decisor — HIPÓTESIS determinista (sin red, sin verificación).

Genera rutas de contacto probables a partir del dominio del prospecto: buzones
genéricos (contacto@, hola@…) y, si se conoce el nombre del decisor, patrones de
correo corporativos habituales (nombre@, n.apellido@…).

HONESTIDAD (crítico): esto NO es un correo verificado. Es una LISTA DE CANDIDATOS
para que el operador pruebe/confirme. La verificación real (SMTP/Hunter) exige un
servicio externo con clave y red; cuando esté disponible, este módulo es el punto
donde se conectaría. Marcado siempre como ``verificado=False``.
"""
from __future__ import annotations

import unicodedata
from urllib.parse import urlsplit

# Buzones genéricos frecuentes, en orden de probabilidad de respuesta comercial.
BUZONES_GENERICOS = ("contacto", "hola", "info", "ventas", "comercial", "prensa")


def _sin_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def dominio_de(sitio_web: str) -> str:
    """Extrae el dominio (sin www) de una URL. '' si no hay uno válido."""
    if not sitio_web:
        return ""
    s = sitio_web.strip()
    if "//" not in s:
        s = "https://" + s
    host = urlsplit(s).netloc.lower().split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host if "." in host else ""


def _tokens_nombre(nombre_decisor: str) -> list[str]:
    limpio = _sin_acentos(nombre_decisor or "").lower()
    return [t for t in "".join(c if c.isalnum() else " " for c in limpio).split() if t]


def patrones_email(dominio: str, nombre_decisor: str = "") -> list[str]:
    """Correos candidatos (hipótesis) para un dominio y, opcional, un decisor.

    Devuelve genéricos siempre; si hay nombre del decisor, antepone los patrones
    corporativos más comunes (nombre.apellido@, ninicial+apellido@, nombre@).
    Sin duplicados y en orden de probabilidad. Nunca verifica.
    """
    dominio = dominio_de(dominio) or dominio.strip().lower()
    if not dominio or "." not in dominio:
        return []
    salida: list[str] = []
    toks = _tokens_nombre(nombre_decisor)
    if len(toks) >= 2:
        nombre, apellido = toks[0], toks[-1]
        salida += [
            f"{nombre}.{apellido}@{dominio}",
            f"{nombre[0]}{apellido}@{dominio}",
            f"{nombre}@{dominio}",
            f"{nombre}{apellido}@{dominio}",
        ]
    elif len(toks) == 1:
        salida.append(f"{toks[0]}@{dominio}")
    salida += [f"{b}@{dominio}" for b in BUZONES_GENERICOS]
    return list(dict.fromkeys(salida))


def rutas_contacto(dominio: str, nombre_decisor: str = "") -> dict:
    """Paquete de contacto (hipótesis): dominio, correos candidatos, verificado=False."""
    dom = dominio_de(dominio) or (dominio or "").strip().lower()
    emails = patrones_email(dom, nombre_decisor)
    return {
        "dominio": dom if "." in dom else "",
        "emails_candidatos": emails,
        "email_sugerido": emails[0] if emails else "",
        "verificado": False,
        "nota": "correos candidatos (hipótesis), sin verificar; confírmalos antes de usar",
    }
