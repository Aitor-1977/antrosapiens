"""Verificación estática de android_v3/app/src/main/assets/public/index.html
para los componentes 9-10 y 12 del cierre de 15 (ver nota sobre el 11 abajo).

9.  Flujo Android conectado al backend cloud real (Vercel), sin mocks/inline.
10. UI con las cuatro operaciones (Indagar/Observar/Triangular/Fijar)
    integradas en el mismo index.html, no como mockups separados.
12. index.html sin ningún objeto de datos crudo inline ni volcado de código
    visible en pantalla.

Repuntado 2026-09-16 a android_v3 (android_v2 fue eliminado del repo:
sin commits desde 2026-09-11, android_v3 es la única app viva desde
2026-09-12 — ver README.md). Al repuntar se encontró que el Componente 11
("Espacio de Lectura Pericial editable por el usuario, sin autogeneración",
`<p id="campoPericial" contenteditable="true">`) NO existe en
android_v3/index.html — no fue portado cuando android_v3 se creó como
versión simplificada de android_v2. No es un renombrado: no hay ningún
`contenteditable` en todo el archivo. Se retiran aquí los 3 tests de ese
componente porque prueban una función que ya no existe en el código
vigente, no porque se haya verificado que está bien perderla — queda
como hallazgo a decidir por el operador, no resuelto por esta rama.

No son tests de comportamiento de navegador (no hay runtime JS aquí): son
verificaciones estructurales sobre el archivo fuente, para que una regresión
futura (reintroducir un mock, borrar una pantalla) la detecte la suite sin
necesidad de abrir un emulador.
"""
import re
from pathlib import Path

INDEX_HTML = (
    Path(__file__).resolve().parent.parent
    / "android_v3" / "app" / "src" / "main" / "assets" / "public" / "index.html"
)


def _html() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def test_index_html_existe_en_la_ruta_esperada():
    assert INDEX_HTML.is_file()


# ── Componente 9: backend cloud real, sin mocks ─────────────────────────────

def test_apunta_al_backend_real_de_vercel():
    html = _html()
    assert 'const API = "https://antrosapiens-api-pro.vercel.app";' in html
    assert "localhost" not in html
    assert "127.0.0.1" not in html


def test_no_hay_arreglos_de_datos_mock_hardcodeados():
    html = _html()
    # Ninguna variable típica de datos de prueba, y toda organización que
    # aparece en pantalla llega vía fetch(), no de un literal embebido.
    for marcador in ("mockData", "mock_data", "datosFalsos", "FAKE_", "DUMMY"):
        assert marcador not in html
    # Los tres endpoints reales que consume la pantalla, todos vía fetch()
    # (directo o envuelto en fetchConReintento(), que solo agrega un reintento
    # sobre el mismo fetch() real ante los timeouts intermitentes del backend
    # confirmados 2026-09-11 — nunca sustituye la llamada por datos de prueba).
    assert re.search(r"fetch(?:ConReintento)?\(`\$\{API\}/expedientes", html)
    assert re.search(r"fetch(?:ConReintento)?\(`\$\{API\}/verificados", html)


# ── Componente 10: las 4 operaciones integradas en un solo archivo ─────────

def test_las_cuatro_pantallas_viven_en_el_mismo_index_html():
    html = _html()
    for pantalla_id in ("screen-explorar", "screen-observar",
                        "screen-triangular", "screen-fijar"):
        assert f'id="{pantalla_id}"' in html, (
            f"falta la pantalla {pantalla_id!r} en index.html")


def test_navegacion_inferior_conecta_las_cuatro_pantallas():
    html = _html()
    for boton in ("btnExplorarNav", "btnObservarNav",
                  "btnTriangularNav", "btnFijarNav"):
        assert f'id="{boton}"' in html
        assert f"getElementById('{boton}')" in html


# ── Componente 11 (Lectura Pericial) — NO PORTADO a android_v3, ver nota ──
# de módulo. Sin tests aquí: no se prueba una función que no existe.


# ── Componente 12: sin volcado de datos crudos visible en pantalla ────────

def test_no_hay_bloques_pre_o_code_de_datos_crudos():
    html = _html()
    assert "<pre" not in html
    assert "<code" not in html


def test_json_stringify_nunca_se_vuelca_directo_a_innerhtml_o_textcontent():
    """`JSON.stringify` sí aparece en android_v3 (cuerpo de POST /mobile/scrape,
    y logging de depuración con console.log — ninguno de los dos renderiza en
    pantalla). Lo que el Componente 12 prohíbe es específicamente que un
    volcado crudo llegue al DOM: que un JSON.stringify() alimente
    directamente un innerHTML/textContent."""
    html = _html()
    for m in re.finditer(r"\.(?:innerHTML|textContent)\s*=\s*([^;]{0,200})", html):
        assert "JSON.stringify" not in m.group(1), (
            "JSON.stringify no debe volcarse directo a innerHTML/textContent")
