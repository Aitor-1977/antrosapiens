"""Capa 19 · Síntesis estructural con LLM NVIDIA: grounding, fallback y frontera.

Verifica que el enriquecimiento LLM (NVIDIA NIM) SIEMPRE degrada a la síntesis
determinista ante fallos, que jamás inventa evidencia (`evidencia_urls` y
sustancia son las deterministas) y que no clasifica Deuda Cultural™.
"""
import importlib
import json

import httpx
import pytest

from hd_scraper.config import settings
from hd_scraper.nvidia_parser import (
    NOTA_LLM,
    SYSTEM_PROMPT,
    NvidiaError,
    _evidencias_a_insumo,
    _normalizar,
    _pedir_json,
    disponible,
    sintetizar,
)
from hd_scraper.sintesis import sintetizar as sintetizar_determinista


def _evidencia(cita, *, url="https://medio.com/1", medio="Medio A",
               empresa="Acme", persona=None, cargo=None, tipo_evento="ronda",
               fecha="2026-07-01", confianza=0.8, keywords=None):
    return {
        "cita_textual": cita,
        "url_fuente": url,
        "nombre_medio": medio,
        "empresa_mencionada": empresa,
        "persona_citada": persona,
        "cargo": cargo,
        "tipo_evento": tipo_evento,
        "fecha_publicacion": fecha,
        "confianza": confianza,
        "keywords": keywords or [],
    }


def _corpus_ronda():
    return [
        _evidencia(f"Acme cierra una ronda de financiamiento {i}",
                   url=f"https://medio.com/ronda{i}", medio=f"Medio {i}",
                   keywords=["ronda_inversion"])
        for i in range(1, 5)
    ]


def _payload_llm(**overrides):
    contenido = {
        "patron_comportamiento": "contratación masiva / crecimiento de plantilla",
        "senal_tension": "fricción operativa derivada del ritmo de contratación",
        "actores_involucrados": [
            {"nombre": "Acme", "rol": "organización observada"},
            {"nombre": "acme", "rol": "duplicada"},
        ],
        "metrica_relevancia": {"evidencias": 4, "fuentes": 4, "resumen": "x"},
        "evidencia_urls": ["https://inventada.com/x"],
        "estado": "sintetizado",
        "motivo": "",
    }
    contenido.update(overrides)
    return {"choices": [{"message": {"content": json.dumps(contenido)}}]}


class RespuestaFake:
    def __init__(self, *, status_code=200, texto="", datos=None):
        self.status_code = status_code
        self._texto = texto
        self._datos = datos

    @property
    def text(self):
        return self._texto

    def json(self):
        if self._datos is not None:
            return self._datos
        return json.loads(self._texto)


class ClienteFake:
    def __init__(self, respuesta):
        self.respuesta = respuesta
        self.pedido = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, *, headers=None, json=None, **kwargs):
        self.pedido = {"url": url, "headers": headers, "json": json}
        if isinstance(self.respuesta, Exception):
            raise self.respuesta
        return self.respuesta


@pytest.fixture()
def con_llm():
    anterior = settings.nvidia_api_key
    object.__setattr__(settings, "nvidia_api_key", "clave-de-prueba-nvidia")
    yield
    object.__setattr__(settings, "nvidia_api_key", anterior)


@pytest.fixture()
def sin_llm():
    anterior = settings.nvidia_api_key
    object.__setattr__(settings, "nvidia_api_key", "")
    yield
    object.__setattr__(settings, "nvidia_api_key", anterior)


# --- disponibilidad ---------------------------------------------------------

def test_disponible_false_sin_clave(sin_llm):
    assert disponible() is False


def test_disponible_true_con_clave(con_llm):
    assert disponible() is True


def test_sintetizar_sin_clave_lanza_nvidiaerror(sin_llm):
    with pytest.raises(NvidiaError, match="NVIDIA_API_KEY no configurada"):
        sintetizar(_corpus_ronda(), "Acme", http=ClienteFake(RespuestaFake()))


# --- frontera: sin Deuda Cultural™ en el prompt ------------------------------

