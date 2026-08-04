"""Orquestador agéntico del radar (hd_scraper/radar).

Verifican el ciclo PLAN→ACT→OBSERVA→DECIDE: construcción del plan bajo los
filtros, detención por plan/presupuesto/saturación y validación del contacto
con hd_scraper.emails (confirmación por dominio + resumen).
"""
import pytest

from hd_scraper.db.models import QuerySpec
from hd_scraper.emails import confirmar_por_dominio
from hd_scraper.filtros import FiltrosRadar, objetivos_por_filtros
from hd_scraper.radar import (
    CONECTORES_RADAR,
    enriquecer_contacto,
    radar_loop,
    _tareas,
)


def foto_expediente(nombre, n_evid, dominio="", validos=(), candidatos=()):
    return {
        "nombre": nombre, "categoria": "Startup", "vertical": "fintech",
        "scoring": "A", "score_icp": 80, "intensidad": 0.8,
        "profundidad_dolor": 0.7, "viabilidad": "alta", "tipo_deuda": "Temporal",
        "deuda_razon": "x", "deuda_secundaria": "", "senal_dominante": "",
        "evidencias": [], "total_evidencias": n_evid, "patrones": [],
        "keywords": [], "contacto": {"dominio": dominio,
                                     "emails_candidatos": list(candidatos),
                                     "emails_validados": list(validos),
                                     "email_sugerido": (validos[0] if validos else ""),
                                     "verificado": False},
        "linkedin": "", "google": "",
        "validacion_cientifica": {"hipotesis_bloqueada": False, "veredicto": "VALIDADA"},
        "gobernanza": {}, "huella": "h", "version": "v1",
    }


def foto(expedientes):
    return {"total": len(expedientes),
            "resumen_scoring": {"A": len(expedientes), "B": 0, "C": 0},
            "expedientes": expedientes}


# ── Plan (filtros → tareas) ────────────────────────────────────────────────

def test_tareas_sin_filtros_es_descubrimiento():
    plan = _tareas(FiltrosRadar(), None)
    assert plan
    assert all(q.exact is False for q in plan)
    assert all(q.categoria in {"VC", "Startup", "Incubadora", "Corporativo"} for q in plan)
    assert all(q.region == "Toda LATAM" for q in plan)


def test_tareas_con_enfoque_y_tamano_es_objetivos():
    filtros = FiltrosRadar(categorias=("VC",), escalas=("11-50",))
    plan = _tareas(filtros, None)
    objetivos = set(o.lower() for o in objetivos_por_filtros(filtros))
    assert plan
    assert all(q.exact for q in plan)
    assert all(q.empresa.lower() in objetivos for q in plan)
    assert all(q.tipo_evento for q in plan)


def test_tareas_llevan_region_y_terminos():
    plan = _tareas(FiltrosRadar(region="México", palabra_clave="fintech"), "(México) fintech")
    assert all(q.region == "México" for q in plan)
    assert all(q.terminos == "(México) fintech" for q in plan)


# ── Validación de contacto ──────────────────────────────────────────────────

def test_enriquecer_contacto_confirma_por_dominio():
    e = foto_expediente(
        "Acme", 3, dominio="acme.com",
        validos=("mario@acme.com",),
        candidatos=("mario@acme.com", "hola@acme.com"),
    )
    enriquecer_contacto(e)
    assert e["contacto"]["email_confirmado"] == "mario@acme.com"
    assert e["contacto"]["emails_confirmados"] == ["mario@acme.com"]
    resumen = e["contacto"]["resumen"]
    assert resumen["vistos"] == 2
    assert "mario@acme.com" in resumen["validos"]


def test_enriquecer_contacto_sin_dominio_no_confirma():
    e = foto_expediente("Acme", 3, dominio="", validos=("mario@acme.com",))
    enriquecer_contacto(e)
    assert e["contacto"]["email_confirmado"] == ""
    assert e["contacto"]["emails_confirmados"] == []


def test_confirmar_por_dominio_desde_modulo():
    assert confirmar_por_dominio("mario@acme.com", "https://www.acme.com")
    assert not confirmar_por_dominio("mario@otra.com", "acme.com")


# ── Ciclo agéntico (loop) ───────────────────────────────────────────────────

