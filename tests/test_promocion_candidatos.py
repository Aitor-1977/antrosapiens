"""Promoción de expedientes 'abierto' -> 'candidato' (Entrega 3)."""
from hd_scraper.db.models import ahora_iso
from hd_scraper.promocion_candidatos import (
    CATEGORIA_EXCLUIDA,
    TIPOS_QUE_PROMUEVEN,
    decidir_promocion,
)
from hd_scraper.promocion_store import (
    categoria_de_organizacion,
    promover,
    promover_lote,
)
from hd_scraper.prospectos import nuevo_prospecto, upsert_prospecto


# ── Decisión pura ────────────────────────────────────────────────────────

def test_promueve_con_autodeclaracion():
    d = decidir_promocion(None, ["senal_primaria_autodeclaracion"])
    assert d.promover is True


def test_promueve_con_huella_practica():
    d = decidir_promocion(None, ["senal_primaria_huella_practica"])
    assert d.promover is True


def test_no_promueve_solo_con_corroborante():
    d = decidir_promocion(None, ["corroborante"])
    assert d.promover is False


def test_no_promueve_solo_con_contextual():
    d = decidir_promocion(None, ["contextual"])
    assert d.promover is False


def test_no_promueve_mezcla_de_corroborante_y_contextual():
    """Ninguna cantidad de corroborante/contextual basta, por sí sola."""
    d = decidir_promocion(None, ["corroborante", "contextual", "corroborante"])
    assert d.promover is False


def test_promueve_con_mezcla_si_hay_al_menos_una_fuerte():
    d = decidir_promocion(None, ["contextual", "corroborante",
                                 "senal_primaria_huella_practica"])
    assert d.promover is True


def test_categoria_corporativo_excluye_sin_importar_evidencia():
    """Nunca promueve, ni con autodeclaración de sobra."""
    d = decidir_promocion(CATEGORIA_EXCLUIDA, ["senal_primaria_autodeclaracion",
                                                "senal_primaria_huella_practica"])
    assert d.promover is False
    assert "Corporativo" in d.razon


def test_categoria_no_resuelta_no_excluye():
    """Sin categoria confirmada, la exclusión de Corporativo no aplica."""
    d = decidir_promocion(None, ["senal_primaria_autodeclaracion"])
    assert d.promover is True


def test_categoria_startup_no_excluye():
    d = decidir_promocion("Startup", ["senal_primaria_autodeclaracion"])
    assert d.promover is True


def test_sin_evidencia_no_promueve():
    d = decidir_promocion("VC", [])
    assert d.promover is False


def test_es_reproducible():
    tipos = ["contextual", "senal_primaria_autodeclaracion"]
    assert decidir_promocion("Startup", tipos) == decidir_promocion("Startup", tipos)


def test_tipos_que_promueven_son_exactamente_los_dos_literales():
    assert set(TIPOS_QUE_PROMUEVEN) == {
        "senal_primaria_autodeclaracion", "senal_primaria_huella_practica"}


# ── Persistencia ─────────────────────────────────────────────────────────

def _expediente(db, organizacion, estado="abierto"):
    return db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        (organizacion, estado))


def _evidencia(db, org, n):
    return db.insert_returning_id(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, url_fuente, "
        "nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (f"cita {n}", ahora_iso(), f"https://ej.test/{n}", "Prensa X", org,
         "lanzamiento", "prensa", f"hp{n}", "google_news", ahora_iso()))


def _clasificar(db, expediente_id, evidencia_id, tipo):
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico) VALUES (?,?,?)",
        (expediente_id, evidencia_id, tipo))


def _prospecto(db, nombre, categoria):
    upsert_prospecto(db, nuevo_prospecto(nombre, categoria))


def test_categoria_de_organizacion_case_insensitive(db):
    _prospecto(db, "Acme", "Startup")
    assert categoria_de_organizacion(db, "acme") == ("Startup", False)
    assert categoria_de_organizacion(db, "ACME") == ("Startup", False)


def test_categoria_de_organizacion_sin_match_es_none(db):
    assert categoria_de_organizacion(db, "Organización Inexistente") == (None, False)


def test_promover_escribe_y_es_idempotente(db):
    exp = _expediente(db, "Acme")
    ev = _evidencia(db, "Acme", 1)
    _clasificar(db, exp, ev, "senal_primaria_autodeclaracion")

    assert promover(db, exp) is True
    fila = dict(db.fetch_one("SELECT estado FROM expedientes_candidatos WHERE id = ?", (exp,)))
    assert fila["estado"] == "candidato"

    # segunda vez: ya no está 'abierto', no reescribe
    assert promover(db, exp) is False


