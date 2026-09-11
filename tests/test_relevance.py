"""Captura Inteligente: filtro de relevancia y calidad (objetivos, sin IA)."""
from hd_scraper.relevance import (
    CALIDAD_ALTA,
    CALIDAD_BAJA,
    CALIDAD_MEDIA,
    MOTIVO_OPINION,
    MOTIVO_SIN_EMPRESA,
    MOTIVO_SIN_EVENTO,
    MOTIVO_SUPERFICIAL,
    calcular_calidad,
    detectar_empresa,
    es_opinion,
    evaluar_relevancia,
)


# ── detección de empresa (nombre propio) ─────────────────────────────────────

def test_detectar_empresa_nombre_al_inicio():
    assert detectar_empresa("Nubank anuncia nueva ronda de inversión") == "Nubank"


def test_detectar_empresa_ignora_articulo_inicial_y_sector():
    # "La" es artículo, "fintech" es genérico -> la empresa es "Clara".
    assert detectar_empresa("La fintech Clara levanta capital serie B") == "Clara"


def test_detectar_empresa_acepta_siglas():
    assert detectar_empresa("BBVA lanza un nuevo producto") == "BBVA"


def test_detectar_empresa_sin_nombre_propio():
    # Tendencia genérica sin empresa nombrada.
    assert detectar_empresa("las startups enfrentan un año difícil") is None


# ── Incidente real 2026-09-10: siglas de cargo/regulador detectadas como
# empresa, con ICP 79-99 en INDAGAR (CEO, CNBV) ──────────────────────────────

def test_detectar_empresa_ignora_cargo_ceo():
    # Antes: "CEO" (sigla por forma) se detectaba como la organización.
    assert detectar_empresa(
        "CEO de Kavak regresa a dirigir la startup en México tras despido "
        "de country manager"
    ) == "Kavak"


def test_detectar_empresa_ignora_regulador_cnbv():
    # Antes: "CNBV" (el regulador bancario de México) se detectaba como
    # empresa, no la fintech real mencionada (Albo).
    assert detectar_empresa(
        "CNBV multa a la fintech Albo con 9 mdp por permitir intercambio "
        "de criptomonedas"
    ) == "Albo"


def test_detectar_empresa_ignora_otros_cargos_y_reguladores():
    assert detectar_empresa("CFO renuncia tras resultados del trimestre") is None
    assert detectar_empresa("SAT investiga a empresas de facturación") is None
    assert detectar_empresa("IMSS reporta aumento en afiliaciones") is None


def test_detectar_empresa_ignora_palabra_comun_lana():
    # Antes: "Lana" (palabra común, no nombre propio de empresa) se detectaba.
    assert detectar_empresa("Lana es una forma común de decir dinero") is None


def test_detectar_empresa_ignora_plural_nuevas():
    # _STOP_CAP ya tenía "nueva"/"nuevo" pero no el plural.
    assert detectar_empresa("Nuevas reglas afectan al sector fintech") is None


# ── marcadores de opinión / tendencia / listículo ────────────────────────────

def test_es_opinion_detecta_marcadores():
    assert es_opinion("Opinión: por qué las fintech fracasan")
    assert es_opinion("El futuro de la banca digital en 2027")
    assert es_opinion("5 claves para entender el churn")
    assert es_opinion("Los mejores bancos digitales de la región")


def test_es_opinion_no_marca_noticia_de_evento():
    assert not es_opinion("Nubank adquiere una startup de pagos")


# ── filtro de relevancia ─────────────────────────────────────────────────────

def test_relevancia_conserva_evento_con_empresa():
    ok, motivo = evaluar_relevancia(
        "Nubank adquiere una fintech de pagos", ["adquisicion"], empresa_identificada=True)
    assert ok and motivo == ""


def test_relevancia_descarta_opinion():
    ok, motivo = evaluar_relevancia(
        "Opinión: el futuro de Nubank", ["adquisicion"], empresa_identificada=True)
    assert not ok and motivo == MOTIVO_OPINION


def test_relevancia_descarta_sin_empresa():
    ok, motivo = evaluar_relevancia(
        "Las startups enfrentan más despidos", ["reduccion_personal"],
        empresa_identificada=False)
    assert not ok and motivo == MOTIVO_SIN_EMPRESA


def test_relevancia_descarta_sin_evento():
    ok, motivo = evaluar_relevancia(
        "Nubank anuncia cambios internos menores", [], empresa_identificada=True)
    assert not ok and motivo == MOTIVO_SIN_EVENTO


