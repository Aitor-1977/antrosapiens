"""Directorio semilla: asegura orgs reales de forma idempotente y acotada,
incluso sobre una base que ya tenía filas (el caso que falló en producción)."""
from hd_scraper.db.models import CATEGORIAS, ahora_iso, calcular_hash_prospecto
from hd_scraper.seed_prospectos import (
    DIRECTORIO_SEMILLA,
    asegurar_directorio_semilla,
    sembrar_prospectos_si_vacio,
)


def test_asegura_directorio_real(db):
    ok = asegurar_directorio_semilla(db)
    assert ok == len(DIRECTORIO_SEMILLA)
    total = db.fetch_one("SELECT COUNT(*) AS n FROM prospectos")["n"]
    assert total == len(DIRECTORIO_SEMILLA)


def test_categorias_validas_y_escala_en_bandas(db):
    from hd_scraper.perfil_fundacional import BANDAS

    asegurar_directorio_semilla(db)
    filas = db.fetch_all("SELECT categoria, escala, sitio_web FROM prospectos")
    for f in filas:
        assert f["categoria"] in CATEGORIAS
        # el directorio trae banda de tamaño pública y verificable (no 'indeterminada').
        assert f["escala"] in BANDAS
        assert f["sitio_web"].startswith("http")


def test_filtro_por_escala(db):
    asegurar_directorio_semilla(db)
    # los fondos VC son equipos pequeños; los corporativos son 501+.
    corp_grandes = db.fetch_one(
        "SELECT COUNT(*) AS n FROM prospectos WHERE categoria='Corporativo' AND escala='501+'")["n"]
    # 10 corporativos históricos + 7 reclasificados desde Startup por estatus
    # de unicornio/consolidación (decisión del operador, 2026-08-22).
    assert corp_grandes == 17
    vc_grandes = db.fetch_one(
        "SELECT COUNT(*) AS n FROM prospectos WHERE categoria='VC' AND escala='501+'")["n"]
    assert vc_grandes == 0


def test_rellena_escala_de_filas_ya_sembradas_como_indeterminada(db):
    """Regresión del caso de producción: filas ya sembradas con
    'indeterminada' deben recibir su banda real al re-asegurar."""
    ahora = ahora_iso()
    # simula el estado previo (sembrado sin banda) de una org curada.
    db.execute(
        """INSERT INTO prospectos (nombre, categoria, escala, hash_dedup, creado_en, actualizado_en)
           VALUES ('Kaszek', 'VC', 'indeterminada', ?, ?, ?)""",
        (calcular_hash_prospecto("Kaszek", "VC"), ahora, ahora),
    )
    asegurar_directorio_semilla(db)
    escala = db.fetch_one("SELECT escala FROM prospectos WHERE nombre='Kaszek'")["escala"]
    assert escala == "11-50"  # se rellenó con la banda real


def test_es_idempotente(db):
    asegurar_directorio_semilla(db)
    # una segunda pasada no duplica (ON CONFLICT por hash_dedup).
    asegurar_directorio_semilla(db)
    total = db.fetch_one("SELECT COUNT(*) AS n FROM prospectos")["n"]
    assert total == len(DIRECTORIO_SEMILLA)


def test_asegura_aunque_la_tabla_ya_tenga_filas(db):
    """Regresión del fallo de producción: una base NO vacía (Neon con filas
    previas) debe recibir igualmente el directorio curado."""
    ahora = ahora_iso()
    db.execute(
        """INSERT INTO prospectos (nombre, categoria, escala, hash_dedup, creado_en, actualizado_en)
           VALUES (?, 'Startup', 'indeterminada', ?, ?, ?)""",
        ("Preexistente", calcular_hash_prospecto("Preexistente", "Startup"), ahora, ahora),
    )
    asegurar_directorio_semilla(db)
    total = db.fetch_one("SELECT COUNT(*) AS n FROM prospectos")["n"]
    # la fila previa + todas las curadas.
    assert total == len(DIRECTORIO_SEMILLA) + 1
    # y hay VC disponible para la Indagación por ecosistema.
    vc = db.fetch_one("SELECT COUNT(*) AS n FROM prospectos WHERE categoria = 'VC'")["n"]
    assert vc == 10


def test_cuatro_ecosistemas_representados(db):
    asegurar_directorio_semilla(db)
    presentes = {f["categoria"] for f in db.fetch_all("SELECT DISTINCT categoria FROM prospectos")}
    assert presentes == set(CATEGORIAS)


def test_alias_de_compatibilidad(db):
    assert sembrar_prospectos_si_vacio(db) == len(DIRECTORIO_SEMILLA)
