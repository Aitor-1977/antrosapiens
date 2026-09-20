"""Pruebas de POST /mobile/scrape — BFF de búsqueda en vivo para Android,
SIN X-Ingest-Token (ver hd_scraper/api/app.py:mobile_scrape).

No reimplementa /scrape: usa el mismo `_correr_query`, mismos conectores
reales (mockeados aquí para no salir a red), mismo contrato de evidencia.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

from hd_scraper.api.app import _MOBILE_RATE_LIMIT_MAX, _mobile_rate_ventanas
from hd_scraper.config import settings
from tests.test_gdelt import FIXTURE_JSON as GDELT_FIXTURE
from tests.test_google_news import FIXTURE_RSS


@pytest.fixture()
def cli(db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    # /mobile/scrape NUNCA exige X-Ingest-Token: se deja configurado igual
    # para probar, en test aparte, que jamás aparece en la respuesta.
    object.__setattr__(settings, "ingest_token", "secreto-123")
    # Evita red real: ambos conectores que /mobile/scrape usa (fijos, no
    # elegibles por el cliente) devuelven fixtures ya usados en sus propias
    # suites (test_google_news.py, test_gdelt.py).
    from hd_scraper.connectors.gdelt import GdeltConnector
    from hd_scraper.connectors.google_news import GoogleNewsConnector
    monkeypatch.setattr(GoogleNewsConnector, "_get", lambda self, url: FIXTURE_RSS)
    monkeypatch.setattr(GdeltConnector, "_get", lambda self, url: GDELT_FIXTURE)
    _mobile_rate_ventanas.clear()
    yield TestClient(api.app)
    object.__setattr__(settings, "ingest_token", "")
    _mobile_rate_ventanas.clear()


def test_mobile_scrape_payload_valido_escribe_evidencia(cli, db):
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["new_evidence"] > 0
    assert db.fetch_one("SELECT COUNT(*) n FROM evidencias")["n"] == d["new_evidence"]


def test_mobile_scrape_payload_invalido_422(cli):
    assert cli.post("/mobile/scrape", json={"empresa": ""}).status_code == 422
    assert cli.post("/mobile/scrape", json={"empresa": "   "}).status_code == 422
    assert cli.post("/mobile/scrape", json={"empresa": "x" * 201}).status_code == 422
    # Sin el campo obligatorio: error de validación de pydantic (422).
    assert cli.post("/mobile/scrape", json={}).status_code == 422


def test_mobile_scrape_conectores_fijos_no_elegibles_por_el_cliente(cli):
    # El cliente NO puede pedir otros conectores ni ampliar la lista: el
    # payload solo declara "empresa" (pydantic ignora cualquier otro campo).
    r = cli.post("/mobile/scrape", json={
        "empresa": "Nubank", "connectors": ["job_boards"], "categoria": "VC",
    })
    assert r.status_code == 200
    assert sorted(r.json()["connectors"]) == ["gdelt", "google_news"]


def test_mobile_scrape_nunca_expone_el_token(cli):
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    cuerpo = r.text
    assert "secreto-123" not in cuerpo
    assert "ingest" not in cuerpo.lower()
    assert "token" not in cuerpo.lower()


def test_mobile_scrape_delega_en_correr_query_existente(cli):
    # Mismo contrato de "resultados" que ya expone /scrape para cada
    # conector (vistos/escritos/filtrados/...), no uno reinventado.
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    resultados = r.json()["resultados"]
    conectores_reportados = {x["connector"] for x in resultados}
    assert conectores_reportados == {"google_news", "gdelt"}
    for x in resultados:
        assert "vistos" in x and "escritos" in x and "filtrados" in x


def test_mobile_scrape_respuesta_incluye_timestamp_y_live(cli):
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    d = r.json()
    assert d["live"] is True
    assert d["timestamp"]
    # Todo el procesamiento (clasificación + promoción) ya ocurrió en esta
    # misma respuesta: nunca queda un job aparte corriendo después.
    assert d["processing_status"] == "completed"


def test_mobile_scrape_busqueda_real_sin_resultados_no_es_error(cli, monkeypatch):
    # LIVE_SEARCH_EMPTY: se buscó de verdad y no había nada nuevo -> 200 con
    # new_evidence=0, nunca un error. Ambos conectores sin artículos.
    monkeypatch.setattr(
        "hd_scraper.connectors.google_news.GoogleNewsConnector._get",
        lambda self, url: '<?xml version="1.0"?><rss><channel></channel></rss>',
    )
    monkeypatch.setattr(
        "hd_scraper.connectors.gdelt.GdeltConnector._get",
        lambda self, url: '{"articles": []}',
    )
    r = cli.post("/mobile/scrape", json={"empresa": "OrganizacionSinNoticias"})
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True and d["live"] is True
    assert d["new_evidence"] == 0


def test_mobile_scrape_rate_limit(cli):
    for _ in range(_MOBILE_RATE_LIMIT_MAX):
        assert cli.post("/mobile/scrape", json={"empresa": "Nubank"}).status_code == 200
    r = cli.post("/mobile/scrape", json={"empresa": "Nubank"})
    assert r.status_code == 429


def test_scrape_sigue_exigiendo_token_sin_cambios(cli):
    # /mobile/scrape es una superficie DISTINTA: /scrape conserva su
    # protección de siempre, sin debilitarse por la existencia de la nueva.
    r = cli.post("/scrape", json={"empresa": "Nubank"})
    assert r.status_code == 401


# ── FASE 10 (misión "AntroLabsHD operativo"): prueba end-to-end de la     ──
# cadena completa disparada por una sola búsqueda — RAW -> clasificación ->
# promoción -> /verificados — no solo "el HTTP fue 200".

_FIXTURE_RSS_KAVAK = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Kavak - Google News</title>
  <item>
    <title>Carlos Herrera, CEO de Kavak, anunció una ronda de inversión para su expansión en LATAM</title>
    <link>https://news.google.com/rss/articles/KAVAK1?oc=5</link>
    <pubDate>Wed, 01 Jul 2026 10:00:00 GMT</pubDate>
    <source url="https://www.example.com">Prensa X</source>
  </item>
</channel>
</rss>
"""


