"""Capa 6 — Motor de Drift Narrativo: tests de captura de snapshots."""
import hashlib

import pytest

from hd_scraper.drift import (
    ESTADOS_NO_OBSERVABLE,
    RUTAS_POR_TIPO,
    TIPOS_PAGINA,
    _hash_texto,
    _limpiar_html,
    _normalizar_url,
    capturar_pagina,
    capturar_snapshot,
    obtener_snapshot_anterior,
    obtener_timeline,
)


# ── utilidades internas ──────────────────────────────────────────────────────

def test_limpiar_html_elimina_scripts_y_nav():
    html = """<html><head><script>var x=1;</script></head>
    <body><nav>Menu</nav><main><p>Contenido real</p></main>
    <footer>Pie</footer></body></html>"""
    texto = _limpiar_html(html)
    assert "Contenido real" in texto
    assert "var x=1" not in texto
    assert "Menu" not in texto
    assert "Pie" not in texto


def test_limpiar_html_vacio():
    assert _limpiar_html("") == ""
    assert _limpiar_html("<div></div>") == ""


def test_hash_texto_determinista():
    h1 = _hash_texto("hola mundo")
    h2 = _hash_texto("hola mundo")
    assert h1 == h2
    assert h1 == hashlib.sha256("hola mundo".encode("utf-8")).hexdigest()


def test_hash_texto_diferente():
    assert _hash_texto("a") != _hash_texto("b")


def test_normalizar_url_con_https():
    assert _normalizar_url("https://example.com", "about") == "https://example.com/about"


def test_normalizar_url_sin_protocolo():
    assert _normalizar_url("example.com", "about") == "https://example.com/about"


def test_normalizar_url_homepage():
    assert _normalizar_url("https://example.com/", "") == "https://example.com"


def test_normalizar_url_trailing_slash():
    assert _normalizar_url("https://example.com///", "about") == "https://example.com/about"


# ── capturar_pagina ─────────────────────────────────────────────────────────

def test_capturar_pagina_ok():
    html = "<html><body><main><p>Contenido sustancial de la empresa que supera el mínimo</p></main></body></html>"
    resultado = capturar_pagina("https://x.com", lambda u: html)
    assert resultado["estado"] == "ok"
    assert "Contenido sustancial" in resultado["texto"]
    assert resultado["url"] == "https://x.com"


def test_capturar_pagina_contenido_vacio():
    resultado = capturar_pagina("https://x.com", lambda u: "<html><body></body></html>")
    assert resultado["estado"] == "contenido_vacio"
    assert resultado["texto"] == ""


def test_capturar_pagina_contenido_muy_corto():
    resultado = capturar_pagina("https://x.com", lambda u: "<html><body><p>Hi</p></body></html>")
    assert resultado["estado"] == "contenido_vacio"


def test_capturar_pagina_spa_detectado():
    html = '<html><body><div id="__next"><noscript>You need to enable JavaScript</noscript><p>' + ("App loading content. " * 3) + '</p></div></body></html>'
    resultado = capturar_pagina("https://x.com", lambda u: html)
    assert resultado["estado"] == "spa"


def test_capturar_pagina_timeout():
    def timeout_get(url):
        raise Exception("Connection timed out")
    resultado = capturar_pagina("https://x.com", timeout_get)
    assert resultado["estado"] == "timeout"


def test_capturar_pagina_403():
    def forbidden_get(url):
        raise Exception("HTTP 403 Forbidden")
    resultado = capturar_pagina("https://x.com", forbidden_get)
    assert resultado["estado"] == "bloqueado"


def test_capturar_pagina_404():
    def notfound_get(url):
        raise Exception("404 Not Found")
    resultado = capturar_pagina("https://x.com", notfound_get)
    assert resultado["estado"] == "error_http"


def test_capturar_pagina_robots():
    def robots_get(url):
        raise Exception("Blocked by robots.txt")
    resultado = capturar_pagina("https://x.com", robots_get)
    assert resultado["estado"] == "robots"


def test_capturar_pagina_error_generico():
    def err(url):
        raise Exception("Something went wrong")
    resultado = capturar_pagina("https://x.com", err)
    assert resultado["estado"] == "error_http"


# ── capturar_snapshot (integración con DB) ───────────────────────────────────

HTML_LARGO = "<html><body><main><p>" + ("Contenido real de la empresa. " * 10) + "</p></main></body></html>"


def _http_ok(url):
    return HTML_LARGO


def _http_fail(url):
    raise Exception("timeout: connection timed out")


