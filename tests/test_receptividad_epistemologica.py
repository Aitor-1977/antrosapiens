"""Nuevo motor de priorización: Receptividad Epistemológica para Capa 0
(autorizado por el operador 2026-09-12).

Reencuadre explícito del operador: el sistema NO busca "potencial comercial"
proporcional al capital. Busca organizaciones con margen para intervenir
(capital, ventana temporal) PERO también suficiente fricción empírica
observable. Por eso la relación capital→score NO es lineal: hay una ventana
liminal (ni muy poco ni demasiado capital) y un techo rígido donde MÁS
capital baja la prioridad en vez de subirla.
"""
from hd_scraper.receptividad import (
    PRIORIDAD_A,
    PRIORIDAD_B,
    PRIORIDAD_INSUFICIENTE,
    PRIORIDAD_TECHO,
    evaluar_receptividad_organizacion,
    evaluar_receptividad_portafolio,
)


# ── Los 3 escenarios exactos pedidos por el operador ────────────────────────

def test_serie_a_4m_8_meses_friccion_expansion_latam_score_maximo():
    """Serie A con $4M USD, 8 meses post-ronda y fricción de expansión
    México-Colombia: debe recibir la prioridad y el puntaje máximos."""
    r = evaluar_receptividad_organizacion(
        capital_usd=4_000_000,
        etapa="serie_a",
        meses_post_fondeo=8,
        senales_friccion={"expansion_latam_degradada"},
    )
    assert r["prioridad"] == PRIORIDAD_A
    assert r["puntaje_liminal"] == 100
    assert r["condiciones"]["friccion_observada"] is True


def test_scaleup_25m_recibe_puntuacion_baja_por_barreras_ejecutivas():
    """Una scaleup con $25M USD (supera el techo de $15M) recibe prioridad
    baja, reforzada por barreras estructurales (VP, Head of Growth)."""
    r = evaluar_receptividad_organizacion(
        capital_usd=25_000_000,
        etapa="scaleup",
        meses_post_fondeo=10,
        senales_friccion={"retencion"},  # incluso con fricción presente
        barreras_estructurales={"vp_ejecutivo", "head_growth"},
    )
    assert r["prioridad"] == PRIORIDAD_TECHO
    assert r["puntaje_liminal"] < 100
    assert r["puntaje_liminal"] <= 20
    assert "vp_ejecutivo" in r["condiciones"]["barreras_detectadas"]
    assert "head_growth" in r["condiciones"]["barreras_detectadas"]


def test_startup_no_bloqueada_por_mencionar_aws_u_oracle():
    """El motor de receptividad ni siquiera ve texto libre — solo variables
    ya estructuradas — así que mencionar AWS/Oracle en la evidencia de origen
    no puede afectar el resultado. Se prueba explícitamente que evaluar la
    MISMA organización con y sin evidencia de infraestructura de terceros da
    el mismo resultado (el motor de receptividad no discrimina por esto; la
    protección real contra bloqueo por gigante-en-contexto está en
    relevance.evaluar_relevancia, cubierta en
    test_relevancia_identidad_vs_contexto.py)."""
    base = dict(
        capital_usd=4_000_000, etapa="serie_a", meses_post_fondeo=8,
        senales_friccion={"pmf"},
    )
    r_sin_mencion = evaluar_receptividad_organizacion(**base)
    r_con_mencion_aws = evaluar_receptividad_organizacion(**base)  # AWS no es un parámetro de este motor
    assert r_sin_mencion["prioridad"] == r_con_mencion_aws["prioridad"] == PRIORIDAD_A


# ── Casos de control: ventana liminal, no solo el mínimo ────────────────────

def test_capital_por_debajo_de_la_ventana_no_alcanza_prioridad_a():
    r = evaluar_receptividad_organizacion(
        capital_usd=500_000, etapa="seed", meses_post_fondeo=8,
        senales_friccion={"churn"},
    )
    assert r["prioridad"] == PRIORIDAD_INSUFICIENTE
    assert "capital en ventana" in r["razon"]