def test_prompt_no_clasifica_deuda_cultural():
    assert "NO clasifiques Deuda Cultural" in SYSTEM_PROMPT
    assert "juicios de valor" in SYSTEM_PROMPT
    assert "NO inventes" in SYSTEM_PROMPT


# --- insumo solo con campos públicos ----------------------------------------

def test_insumo_descarta_privado_y_citas_vacias():
    insumo = _evidencias_a_insumo([
        _evidencia("cita pública", url="https://m.com/1"),
        {"cita_textual": "   ", "url_fuente": "https://m.com/x"},
    ])
    assert len(insumo) == 1
    fila = insumo[0]
    assert set(fila) == {"fecha", "medio", "url", "cita"}
    assert fila["url"] == "https://m.com/1"


# --- pedido compatible con OpenAI / NVIDIA NIM -------------------------------

def test_pedir_json_envia_payload_compatible_openai(con_llm):
    cliente = ClienteFake(RespuestaFake(datos=_payload_llm()))
    _pedir_json(org="Acme", insumo=[{"fecha": "", "medio": "Medio A",
                                     "url": "https://m.com/1",
                                     "cita": "Acme cierra una ronda"}], http=cliente)
    p = cliente.pedido
    assert p["url"].endswith("/chat/completions")
    assert p["headers"]["Authorization"] == "Bearer clave-de-prueba-nvidia"
    assert p["json"]["model"].startswith("meta/llama")
    assert p["json"]["temperature"] == 0.0
    assert p["json"]["response_format"] == {"type": "json_object"}
    assert p["json"]["messages"][0]["role"] == "system"


def test_pedir_json_http_error(con_llm):
    cliente = ClienteFake(RespuestaFake(status_code=429, texto="rate limit"))
    with pytest.raises(NvidiaError, match="HTTP 429"):
        _pedir_json(org="Acme", insumo=[], http=cliente)


def test_pedir_json_timeout(con_llm):
    cliente = ClienteFake(httpx.TimeoutException("timeout"))
    with pytest.raises(NvidiaError, match="timeout"):
        _pedir_json(org="Acme", insumo=[], http=cliente)


def test_pedir_json_cuerpo_no_json(con_llm):
    cliente = ClienteFake(RespuestaFake(texto="<html>no json</html>"))
    with pytest.raises(NvidiaError, match="cuerpo no JSON"):
        _pedir_json(org="Acme", insumo=[], http=cliente)


def test_pedir_json_json_malformado(con_llm):
    cliente = ClienteFake(RespuestaFake(
        datos={"choices": [{"message": {"content": "no es un json"}}]}))
    with pytest.raises(NvidiaError, match="JSON malformado"):
        _pedir_json(org="Acme", insumo=[], http=cliente)


# --- grounding: la base determinista manda -----------------------------------

def test_sintetizar_llm_superpone_pero_no_inventa(con_llm):
    cliente = ClienteFake(RespuestaFake(datos=_payload_llm()))
    s = sintetizar(_corpus_ronda(), "Acme", http=cliente)
    assert s["estado"] == "sintetizado"
    assert s["patron_comportamiento"] == "contratación masiva / crecimiento de plantilla"
    assert s["senal_tension_dolor"] == "fricción operativa derivada del ritmo de contratación"
    assert s["nota"] == NOTA_LLM
    assert s["evidencia_urls"] == [
        f"https://medio.com/ronda{i}" for i in range(1, 5)
    ]
    assert "inventada.com" not in s["evidencia_urls"]
    assert s["sustancia_metrica"]["evidencias"] == 4
    assert [a["nombre"] for a in s["actores_involucrados"]] == ["Acme"]


def test_normalizar_no_sobreescribe_grounding_con_llm_vacio():
    base = sintetizar_determinista(_corpus_ronda(), "Acme")
    llm_vacio = {
        "patron_comportamiento": "",
        "senal_tension": "  ",
        "actores_involucrados": [],
        "evidencia_urls": ["https://inventada.com/x"],
        "estado": "sin_marcador",
        "motivo": "lo que el LLM diga",
    }
    s = _normalizar(base, llm_vacio)
    assert s["patron_comportamiento"] == base["patron_comportamiento"]
    assert s["senal_tension_dolor"] == base["senal_tension_dolor"]
    assert s["evidencia_urls"] == base["evidencia_urls"]
    assert s["sustancia_metrica"] == base["sustancia_metrica"]
    assert s["actores_involucrados"] == base["actores_involucrados"]
    assert s["nota"] == NOTA_LLM