def test_relevancia_descarta_evento_superficial():
    ok, motivo = evaluar_relevancia(
        "Nubank celebra su aniversario", ["lanzamiento"], empresa_identificada=True)
    assert not ok and motivo == MOTIVO_SUPERFICIAL


def test_relevancia_conserva_empresa_sin_evento_en_ecosistema():
    # Descubrimiento por ecosistema (exigir_evento=False): una empresa real que
    # pasa geo/no-empresa/opinión SE CONSERVA aunque no traiga señal fuerte.
    ok, motivo = evaluar_relevancia(
        "Klar presenta su nueva tarjeta en México", [], empresa_identificada=True,
        exigir_evento=False)
    assert ok and motivo == ""
    # Pero los otros filtros SIGUEN activos aun sin exigir evento.
    no_ok, _ = evaluar_relevancia(
        "El Gobierno de España lanza un plan", [], empresa_identificada=True,
        exigir_evento=False)
    assert not no_ok


def test_relevancia_descarta_espana_y_no_empresa():
    from hd_scraper.relevance import MOTIVO_NO_EMPRESA, MOTIVO_NO_LATAM
    # Geografía fuera de LATAM (España / Girona / Castilla).
    ok, m = evaluar_relevancia(
        "El Gobierno de Castilla-La Mancha impulsa la innovación", ["expansion"], True)
    assert not ok and m in (MOTIVO_NO_LATAM, MOTIVO_NO_EMPRESA)
    # Premios (no es empresa).
    ok2, m2 = evaluar_relevancia(
        "Los Premios Princesa de Girona reconocen seis proyectos", ["lanzamiento"], True)
    assert not ok2
    # Reporte de mercado "…AÑO:".
    ok3, m3 = evaluar_relevancia(
        "Venture Capital LATAM 2025: la inversión cae 30%", ["ronda_inversion"], True)
    assert not ok3 and m3 == MOTIVO_NO_EMPRESA
    # Análisis "de cada 10" sin empresa concreta.
    ok4, _ = evaluar_relevancia(
        "Siete de cada 10 startups no están listas para escalar", ["expansion"], True)
    assert not ok4


def test_relevancia_conserva_empresa_mexicana_real():
    ok, motivo = evaluar_relevancia(
        "Konfío levanta una ronda serie C en México", ["ronda_inversion"], True)
    assert ok and motivo == ""


def test_relevancia_descarta_gigantes_geo_y_sucesos():
    from hd_scraper.relevance import (
        MOTIVO_GIGANTE, MOTIVO_NO_EMPRESA, MOTIVO_NO_LATAM,
    )
    # Marca gigante (no es ICP de HD), aunque traiga un evento (multa=regulación).
    ok, m = evaluar_relevancia(
        "Google investigado en Suiza: multa de 4.000M por Android", ["regulacion"], True)
    assert not ok and m in (MOTIVO_NO_LATAM, MOTIVO_GIGANTE)
    # Wendy's (comida rápida global): fuera.
    ok2, m2 = evaluar_relevancia(
        "Wendy's abre su primera sucursal en Jalisco", ["expansion"], True)
    assert not ok2 and m2 == MOTIVO_GIGANTE
    # Nota roja / suceso: no es una empresa.
    ok3, m3 = evaluar_relevancia(
        "Muerte de Marie Claire González: violencia de género", ["reduccion_personal"], True)
    assert not ok3 and m3 == MOTIVO_NO_EMPRESA


def test_relevancia_conserva_startup_latam_pese_a_filtros_nuevos():
    # Una startup real LATAM con evento sigue pasando (no la afectan los filtros).
    ok, m = evaluar_relevancia(
        "Clip lanza una nueva terminal de pago en México", ["lanzamiento"], True)
    assert ok and m == ""


def test_relevancia_descarta_ruido_mediatico():
    from hd_scraper.relevance import MOTIVO_RUIDO
    for titulo, kw in (
        ("El futbol define al campeón de la Liga MX", ["lanzamiento"]),
        ("Farándula: la cantante estrena romance", ["lanzamiento"]),
        ("Ola de calor golpea al norte del país", ["expansion"]),
        ("Tienda inaugura nueva sucursal en el centro", ["expansion"]),
        ("Promoción 2x1 por tiempo limitado", ["lanzamiento"]),
    ):
        ok, m = evaluar_relevancia(titulo, kw, True)
        assert not ok and m == MOTIVO_RUIDO, titulo


