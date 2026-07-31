"""Semilla del directorio de prospectos (organizaciones reales de LATAM).

Propósito operativo: que Motor A entregue organizaciones REALES desde el primer
arranque, sin depender de una corrida de ingesta ni de configurar credenciales.
Cuando la tabla ``prospectos`` está vacía, se siembra este directorio curado.

Frontera Motor A (ver CLAUDE.md): esto es INTAKE ESTRUCTURAL del directorio, del
mismo tipo que ``POST /prospectos`` o ``POST /directorio`` (Wikidata). Cada
entrada es una entidad pública y verificable con su ``categoria`` DECLARADA
(estructural, uno de los cuatro ecosistemas) — NO inferida del discurso. NO se
puntúa, NO se clasifica culturalmente, NO se interpreta.

``escala`` queda SIEMPRE ``'indeterminada'``: la semilla no rastrea el sitio, así
que no hay un dato numérico de tamaño que declarar (patrón ``no_fechado``). La
enriquece después ``perfil_fundacional`` desde la fuente orgánica. ``vertical`` y
``sitio_web`` son datos estructurales públicos de la entidad.

La siembra es IDEMPOTENTE: sólo inserta si la tabla está vacía y usa
``ON CONFLICT (hash_dedup) DO NOTHING`` (portable SQLite/Postgres).
"""
from __future__ import annotations

import logging

from .db.database import Database
from .db.models import ahora_iso, calcular_hash_prospecto

log = logging.getLogger("hd_scraper.seed")

# Directorio curado: (nombre, categoria, vertical, sitio_web).
# Entidades públicas y verificables del ecosistema de innovación de LATAM.
# categoria ∈ {VC, Startup, Incubadora, Corporativo} (declarada, estructural).
DIRECTORIO_SEMILLA: tuple[tuple[str, str, str, str], ...] = (
    # ── VC · fondos de inversión ──────────────────────────────────────────
    ("Kaszek", "VC", "Venture Capital", "https://www.kaszek.com"),
    ("monashees", "VC", "Venture Capital", "https://www.monashees.com.br"),
    ("NXTP Ventures", "VC", "Venture Capital", "https://nxtp.vc"),
    ("ALLVP", "VC", "Venture Capital", "https://allvp.vc"),
    ("Dalus Capital", "VC", "Venture Capital", "https://www.daluscapital.com"),
    ("Cometa", "VC", "Venture Capital", "https://www.cometa.vc"),
    ("Angel Ventures", "VC", "Venture Capital", "https://angelventures.vc"),
    ("Mountain Nazca", "VC", "Venture Capital", "https://www.mountainnazca.com"),
    ("Magma Partners", "VC", "Venture Capital", "https://www.magmapartners.com"),
    ("Amplifica Capital", "VC", "Venture Capital", "https://www.amplifica.capital"),

    # ── Startup ───────────────────────────────────────────────────────────
    ("Nubank", "Startup", "Fintech", "https://nubank.com.br"),
    ("Rappi", "Startup", "Q-commerce / Delivery", "https://www.rappi.com"),
    ("Kavak", "Startup", "Autos usados / Marketplace", "https://www.kavak.com"),
    ("Bitso", "Startup", "Cripto / Fintech", "https://bitso.com"),
    ("Clip", "Startup", "Pagos", "https://www.clip.mx"),
    ("Konfío", "Startup", "Fintech PyME", "https://www.konfio.mx"),
    ("Clara", "Startup", "Gastos corporativos / Fintech", "https://www.clara.com"),
    ("Nowports", "Startup", "Logística / Freight", "https://www.nowports.com"),
    ("Ualá", "Startup", "Fintech", "https://www.uala.com.ar"),
    ("Jüsto", "Startup", "Supermercado online", "https://www.justo.mx"),

    # ── Incubadora · aceleradoras / builders / soporte de ecosistema ──────
    ("Start-Up Chile", "Incubadora", "Aceleradora pública", "https://www.startupchile.org"),
    ("Wayra", "Incubadora", "Aceleradora corporativa", "https://www.wayra.com"),
    ("Endeavor", "Incubadora", "Soporte de ecosistema", "https://endeavor.org"),
    ("INCmty", "Incubadora", "Ecosistema de emprendimiento", "https://incmty.com"),
    ("MassChallenge México", "Incubadora", "Aceleradora", "https://masschallenge.org"),
    ("Founder Institute", "Incubadora", "Programa de fundadores", "https://fi.co"),
    ("Socialab", "Incubadora", "Innovación de impacto", "https://socialab.com"),
    ("Platanus Ventures", "Incubadora", "Aceleradora", "https://platan.us"),
    ("500 Global LATAM", "Incubadora", "Aceleradora / VC", "https://500.co"),
    ("Y Combinator", "Incubadora", "Aceleradora", "https://www.ycombinator.com"),

    # ── Corporativo ───────────────────────────────────────────────────────
    ("Mercado Libre", "Corporativo", "E-commerce / Fintech", "https://www.mercadolibre.com"),
    ("Globant", "Corporativo", "Servicios de tecnología", "https://www.globant.com"),
    ("Grupo Bimbo", "Corporativo", "Alimentos", "https://www.grupobimbo.com"),
    ("FEMSA", "Corporativo", "Bebidas / Retail", "https://www.femsa.com"),
    ("Falabella", "Corporativo", "Retail", "https://www.falabella.com"),
    ("CEMEX", "Corporativo", "Materiales de construcción", "https://www.cemex.com"),
    ("BBVA México", "Corporativo", "Banca", "https://www.bbva.mx"),
    ("Banco Santander México", "Corporativo", "Banca", "https://www.santander.com.mx"),
    ("Arca Continental", "Corporativo", "Bebidas", "https://www.arcacontal.com"),
    ("Grupo Salinas", "Corporativo", "Conglomerado", "https://www.gruposalinas.com"),
)


def sembrar_prospectos_si_vacio(db: Database) -> int:
    """Siembra el directorio curado si ``prospectos`` está vacía. Idempotente.

    Devuelve el número de filas insertadas (0 si ya había prospectos o si otra
    invocación ganó la carrera). Nunca lanza: un fallo de siembra no debe tumbar
    el arranque de la API.
    """
    try:
        n = db.fetch_one("SELECT COUNT(*) AS n FROM prospectos")["n"]
    except Exception:  # pragma: no cover - tabla aún inexistente
        return 0
    if n and n > 0:
        return 0

    ahora = ahora_iso()
    insertadas = 0
    for nombre, categoria, vertical, sitio in DIRECTORIO_SEMILLA:
        try:
            db.execute(
                """INSERT INTO prospectos
                     (nombre, categoria, vertical, sitio_web, escala,
                      hash_dedup, creado_en, actualizado_en)
                   VALUES (?, ?, ?, ?, 'indeterminada', ?, ?, ?)
                   ON CONFLICT (hash_dedup) DO NOTHING""",
                (nombre, categoria, vertical, sitio,
                 calcular_hash_prospecto(nombre, categoria), ahora, ahora),
            )
            insertadas += 1
        except Exception:  # pragma: no cover
            log.warning("no se pudo sembrar el prospecto %r", nombre, exc_info=True)
    if insertadas:
        log.info("directorio semilla: %d prospectos insertados", insertadas)
    return insertadas