def test_busqueda_kavak_atraviesa_scrape_clasificacion_promocion_y_verificados(
    cli, db, monkeypatch
):
    from hd_scraper.candidatos_verificados import listar_candidatos_verificados

    # Búsqueda de una organización DISTINTA de "Clara": clasificar/promover
    # están acotados a org="Kavak" (evidencias_sin_clasificar/expedientes_
    # abiertos con ese filtro), así que esta búsqueda nunca toca ni
    # reprocesa ninguna fila ajena — el caso histórico de "Clara" (cubierto
    # en tests/test_reparacion_clara.py y test_reconstruccion_derivados.py)
    # es un expediente completamente independiente del de "Kavak".
    monkeypatch.setattr(
        "hd_scraper.connectors.google_news.GoogleNewsConnector._get",
        lambda self, url: _FIXTURE_RSS_KAVAK,
    )
    # Determinista y sin red: el link de fixture tiene forma de wrapper de
    # Google News (mismo patrón que otros fixtures de este repo), lo que en
    # las versiones del conector que ya resuelven wrappers dispararía un
    # intento real de _resolver_url_real (best-effort, ver google_news.py)
    # — ya cubierto por su propia suite de tests. raising=False: el método
    # no existe en todas las variantes de esta rama del conector.
    monkeypatch.setattr(
        "hd_scraper.connectors.google_news.GoogleNewsConnector._resolver_url_real",
        lambda self, url: None,
        raising=False,
    )

    r = cli.post("/mobile/scrape", json={"empresa": "Kavak"})
    assert r.status_code == 200
    d = r.json()

    # 1. evidencia nueva existe
    assert d["new_evidence"] >= 1
    assert db.fetch_one(
        "SELECT COUNT(*) n FROM evidencias WHERE empresa_mencionada = 'Kavak'"
    )["n"] >= 1

    # 2. clasificación nueva existe (no solo escrita, VERIFICADA en la tabla),
    # específicamente la fila real de la autodeclaración de Google News (el
    # fixture de GDELT reutiliza un texto genérico ajeno, por eso se filtra
    # por cita_textual, no basta con "alguna fila de Kavak").
    assert d["classified"] >= 1
    fila_clasificada = db.fetch_one(
        "SELECT ec.tipo_epistemologico FROM evidencia_clasificada ec "
        "JOIN evidencias e ON e.id = ec.evidencia_id "
        "WHERE e.empresa_mencionada = 'Kavak' AND e.connector = 'google_news'")
    assert fila_clasificada is not None
    assert fila_clasificada["tipo_epistemologico"] == "senal_primaria_autodeclaracion"

    # 3. candidato válido aparece en /verificados
    assert d["promoted"] >= 1
    nombres = {c["organizacion"]
               for c in listar_candidatos_verificados(db, estado_visibilidad="todos")}
    assert "Kavak" in nombres

    # 3b. bug quirúrgico 2026-09-15: la RESPUESTA MISMA de /mobile/scrape ya
    # trae el candidato/expediente de ESTA organización, acotado por nombre
    # exacto — el cliente no necesita (y no debe) volver a golpear
    # /expedientes ni /verificados para saber qué mostrar.
    assert d["expediente"] is not None
    assert d["expediente"]["nombre"] == "Kavak"
    assert d["candidato"] is not None
    assert d["candidato"]["organizacion"] == "Kavak"

    # 4. segunda ejecución (misma búsqueda) no duplica nada
    n_evidencias_1 = db.fetch_one(
        "SELECT COUNT(*) n FROM evidencias WHERE empresa_mencionada = 'Kavak'")["n"]
    n_clasificadas_1 = db.fetch_one(
        "SELECT COUNT(*) n FROM evidencia_clasificada ec "
        "JOIN evidencias e ON e.id = ec.evidencia_id "
        "WHERE e.empresa_mencionada = 'Kavak'")["n"]
    n_expedientes_1 = db.fetch_one(
        "SELECT COUNT(*) n FROM expedientes_candidatos WHERE organizacion = 'Kavak'")["n"]

    r2 = cli.post("/mobile/scrape", json={"empresa": "Kavak"})
    d2 = r2.json()
    assert d2["new_evidence"] == 0    # dedup por hash_dedup
    assert d2["classified"] == 0      # ya_clasificada, no reclasifica
    assert d2["promoted"] == 0        # WHERE estado='abierto', ya es candidato

    n_evidencias_2 = db.fetch_one(
        "SELECT COUNT(*) n FROM evidencias WHERE empresa_mencionada = 'Kavak'")["n"]
    n_clasificadas_2 = db.fetch_one(
        "SELECT COUNT(*) n FROM evidencia_clasificada ec "
        "JOIN evidencias e ON e.id = ec.evidencia_id "
        "WHERE e.empresa_mencionada = 'Kavak'")["n"]
    n_expedientes_2 = db.fetch_one(
        "SELECT COUNT(*) n FROM expedientes_candidatos WHERE organizacion = 'Kavak'")["n"]
    assert (n_evidencias_1, n_clasificadas_1, n_expedientes_1) == \
           (n_evidencias_2, n_clasificadas_2, n_expedientes_2)
    assert n_expedientes_1 == 1, "no debe crear un segundo expediente para la misma organización"
    # la repetición sigue devolviendo el candidato de Kavak en la respuesta
    # misma (no null solo porque promoted==0 esta vez: ya era candidato).
    assert d2["candidato"] is not None
    assert d2["candidato"]["organizacion"] == "Kavak"


