"""Cascada epistemológica y su persistencia idempotente (Entrega 2)."""
from hd_scraper.clasificacion_epistemologica import (
    TIPO_AUTODECLARACION,
    TIPO_CONTEXTUAL,
    TIPO_CORROBORANTE,
    TIPO_HUELLA_PRACTICA,
    _detectar_organizacion_mencionada,
    clasificar,
    detectar_dominio,
)
from hd_scraper.clasificacion_store import (
    buscar_expediente,
    clasificar_lote,
    obtener_o_crear_expediente,
)
from hd_scraper.db.models import ahora_iso


def _ev(cita, *, org="Acme", origen="prensa", medio="Prensa X",
        persona=None, cargo=None):
    return {
        "id": 1, "cita_textual": cita, "empresa_mencionada": org,
        "nombre_medio": medio, "origen_declaracion": origen,
        "persona_citada": persona, "cargo": cargo, "connector": "google_news",
    }


def _insertar(db, cita, *, org="Acme", origen="prensa", n=0,
              connector="google_news"):
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (cita, ahora_iso(), f"https://ejemplo.test/{n}", "Prensa X", org,
         "lanzamiento", origen, f"hash-{n}", connector, ahora_iso()))


# ── Cascada ────────────────────────────────────────────────────────────────

def test_maxima_autoridad_es_autodeclaracion():
    c = clasificar(_ev("Juan Pérez, CEO de Acme, anunció despidos"))
    assert c.tipo == TIPO_AUTODECLARACION
    assert c.enunciador_nombre == "Juan Pérez"
    assert c.enunciador_dominio == "retencion_talento"


def test_org_de_una_palabra_no_matchea_dentro_de_nombre_propio_mas_largo():
    """Causa raíz real del caso "Clara Brugada" (2026-08-28): antes,
    `_vinculado_a_org` usaba subcadena pura, así que empresa_mencionada
    "Clara" matcheaba dentro de "Clara Brugada" (alcaldesa de CDMX, una
    persona distinta) y vinculaba el cargo a la organización equivocada.
    Ahora exige palabra completa y descarta el caso en que el nombre de una
    sola palabra es solo el primer token de un nombre propio más largo. Aquí
    ni siquiera se llega a evaluar el gate de dominio: el cargo nunca queda
    vinculado a "Clara", así que `_dominio_bajo_autoridad` no se invoca."""
    c = clasificar(_ev(
        'Clara Brugada acompaña a la Presidenta Claudia Sheinbaum en el '
        'arranque de "Sí al Desarme, Sí a la Paz"; destaca reducción de '
        'homicidios en la Ciudad de México - CDMX',
        org="Clara", medio="CDMX"))
    assert c.tipo == TIPO_CONTEXTUAL


def test_org_de_una_palabra_si_matchea_como_mencion_autonoma():
    """Contraste con el test anterior: cuando "Clara" aparece como mención
    autónoma de la organización (no pegada a un apellido), sigue vinculando
    con normalidad — el fix no rompe el caso normal de nombres cortos."""
    c = clasificar(_ev(
        "Clara, la fintech, anunció una ronda de inversión de 50 millones "
        "de dólares liderada por su CEO", org="Clara"))
    assert c.tipo == TIPO_AUTODECLARACION
    assert c.enunciador_dominio == "finanzas"


def test_maxima_autoridad_sin_dominio_de_negocio_cae_a_contextual():
    """Regresión real (2026-08-28): 'Clara Brugada' (alcaldesa de CDMX) se
    clasificó como autodeclaración de la fintech 'Clara' porque el patrón de
    cargo 'presidenta' (referido a la Presidenta de México en el mismo
    titular) disparaba NIVEL_MAXIMA sin que el texto mencionara ningún
    dominio de negocio (DOMINIOS). Máxima autoridad da autoridad sobre
    cualquier dominio de NEGOCIO, no sobre cualquier tema."""
    c = clasificar(_ev(
        'Clara Brugada acompaña a la Presidenta Claudia Sheinbaum en el '
        'arranque de "Sí al Desarme, Sí a la Paz"; destaca reducción de '
        'homicidios en la Ciudad de México - CDMX',
        org="Clara", medio="CDMX"))
    assert c.tipo == TIPO_CONTEXTUAL