def test_promover_no_toca_descartado(db):
    exp = _expediente(db, "Acme", estado="descartado")
    assert promover(db, exp) is False
    fila = dict(db.fetch_one("SELECT estado FROM expedientes_candidatos WHERE id = ?", (exp,)))
    assert fila["estado"] == "descartado"


def test_dry_run_no_escribe(db):
    exp = _expediente(db, "Acme")
    ev = _evidencia(db, "Acme", 1)
    _clasificar(db, exp, ev, "senal_primaria_autodeclaracion")

    rep = promover_lote(db)
    assert rep["aplicado"] is False
    assert rep["promovidos"] == 1  # proyección
    fila = dict(db.fetch_one("SELECT estado FROM expedientes_candidatos WHERE id = ?", (exp,)))
    assert fila["estado"] == "abierto"  # no escribió de verdad


def test_aplicar_promueve_solo_lo_que_corresponde(db):
    con_autodeclaracion = _expediente(db, "Acme")
    _clasificar(db, con_autodeclaracion, _evidencia(db, "Acme", 1),
                "senal_primaria_autodeclaracion")

    solo_corroborante = _expediente(db, "Beta")
    _clasificar(db, solo_corroborante, _evidencia(db, "Beta", 2), "corroborante")

    sin_evidencia = _expediente(db, "Gamma")

    rep = promover_lote(db, aplicar=True)
    assert rep["promovidos"] == 1

    estados = {r["organizacion"]: r["estado"] for r in
               (dict(f) for f in db.fetch_all("SELECT organizacion, estado FROM expedientes_candidatos"))}
    assert estados["Acme"] == "candidato"
    assert estados["Beta"] == "abierto"
    assert estados["Gamma"] == "abierto"


def test_corporativo_nunca_promueve_aunque_tenga_autodeclaracion(db):
    _prospecto(db, "Nubank", "Corporativo")
    exp = _expediente(db, "Nubank")
    _clasificar(db, exp, _evidencia(db, "Nubank", 1), "senal_primaria_autodeclaracion")
    _clasificar(db, exp, _evidencia(db, "Nubank", 2), "senal_primaria_huella_practica")

    rep = promover_lote(db, aplicar=True)
    assert rep["promovidos"] == 0
    fila = dict(db.fetch_one("SELECT estado FROM expedientes_candidatos WHERE id = ?", (exp,)))
    assert fila["estado"] == "abierto"


def test_categoria_no_resuelta_permite_promover(db):
    """Empresa capturada por el scraper pero nunca dada de alta en prospectos."""
    exp = _expediente(db, "Empresa Sin Alta")
    _clasificar(db, exp, _evidencia(db, "Empresa Sin Alta", 1),
                "senal_primaria_huella_practica")

    rep = promover_lote(db, aplicar=True)
    assert rep["promovidos"] == 1


def test_reejecutar_el_lote_no_duplica_ni_falla(db):
    exp = _expediente(db, "Acme")
    _clasificar(db, exp, _evidencia(db, "Acme", 1), "senal_primaria_autodeclaracion")

    promover_lote(db, aplicar=True)
    segunda = promover_lote(db, aplicar=True)
    assert segunda["promovidos"] == 0  # ya no está 'abierto'


def test_filtros_org_y_limite(db):
    e1 = _expediente(db, "Acme")
    _clasificar(db, e1, _evidencia(db, "Acme", 1), "senal_primaria_autodeclaracion")
    e2 = _expediente(db, "Beta")
    _clasificar(db, e2, _evidencia(db, "Beta", 2), "senal_primaria_autodeclaracion")

    assert promover_lote(db, org="Beta")["evaluados"] == 1
    assert promover_lote(db, limite=1)["evaluados"] == 1


def test_no_toca_evidencia_clasificada_ni_prospectos(db):
    _prospecto(db, "Acme", "Startup")
    exp = _expediente(db, "Acme")
    _clasificar(db, exp, _evidencia(db, "Acme", 1), "senal_primaria_autodeclaracion")

    antes_ev = dict(db.fetch_one("SELECT * FROM evidencia_clasificada"))
    antes_pr = dict(db.fetch_one("SELECT * FROM prospectos"))

    promover_lote(db, aplicar=True)

    assert dict(db.fetch_one("SELECT * FROM evidencia_clasificada")) == antes_ev
    assert dict(db.fetch_one("SELECT * FROM prospectos")) == antes_pr