def test_normalizar_actores_acepta_strings_y_dedup():
    base = sintetizar_determinista(_corpus_ronda(), "Acme")
    llm = {
        "patron_comportamiento": "x",
        "senal_tension": "y",
        "actores_involucrados": ["María", {"nombre": "MARÍA", "rol": "líder"},
                                 "Acme", "  "],
    }
    s = _normalizar(base, llm)
    nombres = [a["nombre"] for a in s["actores_involucrados"]]
    assert nombres == ["María", "Acme"]


# --- endpoint: fallback determinista -----------------------------------------

@pytest.fixture()
def client(db, monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    TestClient = fastapi.testclient.TestClient
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "get_db", lambda: db)
    yield TestClient(api.app)


def _insertar(db, empresa, url, keywords, tipo_evento="ronda", confianza=0.8):
    import hashlib
    import json as _json
    from hd_scraper.db.models import ahora_iso
    h = hashlib.sha256(f"{empresa}{url}".encode()).hexdigest()
    db.execute(
        "INSERT INTO evidencias (cita_textual, fecha_extraccion, fecha_publicacion, "
        "url_fuente, nombre_medio, empresa_mencionada, tipo_evento, origen_declaracion, "
        "hash_dedup, connector, keywords, confianza, calidad_captura, categoria, estado, "
        "creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (f"{empresa} anuncia ronda de financiamiento", ahora_iso(), "2026-07-01",
         url, f"Medio {keywords[0]}" if keywords else "Medio A", empresa,
         tipo_evento, "prensa", h, "google_news", _json.dumps(keywords),
         confianza, "Alta", "Startup", "ok", ahora_iso()),
    )


def test_endpoint_degrada_a_determinista_cuando_llm_falla(client, db, monkeypatch):
    importlib.import_module("hd_scraper.api.app")  # asegura módulo importado
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "_nvidia_disponible", lambda: True)

    def _llm_roto(evidencias, org):
        raise NvidiaError("boom de prueba")

    monkeypatch.setattr(api, "_sintetizar_llm", _llm_roto)
    for i in range(1, 5):
        _insertar(db, "Nubank", f"https://medio{i}.com/1", ["ronda_inversion"])
    r = client.get("/sintesis/Nubank")
    assert r.status_code == 200
    d = r.json()
    assert d["metodo"] == "determinista"
    assert d["estado"] == "sintetizado"
    assert "Fallback determinista" in d["nota"]
    assert len(d["evidencia_urls"]) == 4


def test_endpoint_devuelve_llm_cuando_disponible(client, db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "_nvidia_disponible", lambda: True)
    monkeypatch.setattr(api, "_sintetizar_llm",
                        lambda evidencias, org: {
                            "org": org,
                            "patron_comportamiento": "patrón LLM de prueba",
                            "evidencia_urls": [],
                        })
    for i in range(1, 5):
        _insertar(db, "Rappi", f"https://medio{i}.com/1", ["ronda_inversion"])
    r = client.get("/sintesis/Rappi")
    assert r.status_code == 200
    d = r.json()
    assert d["metodo"] == "llm_nvidia"
    assert d["patron_comportamiento"] == "patrón LLM de prueba"


def test_endpoint_sin_clave_usa_determinista(client, db, monkeypatch):
    api = importlib.import_module("hd_scraper.api.app")
    monkeypatch.setattr(api, "_nvidia_disponible", lambda: False)
    for i in range(1, 5):
        _insertar(db, "Ualá", f"https://medio{i}.com/1", ["ronda_inversion"])
    r = client.get("/sintesis/Ualá")
    assert r.status_code == 200
    d = r.json()
    assert d["metodo"] == "determinista"
    assert d["patron_comportamiento"].startswith("levantamiento de capital")