def test_cargo_funcional_dentro_de_su_dominio_es_autodeclaracion():
    c = clasificar(_ev("María López, CFO de Acme, habló de la ronda de inversión"))
    assert c.tipo == TIPO_AUTODECLARACION
    assert c.enunciador_dominio == "finanzas"


def test_cargo_funcional_fuera_de_su_dominio_cae_a_contextual():
    """La REGLA DURA prohíbe conceder autoridad fuera del área del cargo."""
    c = clasificar(_ev("María López, CFO de Acme, habló de la rotación de personal"))
    assert c.tipo == TIPO_CONTEXTUAL


def test_posicion_de_tension_con_friccion_es_corroborante():
    c = clasificar(_ev("Extrabajadores de Acme denuncian despidos masivos"))
    assert c.tipo == TIPO_CORROBORANTE


def test_posicion_de_tension_sin_friccion_no_es_corroborante():
    c = clasificar(_ev("Empleados de Acme reciben un bono anual"))
    assert c.tipo == TIPO_CONTEXTUAL


def test_acto_publicado_por_la_organizacion_es_huella_practica():
    c = clasificar(_ev("Acme busca ingeniero de datos en Ciudad de México",
                       origen="operador"))
    assert c.tipo == TIPO_HUELLA_PRACTICA
    assert c.enunciador_nombre is None


def test_narracion_de_prensa_sin_persona_es_contextual():
    c = clasificar(_ev("Acme amplía su red de sucursales en el país"))
    assert c.tipo == TIPO_CONTEXTUAL


def test_cargo_de_otra_organizacion_no_es_autodeclaracion():
    """Un CEO ajeno hablando de la organización no la autodeclara."""
    c = clasificar(_ev("El CEO de Beta, Luis Ruiz, criticó a Acme"),
                   orgs_conocidas=("Acme", "Beta"))
    assert c.tipo == TIPO_CONTEXTUAL


# ── Autoidentificación situada en primera persona (ampliación 2026-08-27) ──

def test_autoidentificacion_maxima_con_situacion_concreta_es_autodeclaracion():
    c = clasificar(_ev(
        "Soy fundadora de mi startup y cometí el error de contratar "
        "demasiado rápido sin cultura clara.", org='"cometí el error de" startup'))
    assert c.tipo == TIPO_AUTODECLARACION


def test_autoidentificacion_sin_situacion_concreta_no_basta():
    """Primera persona SOLA, sin marcador de situación concreta, no admite."""
    c = clasificar(_ev("Soy fundador y creo que las startups son difíciles."))
    assert c.tipo == TIPO_CONTEXTUAL


def test_autoidentificacion_en_listiculo_sigue_rechazada():
    """La autoidentificación no rescata contenido marcado como opinión/listículo."""
    c = clasificar(_ev(
        "Como fundador, aquí van 10 claves para evitar los errores "
        "más comunes al emprender."))
    assert c.tipo == TIPO_CONTEXTUAL


def test_autoidentificacion_tension_sin_friccion_sigue_siendo_contextual():
    """La vía nueva NO baja el listón de corroborante: sigue exigiendo fricción."""
    c = clasificar(_ev(
        "Fui despedido de mi empresa el año pasado, y desde entonces "
        "entendí muchas cosas."))
    assert c.tipo == TIPO_CONTEXTUAL


def test_como_rol_en_tercera_persona_no_es_autoidentificacion():
    """Falso positivo real detectado en la validación con corpus de Tavily:

    "presentó su renuncia como CEO" es tercera persona (el verbo lleva la
    persona, no la frase "como CEO"); admitirlo confundía descripción de
    prensa con autoidentificación. Debe seguir cayendo en contextual.
    """
    c = clasificar(_ev(
        "El enigmático mensaje que dejó la CEO de 'X' — Linda Yaccarino "
        "presentó su renuncia como CEO de X y antes de irse habló sobre "
        "el cambio logrado en la plataforma."))
    assert c.tipo == TIPO_CONTEXTUAL


