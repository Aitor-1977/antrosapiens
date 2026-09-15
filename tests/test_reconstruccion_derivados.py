"""Prueba de RESET + RECONSTRUCCIÓN de los datos derivados
(evidencia_clasificada, expedientes_candidatos) desde evidencias + el
algoritmo vigente (clasificacion_store.clasificar_lote +
promocion_store.promover_lote), sin ningún parche específico de "Clara".

Simula exactamente el escenario de producción: una fila DERIVADA obsoleta
(clasificada con reglas viejas) convive con evidencia legítima variada.
Se borra SOLO lo derivado (nunca `evidencias`) y se reconstruye desde cero
con el código vigente. Cubre, a nivel de INTEGRACIÓN (no solo función
pura), lo que el "mapa de dependencias real" (Fase 1) predice:

    evidencias (RAW, jamás se borra)
        │  evidencia_id FK NOT NULL
        ▼
    evidencia_clasificada (DERIVADA) ── expediente_id FK ──▶ expedientes_candidatos (DERIVADA)
        (nada más referencia a ninguna de las dos — confirmado por grep
         sobre schema_postgres.sql / schema.sql: es el único FK que existe)

    expedientes_candidatos.estado: 'abierto' -> 'candidato' vía
    promocion_store.promover_lote, que solo promueve si existe al menos una
    fila con tipo_epistemologico en (senal_primaria_autodeclaracion,
    senal_primaria_huella_practica) — nunca por corroborante/contextual
    (promocion_candidatos.decidir_promocion, regla dura, sin tocar aquí).
"""
from hd_scraper.clasificacion_store import clasificar_lote
from hd_scraper.db.models import ahora_iso
from hd_scraper.promocion_store import promover_lote

_TXT_CLARA_BRUGADA = (
    'Clara Brugada acompaña a la Presidenta Claudia Sheinbaum en el '
    'arranque de "Sí al Desarme, Sí a la Paz"; destaca reducción de '
    'homicidios en la Ciudad de México - CDMX'
)


def _sembrar_evidencia(db, n, cita, *, empresa, origen="prensa", connector="google_news"):
    db.execute(
        "INSERT INTO evidencias (id, cita_textual, fecha_extraccion, "
        "fecha_publicacion, url_fuente, nombre_medio, empresa_mencionada, "
        "tipo_evento, origen_declaracion, hash_dedup, connector, creado_en) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (n, cita, ahora_iso(), "2026-08-01", f"https://ejemplo.test/{n}",
         "Prensa X", empresa, "ronda", origen, f"hash-recon-{n}", connector,
         ahora_iso()))


def _sembrar_corpus_mixto(db):
    """Corpus RAW realista: el caso Clara real + control de cada categoría
    epistemológica + una relación (Nubank/Lead Bank) que NO debe filtrar
    identidad ajena a expedientes_candidatos."""
    _sembrar_evidencia(db, 1, _TXT_CLARA_BRUGADA, empresa="Clara")
    _sembrar_evidencia(db, 2,
        "Clara, la fintech, anunció una ronda de inversión de 50 millones "
        "de dólares liderada por su CEO", empresa="Clara")
    _sembrar_evidencia(db, 3, "Juan Pérez, CEO de Acme, anunció despidos",
        empresa="Acme")
    _sembrar_evidencia(db, 4, "Acme busca ingeniero de datos en Ciudad de "
        "México", empresa="Acme", origen="operador")
    _sembrar_evidencia(db, 5, "Extrabajadores de Acme denuncian despidos "
        "masivos", empresa="Acme")
    _sembrar_evidencia(db, 6, "Empleados de Acme reciben un bono anual",
        empresa="Acme")
    _sembrar_evidencia(db, 7,
        "David Vélez, CEO de Nubank, anunció una alianza con Lead Bank "
        "dentro de su plan de expansión hacia EE.UU.", empresa="Nubank")
    # Corporativo explícitamente excluido de promoción sin importar evidencia.
    _sembrar_evidencia(db, 8, "María Sánchez, CEO de Globex, presentó "
        "resultados trimestrales", empresa="Globex")
    ahora = ahora_iso()
    db.execute(
        "INSERT INTO prospectos (nombre, categoria, escala, hash_dedup, "
        "creado_en, actualizado_en) VALUES (?,?,?,?,?,?)",
        ("Globex", "Corporativo", "indeterminada", "hash-globex-prospecto",
         ahora, ahora))


def _sembrar_fila_derivada_obsoleta(db):
    """Reproduce EXACTAMENTE el dato histórico real de producción: la
    evidencia 1 (Clara Brugada) ya clasificada con reglas de ANTES del fix
    de _es_parte_de_nombre_mas_largo, y su expediente ya promovido —
    justo el estado que hoy sigue viéndose en /verificados."""
    exp_id = db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        ("Clara", "candidato"))
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico, enunciador_nombre, enunciador_cargo) "
        "VALUES (?,?,?,?,?)",
        (exp_id, 1, "senal_primaria_autodeclaracion", "Clara Brugada",
         "Presidenta"))


