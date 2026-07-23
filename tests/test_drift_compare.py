"""Capa 6 — Motor de Drift Narrativo: tests del comparador determinista."""
import hashlib

import pytest

from hd_scraper.drift_compare import (
    TIPOS_CAMBIO,
    _extraer_conceptos,
    _normalizar_para_comparar,
    _fragmentos_cambiados,
    comparar,
    detectar_tipo_cambio,
    persistir_evidencias,
)


# ── _normalizar_para_comparar ────────────────────────────────────────────────

def test_normalizar_minusculas():
    assert _normalizar_para_comparar("HOLA MUNDO") == "hola mundo"


def test_normalizar_puntuacion():
    assert _normalizar_para_comparar("¡Hola, mundo!") == "hola mundo"


def test_normalizar_espacios():
    assert _normalizar_para_comparar("  hola   mundo  ") == "hola mundo"


def test_normalizar_vacio():
    assert _normalizar_para_comparar("") == ""
    assert _normalizar_para_comparar(None) == ""


def test_normalizar_acentos_preservados():
    result = _normalizar_para_comparar("Misión estratégica")
    assert "misión" in result
    assert "estratégica" in result


# ── _extraer_conceptos ───────────────────────────────────────────────────────

def test_extraer_conceptos_bigramas():
    texto = "inteligencia artificial para empresas tecnológicas"
    conceptos = _extraer_conceptos(texto)
    assert len(conceptos) > 0
    assert all(len(c.split()) == 2 for c in conceptos)


def test_extraer_conceptos_filtra_stop_words():
    texto = "de la en el para con por"
    conceptos = _extraer_conceptos(texto)
    assert len(conceptos) == 0


def test_extraer_conceptos_texto_vacio():
    assert _extraer_conceptos("") == set()


def test_extraer_conceptos_determinista():
    texto = "plataforma digital para transformación empresarial"
    c1 = _extraer_conceptos(texto)
    c2 = _extraer_conceptos(texto)
    assert c1 == c2


# ── detectar_tipo_cambio ─────────────────────────────────────────────────────

def test_tipo_concepto_nuevo():
    assert detectar_tipo_cambio("", "Somos líderes en innovación") == "concepto_nuevo"


def test_tipo_concepto_eliminado():
    assert detectar_tipo_cambio("Somos líderes en innovación", "") == "concepto_eliminado"


def test_tipo_none_ambos_vacios():
    assert detectar_tipo_cambio("", "") is None


def test_tipo_identidad_somos():
    assert detectar_tipo_cambio("Somos una fintech", "Somos un banco digital") == "identidad"


def test_tipo_identidad_marca():
    assert detectar_tipo_cambio("Nuestra marca representa", "Nuestra marca es sinónimo") == "identidad"


def test_tipo_posicionamiento_mision():
    assert detectar_tipo_cambio(
        "Nuestra misión es democratizar la tecnología",
        "Nuestra misión es liderar la transformación"
    ) == "posicionamiento"


def test_tipo_posicionamiento_lideres():
    assert detectar_tipo_cambio(
        "Líderes en soluciones cloud",
        "Líderes en inteligencia artificial"
    ) == "posicionamiento"


def test_tipo_audiencia_para():
    assert detectar_tipo_cambio(
        "Para empresas medianas",
        "Para consumidores globales"
    ) == "audiencia"


def test_tipo_audiencia_mercado():
    assert detectar_tipo_cambio(
        "Nuestros clientes en latinoamérica",
        "Nuestros clientes en mercado global"
    ) == "audiencia"


def test_tipo_cambio_ontologico_textos_muy_diferentes():
    antes = "Somos una empresa de logística que entrega paquetes a domicilio en la ciudad"
    despues = "Revolucionamos la movilidad urbana con micro-entregas inteligentes mediante drones autónomos"
    tipo = detectar_tipo_cambio(antes, despues)
    assert tipo in TIPOS_CAMBIO


def test_tipo_lenguaje_cambio_menor():
    antes = "Ofrecemos soluciones tecnológicas innovadoras al sector"
    despues = "Brindamos herramientas tecnológicas avanzadas al sector"
    assert detectar_tipo_cambio(antes, despues) == "lenguaje"


