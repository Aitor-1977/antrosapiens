"""Corridas programadas con APScheduler (cada 12 horas por defecto).

En cada corrida:
  1. purga el crudo vencido (retención 90 días),
  2. encola una consulta por (empresa seguida x tipo_evento) para los
     conectores activos,
  3. procesa la cola de jobs (ingesta: escribe en `evidencias`),
  4. clasifica epistemológicamente la evidencia nueva (Entrega 2,
     `clasificacion_store.clasificar_lote`, determinista, sin IA), para que
     `/expedientes` no dependa de que alguien corra
     `scripts.clasificar_evidencia --aplicar` a mano. Cierra el cuello de
     botella identificado en la revisión de cierre de 2026-09-11: sin este
     paso, la clasificación nunca llegaba sola a la evidencia recién
     capturada.

Fase 1: solo el conector google_news está activo. Los tipos de evento a barrer
son configurables; por defecto se barren todos los literales del contrato.

NO conecta `promocion_store.promover_lote` — la promoción a 'candidato' sigue
siendo un paso separado, deliberadamente fuera de esta corrida (ver revisión
de cierre 2026-09-11).
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .clasificacion_store import clasificar_lote
from .config import settings
from .connectors import REGISTRY
from .db.database import Database
from .db.models import TIPOS_EVENTO, QuerySpec
from .filtros import descripcion, filtros_desde_env, objetivos_por_filtros
from .jobs import encolar, procesar_pendientes
from .storage.raw_store import purgar_expirados

log = logging.getLogger("hd_scraper.scheduler")


def corrida(db: Database, tipos_evento: tuple[str, ...] | None = None) -> None:
    """Una corrida completa: purga + encolado + procesamiento."""
    purgados = purgar_expirados(db)
    if purgados:
        log.info("crudos purgados por retención: %d", purgados)

    tipos = tipos_evento or tuple(sorted(TIPOS_EVENTO))
    filtros = filtros_desde_env()
    if filtros.activo:
        log.info("filtros del radar: %s", descripcion(filtros))
    encolados = 0
    for connector, cls in REGISTRY.items():
        if cls.requires_slug:
            # Job boards: se consultan por slug y su tipo_evento es estructural
            # (contratacion). Solo se encolan empresas con slug configurado.
            for empresa, slug in settings.tracked_slugs.items():
                encolar(db, connector,
                        QuerySpec(empresa=empresa, tipo_evento="contratacion", slug=slug))
                encolados += 1
        else:
            # Autonomía: si no hay empresas seguidas configuradas, se barren los
            # objetivos por defecto (HD_TRACKED_EMPRESAS o el directorio semilla),
            # filtrados por enfoque/tamaño cuando el operador lo declaró.
            empresas = settings.tracked_empresas or objetivos_por_filtros(filtros)
            for empresa in empresas:
                for tipo in tipos:
                    encolar(db, connector, QuerySpec(
                        empresa=empresa,
                        tipo_evento=tipo,
                        region=filtros.region,
                        terminos=filtros.terminos_extra,
                    ))
                    encolados += 1
    log.info("jobs encolados: %d", encolados)

    procesados = procesar_pendientes(db)
    log.info("jobs procesados: %d", procesados)

    # Clasificación automática de la evidencia nueva. clasificar_lote solo
    # LEE `evidencias` y escribe en `evidencia_clasificada`/
    # `expedientes_candidatos`: un fallo aquí nunca toca ni borra la
    # evidencia cruda ya escrita por procesar_pendientes. Se captura para que
    # un error de clasificación no tumbe el resto de la corrida programada
    # (purga/encolado/ingesta ya están hechos y no deben perderse).
    try:
        reporte = clasificar_lote(db, aplicar=True)
        log.info(
            "evidencia clasificada: %d escritas, %d expedientes creados, %d saltadas",
            reporte["escritas"], reporte["expedientes_creados"], reporte["saltadas"],
        )
    except Exception:
        log.exception(
            "clasificar_lote falló durante la corrida programada; la "
            "evidencia cruda no se ve afectada (clasificar_lote no escribe "
            "en evidencias). Se reintentará en la próxima corrida."
        )


def build_scheduler(db: Database) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        lambda: corrida(db),
        trigger="interval",
        hours=settings.schedule_hours,
        id="corrida_periodica",
        max_instances=1,
        coalesce=True,
    )
    return scheduler
