"""Bug real 2026-09-17: la automatización de ingesta (GitHub Actions) hizo
visible en /expedientes una "tarjeta" con nombre "startup tecnológica ronda
de inversión" — el término de una consulta libre (buscador de Android o
descubrimiento por categoría), nunca una organización real. Ningún artículo
mencionaba esa frase como entidad; el titular no traía ningún nombre propio
detectable, así que `_construir_expedientes` caía en su fallback y aceptaba
`empresa_mencionada` (la consulta misma) sin verificar que fuera, ella
también, un nombre propio.

Corrección: `empresa_mencionada` solo se acepta como organización cuando
supera el mismo filtro de nombre propio (`detectar_empresa`) que ya se exige
al titular. Reutiliza la función existente; no duplica su lógica.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.db.models import ESTADO_OK, ahora_iso, calcular_hash_dedup


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    return TestClient(api.app)


def _sembrar_evidencia(db, *, empresa, cita_textual, categoria_query="Startup"):
    db.execute(
        """
        INSERT INTO evidencias (
            cita_textual, fecha_extraccion, url_fuente, nombre_medio,
            empresa_mencionada, tipo_evento, origen_declaracion, hash_dedup,
            fecha_publicacion, connector, estado, categoria, keywords,
            confianza, creado_en
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cita_textual, ahora_iso(), "https://ejemplo.com/nota", "Medio de Prueba",
            empresa, "queja", "prensa",
            calcular_hash_dedup(empresa, cita_textual),
            "2026-09-08", "manual_test", ESTADO_OK, categoria_query, "[]", 1.0,
            ahora_iso(),
        ),
    )