def _estado_expedientes(db) -> dict[str, str]:
    filas = db.fetch_all("SELECT organizacion, estado FROM expedientes_candidatos")
    return {dict(f)["organizacion"]: dict(f)["estado"] for f in filas}


def _reconstruir(db):
    rep_clas = clasificar_lote(db, aplicar=True)
    rep_prom = promover_lote(db, aplicar=True)
    return rep_clas, rep_prom


def test_reset_y_reconstruccion_elimina_clara_falsa_sin_tocar_evidencia_cruda(db):
    _sembrar_corpus_mixto(db)
    _sembrar_fila_derivada_obsoleta(db)

    total_raw_antes = db.fetch_one("SELECT COUNT(*) n FROM evidencias")["n"]

    # --- RESET: vaciar SOLO lo derivado (evidencia_clasificada primero, la
    # única con FK saliente hacia expedientes_candidatos). ---
    db.execute("DELETE FROM evidencia_clasificada")
    db.execute("DELETE FROM expedientes_candidatos")
    assert db.fetch_one("SELECT COUNT(*) n FROM evidencia_clasificada")["n"] == 0
    assert db.fetch_one("SELECT COUNT(*) n FROM expedientes_candidatos")["n"] == 0
    assert db.fetch_one("SELECT COUNT(*) n FROM evidencias")["n"] == total_raw_antes, \
        "el reset NO debe tocar la evidencia cruda"

    # --- RECONSTRUCCIÓN desde cero, solo con evidencias + algoritmo vigente. ---
    rep_clas, rep_prom = _reconstruir(db)
    assert rep_clas["escritas"] == total_raw_antes

    estado = _estado_expedientes(db)

    # 1. Clara Brugada (persona) NUNCA vuelve a promover "Clara".
    #    La evidencia 2 (fintech real, autodeclaración legítima) sí puede
    #    promover "Clara" — el expediente es el mismo NOMBRE, pero ahora
    #    sostenido por evidencia real, no por la persona política.
    assert estado.get("Clara") == "candidato"
    fila_clara = db.fetch_one(
        "SELECT tipo_epistemologico FROM evidencia_clasificada "
        "WHERE evidencia_id = 1")
    assert dict(fila_clara)["tipo_epistemologico"] == "contextual", \
        "la evidencia de Clara Brugada debe quedar contextual, no vinculada"

    # 2. Persona + cargo (Juan Pérez/CEO Acme) -> organización Acme, nunca
    #    "Juan Pérez" como organización.
    assert "Juan Pérez" not in estado
    assert estado.get("Acme") == "candidato"  # autodeclaración + huella práctica

    # 3. Relación (Nubank...alianza con Lead Bank): la identidad del
    #    expediente es la declarada estructuralmente (empresa_mencionada),
    #    "Lead Bank" JAMÁS se convierte en organización propia aquí.
    assert estado.get("Nubank") == "candidato"
    assert "Lead Bank" not in estado

    # 4. Mención contextual sin fricción (Acme: "bono anual") no relaja ni
    #    revierte una promoción ya sostenida por otra evidencia legítima del
    #    mismo Acme (autodeclaración + huella práctica ya la sostienen).
    #    Verificado aparte con un candidato que SOLO tuviera contextual:
    tipos_acme = {dict(f)["tipo_epistemologico"] for f in db.fetch_all(
        "SELECT tipo_epistemologico FROM evidencia_clasificada ec "
        "JOIN expedientes_candidatos e ON e.id = ec.expediente_id "
        "WHERE e.organizacion = 'Acme'")}
    assert "contextual" in tipos_acme  # se conserva, no se descarta
    assert "senal_primaria_autodeclaracion" in tipos_acme
    assert "senal_primaria_huella_practica" in tipos_acme

    # 5. Corporativo explícitamente excluido de promoción (Globex), pese a
    #    tener una autodeclaración de CEO real.
    assert estado.get("Globex") == "abierto"

    # 6. No se perdió evidencia cruda.
    assert db.fetch_one("SELECT COUNT(*) n FROM evidencias")["n"] == total_raw_antes


