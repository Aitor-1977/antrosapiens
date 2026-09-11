"""Corrección aprobada por el operador (2026-09-11): IDENTIDAD ≠ RELACIÓN/
CONTEXTO. `evaluar_relevancia` descartaba por MOTIVO_GIGANTE cualquier
titular que mencionara un gigante EN CUALQUIER PARTE del texto, sin
distinguir si el gigante era la organización identificada o solo aparecía
por alianza, competencia, financiamiento, ecosistema o adquisición junto a
una startup real ya identificada por `detectar_empresa()`.

El Motor A identifica y cura organizaciones; no confunde la presencia de un
corporativo en el contexto con la identidad corporativa del prospecto.
"""
from hd_scraper.relevance import (
    GIGANTES,
    MOTIVO_GIGANTE,
    detectar_empresa,
    evaluar_relevancia,
)
from hd_scraper.signals import detectar_keywords


def _evaluar(titulo, organizacion):
    """Reproduce el llamado real: detectar_empresa() ya identificó la
    organización antes de invocar evaluar_relevancia."""
    kws = detectar_keywords(titulo)
    return evaluar_relevancia(titulo, kws, bool(organizacion),
                               exigir_evento=False, organizacion=organizacion)


# ── Los 4 casos reales aprobados: startup real + gigante por relación/contexto ──

def test_startup_conserva_alianza_con_gigante():
    titulo = "Fintual firma alianza con Oracle para modernizar su plataforma de inversión"
    org = detectar_empresa(titulo)
    assert org == "Fintual"
    ok, motivo = _evaluar(titulo, org)
    assert ok and motivo == ""


def test_startup_conserva_competencia_con_gigantes():
    titulo = "Cobre compite contra Google y Apple en el mercado de pagos digitales"
    org = detectar_empresa(titulo)
    assert org == "Cobre"
    ok, motivo = _evaluar(titulo, org)
    assert ok and motivo == ""


def test_startup_conserva_financiamiento_ligado_a_gigante():
    titulo = "Mundi recibe financiamiento de un fondo respaldado por Amazon"
    org = detectar_empresa(titulo)
    assert org == "Mundi"
    ok, motivo = _evaluar(titulo, org)
    assert ok and motivo == ""


def test_startup_conserva_ecosistema_de_gigante():
    titulo = "Simetrik, la startup colombiana, opera dentro del ecosistema de Salesforce"
    org = detectar_empresa(titulo)
    assert org == "Simetrik"
    ok, motivo = _evaluar(titulo, org)
    assert ok and motivo == ""


# ── Control: la organización identificada ES el gigante -> sigue descartándose ──

def test_gigante_real_sigue_descartado_cuando_es_la_organizacion_identificada():
    titulo = "Oracle despide a 21 mil empleados citando eficiencias por automatización"
    org = detectar_empresa(titulo)
    assert org == "Oracle"
    ok, motivo = _evaluar(titulo, org)
    assert not ok and motivo == MOTIVO_GIGANTE


def test_gigante_real_descartado_con_otro_ejemplo():
    # Sin marcador geográfico ajeno a LATAM (R2 correría antes que R5 y
    # tapiaría lo que este test quiere aislar).
    titulo = "Google despide a miles de empleados en su división de nube"
    org = detectar_empresa(titulo)
    assert org == "Google"
    ok, motivo = _evaluar(titulo, org)
    assert not ok and motivo == MOTIVO_GIGANTE


# ── No amplía el alcance: GIGANTES, reclasificaciones y comportamiento previo ──

def test_gigantes_no_se_modifico():
    esperados = {"google", "amazon", "oracle", "apple", "salesforce", "anthropic"}
    assert esperados.issubset(set(GIGANTES))


def test_sin_organizacion_preserva_el_comportamiento_anterior_por_compatibilidad():
    """Un llamador que no pase `organizacion` (parámetro nuevo, opcional)
    conserva exactamente el comportamiento previo: revisa el titular
    completo. Ningún call site debería quedar así hoy, pero la función no
    debe romperse si alguno lo hiciera."""
    titulo = "Wendy's abre su primera sucursal en Jalisco"
    ok, motivo = evaluar_relevancia(titulo, [], True, exigir_evento=False)
    assert not ok and motivo == MOTIVO_GIGANTE