def test_frase_de_consulta_generica_no_aparece_como_organizacion(cli, db):
    """Reproduce el bug: empresa_mencionada es la consulta libre, el titular
    no menciona ninguna entidad. Debe descartarse, no aparecer como candidato."""
    _sembrar_evidencia(
        db, empresa="startup tecnológica ronda de inversión",
        cita_textual="Una firma del sector cerró una ronda para expandirse en la región",
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "startup tecnológica ronda de inversión" not in nombres

    rechazo = db.fetch_one(
        "SELECT motivo FROM rechazos WHERE connector = 'api:_construir_expedientes' "
        "ORDER BY id DESC LIMIT 1")
    assert rechazo is not None
    assert rechazo["motivo"] == "sin_empresa_deteccion"


def test_organizacion_real_sin_nombre_en_el_titular_sigue_apareciendo(cli, db):
    """Control: una organización real (nombre propio genuino) declarada en
    empresa_mencionada, con un titular que tampoco la nombra literalmente,
    debe seguir aceptándose por el fallback — el fix no debe romper el caso
    legítimo que ese fallback existe para cubrir."""
    _sembrar_evidencia(
        db, empresa="Toku",
        cita_textual="La compañía anunció una alianza estratégica en la región",
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Toku" in nombres


# ── Guardia de identidad: nombre de una palabra pegado a otro nombre propio
# (2026-09-20, caso real "Clara" / "Clara Brugada") ─────────────────────────

def test_nombre_de_pila_de_un_tercero_no_se_atribuye_a_la_organizacion(cli, db):
    """Reproduce el caso real: 'Clara' (fintech) es subcadena de 'Clara
    Brugada' (jefa de gobierno de CDMX, persona distinta). La evidencia debe
    descartarse, no aparecer como si fuera de la fintech."""
    _sembrar_evidencia(
        db, empresa="Clara",
        cita_textual="Clara Brugada, entre los mandatarios mejor evaluados",
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Clara" not in nombres

    rechazo = db.fetch_one(
        "SELECT motivo FROM rechazos WHERE connector = 'api:_construir_expedientes' "
        "ORDER BY id DESC LIMIT 1")
    assert rechazo is not None
    assert rechazo["motivo"] == "sin_empresa_deteccion"


def test_apellido_precede_al_nombre_tambien_se_descarta(cli, db):
    """La guardia mira ambos lados: un apellido ANTES del nombre de una sola
    palabra también forma un nombre propio más largo de un tercero."""
    _sembrar_evidencia(
        db, empresa="Clara",
        cita_textual="Doctora Ana Clara asumió la dirección del hospital regional",
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Clara" not in nombres


def test_organizacion_legitima_de_una_palabra_sigue_apareciendo_sin_homonimo(cli, db):
    """Control: 'Clara' mencionada como la propia fintech (sin apellido ni
    nombre propio contiguo) sigue funcionando exactamente igual que antes."""
    _sembrar_evidencia(
        db, empresa="Clara",
        cita_textual="Clara, el nuevo unicornio mexicano tras levantamiento de 70 mdd",
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Clara" in nombres


def test_organizaciones_con_nombre_distintivo_no_se_ven_afectadas(cli, db):
    """Control de no regresión sobre los casos reales sin contaminación
    (0% en Jüsto, Zubale y Palenca): nombres distintivos, con o sin
    caracteres especiales, siguen detectándose igual que antes."""
    _sembrar_evidencia(
        db, empresa="Jüsto",
        cita_textual="El súper en línea Jüsto levanta 65 mdd; busca inteligencia artificial")
    _sembrar_evidencia(
        db, empresa="Zubale",
        cita_textual="Zubale consiguió US$40 millones proponiendo que los supermercados no dependan de Rappi")
    _sembrar_evidencia(
        db, empresa="Palenca",
        cita_textual="La startup mexicana Palenca levanta una inversión de 2.6 mdd")

    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert {"Jüsto", "Zubale", "Palenca"} <= nombres


def test_sufijo_corporativo_contiguo_no_activa_la_guardia(cli, db):
    """Regresión encontrada al escribir la guardia: `detectar_empresa` ya
    trunca "Acme Corp" a "Acme" (una palabra), y "Corp" queda pegado como si
    fuera el apellido de un tercero. "Corp" es un sufijo de forma jurídica
    reconocido (`_SUFIJOS_CORPORATIVOS`), no una persona: no debe activar la
    guardia."""
    _sembrar_evidencia(
        db, empresa="Acme Corp",
        cita_textual="Acme Corp enfrenta fricción con su proveedor principal",
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Acme" in nombres


def test_clasificador_de_sector_contiguo_no_activa_la_guardia(cli, db):
    """Regresión REAL encontrada en producción (2026-09-20) al desplegar
    la guardia: "Fintech Mundi destinaría..." se rechazaba a sí mismo,
    porque "Fintech" pegado antes de "Mundi" se leía como el nombre de pila
    de un tercero. "Fintech" es un clasificador genérico de sector
    (`_GENERICOS_SECTOR`), no una persona: no debe activar la guardia."""
    _sembrar_evidencia(
        db, empresa="Mundi",
        cita_textual=(
            "Fintech Mundi destinaría 20,000 millones de pesos al "
            "financiamiento de pymes exportadoras"),
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Mundi" in nombres


def test_organizacion_de_dos_palabras_no_activa_la_guardia_de_una_palabra(cli, db):
    """La guardia solo aplica a nombres de una sola palabra (mismo criterio
    que `_ocurrencias_org` en clasificacion_epistemologica.py): 'Trace
    Finance' pegado a otro nombre propio no debe descartarse por esto."""
    _sembrar_evidencia(
        db, empresa="Trace Finance",
        cita_textual="Ana Ríos, Trace Finance Roberto cierran alianza estratégica")
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Trace Finance" in nombres


def test_limite_conocido_tercero_como_sujeto_real_sigue_sin_cubrirse(cli, db):
    """Documenta el límite conocido (CLAUDE.md, "Errores recurrentes" #2):
    caso real de Nowports, un exCEO que levanta capital para SU startup
    nueva. El nombre aparece correcto, sin homónimo pegado, así que esta
    guardia no lo descarta. Si esto empieza a fallar es porque alguien
    resolvió el límite: hay que actualizar este test y CLAUDE.md juntos."""
    _sembrar_evidencia(
        db, empresa="Nowports",
        cita_textual=(
            "El exCEO de Nowports atrae US$6 millones para su nueva "
            "startup de IA, respaldada por A16z"),
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Nowports" in nombres


def test_limite_conocido_sin_mencion_en_el_titular_sigue_sin_cubrirse(cli, db):
    """Documenta el segundo límite conocido, TODAVÍA SIN RESOLVER, reportado
    a Mario antes de escribir esta guardia: caso real de "Mundi", un ensayo
    de Substack sobre el ébola que no menciona "Mundi" en ningún lugar del
    titular. La guardia por adjacencia no aplica aquí (no hay ocurrencia que
    verificar); exigir que `mencionada` aparezca en el titular resolvería
    esto, pero rompería el caso legítimo ya protegido de "Toku" (ver
    `test_organizacion_real_sin_nombre_en_el_titular_sigue_apareciendo`):
    Mundi y Toku son ambos organizaciones reales declaradas en
    `seed_prospectos.py` con títulos que tampoco las mencionan. Pendiente de
    decisión del operador. Si esto empieza a fallar es porque se resolvió el
    conflicto: hay que actualizar este test."""
    _sembrar_evidencia(
        db, empresa="Mundi",
        cita_textual="El fuego del ébola",
    )
    r = cli.get("/expedientes", params={"limite": 100})
    nombres = {e["nombre"] for e in r.json()["expedientes"]}
    assert "Mundi" in nombres