def test_radar_loop_plan_completado(monkeypatch):
    def un_solo_objetivo(filtros, terminos):
        return [QuerySpec(empresa="Acme", tipo_evento="ronda",
                          region=filtros.region, exact=True)]
    monkeypatch.setattr("hd_scraper.radar._tareas", un_solo_objetivo)

    def ejecutar(db, query, conectores):
        return [{"connector": "google_news", "escritos": 2, "vistos": 5}]

    def expedientes(categorias, limite):
        return foto([foto_expediente("Acme", 3, dominio="acme.com",
                                     validos=("mario@acme.com",),
                                     candidatos=("mario@acme.com", "hola@acme.com"))])

    res = radar_loop(FiltrosRadar(), db=object(), ejecutar_fn=ejecutar,
                     expedientes_fn=expedientes, conectores=CONECTORES_RADAR,
                     presupuesto_s=60.0, max_rondas=3)
    assert res["detencion"] == "plan_completado"
    assert res["plan"]["tareas_ejecutadas"] == 1
    assert res["total_escritos"] == 2
    assert res["total_vistos"] == 5
    assert res["rondas"][0]["orgs_nuevas"] == ["acme"]
    assert res["contacto"]["total_correos_confirmados"] == 1
    assert res["expedientes"]["expedientes"][0]["contacto"]["email_confirmado"] == "mario@acme.com"


def test_radar_loop_saturacion(monkeypatch):
    def dos_objetivos(filtros, terminos):
        return [QuerySpec(empresa="Acme", tipo_evento="ronda"),
                QuerySpec(empresa="Beta", tipo_evento="ronda")]
    monkeypatch.setattr("hd_scraper.radar._tareas", dos_objetivos)

    def ejecutar(db, query, conectores):
        return [{"connector": "gdelt", "escritos": 0, "vistos": 3}]

    def expedientes(categorias, limite):
        return foto([foto_expediente("Zeta", 0)])

    res = radar_loop(FiltrosRadar(), db=object(), ejecutar_fn=ejecutar,
                     expedientes_fn=expedientes, conectores=CONECTORES_RADAR,
                     presupuesto_s=60.0, max_rondas=4, lote=1)
    assert res["detencion"] == "saturacion"
    assert len(res["rondas"]) == 2
    assert res["total_escritos"] == 0


def test_radar_loop_presupuesto(monkeypatch):
    monkeypatch.setattr("hd_scraper.radar._tareas",
                        lambda f, t: [QuerySpec(empresa="Acme", tipo_evento="ronda")])

    def ejecutar(db, query, conectores):
        return [{"connector": "google_news", "escritos": 1, "vistos": 1}]

    res = radar_loop(FiltrosRadar(), db=object(), ejecutar_fn=ejecutar,
                     expedientes_fn=lambda c, l: foto([]),
                     conectores=CONECTORES_RADAR, presupuesto_s=-1.0)
    assert res["detencion"] == "presupuesto"
    assert res["parcial"] is True
    assert res["rondas"] == []
    assert res["total_escritos"] == 0


def test_radar_loop_sin_tareas(monkeypatch):
    monkeypatch.setattr("hd_scraper.radar._tareas", lambda f, t: [])
    res = radar_loop(FiltrosRadar(), db=object(), ejecutar_fn=lambda *a: [],
                     expedientes_fn=lambda c, l: foto([]))
    assert res["detencion"] == "sin_tareas"
    assert res["plan"]["total_tareas"] == 0


def test_radar_loop_consolida_contacto(monkeypatch):
    monkeypatch.setattr("hd_scraper.radar._tareas",
                        lambda f, t: [QuerySpec(empresa="Acme", tipo_evento="ronda")])

    def ejecutar(db, query, conectores):
        return [{"connector": "google_news", "escritos": 2, "vistos": 4}]

    def expedientes(categorias, limite):
        return foto([
            foto_expediente("Acme", 3, dominio="acme.com",
                            validos=("mario@acme.com",),
                            candidatos=("mario@acme.com", "hola@acme.com")),
            foto_expediente("Beta", 2, dominio="beta.io",
                            validos=("ana@beta.io",),
                            candidatos=("ana@beta.io", "soporte@beta.io")),
        ])

    res = radar_loop(FiltrosRadar(), db=object(), ejecutar_fn=ejecutar,
                     expedientes_fn=expedientes, conectores=CONECTORES_RADAR,
                     presupuesto_s=60.0, max_rondas=2)
    assert res["contacto"]["correos_validos"] == 2
    assert res["contacto"]["organizaciones_con_correo"] == 2
    assert res["contacto"]["total_correos_confirmados"] == 2
    assert set(res["contacto"]["correos_confirmados_por_dominio"]) == {
        "mario@acme.com", "ana@beta.io"}
