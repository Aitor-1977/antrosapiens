"""Validación y confirmación de correos (estructura, determinista, sin red)."""
from hd_scraper.emails import (
    email_utilizable,
    emails_validos,
    confirmar_por_triangulacion,
    confirmar_por_dominio,
    motivo_rechazo,
    normalizar_email,
    resumen_emails,
)


# ── normalización ────────────────────────────────────────────────────────────

def test_normaliza_minusculas_espacios_y_bordes():
    assert normalizar_email("  Juan.Perez@Konfio.MX  ") == "juan.perez@konfio.mx"
    assert normalizar_email("<juan@konfio.mx>") == "juan@konfio.mx"


# ── validación de forma ──────────────────────────────────────────────────────

def test_acepta_correos_corporativos_comunes():
    assert email_utilizable("juan.perez@konfio.mx")
    assert email_utilizable("jperez@kaszek.com")
    assert email_utilizable("ana@mercadolibre.com.co")
    assert email_utilizable("j+finanzas@cova.com.ar")


def test_rechaza_placeholder_y_tld_reservados():
    assert not email_utilizable("juan@example.com")
    assert not email_utilizable("juan@test.com")
    assert not email_utilizable("juan@dominio.local")
    assert motivo_rechazo("juan@example.com") == "dominio de ejemplo/placeholder"


def test_rechaza_buzones_genericos():
    assert not email_utilizable("info@konfio.mx")
    assert not email_utilizable("contacto@konfio.mx")
    assert not email_utilizable("ventas@konfio.mx")
    assert motivo_rechazo("info@konfio.mx") == "buzón genérico (no de decisión)"


def test_rechaza_sintaxis_rota():
    assert not email_utilizable("juan.konfio.mx")
    assert not email_utilizable("juan@")
    assert not email_utilizable("juan@konfio")
    assert not email_utilizable("j..uan@konfio.mx")
    assert not email_utilizable(".juan@konfio.mx")


def test_rechaza_ruido_de_imagen():
    assert not email_utilizable("logo@cdn.com.png")
    assert motivo_rechazo("logo@cdn.com.png") == "parece una URL de imagen, no un correo"


def test_emails_validos_deduplica_y_limpia():
    lista = ["juan.perez@konfio.mx", "JUAN.PEREZ@konfio.mx", "info@konfio.mx",
             "basura", "ana@kaszek.com"]
    # Orden de aparición, normalizado y sin duplicados ni genéricos.
    assert emails_validos(lista) == ["juan.perez@konfio.mx", "ana@kaszek.com"]


# ── confirmación por triangulación (≥2 fuentes) ──────────────────────────────

def test_confirma_solo_lo_que_aparece_en_dos_fuentes():
    fuentes = {
        "https://medio1.com/a": ["juan.perez@konfio.mx", "info@konfio.mx"],
        "https://medio2.com/b": ["Juan.Perez@konfio.mx"],
        "https://medio3.com/c": ["ana@kaszek.com"],
    }
    assert confirmar_por_triangulacion(fuentes) == {"juan.perez@konfio.mx"}


def test_no_confirma_una_sola_mencion_ni_genericos():
    fuentes = {"https://m.com/a": ["ana@kaszek.com"], "https://m.com/b": ["ana@kaszek.com"]}
    assert confirmar_por_triangulacion({"https://m.com/a": ["info@kaszek.com"]}) == set()
    assert confirmar_por_triangulacion(fuentes) == {"ana@kaszek.com"}


def test_fuente_vacia_o_none_no_rompe():
    assert confirmar_por_triangulacion({}) == set()
    assert confirmar_por_triangulacion(None) == set()


# ── confirmación por dominio oficial ─────────────────────────────────────────

def test_dominio_coincide_solo_con_dominio_oficial():
    assert confirmar_por_dominio("juan.perez@konfio.mx", "https://www.konfio.mx")
    assert not confirmar_por_dominio("juan.perez@otro.com", "konfio.mx")
    assert not confirmar_por_dominio("info@konfio.mx", "konfio.mx")  # genérico
    assert not confirmar_por_dominio("juan@konfio.mx", "")


# ── resumen legible ──────────────────────────────────────────────────────────

def test_resumen_separa_validos_y_rechazados():
    r = resumen_emails(["juan.perez@konfio.mx", "info@konfio.mx", "roto"])
    assert r["vistos"] == 3
    assert r["validos"] == ["juan.perez@konfio.mx"]
    assert any(m[0] == "info@konfio.mx" for m in r["rechazados"])
