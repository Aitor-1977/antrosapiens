"""Script `scripts.trazabilidad.py` — lectura de la cadena de trazabilidad.

Cubre:
  A. Dos organizaciones DISTINTAS con el mismo ID de expediente => detectado.
  B. Un expediente repetido dentro de la MISMA organización no es violación.
  C. Expediente vacío se ignora (no es "compartido").
  D. `_leer_candidatos` lee la cadena exacta persistida (sin escritura).
  E. `_cadena` imprime el formato y los marcadores de huecos.
"""
import hashlib

import pytest

from hd_scraper import candidato as cand
from hd_scraper.db.models import ahora_iso
from scripts import trazabilidad


# ── A. Dos organizaciones distintas, mismo expediente ─────────────────────────

def test_duplicado_expediente_entre_orgs_distintas():
    filas = [
        {"org_nombre": "Acme Corp", "expediente_hash": "h-exp"},
        {"org_nombre": "Beta Inc", "expediente_hash": "h-exp"},
        {"org_nombre": "Gamma", "expediente_hash": "otro"},
    ]
    dups = trazabilidad._duplicados_expediente(filas)
    assert len(dups) == 1
    h, orgs = dups[0]
    assert h == "h-exp"
    assert orgs == ["Acme Corp", "Beta Inc"]


# ── B. El mismo expediente en la misma organización no es violación ───────────

def test_expediente_repetido_misma_org_no_viola():
    filas = [
        {"org_nombre": "Acme Corp", "expediente_hash": "h-exp"},
        {"org_nombre": "Acme Corp", "expediente_hash": "h-exp"},
        {"org_nombre": "Acme Corp", "expediente_hash": "h-exp-2"},
    ]
    assert trazabilidad._duplicados_expediente(filas) == []


# ── C. Expediente vacío se ignora ─────────────────────────────────────────────

def test_expediente_vacio_se_ignora():
    filas = [
        {"org_nombre": "Acme Corp", "expediente_hash": ""},
        {"org_nombre": "Beta Inc", "expediente_hash": None},
        {"org_nombre": "Gamma", "expediente_hash": "  "},
    ]
    assert trazabilidad._duplicados_expediente(filas) == []


# ── D. Lectura de la cadena exacta persistida ─────────────────────────────────

def _insertar_prospecto(db, nombre):
    db.execute(
        """INSERT INTO prospectos (nombre, categoria, escala, hash_dedup,
             creado_en, actualizado_en)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (nombre, "Startup", "11-50",
         hashlib.sha256(f"{nombre}|Startup".encode()).hexdigest(),
         ahora_iso(), ahora_iso()),
    )
    return db.fetch_one("SELECT id FROM prospectos WHERE nombre = ?",
                        (nombre,))["id"]


def test_leer_candidatos_devuelve_la_cadena(db):
    pid = _insertar_prospecto(db, "Acme Corp")
    exp = {
        "nombre": "Acme Corp",
        "huella": "huella-acme",
        "total_evidencias": 1,
        "evidencias": [{"url": "https://a.com/1", "texto": "Acme Corp señal",
                        "confianza": 0.8}],
        "validacion_cientifica": {"veredicto": "VALIDADA",
                                  "hipotesis_bloqueada": False},
    }
    cand.materializar_candidatos(db, [exp])

    filas = trazabilidad._leer_candidatos(db)
    assert len(filas) == 1
    c = filas[0]
    assert c["org_nombre"] == "Acme Corp"
    assert c["candidato_id"] == cand.candidato_id("Acme Corp")
    assert c["prospecto_id"] == pid
    assert c["expediente_hash"] == "huella-acme"


# ── E. Formato de la cadena impresa ───────────────────────────────────────────

def test_cadena_completa():
    c = {"org_nombre": "Acme Corp", "candidato_id": "abc",
         "prospecto_id": 7, "expediente_hash": "h-exp"}
    assert (trazabilidad._cadena(c)
            == "Acme Corp -> abc -> 7 -> h-exp")


def test_cadena_con_huecos():
    c = {"org_nombre": "Acme Corp", "candidato_id": "abc",
         "prospecto_id": None, "expediente_hash": "  "}
    assert (trazabilidad._cadena(c)
            == "Acme Corp -> abc -> (sin prospecto) -> (sin expediente)")


def test_dsn_desc_no_expone_credenciales():
    dsn = "postgresql://user:secret@db.example.com:5432/hamaca"
    assert "secret" not in trazabilidad._dsn_desc(dsn)
    assert "postgresql://db.example.com:5432/hamaca" == trazabilidad._dsn_desc(dsn)
