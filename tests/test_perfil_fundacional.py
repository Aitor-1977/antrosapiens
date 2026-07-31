"""Tests del extractor de Perfil Fundacional (fuentes orgánicas, cero prensa).

Validan la lógica de extracción de forma determinista (sin red real): la escala
obligatoria, el año de fundación, el rastreo del sitio propio con un transporte
simulado, y la persistencia de ``escala`` en ``prospectos``.
"""
import httpx

from hd_scraper import perfil_fundacional as pf
from hd_scraper.prospectos import nuevo_prospecto, upsert_prospecto


# --- Escala/tamaño (parámetro obligatorio) --------------------------------

def test_escala_rango_explicito():
    assert pf.escala_desde_texto("Un equipo de 51-200 empleados en la región.") == "51-200"
    assert pf.escala_desde_texto("11-50 colaboradores") == "11-50"


def test_escala_numero_simple():
    assert pf.escala_desde_texto("Somos 40 personas apasionadas.") == "11-50"
    assert pf.escala_desde_texto("Contamos con 120 empleados.") == "51-200"
    assert pf.escala_desde_texto("Más de 1200 colaboradores en LatAm.") == "501+"


def test_escala_indeterminada_sin_dato():
    # Sin mención numérica de personas → nunca se infiere: 'indeterminada'.
    assert pf.escala_desde_texto("Transformamos la banca de la región.") == pf.ESCALA_INDETERMINADA
    assert pf.escala_desde_texto("") == pf.ESCALA_INDETERMINADA


def test_escala_es_obligatoria_en_el_perfil():
    p = pf.PerfilFundacional(empresa="ACME")
    assert p.escala == pf.ESCALA_INDETERMINADA  # siempre presente


# --- Año de fundación ------------------------------------------------------

def test_anio_fundacion():
    assert pf.anio_fundacion_desde_texto("Fundada en 2016 en la Ciudad de México.") == "2016"
    assert pf.anio_fundacion_desde_texto("Founded 2009, we build tools.") == "2009"
    assert pf.anio_fundacion_desde_texto("Sin fecha declarada.") is None
    # Rechaza años imposibles (no hay palabra clave que los valide como fundación).
    assert pf.anio_fundacion_desde_texto("Ganamos 3000 clientes.") is None


# --- Extracción pura desde HTML -------------------------------------------

def test_extraer_perfil_desde_html():
    html = (
        "<html><head><title>Nosotros</title></head><body>"
        "<script>var x=1;</script>"
        "<h1>Quiénes somos</h1>"
        "<p>Fundada en 2018. Somos un equipo de 85 empleados en Bogotá.</p>"
        "</body></html>"
    )
    perfil = pf.extraer_perfil(html, "https://acme.co/nosotros", "Acme")
    assert perfil.escala == "51-200"
    assert perfil.anio_fundacion == "2018"
    assert perfil.url_perfil == "https://acme.co/nosotros"
    assert "empleados" in perfil.discurso_corporativo
    assert "var x" not in perfil.discurso_corporativo  # el script no entra


def test_a_thick_incluye_escala_y_perfil():
    thick = pf.PerfilFundacional(empresa="Acme", escala="51-200").a_thick()
    assert thick["escala"] == "51-200"
    assert thick["tipo_discurso"] == "perfil"
    assert thick["fuente_discurso"] == "sitio_oficial"


# --- Rastreo del sitio PROPIO (red simulada, cero prensa) -----------------

def _client_simulado(mapa: dict[str, str]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        html = mapa.get(request.url.path)
        if html is None:
            return httpx.Response(404)
        return httpx.Response(200, text=html)
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_construir_perfil_desde_sitio_propio():
    about = ("<html><body><h1>Nosotros</h1>"
             "<p>Fundada en 2016. Somos un equipo de 120 empleados en México.</p>"
             "</body></html>")
    client = _client_simulado({"/": "<html><body>Home</body></html>", "/nosotros": about})
    perfil = pf.construir_perfil("Nubank", "nubank.com.mx", client=client)
    assert perfil.escala == "51-200"
    assert perfil.anio_fundacion == "2016"
    assert perfil.url_perfil.endswith("nubank.com.mx")


def test_construir_perfil_sin_datos_es_indeterminada():
    client = _client_simulado({"/": "<html><body>Bienvenido</body></html>"})
    perfil = pf.construir_perfil("Opaca SA", "opaca.example", client=client)
    assert perfil.escala == pf.ESCALA_INDETERMINADA


# --- Integración: la escala se persiste en prospectos ---------------------

def test_upsert_persiste_escala(db):
    perfil = pf.PerfilFundacional(
        empresa="Nubank", escala="51-200", anio_fundacion="2016",
        discurso_corporativo="Fundada en 2016. 120 empleados.",
        url_perfil="https://nubank.com.mx/nosotros",
    )
    p = nuevo_prospecto("Nubank", "Startup", **perfil.a_thick())
    res = upsert_prospecto(db, p)
    assert res["ok"] and res["accion"] == "insertado"

    row = db.fetch_one("SELECT escala FROM prospectos WHERE nombre='Nubank'")
    assert row["escala"] == "51-200"
