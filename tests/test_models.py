from hd_scraper.db.models import (
    calcular_hash_dedup,
    clave_contenido,
    hash_contenido,
    normalizar_empresa,
    normalizar_titulo,
    normalizar_url,
)


def test_normalizar_url_quita_query_fragmento_y_slash():
    a = normalizar_url("https://News.Example.com/nota/123/?utm=x#frag")
    b = normalizar_url("https://news.example.com/nota/123")
    assert a == b == "https://news.example.com/nota/123"


def test_normalizar_empresa_colapsa_espacios_y_baja_caso():
    assert normalizar_empresa("  Nu   Bank ") == "nu bank"


def test_hash_dedup_estable_y_sensible_a_empresa_y_url():
    h1 = calcular_hash_dedup("Nubank", "https://x.com/a?b=1")
    h2 = calcular_hash_dedup("nubank", "https://x.com/a")  # normaliza igual
    assert h1 == h2
    h3 = calcular_hash_dedup("Otra", "https://x.com/a")
    assert h1 != h3


# ── Dedup robusto de contenido (Captura Inteligente) ─────────────────────────

def test_normalizar_titulo_quita_medio_acentos_y_puntuacion():
    a = normalizar_titulo("Nubank anuncia ronda de inversión - Bloomberg Línea")
    b = normalizar_titulo("Nubank anuncia ronda de inversion")
    assert a == b == "nubank anuncia ronda de inversion"


def test_hash_contenido_colapsa_mismo_articulo_distinta_fuente():
    h1 = hash_contenido("Nubank adquiere fintech - Medio A")
    h2 = hash_contenido("Nubank adquiere fintech - Medio B")
    assert h1 and h1 == h2


def test_clave_contenido_prioriza_canonica_luego_url():
    # 1) Canónica declarada por la fuente gana sobre la URL cruda.
    k_can = clave_contenido("https://news.google.com/rss/articles/XYZ?oc=5",
                            meta={"canonical": "https://nubank.com.br/nota/1?utm_source=x"})
    assert k_can == "url:https://nubank.com.br/nota/1"
    # 2) Sin canónica: URL normalizada (sin UTM ni fragmento).
    k_url = clave_contenido("https://medio.com/n/2/?utm_medium=rss#x")
    assert k_url == "url:https://medio.com/n/2"
    # 3) Sin URL: hash del título como respaldo.
    k_txt = clave_contenido("", titulo="Nubank adquiere fintech")
    assert k_txt.startswith("txt:")
