"""Validación y confirmación de correos (estructura, determinista, sin red).

Limpieza y verificación de las direcciones de correo que entran a los flujos de
contacto del radar. Dos conceptos distintos y complementarios:

  - ``validar``: el correo es UTILIZABLE por forma (sintaxis, dominio, TLD) y no
    es un buzón genérico ni un placeholder. Sin red. Produce correos LIMPIOS.
  - ``confirmar``: el correo está RESPALDADO por la evidencia. Determinista:
    un correo se confirma cuando aparece en ≥2 fuentes independientes
    (triangulación) o cuando su dominio coincide con el dominio oficial del
    prospecto y la fuente lo declaró. No decide contacto: solo marca qué correos
    están verificados frente a los que son hipótesis.

Sobre la invariante "no interpreta": la validación es estructural (sintaxis y
vocabulario de buzones), la confirmación es conteo/triangulación de fuentes.
Nunca se infiere que un correo "es el correcto"; se reporta cuánto lo respalda
la evidencia. La decisión de uso sigue siendo del operador.
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

# Sintaxis básica: local@dominio.tld. El TLD se valida aparte (2+ letras).
PATRON_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

# Buzones genéricos o de sistema: nunca son contactos de decisión.
BUZONES_GENERICOS = {
    "info", "contact", "contacto", "support", "soporte", "noreply", "no-reply",
    "no.reply", "hello", "hola", "admin", "webmaster", "press", "prensa", "sales",
    "ventas", "help", "helpdesk", "service", "team", "legal", "hi", "correo", "mail",
    "careers", "jobs", "empleo", "rrhh", "hr", "newsletter", "notificaciones",
    "seguridad", "privacy", "privacidad", "marketing", "comercial", "reclamaciones",
    "postmaster", "abuse", "billing", "contactanos", "contactus", "soporte_tecnico",
}

# Extensiones de imagen: un email con dominio *.png/*.jpg es casi seguro un ruido
# de extracción (URL de imagen con '@' en el path), no una dirección real.
EXTENSIONES_DE_IMAGEN = {"png", "jpg", "jpeg", "gif", "webp", "svg", "webp"}

# Dominios de ejemplo/placeholder y TLD reservados: no son contactos reales.
DOMINIOS_PLACEHOLDER = {
    "example.com", "example.org", "example.net", "domain.com", "domain.org",
    "test.com", "test.org", "email.com", "mail.com", "yourdomain.com", "sitioweb.com",
}
TLD_NO_REALES = {"local", "test", "invalid", "localhost", "onion", "example"}

MIN_LOGO_MATCH = 2  # fuentes independientes mínimas para confirmar un correo


def _sin_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar_email(email: str) -> str:
    """Minúsculas, sin espacios, sin puntuación de borde ni final de frase.

    Conserva un punto INICIAL (el validador debe poder rechazar ".juan@…");
    solo quita la puntuación final (coma, punto de cierre de frase, corchetes).
    """
    e = (email or "").strip().strip(" ;:()<>'\"")
    while e.endswith((",", ".")):
        e = e[:-1]
    return e.lower()


def _dominio(email: str) -> str:
    return (email or "").split("@", 1)[1] if "@" in (email or "") else ""


def _tld(dominio: str) -> str:
    return dominio.rsplit(".", 1)[-1] if "." in dominio else ""


def email_utilizable(email: str) -> bool:
    """¿El correo es limpio y utilizable? Solo forma y vocabulario, sin red."""
    e = normalizar_email(email)
    if not PATRON_EMAIL.match(e):
        return False
    local = e.split("@", 1)[0]
    dominio = _dominio(e)
    if dominio in DOMINIOS_PLACEHOLDER:
        return False
    if _tld(dominio) in TLD_NO_REALES:
        return False
    if _tld(dominio) in EXTENSIONES_DE_IMAGEN:
        return False
    if local.count("@") > 0 or ".." in local or local.startswith(".") or local.endswith("."):
        return False
    if local[0].isdigit() or not local[0].isalnum():
        return False
    if _es_generico(local):
        return False
    return True


def _es_generico(local: str) -> bool:
    if local in BUZONES_GENERICOS:
        return True
    return any(
        local.startswith(f"{g}.") or local.startswith(f"{g}-") or local.startswith(f"{g}_")
        for g in BUZONES_GENERICOS
    )


def motivo_rechazo(email: str) -> str:
    """Motivo legible si el correo no es utilizable; '' si lo es."""
    e = normalizar_email(email)
    if not PATRON_EMAIL.match(e):
        return "sintaxis inválida"
    local = e.split("@", 1)[0]
    dominio = _dominio(e)
    if dominio in DOMINIOS_PLACEHOLDER:
        return "dominio de ejemplo/placeholder"
    if _tld(dominio) in TLD_NO_REALES:
        return "TLD reservado o no real"
    if _tld(dominio) in EXTENSIONES_DE_IMAGEN:
        return "parece una URL de imagen, no un correo"
    if ".." in local or local.startswith(".") or local.endswith("."):
        return "local con puntos consecutivos o de borde"
    if _es_generico(local):
        return "buzón genérico (no de decisión)"
    return ""


def emails_validos(lista: list[str] | tuple[str, ...]) -> list[str]:
    """Limpia, normaliza y deduplica una lista de correos (solo los utilizables)."""
    vistos: set[str] = set()
    salida: list[str] = []
    for e in lista or ():
        norm = normalizar_email(e)
        if not email_utilizable(norm):
            continue
        if norm not in vistos:
            vistos.add(norm)
            salida.append(norm)
    return salida


def confirmar_por_triangulacion(emails_por_fuente: dict[str, list[str]]) -> set[str]:
    """Correos respaldados por ≥2 fuentes independientes (triangulación).

    ``emails_por_fuente`` mapea una clave de fuente (medio/url) a los correos
    crudos hallados en ella. Un correo se confirma si aparece en al menos
    ``MIN_LOGO_MATCH`` fuentes distintas. Determinista y sin red.
    """
    por_correo: dict[str, set[str]] = defaultdict(set)
    for fuente, emails in (emails_por_fuente or {}).items():
        for e in emails or ():
            norm = normalizar_email(e)
            if email_utilizable(norm):
                por_correo[norm].add(fuente)
    return {correo for correo, fuentes in por_correo.items() if len(fuentes) >= MIN_LOGO_MATCH}


def _host_oficial(dominio_oficial: str) -> str:
    """Host (sin www) a partir de un dominio o URL oficial. '' si no hay."""
    s = _sin_acentos((dominio_oficial or "").strip().lower())
    if "//" in s:
        s = s.split("//", 1)[1]
    s = s.split("/", 1)[0].split("?")[0].split("#")[0].split("@")[-1].split(":")[0]
    if s.startswith("www."):
        s = s[4:]
    return s


def confirmar_por_dominio(email: str, dominio_oficial: str) -> bool:
    """¿El correo pertenece al dominio oficial del prospecto? Determinista."""
    if not email_utilizable(email):
        return False
    host = _host_oficial(dominio_oficial)
    if not host:
        return False
    return _dominio(normalizar_email(email)) == host


def resumen_emails(emails: list[str]) -> dict:
    """Resumen legible de una lista: válidos, rechazados y motivos."""
    validos: list[str] = []
    rechazados: list[tuple[str, str]] = []
    for e in emails or ():
        norm = normalizar_email(e)
        if email_utilizable(norm):
            validos.append(norm)
        else:
            rechazados.append((norm, motivo_rechazo(norm)))
    return {
        "vistos": len(emails or ()),
        "validos": sorted(set(validos)),
        "rechazados": sorted(set(rechazados)),
    }
