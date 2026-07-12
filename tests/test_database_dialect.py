"""Pruebas del wrapper multi-motor (sin conectar a Postgres real)."""
from hd_scraper.db.database import Database, _es_postgres


def test_deteccion_de_motor():
    assert _es_postgres("postgres://u:p@h/db")
    assert _es_postgres("postgresql://u:p@h/db?sslmode=require")
    assert not _es_postgres("sqlite:///data/x.db")
    assert not _es_postgres(":memory:")


def test_sqlite_no_traduce_marcadores(db):
    # En SQLite el SQL queda igual (marcador ?).
    assert db.dialect == "sqlite"
    assert db._q("SELECT 1 WHERE a = ?") == "SELECT 1 WHERE a = ?"


def test_traduccion_a_postgres_sin_conectar():
    # Instancia "en seco": solo probamos la traducción de marcadores del dialecto
    # Postgres sin abrir conexión (evita depender de un servidor real).
    fake = Database.__new__(Database)
    fake.dialect = "postgres"
    assert fake._q("INSERT INTO t (a, b) VALUES (?, ?)") == "INSERT INTO t (a, b) VALUES (%s, %s)"
    assert fake._q("SELECT * FROM t WHERE id = ?") == "SELECT * FROM t WHERE id = %s"


def test_insert_returning_id_sqlite(db):
    db.execute(
        "INSERT INTO jobs (connector, query_json, creado_en, actualizado_en) "
        "VALUES (?, ?, ?, ?)",
        ("x", "{}", "t", "t"),
    )
    # insert_returning_id devuelve un entero creciente en SQLite.
    rid = db.insert_returning_id(
        "INSERT INTO jobs (connector, query_json, creado_en, actualizado_en) "
        "VALUES (?, ?, ?, ?)",
        ("y", "{}", "t", "t"),
    )
    assert isinstance(rid, int) and rid >= 1