def test_atribucion_de_prensa_en_tercera_persona_sin_dominio_cae_a_contextual():
    """Límite aceptado del gate de dominio (2026-08-28, ver
    ``test_maxima_autoridad_sin_dominio_de_negocio_cae_a_contextual``): esta
    frase es una autodeclaración legítima de la fundadora sobre su propia
    empresa, pero "crecer muy rápido" no está en el léxico cerrado de
    ``DOMINIOS`` (no es literalmente "expansión" ni ninguna otra palabra
    listada). El gate no distingue "prensa sobre otro tema" (el caso real que
    lo motivó — Clara Brugada) de "founder hablando en lenguaje natural que
    no toca el léxico" — ambos caen a `contextual`. Aceptado explícitamente
    por el operador como costo del fix: la REGLA DURA prefiere perder señal
    ambigua a admitir un falso positivo evidente."""
    c = clasificar(_ev(
        'Ana Torres, fundadora de Acme, admitió: "cometimos el error de '
        'crecer muy rápido".'))
    assert c.tipo == TIPO_CONTEXTUAL


def test_posesivo_mas_evento_sin_rol_explicito_es_autodeclaracion():
    """"Cerré mi startup" nunca dice "soy fundador", pero identifica posición.

    Nota: se evita a propósito la frase "lo que aprendí", que coincide con un
    marcador de opinión ya existente en ``relevance.MARCADORES_OPINION`` — ver
    ``test_frase_lo_que_aprendi_colisiona_con_filtro_de_opinion`` más abajo,
    que documenta esa colisión real encontrada en el corpus de validación.
    """
    c = clasificar(_ev(
        "Cerré mi startup después de 5 semanas, sin haber validado el "
        "mercado a tiempo."))
    assert c.tipo == TIPO_AUTODECLARACION


def test_frase_lo_que_aprendi_colisiona_con_filtro_de_opinion():
    """Hallazgo real de la validación 2026-08-27: un testimonio genuino de
    founder titulado "esto es lo que aprendí" NO se admite, porque esa frase
    ya es un marcador de opinión/reflexión genérica en ``relevance.py``
    (reutilizado aquí a propósito como filtro anti-ruido). Es una limitación
    conocida, no un bug: se documenta con un test en vez de solo en el chat.
    """
    c = clasificar(_ev(
        "Cerré mi startup después de 5 semanas. Esto es lo que aprendí sobre "
        "validar antes de construir."))
    assert c.tipo == TIPO_CONTEXTUAL


def test_posesivo_mas_evento_sin_marcador_no_es_admitido():
    """Sin verbo de evento, el posesivo solo no basta."""
    c = clasificar(_ev("Mi startup está creciendo bien este trimestre."))
    assert c.tipo == TIPO_CONTEXTUAL


def test_salvaguarda_empleado_no_dueno_no_asciende_a_autodeclaracion():
    """"Mi jefe" marca que quien habla es empleado, no dueño: no autodeclaracion."""
    c = clasificar(_ev(
        "Mi jefe me pidió que dejara mi proyecto paralelo, así que cerré mi "
        "startup y aprendí a priorizar mejor mi tiempo."))
    assert c.tipo != TIPO_AUTODECLARACION


def test_salvaguarda_empleado_con_friccion_es_corroborante():
    c = clasificar(_ev(
        "Mi jefe me pidió trabajar horas extra sin pago; cerré mi startup "
        "paralela porque ya no daba abasto y renuncié poco después."))
    assert c.tipo == TIPO_CORROBORANTE


def test_columnas_del_contrato_tienen_prioridad_sobre_el_texto():
    c = clasificar(_ev("Acme amplía su red de sucursales en el país",
                       persona="Ana Gómez", cargo="fundadora"))
    assert c.tipo == TIPO_AUTODECLARACION
    assert c.enunciador_nombre == "Ana Gómez"


def test_clasificacion_es_reproducible():
    ev = _ev("Juan Pérez, CEO de Acme, anunció despidos")
    assert clasificar(ev) == clasificar(ev)


def test_nunca_nombra_deuda_cultural():
    """El módulo no emite vocabulario de Motor B bajo ninguna rama."""
    prohibidas = ("deuda", "ontolog", "moral", "temporal", "relacional",
                  "epistemica", "epistémica")
    citas = ("Juan Pérez, CEO de Acme, anunció despidos",
             "Extrabajadores de Acme denuncian despidos masivos",
             "Acme amplía su red de sucursales en el país")
    for cita in citas:
        c = clasificar(_ev(cita))
        texto = " ".join(str(v) for v in (c.tipo, c.enunciador_cargo,
                                          c.enunciador_dominio, c.razon)).lower()
        assert not any(p in texto for p in prohibidas), cita