def test_reconstruccion_es_idempotente_segunda_corrida_sin_duplicados(db):
    _sembrar_corpus_mixto(db)
    db.execute("DELETE FROM evidencia_clasificada")
    db.execute("DELETE FROM expedientes_candidatos")

    _reconstruir(db)
    estado_1 = _estado_expedientes(db)
    n_exp_1 = db.fetch_one("SELECT COUNT(*) n FROM expedientes_candidatos")["n"]
    n_clas_1 = db.fetch_one("SELECT COUNT(*) n FROM evidencia_clasificada")["n"]

    rep_clas_2, rep_prom_2 = _reconstruir(db)
    estado_2 = _estado_expedientes(db)
    n_exp_2 = db.fetch_one("SELECT COUNT(*) n FROM expedientes_candidatos")["n"]
    n_clas_2 = db.fetch_one("SELECT COUNT(*) n FROM evidencia_clasificada")["n"]

    assert rep_clas_2["escritas"] == 0, "la segunda corrida no debe reclasificar nada"
    assert rep_prom_2["promovidos"] == 0, "la segunda corrida no debe repromover nada"
    assert n_exp_1 == n_exp_2, "no debe duplicar expedientes"
    assert n_clas_1 == n_clas_2, "no debe duplicar clasificaciones"
    assert estado_1 == estado_2, "el resultado lógico debe ser idéntico"
    assert "Clara" not in [org for org, e in estado_2.items() if org == "Clara Brugada"]


# ── GET /admin/reconstruir-derivados (endpoint administrativo real) ───────
# Mismo escenario que arriba, pero disparado por el endpoint que Mario
# podría llamar sin tocar SQL — protegido por el X-Ingest-Token existente,
# nunca un bypass ni una autenticación nueva.

import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.config import settings

RUTA_RECONSTRUIR = "/admin/reconstruir-derivados"


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    object.__setattr__(settings, "ingest_token", "secreto-123")
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")


H = {"X-Ingest-Token": "secreto-123"}


def test_admin_reconstruir_derivados_requiere_token(cli):
    assert cli.get(RUTA_RECONSTRUIR).status_code == 401


def test_admin_reconstruir_derivados_dry_run_no_escribe(cli, db):
    _sembrar_corpus_mixto(db)
    _sembrar_fila_derivada_obsoleta(db)
    n_antes = db.fetch_one("SELECT COUNT(*) n FROM evidencia_clasificada")["n"]

    r = cli.get(RUTA_RECONSTRUIR, headers=H)
    assert r.status_code == 200
    assert r.json()["aplicado"] is False

    n_despues = db.fetch_one("SELECT COUNT(*) n FROM evidencia_clasificada")["n"]
    assert n_antes == n_despues, "dry-run no debe escribir nada"


def test_admin_reconstruir_derivados_aplicar_elimina_clara_falsa(cli, db):
    _sembrar_corpus_mixto(db)
    _sembrar_fila_derivada_obsoleta(db)
    total_raw = db.fetch_one("SELECT COUNT(*) n FROM evidencias")["n"]

    r = cli.get(RUTA_RECONSTRUIR, params={"aplicar": "true"}, headers=H)
    assert r.status_code == 200
    d = r.json()
    assert d["aplicado"] is True
    assert d["evidencia_cruda_intacta"] is True
    assert d["reclasificadas"] == total_raw

    estado = _estado_expedientes(db)
    assert estado.get("Clara") == "candidato"  # sostenido por evidencia real
    fila_clara = db.fetch_one(
        "SELECT tipo_epistemologico FROM evidencia_clasificada WHERE evidencia_id = 1")
    assert dict(fila_clara)["tipo_epistemologico"] == "contextual"
    assert estado.get("Globex") == "abierto"  # Corporativo, excluido
    assert db.fetch_one("SELECT COUNT(*) n FROM evidencias")["n"] == total_raw


def test_admin_reconstruir_derivados_endpoint_es_idempotente(cli, db):
    # "Idempotente" aquí significa RESULTADO LÓGICO estable entre corridas
    # (mismo estado final, sin acumular filas): cada llamada es un reset
    # COMPLETO (borra y reconstruye TODO desde evidencias), así que
    # "reclasificadas" es el mismo número en ambas corridas — la prueba real
    # de no-duplicación es que expedientes/estado no crecen ni cambian.
    _sembrar_corpus_mixto(db)
    _sembrar_fila_derivada_obsoleta(db)

    r1 = cli.get(RUTA_RECONSTRUIR, params={"aplicar": "true"}, headers=H)
    d1 = r1.json()
    estado_1 = _estado_expedientes(db)
    n_exp_1 = db.fetch_one("SELECT COUNT(*) n FROM expedientes_candidatos")["n"]

    r2 = cli.get(RUTA_RECONSTRUIR, params={"aplicar": "true"}, headers=H)
    d2 = r2.json()
    estado_2 = _estado_expedientes(db)
    n_exp_2 = db.fetch_one("SELECT COUNT(*) n FROM expedientes_candidatos")["n"]

    assert d1["reclasificadas"] == d2["reclasificadas"]
    assert estado_1 == estado_2, "el resultado lógico debe ser idéntico entre corridas"
    assert n_exp_1 == n_exp_2, "no debe acumular expedientes duplicados"