def test_tipo_siempre_en_tipos_validos():
    casos = [
        ("", "nuevo contenido"),
        ("viejo contenido", ""),
        ("Somos una empresa", "Somos otra empresa"),
        ("Para pymes", "Para corporativos"),
        ("Texto A completamente diferente", "ZZZZ YYYY XXXX diferente absoluto"),
    ]
    for antes, despues in casos:
        tipo = detectar_tipo_cambio(antes, despues)
        assert tipo is None or tipo in TIPOS_CAMBIO


# ── _fragmentos_cambiados ────────────────────────────────────────────────────

def test_fragmentos_sin_cambios():
    texto = "Línea uno\nLínea dos"
    assert _fragmentos_cambiados(texto, texto) == []


def test_fragmentos_reemplazo():
    cambios = _fragmentos_cambiados("Línea vieja", "Línea nueva")
    assert len(cambios) >= 1
    assert any("vieja" in c[0] for c in cambios)
    assert any("nueva" in c[1] for c in cambios)


def test_fragmentos_insercion():
    cambios = _fragmentos_cambiados("", "Contenido nuevo")
    assert len(cambios) >= 1
    assert any(c[0] == "" for c in cambios)


def test_fragmentos_eliminacion():
    cambios = _fragmentos_cambiados("Contenido viejo", "")
    assert len(cambios) >= 1
    assert any(c[1] == "" for c in cambios)


# ── comparar ─────────────────────────────────────────────────────────────────

def _snap(org, tipo, texto, sid=1):
    return {
        "id": sid, "org_nombre": org, "tipo_pagina": tipo,
        "texto": texto, "hash_contenido": hashlib.sha256(texto.encode()).hexdigest(),
    }


def test_comparar_misma_org_detecta_cambios():
    s1 = _snap("Acme", "homepage", "Somos la plataforma líder en logística\nPara empresas de retail", 1)
    s2 = _snap("Acme", "homepage", "Somos la plataforma líder en inteligencia artificial\nPara consumidores finales", 2)
    evs = comparar(s1, s2)
    assert len(evs) > 0
    assert all(e["org_nombre"] == "Acme" for e in evs)
    assert all(e["tipo_cambio"] in TIPOS_CAMBIO for e in evs)


def test_comparar_sin_cambios():
    texto = "Somos una empresa de tecnología"
    s1 = _snap("Acme", "homepage", texto, 1)
    s2 = _snap("Acme", "homepage", texto, 2)
    assert comparar(s1, s2) == []


def test_comparar_org_diferente():
    s1 = _snap("Acme", "homepage", "Texto A", 1)
    s2 = _snap("Beta", "homepage", "Texto B", 2)
    assert comparar(s1, s2) == []


def test_comparar_tipo_diferente():
    s1 = _snap("Acme", "homepage", "Texto A", 1)
    s2 = _snap("Acme", "about", "Texto B", 2)
    assert comparar(s1, s2) == []


def test_comparar_detecta_concepto_nuevo():
    s1 = _snap("Acme", "homepage", "Texto base simple de la empresa", 1)
    s2 = _snap("Acme", "homepage", "Texto base simple de la empresa\nInteligencia artificial avanzada para todos", 2)
    evs = comparar(s1, s2)
    tipos = {e["tipo_cambio"] for e in evs}
    assert "concepto_nuevo" in tipos


def test_comparar_detecta_concepto_eliminado():
    s1 = _snap("Acme", "homepage", "Somos líderes en inteligencia artificial avanzada\nInnovación constante y disruptiva", 1)
    s2 = _snap("Acme", "homepage", "Somos una empresa de servicios generales", 2)
    evs = comparar(s1, s2)
    tipos = {e["tipo_cambio"] for e in evs}
    assert "concepto_eliminado" in tipos or "concepto_nuevo" in tipos


def test_comparar_fragmentos_truncados():
    largo = "X" * 1000
    s1 = _snap("Acme", "homepage", largo, 1)
    s2 = _snap("Acme", "homepage", "Y" * 1000, 2)
    evs = comparar(s1, s2)
    for e in evs:
        assert len(e.get("fragmento_antes", "")) <= 500
        assert len(e.get("fragmento_despues", "")) <= 500


def test_comparar_ignora_cambios_minimos():
    s1 = _snap("Acme", "homepage", "Ok\nA", 1)
    s2 = _snap("Acme", "homepage", "Ok\nB", 2)
    evs = comparar(s1, s2)
    fragment_evs = [e for e in evs if e["tipo_cambio"] not in ("concepto_nuevo", "concepto_eliminado")]
    for e in fragment_evs:
        total = len(e.get("fragmento_antes", "") or "") + len(e.get("fragmento_despues", "") or "")
        assert total >= 10 or e["tipo_cambio"] in ("concepto_nuevo", "concepto_eliminado")