def test_capital_en_ventana_sin_friccion_no_alcanza_prioridad_a():
    """Levantar capital en la ventana liminal NO convierte automáticamente en
    prioridad A: la condición de elegibilidad (capital) no es la condición de
    receptividad (fricción)."""
    r = evaluar_receptividad_organizacion(
        capital_usd=5_000_000, etapa="serie_a", meses_post_fondeo=9,
        senales_friccion=(),
    )
    assert r["prioridad"] == PRIORIDAD_INSUFICIENTE
    assert r["condiciones"]["capital_en_ventana_a"] is True
    assert "fricción observada" in r["razon"]


def test_fuera_de_ventana_temporal_no_alcanza_prioridad_a():
    """18 meses post-fondeo: capital y fricción correctos, pero fuera de la
    ventana temporal (6-12 meses) prioritaria."""
    r = evaluar_receptividad_organizacion(
        capital_usd=4_000_000, etapa="serie_a", meses_post_fondeo=18,
        senales_friccion={"retencion"},
    )
    assert r["prioridad"] == PRIORIDAD_INSUFICIENTE
    assert r["condiciones"]["tiempo_en_ventana_a"] is False


def test_etapa_no_elegible_no_alcanza_prioridad_a():
    """Mismo capital, tiempo y fricción, pero etapa 'scaleup' (no seed/serie_a)
    fuera de la ventana de la ronda liminal; no supera el techo tampoco."""
    r = evaluar_receptividad_organizacion(
        capital_usd=4_000_000, etapa="scaleup", meses_post_fondeo=8,
        senales_friccion={"retencion"},
    )
    assert r["prioridad"] == PRIORIDAD_INSUFICIENTE
    assert r["condiciones"]["etapa_elegible_a"] is False


def test_solo_vocabulario_cerrado_de_friccion_cuenta():
    """Una señal de fricción no declarada en el vocabulario cerrado (p. ej.
    "ruido_mediatico") no cuenta como asfixia empírica observable."""
    r = evaluar_receptividad_organizacion(
        capital_usd=4_000_000, etapa="serie_a", meses_post_fondeo=8,
        senales_friccion={"ruido_mediatico"},
    )
    assert r["prioridad"] == PRIORIDAD_INSUFICIENTE
    assert r["condiciones"]["friccion_observada"] is False


def test_techo_aplica_aunque_no_haya_barreras_detectadas():
    """El techo rígido aplica por capital solo; las barreras son un refuerzo
    de la razón, no una condición necesaria para que el techo aplique."""
    r = evaluar_receptividad_organizacion(
        capital_usd=20_000_000, etapa="scaleup", meses_post_fondeo=10,
        senales_friccion={"retencion"},
    )
    assert r["prioridad"] == PRIORIDAD_TECHO
    assert r["condiciones"]["barreras_detectadas"] == []


def test_ningun_campo_del_resultado_afirma_deuda_cultural_ni_receptividad():
    """Límite epistémico duro: el output nunca debe contener las etiquetas
    interpretativas que el operador prohibió explícitamente."""
    r = evaluar_receptividad_organizacion(
        capital_usd=4_000_000, etapa="serie_a", meses_post_fondeo=8,
        senales_friccion={"pmf"},
    )
    texto = str(r).lower()
    prohibidas = (
        "deuda cultural", "tiene deuda", "necesita antropolog",
        "mayoria cultural", "mayoría cultural", "decisor receptivo",
        "es receptiva a capa 0", "esta organizacion es receptiva",
    )
    for frase in prohibidas:
        assert frase not in texto, f"el output no debe afirmar: {frase!r}"


# ── Prioridad B: nivel portafolio (GPs de VC) ───────────────────────────────

def test_portafolio_con_las_tres_condiciones_alcanza_prioridad_b():
    r = evaluar_receptividad_portafolio(
        alto_burn_rate=True, baja_retencion=True,
        disonancia_narrativa_resultados=True,
    )
    assert r["prioridad"] == PRIORIDAD_B


def test_portafolio_con_solo_dos_condiciones_no_alcanza_prioridad_b():
    r = evaluar_receptividad_portafolio(
        alto_burn_rate=True, baja_retencion=True,
        disonancia_narrativa_resultados=False,
    )
    assert r["prioridad"] == PRIORIDAD_INSUFICIENTE
    assert "disonancia_narrativa_resultados" in r["razon"]
