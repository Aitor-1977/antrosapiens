from hd_scraper.db.models import calcular_hash_prospecto
from hd_scraper.prospectos import nuevo_prospecto, upsert_prospecto
from hd_scraper.validation.validator import validate_prospecto


# --- Validación del contrato de prospecto --------------------------------

def test_categoria_obligatoria_y_valida():
    ok = validate_prospecto(nuevo_prospecto("ACME Ventures", "VC"))
    assert ok.ok

    sin_cat = nuevo_prospecto("ACME Ventures", "")
    assert not validate_prospecto(sin_cat).ok

    mala = nuevo_prospecto("ACME", "Fondo")  # no está en CATEGORIAS
    r = validate_prospecto(mala)
    assert not r.ok and r.motivo.startswith("categoria_invalida")


def test_hash_inconsistente_se_rechaza():
    p = nuevo_prospecto("ACME", "VC")
    p.hash_dedup = "xxx"
    assert validate_prospecto(p).motivo == "hash_dedup_inconsistente"


def test_fecha_captura_no_iso_se_rechaza():
    p = nuevo_prospecto("ACME", "Startup", fecha_captura="ayer")
    assert validate_prospecto(p).motivo == "fecha_captura_no_iso8601"


# --- Escritura / upsert ---------------------------------------------------

def test_alta_con_thick_data(db):
    p = nuevo_prospecto(
        "Nubank", "Startup",
        discurso_corporativo="Somos la mayor fintech de LatAm; nuestra promesa...",
        tipo_discurso="promesa_valor",
        url_perfil="https://nubank.com.mx/about",
        fuente_discurso="sitio_oficial",
        fecha_captura="2026-07-12T00:00:00+00:00",
    )
    res = upsert_prospecto(db, p)
    assert res["ok"] and res["accion"] == "insertado"

    row = db.fetch_one("SELECT * FROM prospectos WHERE nombre='Nubank'")
    assert row["categoria"] == "Startup"
    assert "fintech" in row["discurso_corporativo"]
    assert row["tipo_discurso"] == "promesa_valor"


def test_upsert_enriquece_sin_duplicar(db):
    upsert_prospecto(db, nuevo_prospecto("Kaszek", "VC"))
    # Segunda captura: añade el discurso (Thick Data) al mismo prospecto.
    res = upsert_prospecto(db, nuevo_prospecto(
        "Kaszek", "VC", discurso_corporativo="Tesis: fintech e infra en LatAm.",
        tipo_discurso="tesis_inversion"))
    assert res["accion"] == "actualizado"

    filas = db.fetch_all("SELECT * FROM prospectos WHERE nombre='Kaszek'")
    assert len(filas) == 1  # no se duplicó
    assert filas[0]["discurso_corporativo"].startswith("Tesis")


def test_upsert_no_borra_discurso_previo_con_none(db):
    upsert_prospecto(db, nuevo_prospecto("Y Combinator", "Incubadora",
                                         discurso_corporativo="Programa de aceleración."))
    # Re-alta sin discurso: COALESCE conserva el texto previo.
    upsert_prospecto(db, nuevo_prospecto("Y Combinator", "Incubadora"))
    row = db.fetch_one("SELECT discurso_corporativo FROM prospectos WHERE nombre='Y Combinator'")
    assert row["discurso_corporativo"] == "Programa de aceleración."


def test_prospecto_invalido_va_a_rechazos(db):
    res = upsert_prospecto(db, nuevo_prospecto("X", "NoExiste"))
    assert not res["ok"] and res["accion"] == "rechazado"
    assert db.fetch_one("SELECT COUNT(*) n FROM prospectos")["n"] == 0
    assert db.fetch_one("SELECT COUNT(*) n FROM rechazos WHERE connector='prospecto'")["n"] == 1


def test_categoria_distinta_es_otro_prospecto(db):
    # Mismo nombre pero distinta categoria => hash distinto => dos prospectos.
    upsert_prospecto(db, nuevo_prospecto("Globant", "Corporativo"))
    upsert_prospecto(db, nuevo_prospecto("Globant", "Startup"))
    assert db.fetch_one("SELECT COUNT(*) n FROM prospectos WHERE nombre='Globant'")["n"] == 2
    assert calcular_hash_prospecto("Globant", "Corporativo") != calcular_hash_prospecto("Globant", "Startup")


# --- API de solo lectura --------------------------------------------------

def test_api_prospectos(db, monkeypatch):
    import importlib
    api = importlib.import_module("hd_scraper.api.app")  # módulo real (evita colisión con el símbolo app)
    monkeypatch.setattr(api, "get_db", lambda: db)
    from fastapi.testclient import TestClient

    upsert_prospecto(db, nuevo_prospecto("Kaszek", "VC", discurso_corporativo="Tesis LatAm."))
    upsert_prospecto(db, nuevo_prospecto("Nubank", "Startup"))

    cli = TestClient(api.app)
    r = cli.get("/prospectos", params={"categoria": "VC"})
    assert r.status_code == 200 and r.json()["total"] == 1
    assert r.json()["items"][0]["nombre"] == "Kaszek"

    assert cli.get("/prospectos", params={"categoria": "Fondo"}).status_code == 400

    cats = cli.get("/prospectos/categorias").json()["categorias"]
    assert cats["VC"] == 1 and cats["Startup"] == 1 and cats["Corporativo"] == 0

    solo_discurso = cli.get("/prospectos", params={"con_discurso": True}).json()
    assert solo_discurso["total"] == 1  # solo Kaszek tiene Thick Data
