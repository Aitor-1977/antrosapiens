"""Orquestador agéntico del radar: filtros inteligentes + validación de contacto.

Implementa el ciclo agéntico determinista de Motor A sobre el radar:

    1. PLAN    — los ``FiltrosRadar`` (región, enfoque, tamaño, palabra clave)
                 definen el plan de barrido: los objetivos que cumplen los
                 filtros o, sin ellos, el descubrimiento amplio de los cuatro
                 ecosistemas.
    2. ACT     — ejecuta un lote acotado de tareas (search → guardar) respetando
                 el presupuesto de tiempo de la función serverless.
    3. OBSERVA — reconstruye los Expedientes Vivos (análisis + Dictamen
                 Científico + gobernanza) y valida el contacto con
                 ``hd_scraper.emails`` (correos válidos y confirmados por
                 dominio oficial).
    4. DECIDE  — si una ronda no produjo escritos ni organizaciones nuevas, el
                 ciclo se detiene por SATURACIÓN; también se detiene al agotar
                 el presupuesto o el plan, sin recomenzar sin criterio.

El bucle es determinista y sin IA: los filtros son configuración ESTRUCTURAL
declarada por el operador y la "observación" es conteo de lo que la evidencia ya
almacenada sostiene. Motor A barre y valida; no decide contacto ni ejecuta
acción (eso es exclusivo del operador vía Motor B).
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from .db.models import QuerySpec
from .discovery import queries_para, region_clause
from .emails import confirmar_por_dominio, resumen_emails
from .filtros import FiltrosRadar, descripcion, objetivos_por_filtros

# Tipos de señal del contrato, en orden de interés para el radar.
TIPOS_BARRIDA: tuple[str, ...] = (
    "queja", "ronda", "contratacion", "despido", "lanzamiento", "cambio_sitio",
)

# Ecosistemas del contrato, en orden canónico del descubrimiento amplio.
CATEGORIAS_ORDEN: tuple[str, ...] = ("VC", "Startup", "Incubadora", "Corporativo")

# Conectores de prensa aptos para serverless (una petición por conector).
CONECTORES_RADAR: tuple[str, ...] = ("google_news", "gdelt")

PRESUPUESTO_DEFAULT_S: float = 55.0   # techo de tiempo de la función serverless
MAX_RONDAS_DEFAULT: int = 3           # rondas máximas del ciclo
MIN_RONDAS_SATURACION: int = 2        # rondas mínimas antes de declarar saturación
LOTE_POR_RONDA: int = 8               # tareas por ronda (acota el ciclo)
LIMITE_EXPEDIENTES: int = 30


@dataclass
class RondaRadar:
    """Una iteración del ciclo: qué se barrió y qué señal nueva aportó."""
    numero: int
    escritos: int = 0
    vistos: int = 0
    orgs_nuevas: tuple[str, ...] = ()

    def a_dict(self) -> dict:
        return {
            "ronda": self.numero,
            "escritos": self.escritos,
            "vistos": self.vistos,
            "orgs_nuevas": list(self.orgs_nuevas),
        }


def _tareas(filtros: FiltrosRadar, terminos: str | None) -> list[QuerySpec]:
    """Plan de barrido: tareas (QuerySpec) derivadas de los filtros.

    Con enfoque/tamaño declarados el radar barre los OBJETIVOS que cumplen los
    filtros (``HD_TRACKED_EMPRESAS`` explícita o el directorio semilla filtrado).
    Sin esos filtros barre el DESCUBRIMIENTO amplio de los cuatro ecosistemas;
    la región y la palabra clave moldean cada consulta. Determinista.
    """
    plan: list[QuerySpec] = []
    if filtros.categorias or filtros.escalas:
        for objetivo in objetivos_por_filtros(filtros):
            for tipo in TIPOS_BARRIDA:
                plan.append(QuerySpec(
                    empresa=objetivo, tipo_evento=tipo,
                    terminos=terminos, region=filtros.region, exact=True,
                ))
    else:
        for cat in CATEGORIAS_ORDEN:
            for tipo in TIPOS_BARRIDA:
                for termino, tipo_ev in queries_para(cat, tipo, "todas"):
                    plan.append(QuerySpec(
                        empresa=termino, tipo_evento=tipo_ev,
                        terminos=terminos, categoria=cat,
                        region=filtros.region, exact=False,
                    ))
    return plan


def enriquecer_contacto(expediente: dict) -> dict:
    """Valida el contacto del expediente con ``hd_scraper.emails``.

    Añade al paquete de contacto ``email_confirmado`` (primer correo válido cuyo
    dominio coincide con el oficial), ``emails_confirmados`` (todos los que lo
    cumplen) y ``resumen`` (vistos/válidos/rechazados con motivo). Nunca decide
    el uso del correo: solo marca lo que la evidencia estructural sostiene.
    """
    contacto = dict(expediente.get("contacto") or {})
    dominio = (contacto.get("dominio") or "").strip()
    candidatos = contacto.get("emails_candidatos") or []
    validos = contacto.get("emails_validados") or []
    confirmados = [
        e for e in validos if dominio and confirmar_por_dominio(e, dominio)
    ]
    contacto["email_confirmado"] = confirmados[0] if confirmados else ""
    contacto["emails_confirmados"] = confirmados
    contacto["resumen"] = resumen_emails(candidatos)
    expediente["contacto"] = contacto
    return expediente


def _resumen_contacto(expedientes: list[dict]) -> dict:
    """Consolidado de contacto del radar: correos válidos y confirmados."""
    total_validos = 0
    orgs_con_correo = 0
    confirmados: dict[str, set[str]] = {}
    for e in expedientes:
        c = e.get("contacto") or {}
        validos = c.get("emails_validados") or []
        total_validos += len(validos)
        if validos:
            orgs_con_correo += 1
        for correo in c.get("emails_confirmados") or ():
            confirmados.setdefault(correo, set()).add(e.get("nombre", ""))
    return {
        "correos_validos": total_validos,
        "organizaciones_con_correo": orgs_con_correo,
        "correos_confirmados_por_dominio": {
            correo: sorted(orgs) for correo, orgs in confirmados.items()
        },
        "total_correos_confirmados": len(confirmados),
    }


def _filtros_a_dict(filtros: FiltrosRadar) -> dict:
    return {
        "region": filtros.region,
        "enfoque": list(filtros.categorias),
        "tamano": list(filtros.escalas),
        "palabra_clave": filtros.palabra_clave,
        "descripcion": descripcion(filtros),
    }


def radar_loop(
    filtros: FiltrosRadar,
    *,
    db,
    ejecutar_fn,
    expedientes_fn,
    conectores: tuple[str, ...] = CONECTORES_RADAR,
    presupuesto_s: float = PRESUPUESTO_DEFAULT_S,
    max_rondas: int = MAX_RONDAS_DEFAULT,
    lote: int = LOTE_POR_RONDA,
    limite_expedientes: int = LIMITE_EXPEDIENTES,
    materializar_fn=None,
) -> dict:
    """Ciclo agéntico del radar (ver docstring del módulo). Determinista.

    ``ejecutar_fn(db, query, conectores) -> list[dict]`` ejecuta una tarea y
    devuelve resultados por conector (claves ``escritos`` y ``vistos``).
    ``expedientes_fn(categorias, limite) -> dict`` reconstruye los Expedientes
    Vivos (con Dictamen Científico y gobernanza) tras cada ronda.
    ``materializar_fn(db, expedientes)`` (opcional) materializa los Candidatos
    Comerciales de las organizaciones detectadas (reparación BC-I↔BC-II); sin
    él el radar conserva el comportamiento anterior.

    Devuelve el informe consolidado: filtros aplicados, plan, rondas, motivo de
    detención (``plan_completado | presupuesto | saturacion | max_rondas``),
    expedientes ya validados y el resumen de contacto.
    """
    t0 = time.monotonic()
    zona = region_clause(filtros.region)
    terminos = " ".join(t for t in (zona, filtros.terminos_extra) if t) or None
    plan = _tareas(filtros, terminos)

    vacio = {
        "modo": "radar",
        "filtros": _filtros_a_dict(filtros),
        "plan": {"total_tareas": 0, "tareas_ejecutadas": 0,
                 "tipo_eventos": list(TIPOS_BARRIDA)},
        "rondas": [],
        "detencion": "sin_tareas",
        "parcial": False,
        "tiempo_s": 0.0,
        "total_escritos": 0,
        "total_vistos": 0,
        "expedientes": {"total": 0, "resumen_scoring": {"A": 0, "B": 0, "C": 0},
                        "expedientes": []},
        "contacto": _resumen_contacto([]),
        "candidatos": None,
    }
    if not plan:
        vacio["nota"] = "sin tareas bajo los filtros (revisa enfoque/tamaño/región)"
        return vacio

    rondas: list[RondaRadar] = []
    prev_senal: set[str] = set()
    total_escritos = total_vistos = 0
    ejecutadas = 0
    detencion = "plan_completado"
    ultima_foto: dict = vacio["expedientes"]
    ultima_candidatos = None
    categorias = list(filtros.categorias) if filtros.categorias else None

    for numero in range(1, max_rondas + 1):
        if time.monotonic() - t0 > presupuesto_s:
            detencion = "presupuesto"
            break
        if ejecutadas >= len(plan):
            detencion = "plan_completado"
            break

        ronda = RondaRadar(numero=numero)
        for query in plan[ejecutadas: ejecutadas + lote]:
            if time.monotonic() - t0 > presupuesto_s:
                detencion = "presupuesto"
                break
            for res in ejecutar_fn(db, query, conectores):
                ronda.escritos += res.get("escritos", 0)
                ronda.vistos += res.get("vistos", 0)
            ejecutadas += 1

        total_escritos += ronda.escritos
        total_vistos += ronda.vistos

        # OBSERVA: fotografía de la base tras la ronda (valida + contacto).
        ultima_foto = expedientes_fn(categorias, limite_expedientes)
        for e in ultima_foto.get("expedientes", []):
            enriquecer_contacto(e)

        # Reparación BC-I↔BC-II: materializa los Candidatos Comerciales de las
        # organizaciones detectadas (opcional; por defecto el radar no cambia).
        if materializar_fn is not None:
            try:
                ultima_candidatos = materializar_fn(db, ultima_foto.get("expedientes", []))
            except Exception:  # pragma: no cover - el radar jamás colapsa por esto
                pass

        orgs_ahora = {
            e["nombre"].lower()
            for e in ultima_foto.get("expedientes", [])
            if e.get("total_evidencias", 0) > 0
        }
        ronda = RondaRadar(
            numero=numero, escritos=ronda.escritos, vistos=ronda.vistos,
            orgs_nuevas=tuple(sorted(orgs_ahora - prev_senal)),
        )
        rondas.append(ronda)
        prev_senal |= orgs_ahora

        # DECIDE: sin escritos ni organizaciones nuevas ⇒ saturación.
        if numero >= MIN_RONDAS_SATURACION and ronda.escritos == 0 and not ronda.orgs_nuevas:
            detencion = "saturacion"
            break
    else:
        detencion = "max_rondas"

    return {
        "modo": "radar",
        "filtros": _filtros_a_dict(filtros),
        "plan": {"total_tareas": len(plan), "tareas_ejecutadas": ejecutadas,
                 "tipo_eventos": list(TIPOS_BARRIDA)},
        "rondas": [r.a_dict() for r in rondas],
        "detencion": detencion,
        "parcial": detencion == "presupuesto",
        "tiempo_s": round(time.monotonic() - t0, 1),
        "total_escritos": total_escritos,
        "total_vistos": total_vistos,
        "expedientes": ultima_foto,
        "contacto": _resumen_contacto(ultima_foto.get("expedientes", [])),
        "candidatos": ultima_candidatos,
    }