def test_detectar_dominio_sin_marcador_es_indeterminado():
    assert detectar_dominio("Acme celebra su aniversario") == "indeterminado"


# ── Persistencia ───────────────────────────────────────────────────────────

def test_dry_run_no_escribe(db):
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos", n=1)
    rep = clasificar_lote(db)
    assert rep["pendientes"] == 1
    assert rep["escritas"] == 0
    assert db.fetch_all("SELECT * FROM evidencia_clasificada") == []
    assert db.fetch_all("SELECT * FROM expedientes_candidatos") == []


def test_aplicar_escribe_y_abre_expediente(db):
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos", n=1)
    rep = clasificar_lote(db, aplicar=True)
    assert rep["escritas"] == 1
    assert rep["expedientes_creados"] == 1
    fila = dict(db.fetch_one("SELECT * FROM expedientes_candidatos"))
    assert fila["estado"] == "abierto"
    clas = dict(db.fetch_one("SELECT * FROM evidencia_clasificada"))
    assert clas["tipo_epistemologico"] == TIPO_AUTODECLARACION
    assert clas["expediente_id"] == fila["id"]


def test_reejecutar_no_duplica(db):
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos", n=1)
    _insertar(db, "Acme busca ingeniero de datos", n=2, origen="operador")
    clasificar_lote(db, aplicar=True)
    segunda = clasificar_lote(db, aplicar=True)
    assert segunda["pendientes"] == 0
    assert segunda["escritas"] == 0
    assert len(db.fetch_all("SELECT id FROM evidencia_clasificada")) == 2
    assert len(db.fetch_all("SELECT id FROM expedientes_candidatos")) == 1


def test_expediente_existente_se_reutiliza_sin_tocar_su_estado(db):
    eid, creado = obtener_o_crear_expediente(db, "Acme")
    assert creado
    db.execute("UPDATE expedientes_candidatos SET estado = 'candidato' WHERE id = ?",
               (eid,))
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos", n=1)
    clasificar_lote(db, aplicar=True)
    fila = dict(db.fetch_one("SELECT * FROM expedientes_candidatos WHERE id = ?",
                             (eid,)))
    assert fila["estado"] == "candidato"      # este módulo no lo degrada
    assert buscar_expediente(db, "acme") == eid   # coincidencia sin distinguir caja


def test_filtros_acotan_el_lote(db):
    _insertar(db, "Acme amplía su red", org="Acme", n=1)
    _insertar(db, "Beta amplía su red", org="Beta", n=2)
    assert clasificar_lote(db, org="Beta")["pendientes"] == 1
    assert clasificar_lote(db, limite=1)["pendientes"] == 1


# ── Organización explícitamente mencionada (ampliación 2026-08-28) ─────────

def test_detecta_soy_fundador_de():
    assert _detectar_organizacion_mencionada(
        "Soy fundadora de Acme y cometí el error de crecer muy rápido."
    ) == "Acme"


def test_detecta_funde():
    assert _detectar_organizacion_mencionada(
        "Fundé Acme en 2019 con dos amigos de la universidad."
    ) == "Acme"


def test_detecta_mi_startup_se_llama():
    assert _detectar_organizacion_mencionada(
        "Mi startup se llama Acme y hoy tiene 40 empleados."
    ) == "Acme"


def test_detecta_mi_empresa_coma_nombre_coma():
    assert _detectar_organizacion_mencionada(
        "Mi empresa, Acme, tuvo que despedir a la mitad del equipo."
    ) == "Acme"


def test_cometi_el_error_sin_organizacion_es_null():
    assert _detectar_organizacion_mencionada(
        "Cometí el error de contratar rápido en mi startup."
    ) is None


def test_generalizacion_sobre_startups_es_null():
    assert _detectar_organizacion_mencionada(
        "Las startups en general fallan por falta de validación."
    ) is None


def test_mi_jefe_no_produce_organizacion_propia():
    assert _detectar_organizacion_mencionada(
        "Mi jefe me pidió que dejara mi proyecto paralelo, así que cerré "
        "mi startup."
    ) is None