def test_comparar_evidencias_tienen_campos_requeridos():
    s1 = _snap("Acme", "homepage", "Nuestra misión es innovar en logística", 1)
    s2 = _snap("Acme", "homepage", "Nuestra misión es liderar en inteligencia artificial", 2)
    evs = comparar(s1, s2)
    assert len(evs) > 0
    for e in evs:
        assert "org_nombre" in e
        assert "tipo_cambio" in e
        assert "tipo_pagina" in e
        assert "descripcion" in e
        assert "snapshot_anterior_id" in e
        assert "snapshot_actual_id" in e
        assert e["snapshot_anterior_id"] == 1
        assert e["snapshot_actual_id"] == 2


def test_comparar_limita_conceptos_nuevos():
    lineas = "\n".join(f"concepto único especial {i} plataforma" for i in range(20))
    s1 = _snap("Acme", "homepage", "Texto simple base", 1)
    s2 = _snap("Acme", "homepage", lineas, 2)
    evs = comparar(s1, s2)
    conceptos_nuevos = [e for e in evs if e["tipo_cambio"] == "concepto_nuevo"
                        and e["descripcion"].startswith("Concepto nuevo:")]
    assert len(conceptos_nuevos) <= 5


# ── persistir_evidencias ─────────────────────────────────────────────────────

def test_persistir_evidencias_nuevas(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift_compare.get_db", lambda: db)
    db.execute(
        "INSERT INTO drift_snapshots (org_nombre, tipo_pagina, url, texto, hash_contenido, estado_observable, capturado_en) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Acme", "homepage", "https://acme.com", "texto", "abc", "ok", "2025-01-01T00:00:00Z"),
    )
    db.execute(
        "INSERT INTO drift_snapshots (org_nombre, tipo_pagina, url, texto, hash_contenido, estado_observable, capturado_en) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Acme", "homepage", "https://acme.com", "texto2", "def", "ok", "2025-01-02T00:00:00Z"),
    )
    evs = [{
        "org_nombre": "Acme",
        "tipo_cambio": "posicionamiento",
        "tipo_pagina": "homepage",
        "fragmento_antes": "texto viejo",
        "fragmento_despues": "texto nuevo",
        "descripcion": "Cambió (posicionamiento)",
        "snapshot_anterior_id": 1,
        "snapshot_actual_id": 2,
    }]
    nuevas = persistir_evidencias(evs)
    assert nuevas == 1


def test_persistir_evidencias_dedup(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift_compare.get_db", lambda: db)
    db.execute(
        "INSERT INTO drift_snapshots (org_nombre, tipo_pagina, url, texto, hash_contenido, estado_observable, capturado_en) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Acme", "homepage", "https://acme.com", "texto", "abc", "ok", "2025-01-01T00:00:00Z"),
    )
    db.execute(
        "INSERT INTO drift_snapshots (org_nombre, tipo_pagina, url, texto, hash_contenido, estado_observable, capturado_en) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Acme", "homepage", "https://acme.com", "texto2", "def", "ok", "2025-01-02T00:00:00Z"),
    )
    ev = {
        "org_nombre": "Acme",
        "tipo_cambio": "lenguaje",
        "tipo_pagina": "homepage",
        "fragmento_antes": "fragmento A",
        "fragmento_despues": "fragmento B",
        "descripcion": "Cambió (lenguaje)",
        "snapshot_anterior_id": 1,
        "snapshot_actual_id": 2,
    }
    assert persistir_evidencias([ev]) == 1
    assert persistir_evidencias([ev]) == 0


def test_persistir_evidencias_vacia(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift_compare.get_db", lambda: db)
    assert persistir_evidencias([]) == 0


# ── constantes ───────────────────────────────────────────────────────────────

def test_tipos_cambio_cerrados():
    esperados = {
        "posicionamiento", "audiencia", "lenguaje", "identidad",
        "concepto_nuevo", "concepto_eliminado", "contradiccion", "cambio_ontologico",
    }
    assert set(TIPOS_CAMBIO) == esperados


def test_tipos_cambio_son_8():
    assert len(TIPOS_CAMBIO) == 8
