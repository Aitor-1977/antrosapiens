"""Semilla del directorio de prospectos (organizaciones reales de LATAM).

Propósito operativo: que Motor A entregue organizaciones REALES desde el primer
arranque, sin depender de una corrida de ingesta ni de configurar credenciales.
El directorio curado se ASEGURA (idempotente) en cada arranque.

Frontera Motor A (ver CLAUDE.md): esto es INTAKE ESTRUCTURAL del directorio, del
mismo tipo que ``POST /prospectos`` o ``POST /directorio`` (Wikidata). Cada
entrada es una entidad pública y verificable con su ``categoria`` DECLARADA
(estructural, uno de los cuatro ecosistemas) — NO inferida del discurso. NO se
puntúa, NO se clasifica culturalmente, NO se interpreta.

``escala`` queda SIEMPRE ``'indeterminada'``: la semilla no rastrea el sitio, así
que no hay un dato numérico de tamaño que declarar (patrón ``no_fechado``). La
enriquece después ``perfil_fundacional`` desde la fuente orgánica. ``vertical`` y
``sitio_web`` son datos estructurales públicos de la entidad.

Idempotencia (clave para producción): se usa
``INSERT ... ON CONFLICT (hash_dedup) DO NOTHING`` (portable SQLite/Postgres), y
el directorio se asegura SIEMPRE, no sólo cuando la tabla está vacía. Esto evita
el fallo observado en producción: una base persistente (Neon) con filas previas
hacía que un guardado «sólo si vacía» se saltara por completo y la Indagación
quedara sin organizaciones. Las filas que el operador haya dado de alta NO se
tocan (ON CONFLICT no sobrescribe); sólo se garantiza que las curadas existan.
"""
from __future__ import annotations

import logging

from .db.database import Database
from .db.models import ahora_iso, calcular_hash_prospecto

log = logging.getLogger("hd_scraper.seed")

# Directorio curado: (nombre, categoria, vertical, sitio_web, escala).
# Entidades públicas y verificables del ecosistema de innovación de LATAM.
# categoria ∈ {VC, Startup, Incubadora, Corporativo} (declarada, estructural).
# escala ∈ BANDAS: banda de tamaño PÚBLICA y verificable de la organización
# (autorizado por el operador el 2026-08-01 para habilitar el filtro por tamaño).
# Es un hecho estructural declarado (rango de plantilla público), NO un juicio;
# `perfil_fundacional` puede refinarla luego desde la fuente orgánica.
DIRECTORIO_SEMILLA: tuple[tuple[str, str, str, str, str], ...] = (
    # ── VC · fondos de inversión (equipos pequeños) ───────────────────────
    ("Kaszek", "VC", "Venture Capital", "https://www.kaszek.com", "11-50"),
    ("monashees", "VC", "Venture Capital", "https://www.monashees.com.br", "11-50"),
    ("NXTP Ventures", "VC", "Venture Capital", "https://nxtp.vc", "11-50"),
    ("ALLVP", "VC", "Venture Capital", "https://allvp.vc", "11-50"),
    ("Dalus Capital", "VC", "Venture Capital", "https://www.daluscapital.com", "11-50"),
    ("Cometa", "VC", "Venture Capital", "https://www.cometa.vc", "1-10"),
    ("Angel Ventures", "VC", "Venture Capital", "https://angelventures.vc", "11-50"),
    ("Mountain Nazca", "VC", "Venture Capital", "https://www.mountainnazca.com", "11-50"),
    ("Magma Partners", "VC", "Venture Capital", "https://www.magmapartners.com", "11-50"),
    ("Amplifica Capital", "VC", "Venture Capital", "https://www.amplifica.capital", "1-10"),

    # ── Startup ───────────────────────────────────────────────────────────
    ("Nubank", "Startup", "Fintech", "https://nubank.com.br", "501+"),
    ("Rappi", "Startup", "Q-commerce / Delivery", "https://www.rappi.com", "501+"),
    ("Kavak", "Startup", "Autos usados / Marketplace", "https://www.kavak.com", "501+"),
    ("Bitso", "Startup", "Cripto / Fintech", "https://bitso.com", "501+"),
    ("Clip", "Startup", "Pagos", "https://www.clip.mx", "501+"),
    ("Konfío", "Startup", "Fintech PyME", "https://www.konfio.mx", "501+"),
    ("Clara", "Startup", "Gastos corporativos / Fintech", "https://www.clara.com", "201-500"),
    ("Nowports", "Startup", "Logística / Freight", "https://www.nowports.com", "201-500"),
    ("Ualá", "Startup", "Fintech", "https://www.uala.com.ar", "501+"),
    ("Jüsto", "Startup", "Supermercado online", "https://www.justo.mx", "501+"),
    # Startups tempranas / en crecimiento (bandas públicas aproximadas; el
    # perfil fundacional las refina). Cubren tamaños pequeños/medianos: el ICP
    # real de HD, donde la Deuda Cultural muerde antes del product-market fit.
    ("Palenca", "Startup", "Infraestructura de datos laborales", "https://palenca.com", "1-10"),
    ("Trii", "Startup", "Inversión minorista", "https://www.trii.co", "1-10"),
    ("Toku", "Startup", "Pagos y cobranza", "https://www.trytoku.com", "1-10"),
    ("Cobre", "Startup", "Pagos B2B", "https://cobre.co", "11-50"),
    ("Mundi", "Startup", "Comercio / Trade finance", "https://www.mundi.io", "11-50"),
    ("Kamino", "Startup", "Finanzas para PyME", "https://www.kamino.com.br", "11-50"),
    ("Trace Finance", "Startup", "Fintech transfronteriza", "https://www.tracefinance.io", "11-50"),
    ("Divibank", "Startup", "Financiamiento a creadores", "https://www.divibank.co", "11-50"),
    ("Pomelo", "Startup", "Infraestructura fintech", "https://www.pomelo.la", "51-200"),
    ("Simetrik", "Startup", "Conciliación financiera", "https://www.simetrik.com", "51-200"),
    ("Fintual", "Startup", "Inversión", "https://fintual.com", "51-200"),
    ("Zubale", "Startup", "Retail / Gig economy", "https://www.zubale.com", "51-200"),

    # ── Incubadora · aceleradoras / builders / soporte de ecosistema ──────
    ("Start-Up Chile", "Incubadora", "Aceleradora pública", "https://www.startupchile.org", "11-50"),
    ("Wayra", "Incubadora", "Aceleradora corporativa", "https://www.wayra.com", "51-200"),
    ("Endeavor", "Incubadora", "Soporte de ecosistema", "https://endeavor.org", "201-500"),
    ("INCmty", "Incubadora", "Ecosistema de emprendimiento", "https://incmty.com", "11-50"),
    ("MassChallenge México", "Incubadora", "Aceleradora", "https://masschallenge.org", "51-200"),
    ("Founder Institute", "Incubadora", "Programa de fundadores", "https://fi.co", "11-50"),
    ("Socialab", "Incubadora", "Innovación de impacto", "https://socialab.com", "11-50"),
    ("Platanus Ventures", "Incubadora", "Aceleradora", "https://platan.us", "1-10"),
    ("500 Global LATAM", "Incubadora", "Aceleradora / VC", "https://500.co", "51-200"),
    ("Y Combinator", "Incubadora", "Aceleradora", "https://www.ycombinator.com", "51-200"),

    # ── Corporativo (gran escala) ─────────────────────────────────────────
    ("Mercado Libre", "Corporativo", "E-commerce / Fintech", "https://www.mercadolibre.com", "501+"),
    ("Globant", "Corporativo", "Servicios de tecnología", "https://www.globant.com", "501+"),
    ("Grupo Bimbo", "Corporativo", "Alimentos", "https://www.grupobimbo.com", "501+"),
    ("FEMSA", "Corporativo", "Bebidas / Retail", "https://www.femsa.com", "501+"),
    ("Falabella", "Corporativo", "Retail", "https://www.falabella.com", "501+"),
    ("CEMEX", "Corporativo", "Materiales de construcción", "https://www.cemex.com", "501+"),
    ("BBVA México", "Corporativo", "Banca", "https://www.bbva.mx", "501+"),
    ("Banco Santander México", "Corporativo", "Banca", "https://www.santander.com.mx", "501+"),
    ("Arca Continental", "Corporativo", "Bebidas", "https://www.arcacontal.com", "501+"),
    ("Grupo Salinas", "Corporativo", "Conglomerado", "https://www.gruposalinas.com", "501+"),
)