# ── bug quirúrgico 2026-09-15: una búsqueda NUNCA debe filtrarse con         ──
# organizaciones ajenas que ya existan históricamente en /verificados —
# reproduce el caso real reportado: "Clara" (candidato histórico stale)
# apareciendo en la pantalla al buscar una empresa distinta.
def test_mobile_scrape_no_filtra_candidato_historico_de_otra_organizacion(cli, db):
    from hd_scraper.db.models import ahora_iso

    # Candidato histórico "Clara" ya promovido (simula el caso real de
    # producción: una fila stale en evidencia_clasificada/expedientes_
    # candidatos, sin depender de correr el reset/reconstrucción).
    db.execute(
        "INSERT INTO evidencias (id, cita_textual, fecha_extraccion, "
        "fecha_publicacion, url_fuente, nombre_medio, empresa_mencionada, "
        "tipo_evento, origen_declaracion, hash_dedup, connector, estado, creado_en) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (9001, "Clara Brugada acompaña a la Presidenta...", ahora_iso(),
         "2026-07-09", "https://example.com/clara", "CDMX", "Clara",
         "ronda", "prensa", "hash-clara-historico", "google_news", "ok",
         ahora_iso()))
    exp_id = db.insert_returning_id(
        "INSERT INTO expedientes_candidatos (organizacion, estado) VALUES (?, ?)",
        ("Clara", "candidato"))
    db.execute(
        "INSERT INTO evidencia_clasificada (expediente_id, evidencia_id, "
        "tipo_epistemologico, enunciador_nombre, enunciador_cargo) "
        "VALUES (?,?,?,?,?)",
        (exp_id, 9001, "senal_primaria_autodeclaracion", "Clara Brugada",
         "Presidenta"))

    # Búsqueda real de una organización DISTINTA de "Clara".
    r = cli.post("/mobile/scrape", json={"empresa": "Kavak"})
    assert r.status_code == 200
    d = r.json()

    cuerpo = r.text
    assert "Clara" not in cuerpo, "una búsqueda de Kavak jamás debe traer el candidato histórico Clara"
    if d["expediente"] is not None:
        assert d["expediente"]["nombre"] == "Kavak"
    if d["candidato"] is not None:
        assert d["candidato"]["organizacion"] == "Kavak"
