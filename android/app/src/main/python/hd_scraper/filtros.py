"""Filtros avanzados del radar (Región, Enfoque, Tamaño, Palabra clave).

Convierten los selectores de la UI en parámetros de consulta deterministas que
los motores de búsqueda e ingesta aplican automáticamente (scheduler, run_once,
ingesta CLI y conectores). Es configuración ESTRUCTURAL — lo que el operador
declara al lanzar la corrida —, no interpretación de contenido:

  - ``region``      → parámetros ``gl``/``hl``/``ceid`` en Google News RSS y
                      ``sourcecountry`` en GDELT.
  - ``categorias``  → filtra el directorio de objetivos por ecosistema
                      (VC | Startup | Incubadora | Corporativo).
  - ``escalas``     → filtra el directorio de objetivos por banda de tamaño.
  - ``palabra_clave`` → términos extra que se agregan a la consulta.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .db.models import CATEGORIAS
from .perfil_fundacional import BANDAS

REGION_DEFAULT = "Toda LATAM"

# Región → parámetros de búsqueda estructurales por fuente.
# ``country`` es el ISO 3166-1 alfa-2 que GDELT entiende en ``sourcecountry``.
# "Toda LATAM" no restringe país: solo la lengua/región de Google News.
REGIONES: dict[str, dict[str, str]] = {
    "Toda LATAM": {"gl": "MX", "hl": "es-419", "ceid": "MX:es-419", "country": ""},
    "México":     {"gl": "MX", "hl": "es",     "ceid": "MX:es",     "country": "MX"},
    "Brasil":     {"gl": "BR", "hl": "pt-BR",  "ceid": "BR:pt-BR",  "country": "BR"},
    "Argentina":  {"gl": "AR", "hl": "es",     "ceid": "AR:es",     "country": "AR"},
    "Colombia":   {"gl": "CO", "hl": "es",     "ceid": "CO:es",     "country": "CO"},
    "Chile":      {"gl": "CL", "hl": "es",     "ceid": "CL:es",     "country": "CL"},
    "Perú":       {"gl": "PE", "hl": "es",     "ceid": "PE:es",     "country": "PE"},
    "Uruguay":    {"gl": "UY", "hl": "es",     "ceid": "UY:es",     "country": "UY"},
    "Ecuador":    {"gl": "EC", "hl": "es",     "ceid": "EC:es",     "country": "EC"},
    "Panamá":     {"gl": "PA", "hl": "es",     "ceid": "PA:es",     "country": "PA"},
    "Costa Rica": {"gl": "CR", "hl": "es",     "ceid": "CR:es",     "country": "CR"},
    "Guatemala":  {"gl": "GT", "hl": "es",     "ceid": "GT:es",     "country": "GT"},
}

ESCALAS: tuple[str, ...] = tuple(BANDAS)          # bandas de tamaño (1-10…501+)
CATEGORIAS_FILTRO: tuple[str, ...] = tuple(sorted(CATEGORIAS))

# Variables de entorno con las que configurar los filtros sin tocar la UI.
VAR_REGION = "HD_RADAR_REGION"
VAR_CATEGORIAS = "HD_RADAR_CATEGORIAS"
VAR_ESCALAS = "HD_RADAR_ESCALAS"
VAR_PALABRA_CLAVE = "HD_RADAR_PALABRA_CLAVE"


@dataclass(frozen=True)
class FiltrosRadar:
    """Filtros declarados por el operador (estructurales, deterministas)."""
    region: str = REGION_DEFAULT
    categorias: tuple[str, ...] = ()
    escalas: tuple[str, ...] = ()
    palabra_clave: str = ""

    @property
    def activo(self) -> bool:
        return (
            self.region != REGION_DEFAULT
            or bool(self.categorias)
            or bool(self.escalas)
            or bool(self.palabra_clave)
        )

    @property
    def terminos_extra(self) -> str | None:
        kw = self.palabra_clave.strip()
        return kw or None


def _parse_csv(nombre: str, validos: set[str]) -> tuple[str, ...]:
    """Parsea una variable CSV y descarta valores fuera del vocabulario."""
    valores = tuple(v.strip() for v in os.getenv(nombre, "").split(",") if v.strip())
    return tuple(v for v in valores if v in validos)


def filtros_desde_env() -> FiltrosRadar:
    """Filtros desde variables de entorno (HD_RADAR_*). Nunca lanza."""
    region = os.getenv(VAR_REGION, REGION_DEFAULT)
    if region not in REGIONES:
        region = REGION_DEFAULT
    return FiltrosRadar(
        region=region,
        categorias=_parse_csv(VAR_CATEGORIAS, set(CATEGORIAS)),
        escalas=_parse_csv(VAR_ESCALAS, set(ESCALAS)),
        palabra_clave=os.getenv(VAR_PALABRA_CLAVE, "").strip(),
    )


def _coincide_filtros(nombre: str, filtros: FiltrosRadar) -> bool:
    """¿El objetivo de la semilla cumple categorías/escalas?.

    Los nombres que no están en la semilla (p. ej. altas del operador) NO se
    filtran: solo se filtra lo que tiene metadatos declarados.
    """
    from .seed_prospectos import DIRECTORIO_SEMILLA

    for sem_nombre, cat, _vert, _sitio, escala in DIRECTORIO_SEMILLA:
        if sem_nombre == nombre:
            if filtros.categorias and cat not in filtros.categorias:
                return False
            if filtros.escalas and escala not in filtros.escalas:
                return False
            return True
    return True


def objetivos_por_filtros(filtros: FiltrosRadar | None = None) -> tuple[str, ...]:
    """Objetivos a barrer bajo los filtros.

    Si el operador lista ``HD_TRACKED_EMPRESAS`` explícitas, esa lista gana y no
    se filtra (la explícita manda). En modo autónomo (sin tracked), se parte del
    directorio semilla y se filtran categorías/escalas.
    """
    from .objetivos import objetivos_por_defecto

    filtros = filtros or FiltrosRadar()
    base = objetivos_por_defecto()
    if os.getenv("HD_TRACKED_EMPRESAS"):
        return base
    if not filtros.categorias and not filtros.escalas:
        return base
    return tuple(n for n in base if _coincide_filtros(n, filtros))


def descripcion(filtros: FiltrosRadar) -> str:
    """Línea legible con los filtros aplicados (para logs/reportes)."""
    partes = [f"región={filtros.region}"]
    if filtros.categorias:
        partes.append("enfoque=" + ",".join(filtros.categorias))
    if filtros.escalas:
        partes.append("tamaño=" + ",".join(filtros.escalas))
    if filtros.palabra_clave:
        partes.append(f"keyword={filtros.palabra_clave}")
    return " ".join(partes)