def _rollback(db: Database) -> None:
    """Deshace una transacción fallida (evita el cascadeo 'transaction aborted'
    de Postgres, que dejaría 0 filas sembradas si un INSERT falla)."""
    try:
        db.conn.rollback()
    except Exception:  # pragma: no cover
        pass


def asegurar_directorio_semilla(db: Database) -> int:
    """Garantiza que el directorio curado exista en ``prospectos``. Idempotente.

    Se ejecuta SIEMPRE (no sólo con la tabla vacía): usa ON CONFLICT sobre
    ``hash_dedup`` para no duplicar ni sobrescribir. Devuelve cuántas sentencias
    de alta se ejecutaron sin error. Nunca lanza: un fallo de siembra no debe
    tumbar el arranque de la API.
    """
    ahora = ahora_iso()
    ok = 0
    for nombre, categoria, vertical, sitio, escala in DIRECTORIO_SEMILLA:
        try:
            # Si la fila ya existe (base persistente ya sembrada), rellena la
            # banda de tamaño SÓLO si seguía 'indeterminada'; nunca pisa una
            # escala ya declarada (p. ej. la que refine `perfil_fundacional`).
            db.execute(
                """INSERT INTO prospectos
                     (nombre, categoria, vertical, sitio_web, escala,
                      hash_dedup, creado_en, actualizado_en)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (hash_dedup) DO UPDATE SET
                     escala         = excluded.escala,
                     actualizado_en = excluded.actualizado_en
                   WHERE prospectos.escala = 'indeterminada'""",
                (nombre, categoria, vertical, sitio, escala,
                 calcular_hash_prospecto(nombre, categoria), ahora, ahora),
            )
            ok += 1
        except Exception:  # pragma: no cover
            _rollback(db)
            log.warning("no se pudo asegurar el prospecto semilla %r", nombre, exc_info=True)
    log.info("directorio semilla asegurado (%d/%d sentencias ok)", ok, len(DIRECTORIO_SEMILLA))
    return ok


# Alias de compatibilidad: antes la siembra era «sólo si vacía». Se mantiene el
# nombre para no romper llamadas externas, pero ahora ASEGURA el directorio.
def sembrar_prospectos_si_vacio(db: Database) -> int:
    return asegurar_directorio_semilla(db)
