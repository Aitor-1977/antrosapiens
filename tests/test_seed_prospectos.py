"""Semilla del directorio de prospectos: siembra real, idempotente y acotada."""
from hd_scraper.db.models import CATEGORIAS
from hd_scraper.seed_prospectos import (
    DIRECTORIO_SEMILLA,
    sembrar_prospectos_si_vacio,
)


def test_siembra_puebla_directorio_real(db):
    insertadas = sembrar_prospectos_si_vacio(db)
    assert insertadas == len(DIRECTORIO_SEMILLA)
    total = db.fetch_one("SELECT COUNT(*) AS n FROM prospectos")["n"]
    assert total == len(DIRECTORIO_SEMILLA)


def test_categorias_validas_y_escala_indeterminada(db):
    sembrar_prospectos_si_vacio(db)
    filas = db.fetch_all("SELECT categoria, escala, sitio_web FROM prospectos")
    for f in filas:
        # categoria declarada, dentro del CHECK de la tabla.
        assert f["categoria"] in CATEGORIAS
        # la semilla no rastrea el sitio: escala queda indeterminada (no_fechado).
        assert f["escala"] == "indeterminada"
        # dato estructural público presente.
        assert f["sitio_web"].startswith("http")


def test_siembra_es_idempotente(db):
    assert sembrar_prospectos_si_vacio(db) == len(DIRECTORIO_SEMILLA)
    # una segunda pasada no inserta ni duplica.
    assert sembrar_prospectos_si_vacio(db) == 0
    total = db.fetch_one("SELECT COUNT(*) AS n FROM prospectos")["n"]
    assert total == len(DIRECTORIO_SEMILLA)


def test_no_siembra_si_ya_hay_prospectos(db):
    from hd_scraper.db.models import ahora_iso, calcular_hash_prospecto

    ahora = ahora_iso()
    db.execute(
        """INSERT INTO prospectos (nombre, categoria, escala, hash_dedup, creado_en, actualizado_en)
           VALUES (?, 'Startup', 'indeterminada', ?, ?, ?)""",
        ("Preexistente", calcular_hash_prospecto("Preexistente", "Startup"), ahora, ahora),
    )
    # con la tabla ya poblada, la semilla no toca nada.
    assert sembrar_prospectos_si_vacio(db) == 0
    total = db.fetch_one("SELECT COUNT(*) AS n FROM prospectos")["n"]
    assert total == 1


def test_cuatro_ecosistemas_representados(db):
    sembrar_prospectos_si_vacio(db)
    filas = db.fetch_all("SELECT DISTINCT categoria FROM prospectos")
    presentes = {f["categoria"] for f in filas}
    assert presentes == set(CATEGORIAS)
