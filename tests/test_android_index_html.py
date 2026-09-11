"""Verificación estática de android_v2/app/src/main/assets/public/index.html
para los componentes 9-12 del cierre de 15:

9.  Flujo Android conectado al backend cloud real (Vercel), sin mocks/inline.
10. UI con las cuatro operaciones (Indagar/Observar/Triangular/Fijar)
    integradas en el mismo index.html, no como mockups separados.
11. Espacio de Lectura Pericial editable por el usuario, sin autogeneración.
12. index.html sin ningún objeto de datos crudo inline ni volcado de código
    visible en pantalla.

No son tests de comportamiento de navegador (no hay runtime JS aquí): son
verificaciones estructurales sobre el archivo fuente, para que una regresión
futura (reintroducir un mock, borrar una pantalla, prellenar la lectura
pericial) la detecte la suite sin necesidad de abrir un emulador.
"""
import re
from pathlib import Path

INDEX_HTML = (
    Path(__file__).resolve().parent.parent
    / "android_v2" / "app" / "src" / "main" / "assets" / "public" / "index.html"
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


# ── Componente 11: Lectura Pericial editable, sin autogeneración ───────────

def test_campo_pericial_es_editable_por_el_usuario():
    html = _html()
    m = re.search(r'<p id="campoPericial"[^>]*>', html)
    assert m, "no se encontró el campo de Lectura Pericial"
    etiqueta = m.group(0)
    assert 'contenteditable="true"' in etiqueta


def test_campo_pericial_nace_vacio_sin_texto_generado_por_el_sistema():
    """El elemento no debe contener ningún texto entre sus etiquetas (solo el
    placeholder CSS ``:empty::before``, que no es contenido real, es solo
    visual): el peritaje es SIEMPRE del humano, nunca autogenerado."""
    html = _html()
    m = re.search(r'<p id="campoPericial"[^>]*></p>', html)
    assert m, (
        "el campo pericial debe estar vacío en el HTML (</p> inmediato tras "
        "la apertura); si tiene contenido entre las etiquetas, alguien está "
        "prellenando la lectura pericial")


def test_campo_pericial_nunca_se_rellena_por_codigo_con_texto_generado():
    """Ningún punto del script asigna textContent/innerHTML al campo
    pericial: solo el propio usuario lo escribe (edición directa del
    contenteditable), nunca una función del sistema."""
    html = _html()
    assert "campoPericial').textContent =" not in html
    assert "campoPericial').innerHTML =" not in html
    assert "campoPericial\").textContent =" not in html
    assert "campoPericial\").innerHTML =" not in html


# ── Componente 12: sin volcado de datos crudos visible en pantalla ────────

def test_no_hay_json_stringify_ni_bloques_pre_de_datos_crudos():
    html = _html()
    assert "JSON.stringify" not in html
    assert "<pre" not in html
    assert "<code" not in html
