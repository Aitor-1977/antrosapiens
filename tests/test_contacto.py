"""Rutas de contacto (hipótesis determinista, sin verificación)."""
from hd_scraper.contacto import dominio_de, patrones_email, rutas_contacto


def test_dominio_de_varias_formas():
    assert dominio_de("https://www.kaszek.com/portafolio") == "kaszek.com"
    assert dominio_de("kaszek.com") == "kaszek.com"
    assert dominio_de("http://konfio.mx") == "konfio.mx"
    assert dominio_de("") == ""
    assert dominio_de("no-es-url") == ""


def test_patrones_genericos_sin_nombre():
    e = patrones_email("konfio.mx")
    assert "contacto@konfio.mx" in e and "ventas@konfio.mx" in e
    assert all("@konfio.mx" in x for x in e)


def test_patrones_con_nombre_decisor_van_primero():
    e = patrones_email("konfio.mx", "María López")
    assert e[0] == "maria.lopez@konfio.mx"
    assert "mlopez@konfio.mx" in e and "maria@konfio.mx" in e
    # Sin duplicados.
    assert len(e) == len(set(e))


def test_rutas_contacto_marca_no_verificado():
    r = rutas_contacto("https://konfio.mx", "Juan Pérez")
    assert r["dominio"] == "konfio.mx"
    assert r["verificado"] is False
    assert r["email_sugerido"] == "juan.perez@konfio.mx"
    assert r["emails_candidatos"]


def test_rutas_contacto_sin_dominio_valido():
    r = rutas_contacto("", "Juan Pérez")
    assert r["dominio"] == "" and r["emails_candidatos"] == []
