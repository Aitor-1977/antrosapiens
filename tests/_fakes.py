"""Conectores falsos para los tests del orquestador y el concentrador.

No se recogen como tests (sin prefijo ``test_``). Cada fake produce evidencia
válida para el contrato sin tocar la red: ``search`` devuelve ítems fijos y
``normalize`` mapea al ``EvidenceRecord`` con un ``hash_dedup`` coherente.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable

from hd_scraper.connectors import REGISTRY
from hd_scraper.connectors.base import Connector
from hd_scraper.db.models import (
    EvidenceRecord,
    QuerySpec,
    RawItem,
    ahora_iso,
    calcular_hash_dedup,
)


class _FakeConnector(Connector):
    """Base de fake: subclases fijan ``name`` e ``ITEMS`` = [(titulo, url, fecha)]."""

    origen_declaracion_default = "prensa"
    ITEMS: tuple[tuple[str, str, str | None], ...] = ()

    def search(self, query: QuerySpec) -> Iterable[RawItem]:
        for titulo, url, fecha in self.ITEMS:
            yield RawItem(
                url=url,
                contenido=titulo,
                formato="html",
                meta={"titulo": titulo, "fecha_publicacion": fecha},
            )

    def fetch(self, url: str) -> RawItem:  # pragma: no cover - no se usa en los tests
        raise NotImplementedError

    def normalize(self, raw: RawItem) -> EvidenceRecord:
        empresa = "Nubank"
        return EvidenceRecord(
            cita_textual=raw.meta["titulo"],
            fecha_extraccion=ahora_iso(),
            url_fuente=raw.url,
            nombre_medio=self.name,
            empresa_mencionada=empresa,
            tipo_evento="ronda",
            origen_declaracion="prensa",
            hash_dedup=calcular_hash_dedup(empresa, raw.url),
            fecha_publicacion=raw.meta.get("fecha_publicacion"),
            connector=self.name,
        )


class FakeAConnector(_FakeConnector):
    name = "fake_a"
    ITEMS = (
        ("Nubank cierra una ronda Serie F", "https://ejemplo.test/a/nubank-ronda",
         "2026-08-01T00:00:00+00:00"),
    )


class FakeBConnector(_FakeConnector):
    name = "fake_b"
    ITEMS = (
        ("Nubank anuncia expansion regional", "https://ejemplo.test/b/nubank-expansion",
         "2026-08-11T00:00:00+00:00"),
    )


class FakeSlugConnector(_FakeConnector):
    name = "fake_slug"
    requires_slug = True
    ITEMS = (
        ("Nubank publica vacante de ingenieria", "https://ejemplo.test/slug/nubank-jobs",
         "2026-08-05T00:00:00+00:00"),
    )


@contextmanager
def fakes_registrados(*clases: type[Connector]):
    """Registra conectores fake en ``REGISTRY`` mientras dure el bloque.

    Muta el dict compartido (``orquestador`` lo importa por referencia), y lo
    deja como estaba al salir.
    """
    previos = dict(REGISTRY)
    for cls in clases:
        REGISTRY[cls.name] = cls
    try:
        yield
    finally:
        REGISTRY.clear()
        REGISTRY.update(previos)
