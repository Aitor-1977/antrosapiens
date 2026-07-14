"""Descubrimiento: composición de consultas por categoría + tipo + vertical."""
from hd_scraper.discovery import TIPO_KEYWORDS, queries_para, region_clause


def test_queries_emite_una_por_variante():
    # El bucket de fricción "queja" tiene varias variantes -> varias consultas.
    qs = queries_para("Startup", "queja", vertical="fintech")
    textos = [t for t, _ in qs]
    assert len(textos) == len(set(textos))            # sin duplicados
    assert len(textos) == len(TIPO_KEYWORDS["queja"])  # una por variante (1 base)
    # Todas llevan la base del ecosistema y la vertical.
    assert all(t.startswith("startup fintech") for t in textos)
    # Y el tipo_evento se conserva (literal del contrato).
    assert all(tipo == "queja" for _, tipo in qs)


def test_queja_cubre_fricciones_ampliadas():
    variantes = " ".join(TIPO_KEYWORDS["queja"]).lower()
    for termino in ("pérdida de clientes", "cancelación", "demanda", "regulatorio",
                    "crecimiento", "reestructuración", "crisis", "cierre de operaciones"):
        assert termino in variantes


def test_region_clause_latam():
    c = region_clause("LATAM")
    assert c.startswith("(") and "México" in c and '"Costa Rica"' in c