def test_capturar_snapshot_crea_registros(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    resultados = capturar_snapshot("Acme Corp", "https://acme.com", _http_ok, tipos=("homepage",))
    assert len(resultados) == 1
    assert resultados[0]["estado"] == "ok"
    assert resultados[0]["org_nombre"] == "Acme Corp"
    assert resultados[0]["tipo_pagina"] == "homepage"
    assert resultados[0]["id"] is not None


def test_capturar_snapshot_dedup_por_hash(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    r1 = capturar_snapshot("Acme Corp", "https://acme.com", _http_ok, tipos=("homepage",))
    r2 = capturar_snapshot("Acme Corp", "https://acme.com", _http_ok, tipos=("homepage",))
    assert r1[0]["estado"] == "ok"
    assert r2[0]["estado"] == "sin_cambios"


def test_capturar_snapshot_nuevo_si_contenido_cambia(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    contenidos = iter([
        "<html><body><main><p>" + ("Versión uno del contenido. " * 10) + "</p></main></body></html>",
        "<html><body><main><p>" + ("Versión dos del contenido cambiado. " * 10) + "</p></main></body></html>",
    ])

    def http_secuencial(url):
        return next(contenidos)

    r1 = capturar_snapshot("Acme Corp", "https://acme.com", http_secuencial, tipos=("homepage",))
    r2 = capturar_snapshot("Acme Corp", "https://acme.com", http_secuencial, tipos=("homepage",))
    assert r1[0]["estado"] == "ok"
    assert r2[0]["estado"] == "ok"
    assert r1[0]["id"] != r2[0]["id"]


def test_capturar_snapshot_estado_no_observable(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    resultados = capturar_snapshot("Acme Corp", "https://acme.com", _http_fail, tipos=("homepage",))
    assert len(resultados) == 1
    assert resultados[0]["estado"] in ESTADOS_NO_OBSERVABLE


def test_capturar_snapshot_multiples_tipos(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    resultados = capturar_snapshot("Acme Corp", "https://acme.com", _http_ok, tipos=("homepage", "about"))
    assert len(resultados) == 2


def test_capturar_snapshot_todos_los_tipos(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    resultados = capturar_snapshot("Acme Corp", "https://acme.com", _http_ok)
    assert len(resultados) == len(TIPOS_PAGINA)


def test_capturar_snapshot_tipo_invalido_ignorado(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    resultados = capturar_snapshot("Acme Corp", "https://acme.com", _http_ok, tipos=("inexistente",))
    assert len(resultados) == 0


# ── obtener_snapshot_anterior ────────────────────────────────────────────────

def test_obtener_snapshot_anterior_existe(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    contenidos = iter([
        "<html><body><main><p>" + ("Primera versión del sitio web. " * 10) + "</p></main></body></html>",
        "<html><body><main><p>" + ("Segunda versión del sitio web actualizado. " * 10) + "</p></main></body></html>",
    ])

    def http_seq(url):
        return next(contenidos)

    r1 = capturar_snapshot("Acme Corp", "https://acme.com", http_seq, tipos=("homepage",))
    r2 = capturar_snapshot("Acme Corp", "https://acme.com", http_seq, tipos=("homepage",))
    anterior = obtener_snapshot_anterior("Acme Corp", "homepage", r2[0]["id"])
    assert anterior is not None
    assert anterior["id"] == r1[0]["id"]


def test_obtener_snapshot_anterior_no_existe(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    capturar_snapshot("Acme Corp", "https://acme.com", _http_ok, tipos=("homepage",))
    anterior = obtener_snapshot_anterior("Acme Corp", "homepage", 1)
    assert anterior is None


# ── obtener_timeline ─────────────────────────────────────────────────────────

def test_obtener_timeline_vacio(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    tl = obtener_timeline("NoExiste")
    assert tl["total_snapshots"] == 0
    assert tl["total_evidencias"] == 0
    assert tl["org_nombre"] == "NoExiste"


def test_obtener_timeline_con_datos(db, monkeypatch):
    monkeypatch.setattr("hd_scraper.drift.get_db", lambda: db)
    capturar_snapshot("Acme Corp", "https://acme.com", _http_ok, tipos=("homepage",))
    tl = obtener_timeline("Acme Corp")
    assert tl["total_snapshots"] == 1
    assert len(tl["snapshots"]) == 1


# ── constantes ───────────────────────────────────────────────────────────────

def test_tipos_pagina_completos():
    assert "homepage" in TIPOS_PAGINA
    assert "about" in TIPOS_PAGINA
    assert "mision" in TIPOS_PAGINA
    assert "propuesta_valor" in TIPOS_PAGINA
    assert "manifiesto" in TIPOS_PAGINA


def test_rutas_por_tipo_cubre_todos():
    for tipo in TIPOS_PAGINA:
        assert tipo in RUTAS_POR_TIPO
        assert len(RUTAS_POR_TIPO[tipo]) >= 1


def test_estados_no_observable():
    assert "spa" in ESTADOS_NO_OBSERVABLE
    assert "timeout" in ESTADOS_NO_OBSERVABLE
    assert "error_http" in ESTADOS_NO_OBSERVABLE
    assert "bloqueado" in ESTADOS_NO_OBSERVABLE
    assert "robots" in ESTADOS_NO_OBSERVABLE
