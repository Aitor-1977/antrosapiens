"""Perfil Fundacional — extracción estructural desde fuentes ORGÁNICAS.

Autorizado por el operador (Mario) el 2026-07-31: el motor debe construir un
perfil fundacional, histórico y estructural de la entidad a partir de sus
PROPIAS fuentes (su sitio web), ignorando el ruido mediático genérico. La
extracción deja de perseguir "noticias" para rastrear el dominio de la
organización.

Naturaleza (frontera Motor A, ver CLAUDE.md): esto es EXTRACCIÓN OBJETIVA de
hechos que la propia organización declara (tamaño/escala, año de fundación,
descripción). NO puntúa, NO clasifica culturalmente, NO interpreta. Es
determinista y reproducible: el mismo HTML produce el mismo perfil. Por eso NO
activa la «Regla de ampliación» (que rige la interpretación, no la extracción de
campos objetivos): un tamaño declarado es un dato, no un juicio.

Cero prensa: solo se consultan rutas del dominio propio de la organización.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

from .config import settings
from .db.models import ahora_iso

# Banda de escala cuando la fuente no declara tamaño (patrón `no_fechado`).
ESCALA_INDETERMINADA = "indeterminada"
BANDAS = ["1-10", "11-50", "51-200", "201-500", "501+"]

# Rutas orgánicas típicas del perfil fundacional (sitio propio, nunca prensa).
RUTAS_PERFIL = ["", "/about", "/about-us", "/nosotros", "/quienes-somos",
                "/sobre-nosotros", "/company", "/es/nosotros", "/acerca-de"]

_ANIO_MIN = 1900


# ── Extracción pura (sin red; determinista y testeable) ────────────────────

def texto_plano(html: str) -> str:
    """HTML → texto plano determinista (elimina script/style/tags/entidades)."""
    if not html:
        return ""
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'")):
        html = html.replace(a, b)
    return re.sub(r"\s+", " ", html).strip()


def _banda(n: int) -> str:
    if n <= 10:
        return "1-10"
    if n <= 50:
        return "11-50"
    if n <= 200:
        return "51-200"
    if n <= 500:
        return "201-500"
    return "501+"


def _int(s: str) -> Optional[int]:
    d = re.sub(r"[^\d]", "", s or "")
    return int(d) if d else None


# Menciones de personas (ES/EN). La escala solo se fija con un dato NUMÉRICO
# EXPLÍCITO de personas — nunca se infiere.
_PERSONAS = (r"(?:emplead[oa]s|colaborador[ae]s|personas|trabajador[ae]s|"
             r"integrantes|employees|people|team\s+members)")
_RE_RANGO = re.compile(r"(\d[\d.,]*)\s*[-–a]\s*(\d[\d.,]*)\s*\+?\s*" + _PERSONAS, re.I)
_RE_NUM = re.compile(r"(\d[\d.,]*)\s*\+?\s*" + _PERSONAS, re.I)


def escala_desde_texto(texto: str) -> str:
    """Banda de escala/tamaño a partir de hechos declarados. Determinista.

    Devuelve una de ``BANDAS`` o ``'indeterminada'``. Exige una mención numérica
    explícita de personas; no infiere tamaño de señales indirectas.
    """
    if not texto:
        return ESCALA_INDETERMINADA
    # Rango explícito ("51-200 empleados"): la banda la fija el límite superior.
    m = _RE_RANGO.search(texto)
    if m:
        hi = _int(m.group(2))
        if hi:
            return _banda(hi)
    # Número simple ("120 empleados", "somos 40 personas"): toma el mayor válido.
    mejor: Optional[int] = None
    for mm in _RE_NUM.finditer(texto):
        n = _int(mm.group(1))
        if n and 1 <= n <= 5_000_000:
            mejor = n if mejor is None else max(mejor, n)
    if mejor is not None:
        return _banda(mejor)
    return ESCALA_INDETERMINADA


_RE_FUNDACION = re.compile(
    r"(?:fundad[ao]s?|founded|establecid[ao]s?|cread[ao]s?|nacimos|desde|since|est\.?)"
    r"\D{0,12}(\d{4})",
    re.I,
)


def anio_fundacion_desde_texto(texto: str) -> Optional[str]:
    """Año de fundación declarado (1900..año actual). ``None`` si no aparece."""
    if not texto:
        return None
    anio_actual = datetime.now(timezone.utc).year
    for m in _RE_FUNDACION.finditer(texto):
        y = int(m.group(1))
        if _ANIO_MIN <= y <= anio_actual:
            return str(y)
    return None


def _descripcion(texto: str, limite: int = 600) -> str:
    return (texto or "")[:limite].strip()


@dataclass
class PerfilFundacional:
    """Perfil estructural de una organización desde su fuente orgánica.

    ``escala`` es OBLIGATORIO: siempre lleva una banda o ``'indeterminada'``.
    """
    empresa: str
    escala: str = ESCALA_INDETERMINADA
    anio_fundacion: Optional[str] = None
    discurso_corporativo: Optional[str] = None
    url_perfil: Optional[str] = None
    fuente_discurso: str = "sitio_oficial"
    fecha_captura: str = field(default_factory=ahora_iso)

    def a_thick(self) -> dict:
        """Mapea a los campos que consumen ``nuevo_prospecto``/``upsert_prospecto``."""
        return {
            "discurso_corporativo": self.discurso_corporativo,
            "tipo_discurso": "perfil",
            "url_perfil": self.url_perfil,
            "fuente_discurso": self.fuente_discurso,
            "fecha_captura": self.fecha_captura,
            "escala": self.escala,
        }


def extraer_perfil(html: str, url: str, empresa: str) -> PerfilFundacional:
    """Construye el ``PerfilFundacional`` desde HTML ya descargado (función pura)."""
    texto = texto_plano(html)
    return PerfilFundacional(
        empresa=empresa,
        escala=escala_desde_texto(texto),
        anio_fundacion=anio_fundacion_desde_texto(texto),
        discurso_corporativo=_descripcion(texto) or None,
        url_perfil=url or None,
    )


# ── Recolección orgánica (con red; SOLO el dominio propio) ─────────────────

def _dominio_a_base(dominio: str) -> str:
    d = (dominio or "").strip()
    if not d:
        return ""
    if not d.startswith(("http://", "https://")):
        d = "https://" + d
    return d.rstrip("/")


def construir_perfil(empresa: str, dominio: str,
                     client: httpx.Client | None = None) -> PerfilFundacional:
    """Rastrea el sitio PROPIO de la organización y arma el perfil fundacional.

    Solo consulta rutas del dominio de la entidad (cero prensa). Combina el texto
    de las rutas de "quiénes somos" y extrae los hechos estructurales. Nunca
    lanza por errores de red: si no alcanza ninguna ruta, devuelve un perfil con
    escala ``'indeterminada'``.
    """
    base = _dominio_a_base(dominio)
    if not base:
        return PerfilFundacional(empresa=empresa)
    propio = client or httpx.Client(
        timeout=settings.request_timeout_s,
        headers={"User-Agent": settings.user_agent},
        follow_redirects=True,
    )
    textos: list[str] = []
    url_ok: Optional[str] = None
    try:
        for ruta in RUTAS_PERFIL:
            url = base + ruta
            try:
                resp = propio.get(url)
            except Exception:
                continue
            if resp.status_code != 200 or not resp.text:
                continue
            textos.append(texto_plano(resp.text))
            if url_ok is None:
                url_ok = url
    finally:
        if client is None:
            propio.close()
    if not textos:
        return PerfilFundacional(empresa=empresa, url_perfil=base)
    combinado = " ".join(textos)
    return PerfilFundacional(
        empresa=empresa,
        escala=escala_desde_texto(combinado),
        anio_fundacion=anio_fundacion_desde_texto(combinado),
        discurso_corporativo=_descripcion(combinado) or None,
        url_perfil=url_ok or base,
    )