def test_consulta_tavily_como_texto_no_es_organizacion():
    """La frase de búsqueda en sí, si apareciera como cita_textual, no debe
    producir una organización — no hay patrón de aposición/fundación."""
    assert _detectar_organizacion_mencionada('"cometí el error de" startup') is None


def test_clasificar_lote_usa_organizacion_mencionada_para_busqueda_dinamica(db):
    """La evidencia_id del conector Tavily NUNCA usa la frase de búsqueda
    (empresa_mencionada) como organización del expediente — solo la
    organización extraída del contenido."""
    _insertar(
        db,
        "Soy fundador de Acme y cometí el error de crecer muy rápido.",
        org='"cometí el error de" startup',  # la frase, tal como la guarda el conector real
        origen="usuario",
        n=1,
        connector="busqueda_dinamica_founder",
    )
    rep = clasificar_lote(db, aplicar=True)
    assert rep["expedientes_creados"] == 1
    assert buscar_expediente(db, "Acme") is not None
    assert buscar_expediente(db, '"cometí el error de" startup') is None


def test_clasificar_lote_sin_organizacion_persiste_sin_expediente(db):
    """§8.3 (2026-08-29): sin patrón de organización en el contenido, la fila
    del conector Tavily se clasifica y SE PERSISTE (ya no se pierde), con
    expediente_id = NULL — no genera expediente ni puede promoverse."""
    _insertar(
        db,
        "Cometí el error de contratar rápido en mi startup.",
        org='"cometí el error de" startup',
        origen="usuario",
        n=2,
        connector="busqueda_dinamica_founder",
    )
    rep = clasificar_lote(db, aplicar=True)
    assert rep["expedientes_creados"] == 0
    assert rep["escritas"] == 1
    assert buscar_expediente(db, '"cometí el error de" startup') is None

    fila = dict(db.fetch_one(
        "SELECT expediente_id FROM evidencia_clasificada WHERE evidencia_id = "
        "(SELECT id FROM evidencias WHERE hash_dedup = 'hash-2')"))
    assert fila["expediente_id"] is None


def test_clasificar_lote_conectores_fase1_no_cambian_de_comportamiento(db):
    """Los conectores que ya usaban empresa_mencionada como org real (Fase 1)
    siguen exactamente igual: no se ven afectados por esta ampliación."""
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos",
             org="Acme", n=3, connector="google_news")
    rep = clasificar_lote(db, aplicar=True)
    assert rep["expedientes_creados"] == 1
    assert buscar_expediente(db, "Acme") is not None


def test_la_evidencia_original_no_se_modifica(db):
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos", n=1)
    antes = dict(db.fetch_one("SELECT * FROM evidencias"))
    clasificar_lote(db, aplicar=True)
    assert dict(db.fetch_one("SELECT * FROM evidencias")) == antes


# ── Resiliencia de red (reconexión y reintentos) ────────────────────────────

def test_reintenta_tras_caida_de_conexion_transitoria_y_termina_escribiendo(db, monkeypatch):
    """Regresión: en Termux sobre datos móviles el socket se cayó a media
    evidencia con 'SSL SYSCALL error: Software caused connection abort'. La
    primera escritura falla, la reconexión ocurre, el reintento escribe bien."""
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos", n=1)

    original_execute = db.execute
    fallos = {"n": 0}

    def flaky(sql, params=()):
        if "INSERT INTO evidencia_clasificada" in sql and fallos["n"] == 0:
            fallos["n"] += 1
            raise RuntimeError("SSL SYSCALL error: Software caused connection abort")
        return original_execute(sql, params)

    reconexiones = {"n": 0}
    monkeypatch.setattr(db, "execute", flaky)
    monkeypatch.setattr(db, "reconectar",
                        lambda: reconexiones.__setitem__("n", reconexiones["n"] + 1))

    rep = clasificar_lote(db, aplicar=True, sleep=lambda s: None)

    assert rep["escritas"] == 1
    assert rep["saltadas"] == 0
    assert reconexiones["n"] == 1
    assert len(db.fetch_all("SELECT id FROM evidencia_clasificada")) == 1


