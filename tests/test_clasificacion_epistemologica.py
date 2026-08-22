"""Cascada epistemológica y su persistencia idempotente (Entrega 2)."""
from hd_scraper.clasificacion_epistemologica import (
    TIPO_AUTODECLARACION,
    TIPO_CONTEXTUAL,
    TIPO_CORROBORANTE,
    TIPO_HUELLA_PRACTICA,
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


def _insertar(db, cita, *, org="Acme", origen="prensa", n=0):
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (cita, ahora_iso(), f"https://ejemplo.test/{n}", "Prensa X", org,
         "lanzamiento", origen, f"hash-{n}", "google_news", ahora_iso()))


# ── Cascada ────────────────────────────────────────────────────────────────

def test_maxima_autoridad_es_autodeclaracion():
    c = clasificar(_ev("Juan Pérez, CEO de Acme, anunció despidos"))
    assert c.tipo == TIPO_AUTODECLARACION
    assert c.enunciador_nombre == "Juan Pérez"
    assert c.enunciador_dominio == "retencion_talento"


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


def test_la_evidencia_original_no_se_modifica(db):
    _insertar(db, "Juan Pérez, CEO de Acme, anunció despidos", n=1)
    antes = dict(db.fetch_one("SELECT * FROM evidencias"))
    clasificar_lote(db, aplicar=True)
    assert dict(db.fetch_one("SELECT * FROM evidencias")) == antes


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


def test_verbo_de_habla_permite_autodeclaracion_con_nombre_correcto():
    c = clasificar(_ev(
        "David Vélez, CEO de Nubank, dijo que la banca estadounidense es la "
        "próxima frontera", org="Nubank"))
    assert c.tipo == TIPO_AUTODECLARACION
    assert c.enunciador_nombre == "David Vélez"


def test_cita_textual_no_captura_frase_capitalizada_ajena_como_nombre():
    """'Estados Unidos' no debe leerse como el nombre de quien habla."""
    c = clasificar(_ev(
        'El CEO de Nubank afirmó: "vamos a conquistar Estados Unidos"',
        org="Nubank"))
    assert c.enunciador_nombre is None
    assert c.enunciador_nombre != "Estados Unidos"