def test_relevancia_descarta_eventos_superficiales():
    for titulo, kw in (
        ("Rappi patrocina el festival de la ciudad", ["alianza"]),
        ("Kavak celebra su aniversario con música", ["lanzamiento"]),
        ("Bitso participa en la conferencia de blockchain", ["alianza"]),
        ("Nubank obtiene certificación Great Place to Work", ["lanzamiento"]),
        ("Mercado Libre sube en bolsa tras reporte trimestral", ["crecimiento"]),
    ):
        ok, m = evaluar_relevancia(titulo, kw, True)
        assert not ok and m == MOTIVO_SUPERFICIAL, titulo


def test_relevancia_conserva_dolor_aunque_superficial_ausente():
    ok, m = evaluar_relevancia(
        "Kavak despide al 30% de su plantilla en reestructuración",
        ["reduccion_personal"], True)
    assert ok and m == ""


# ── calidad de captura (informativa) ─────────────────────────────────────────

def test_calidad_alta_media_baja():
    assert calcular_calidad(True, True, True) == CALIDAD_ALTA
    assert calcular_calidad(True, True, False) == CALIDAD_MEDIA
    assert calcular_calidad(True, False, False) == CALIDAD_BAJA
    assert calcular_calidad(False, False, False) == CALIDAD_BAJA


def test_calidad_duplicado_fuerza_baja():
    assert calcular_calidad(True, True, True, sin_duplicado=False) == CALIDAD_BAJA


# ── Regresión: detectar_empresa() más conservador (auditoría 2026-09-11,     ─
# hallazgo ALTO) — un verbo o un nombre de persona al inicio del titular NO
# debe promoverse a organización. Casos reales del reporte del operador.

def test_detectar_empresa_ignora_verbo_de_titular_invertido():
    # "Cierra Konfío tercera adquisición..." (orden invertido verbo-sujeto,
    # común en titulares en español): "Cierra" es un verbo conjugado, no un
    # nombre propio. La organización real ("Konfío") sigue siendo detectable.
    assert detectar_empresa(
        "Cierra Konfío tercera adquisición; compra Sr. Pago"
    ) == "Konfío"


def test_detectar_empresa_ignora_nombre_de_persona_tras_cargo():
    # "Nu México tendrá nuevo CEO: Armando Herrera" — "Armando" (nombre de
    # pila) y "Herrera" (su apellido, adyacente) no son una organización.
    # Sin otro candidato en el titular, el resultado correcto es None: no se
    # inventa una organización a partir de un nombre de persona.
    assert detectar_empresa(
        "Nu México tendrá nuevo CEO: Armando Herrera"
    ) is None


def test_detectar_empresa_ignora_nombre_de_pila_seguido_de_apellido():
    # Control aislado del mecanismo (sin el ruido de "Nu"/"CEO" del caso de
    # arriba): un nombre de pila conocido, seguido de otro token capitalizado
    # contiguo (su apellido), no debe producir ninguno de los dos como
    # organización. La organización real, más adelante, sí se detecta.
    assert detectar_empresa(
        "Ana Ríos, CEO de Kavak, anuncia una reestructuración"
    ) == "Kavak"


def test_detectar_empresa_ignora_grupo_y_galeria_genericos():
    assert detectar_empresa("Grupo anuncia una alianza estratégica en la región") is None
    assert detectar_empresa("Galería presenta una nueva muestra de arte digital") is None
    # Con nombre propio pegado, "Grupo"/"Galería" siguen actuando como
    # genéricos de sector (mismo patrón que "Banco Santander" -> "Santander")
    # y el token real de la organización sigue siendo detectable.
    assert detectar_empresa("Grupo Bimbo anuncia recorte de personal") == "Bimbo"


def test_detectar_empresa_ignora_sigla_ia_ya_protegida():
    # "IA" ya estaba en _SIGLAS_NO_EMPRESA antes de esta corrección: control
    # de no regresión, no un caso nuevo.
    assert detectar_empresa("IA transforma la forma de invertir en la región") is None


def test_detectar_empresa_caso_positivo_no_se_ve_afectado():
    # La organización real sigue siendo el primer candidato cuando el
    # titular no tiene ningún verbo/nombre de persona que filtrar antes.
    assert detectar_empresa("Nubank anuncia nueva ronda de inversión") == "Nubank"


def test_detectar_empresa_organizacion_ausente_es_none_no_inventada():
    # Titular sin ninguna organización nombrable: la ausencia se representa
    # como None, nunca como una entidad inventada por descarte.
    assert detectar_empresa(
        "Juan Pérez fue nombrado nuevo director general de la compañía"
    ) is None