def test_categoria_detecta_conflicto_ante_duplicados_no_elige_en_silencio(db):
    """Regresión del incidente 2026-08-22/23: un reseed (o un alta duplicada
    vía /prospectos/bulk) tras cambiar categoria crea un duplicado
    (hash_dedup distinto, porque incluye categoria) sin borrar la fila vieja.
    Elegir en silencio la fila más reciente fue justo lo que dejó promover a
    Bitso/Kavak/Nubank/Rappi/Ualá pese a estar marcadas 'Corporativo': un
    duplicado 'Startup' más nuevo ganaba la lectura. Ahora debe señalar el
    conflicto, no resolverlo adivinando cuál es la buena."""
    _prospecto(db, "Nubank", "Startup")
    _prospecto(db, "Nubank", "Corporativo")  # simula el duplicado real

    assert len(db.fetch_all("SELECT id FROM prospectos WHERE nombre = 'Nubank'")) == 2
    assert categoria_de_organizacion(db, "Nubank") == (None, True)


def test_categoria_sin_conflicto_con_dos_filas_iguales(db):
    """Dos filas con la MISMA categoria (p. ej. un alta repetida sin cambio
    de categoria) no es el defecto de datos que preocupa: no es conflicto."""
    _prospecto(db, "Acme", "Startup")
    db.execute(
        "INSERT INTO prospectos (nombre, categoria, hash_dedup, creado_en, "
        "actualizado_en) VALUES (?, ?, ?, ?, ?)",
        ("Acme", "Startup", "hash-duplicado-mismo-valor", ahora_iso(), ahora_iso()))

    assert len(db.fetch_all("SELECT id FROM prospectos WHERE nombre = 'Acme'")) == 2
    assert categoria_de_organizacion(db, "Acme") == ("Startup", False)


def test_conflicto_bloquea_promocion_aunque_haya_autodeclaracion(db):
    """El expediente NO promueve mientras el conflicto en prospectos no se
    resuelva a mano, aun con evidencia que normalmente bastaría."""
    _prospecto(db, "Nubank", "Startup")
    _prospecto(db, "Nubank", "Corporativo")
    exp = _expediente(db, "Nubank")
    _clasificar(db, exp, _evidencia(db, "Nubank", 1), "senal_primaria_autodeclaracion")

    rep = promover_lote(db, aplicar=True)
    assert rep["promovidos"] == 0
    assert rep["conflictos_categoria"] == 1
    detalle = rep["detalle"][0]
    assert detalle["categoria_en_conflicto"] is True
    assert detalle["promovido"] is False
    assert "conflicto" in detalle["razon"].lower()
    fila = dict(db.fetch_one("SELECT estado FROM expedientes_candidatos WHERE id = ?", (exp,)))
    assert fila["estado"] == "abierto"


def test_conflicto_se_registra_en_el_log(db, caplog):
    import logging
    _prospecto(db, "Nubank", "Startup")
    _prospecto(db, "Nubank", "Corporativo")

    with caplog.at_level(logging.WARNING, logger="hd_scraper.promocion_store"):
        categoria_de_organizacion(db, "Nubank")

    assert any("conflicto" in r.message.lower() for r in caplog.records)


def test_sin_conflicto_categoria_en_conflicto_es_false_en_el_detalle(db):
    _prospecto(db, "Acme", "Startup")
    exp = _expediente(db, "Acme")
    _clasificar(db, exp, _evidencia(db, "Acme", 1), "senal_primaria_autodeclaracion")

    rep = promover_lote(db, aplicar=True)
    assert rep["conflictos_categoria"] == 0
    assert rep["detalle"][0]["categoria_en_conflicto"] is False
    assert rep["promovidos"] == 1


def test_evidencia_sin_expediente_nunca_se_promueve(db):
    """§8.3 (2026-08-29): una evidencia_clasificada con expediente_id=NULL
    (sin organización identificable) no tiene ningún expediente que evaluar
    — promover_lote solo recorre `expedientes_candidatos`, y una fila
    huérfana no crea ninguna ahí. Confirma que no se cuela en la promoción
    ni provoca error."""
    ev = _evidencia(db, "sin organizacion", 99)
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico) VALUES (?,?,?)",
        (None, ev, "senal_primaria_autodeclaracion"))

    rep = promover_lote(db, aplicar=True)
    assert rep["evaluados"] == 0
    assert rep["promovidos"] == 0