def test_error_de_conexion_persistente_salta_la_evidencia_sin_tumbar_el_lote(db, monkeypatch):
    """Si la reconexión nunca sostiene (red realmente caída), se agotan los
    reintentos, esa evidencia se salta (queda pendiente para la próxima
    corrida) y el resto del lote se procesa igual."""
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos", org="Acme", n=1)
    _insertar(db, "Beta busca ingeniero de datos", org="Beta", origen="operador", n=2)

    original_execute = db.execute

    def siempre_falla_para_evidencia_1(sql, params=()):
        if "INSERT INTO evidencia_clasificada" in sql and params[1] == 1:
            raise RuntimeError("could not receive data from server")
        return original_execute(sql, params)

    monkeypatch.setattr(db, "execute", siempre_falla_para_evidencia_1)
    monkeypatch.setattr(db, "reconectar", lambda: None)

    rep = clasificar_lote(db, aplicar=True, max_reintentos=2, sleep=lambda s: None)

    assert rep["saltadas"] == 1
    assert rep["escritas"] == 1  # Beta sí se escribió
    assert len(db.fetch_all("SELECT id FROM evidencia_clasificada")) == 1


def test_error_que_no_es_de_conexion_no_se_reintenta(db, monkeypatch):
    """Un error de datos/programación (no de red) se salta de inmediato: no
    tiene sentido reintentarlo, y no debe consumir los `max_reintentos`."""
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos", n=1)

    intentos = {"n": 0}
    original_execute = db.execute

    def falla_con_error_de_datos(sql, params=()):
        if "INSERT INTO evidencia_clasificada" in sql:
            intentos["n"] += 1
            raise ValueError("CHECK constraint failed: chk_tipo")
        return original_execute(sql, params)

    monkeypatch.setattr(db, "execute", falla_con_error_de_datos)

    rep = clasificar_lote(db, aplicar=True, sleep=lambda s: None)

    assert intentos["n"] == 1  # ni un reintento
    assert rep["saltadas"] == 1
    assert rep["escritas"] == 0


def test_friccion_anterior_a_la_posicion_de_tension_no_cuenta():
    """«Acme demanda más clientes» no es la queja de un cliente."""
    c = clasificar(_ev("Acme demanda más clientes para su nueva plataforma"))
    assert c.tipo == TIPO_CONTEXTUAL


def test_cargo_generico_declarado_hereda_su_dominio():
    c = clasificar(_ev("Acme reorganiza su cadena de suministro",
                       persona="Ana Gómez", cargo="directora de operaciones"))
    assert c.tipo == TIPO_AUTODECLARACION
    assert c.enunciador_dominio == "operaciones"


def test_mencion_de_cargo_sin_habla_no_es_autodeclaracion():
    """Un titular puede narrar en tercera persona sin que el CEO haya dicho nada."""
    c = clasificar(_ev(
        "El nuevo plan del multimillonario CEO de Nubank: conquistar la banca "
        "estadounidense con el modelo que revolucionó América Latina",
        org="Nubank"))
    assert c.tipo == TIPO_CONTEXTUAL
    assert c.enunciador_nombre is None
    assert c.enunciador_cargo is None


def test_verbo_de_habla_permite_atribuir_el_nombre_correcto():
    """El verbo de habla ('dijo') sigue permitiendo atribuir el nombre
    correctamente incluso cuando el gate de dominio (2026-08-28) baja el
    `tipo` a `contextual` por no tocar el léxico cerrado de ``DOMINIOS``
    ("banca... próxima frontera" no es ninguna palabra de la lista) — ver
    ``test_atribucion_de_prensa_en_tercera_persona_sin_dominio_cae_a_contextual``.
    La atribución de nombre es independiente de esa rama final."""
    c = clasificar(_ev(
        "David Vélez, CEO de Nubank, dijo que la banca estadounidense es la "
        "próxima frontera", org="Nubank"))
    assert c.tipo == TIPO_CONTEXTUAL
    assert c.enunciador_nombre == "David Vélez"


def test_cita_textual_no_captura_frase_capitalizada_ajena_como_nombre():
    """'Estados Unidos' no debe leerse como el nombre de quien habla."""
    c = clasificar(_ev(
        'El CEO de Nubank afirmó: "vamos a conquistar Estados Unidos"',
        org="Nubank"))
    assert c.enunciador_nombre is None
    assert c.enunciador_nombre != "Estados Unidos"
