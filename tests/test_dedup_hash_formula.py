"""Componente 6 del cierre de 15: la deduplicación de organizaciones usa
exactamente sha256(nombre_normalizado + "|" + categoria). Fija la fórmula
byte a byte (no solo estabilidad/unicidad, que ya cubre test_prospectos.py),
para que un cambio futuro de formato la rompa de forma visible."""
import hashlib

from hd_scraper.db.models import calcular_hash_prospecto, normalizar_empresa


def test_hash_prospecto_es_sha256_de_nombre_normalizado_mas_pipe_mas_categoria():
    nombre, categoria = "Kaszek", "VC"
    esperado = hashlib.sha256(
        f"{normalizar_empresa(nombre)}|{categoria}".encode("utf-8")
    ).hexdigest()
    assert calcular_hash_prospecto(nombre, categoria) == esperado


def test_hash_prospecto_normaliza_el_nombre_pero_no_la_categoria():
    """La normalización colapsa mayúsculas/espacios del NOMBRE (para que
    "Kaszek" y "kaszek " deduplican igual); la categoría viaja literal — es
    uno de los cuatro valores cerrados de CATEGORIAS, no texto libre."""
    assert calcular_hash_prospecto("Kaszek", "VC") == calcular_hash_prospecto(" kaszek ", "VC")
    assert calcular_hash_prospecto("Kaszek", "VC") != calcular_hash_prospecto("Kaszek", "vc")


def test_hash_prospecto_es_sensible_a_categoria():
    assert (calcular_hash_prospecto("Globant", "Startup")
            != calcular_hash_prospecto("Globant", "Corporativo"))
