"""Reparación BC-I ↔ BC-II — Candidato Comercial referencial.

La costura débil del modelo de dominio (docs/0002, docs/0007 · Prioridad 1) era
la unión NOMINAL entre la *Organización Observada* (BC-I, Motor A) y el
*Prospecto* (BC-II): se unían por nombre de empresa / ``hash_dedup`` del nombre.

Este módulo materializa cada organización detectada como un **Candidato
Comercial independiente y trazable**, sustituyendo esa unión nominal por una
**identidad referencial determinista**:

    organización (BC-I)  →  candidato  →  prospecto (BC-II)
                                  ↘  expediente (BC-I)  →  evidencia

- ``candidato_id`` es el ID estable por organización/candidato: sha256 del
  nombre normalizado. Determinista: reprocesar la misma organización produce
  siempre el mismo candidato (mismo insumo ⇒ mismo ID).
- Cada candidato es independiente: sus transiciones y sus referencias a
  evidencia jamás se mezclan con las de otro candidato.
- Cada transición (Detectado / Observado / Descartado) conserva la referencia
  a la evidencia que la sustenta (``evidencia_id``, ``evidencia_url``,
  ``evidencia_texto``).
- **Regla Cero (G0):** ninguna entidad de BC-II puede avanzar sin un peritaje
  validado originado en BC-I. Se aplica como guard de dominio en la transición
  ``detectado → observado``: exige dictamen con veredicto VALIDADA o
  VALIDADA_PARCIAL y sin hipótesis bloqueada. Sin peritaje validado, el
  candidato no avanza.
- ``organizacion_id`` (índice estable de ``observatorio._id_map``) se reutiliza
  cuando el materializador dispone del conjunto de expedientes: así el
  candidato referencia la misma identidad de organización que expone el
  Expediente Vivo.

Estrictamente determinista y sin IA. NO decide contacto ni acción comercial:
las transiciones de Observado/Descartado son del operador (G0 solo las habilita
o las bloquea); el materializado solo registra el hecho de la detección.
"""
from __future__ import annotations

import hashlib
import logging

from .db.models import normalizar_empresa

logger = logging.getLogger("hd_scraper.candidato")

# ── Estados del candidato (máquina de estados explícita y cerrada) ────────────
# - detectado:   la organización apareció en el radar (hay evidencia en BC-I).
# - observado:   bajo observación activa, respaldada por un peritaje validado (G0).
# - descartado:  se descartó (decisión del operador, siempre con motivo y evidencia).
ESTADOS = ("detectado", "observado", "descartado")

ESTADOS_LABELS = {
    "detectado": "Detectado",
    "observado": "Observado",
    "descartado": "Descartado",
}

# Sucesores válidos por estado. "" es el estado previo a la creación.
_ESTADO_SUCESORES = {
    "": ("detectado",),
    "detectado": ("observado", "descartado"),
    "observado": ("detectado", "descartado"),
    "descartado": ("detectado",),
}

# Veredictos del Dictamen Científico que satisfacen la Regla Cero.
G0_VEREDICTOS = ("VALIDADA", "VALIDADA_PARCIAL")

_LEGACY_SALT = "candidato:v1"


class G0Denied(Exception):
    """La Regla Cero bloqueó la transición: no hay peritaje validado."""


def candidato_id(org_nombre: str) -> str:
    """ID estable por organización/candidato.

    sha256 del nombre normalizado (``normalizar_empresa``: minúsculas y sin
    espacios redundantes). Determinista y referencial: A y B distintos ⇒ IDs
    distintos; reprocesar A ⇒ el mismo ID. Es la clave de la unión BC-I ↔ BC-II.
    """
    base = f"{_LEGACY_SALT}|{normalizar_empresa(org_nombre)}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def hash_dedup_legacy(org_nombre: str) -> str:
    """Hash legacy de ``pipeline_comercial`` (sha256 de minúsculas, 32 chars).

    Se conserva para mapear 1:1 los registros de pipeline ya existentes (los
    datos de hoy no se rompen) con la identidad referencial del candidato.
    """
    return hashlib.sha256(
        (org_nombre or "").strip().lower().encode("utf-8")
    ).hexdigest()[:32]


def _evidencia_mejor(exp: dict) -> dict:
    """Evidencia con mayor confianza del expediente (pura, sin red)."""
    evs = list(exp.get("evidencias", []) or [])
    if isinstance(evs and evs[0], dict) and "items" in (evs[0] or {}):
        evs = list((exp.get("evidencias") or {}).get("items", []) or [])
    mejores = sorted(
        (e for e in evs if (e.get("url") or e.get("url_fuente"))),
        key=lambda e: float(e.get("confianza") or 0.0),
        reverse=True,
    )
    if not mejores:
        return {}
    e = mejores[0]
    return {
        "url": (e.get("url") or e.get("url_fuente") or "").strip(),
        "texto": (e.get("texto") or e.get("cita_textual") or "").strip(),
    }


def _resolver_id_evidencia(db, url: str):
    """Resuelve el ``evidencias.id`` por URL fuente (referencia estable)."""
    if not url or db is None:
        return None
    try:
        fila = db.fetch_one(
            "SELECT id FROM evidencias WHERE url_fuente = ? ORDER BY id LIMIT 1",
            (url,),
        )
        return fila["id"] if fila else None
    except Exception:  # pragma: no cover - defensivo, nunca tumba la materialización
        return None


def g0_permitido(exp: dict) -> dict:
    """Regla Cero: ¿el peritaje de BC-I habilita el avance del candidato?

    Requiere dictamen presente, veredicto VALIDADA/VALIDADA_PARCIAL e hipótesis
    NO bloqueada. Sin dictamen ⇒ NO avanza (la ciencia es el candado).
    Pura y determinista: mismo expediente ⇒ mismo resultado.
    """
    val = exp.get("validacion_cientifica") or {}
    if not val:
        return {"permitido": False, "veredicto": "", "hipotesis_bloqueada": True,
                "motivo": "sin dictamen científico: la Regla Cero exige peritaje validado"}
    veredicto = val.get("veredicto", "") or ""
    bloqueada = bool(val.get("hipotesis_bloqueada", exp.get("hipotesis_bloqueada", False)))
    permitido = not bloqueada and veredicto in G0_VEREDICTOS
    return {
        "permitido": permitido,
        "veredicto": veredicto,
        "hipotesis_bloqueada": bloqueada,
        "motivo": ("" if permitido else
                   f"dictamen {veredicto or 'ausente'}"
                   f"{' con hipótesis bloqueada' if bloqueada else ''}"
                   ": la Regla Cero impide avanzar sin peritaje validado"),
    }


def _prospecto_referencia(db, org_nombre: str):
    """Prospecto (BC-II) referenciado por nombre normalizado, si existe."""
    if db is None:
        return None
    try:
        fila = db.fetch_one(
            "SELECT id, nombre, categoria FROM prospectos "
            "WHERE LOWER(TRIM(nombre)) = ? ORDER BY id LIMIT 1",
            (normalizar_empresa(org_nombre),),
        )
        return {"id": fila["id"], "nombre": fila["nombre"],
                "categoria": fila["categoria"]} if fila else None
    except Exception:  # pragma: no cover
        return None


def _registrar_transicion(
    db, org_nombre: str, estado_desde: str, estado_hasta: str, *,
    notas: str = "", evidencia: dict | None = None, expediente_hash: str = "",
) -> int:
    """Registra una transición con su referencia a evidencia. Devuelve el id."""
    evidencia = evidencia or {}
    ev_id = evidencia.get("id")
    if ev_id is None:
        ev_id = _resolver_id_evidencia(db, evidencia.get("url", ""))
    db.execute(
        """INSERT INTO candidato_transiciones
             (candidato_id, org_nombre, estado_desde, estado_hasta, notas,
              evidencia_id, evidencia_url, evidencia_texto, expediente_hash, fecha)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (candidato_id(org_nombre), org_nombre.strip(), estado_desde, estado_hasta,
         notas, ev_id, evidencia.get("url") or "", evidencia.get("texto") or "",
         expediente_hash, _ahora()),
    )
    fila = db.fetch_one(
        "SELECT id FROM candidato_transiciones "
        "WHERE candidato_id = ? ORDER BY id DESC LIMIT 1",
        (candidato_id(org_nombre),),
    )
    return fila["id"] if fila else -1


def _ahora() -> str:
    from .db.models import ahora_iso
    return ahora_iso()


def asegurar_candidato(
    db, org_nombre: str, exp: dict | None = None,
) -> dict:
    """Materializa un candidato para la organización, si aún no existe.

    Idempotente: reprocesar la misma organización devuelve el mismo candidato
    sin duplicar filas ni transiciones. La transición inicial ``→ detectado``
    se registra SOLO al crear el candidato y referencia la mejor evidencia
    disponible (url + texto + ``evidencias.id`` resuelto). ``exp`` puede ser un
    expediente de BC-I (con ``evidencias``, ``huella``); sin él, la evidencia
    se resuelve desde la base por nombre de empresa.
    """
    cid = candidato_id(org_nombre)
    org = (org_nombre or "").strip()

    existente = db.fetch_one(
        "SELECT * FROM candidatos WHERE candidato_id = ?", (cid,),
    )
    if existente:
        return {"accion": "existente", "candidato_id": cid,
                "id": existente["id"], "estado": existente["estado"]}

    evidencia = _evidencia_mejor(exp) if exp else {}
    if not evidencia:
        try:
            fila = db.fetch_one(
                "SELECT id, url_fuente, cita_textual FROM evidencias "
                "WHERE empresa_mencionada = ? ORDER BY id LIMIT 1",
                (org,),
            )
            if fila:
                evidencia = {"id": fila["id"], "url": fila["url_fuente"],
                             "texto": fila["cita_textual"]}
        except Exception:  # pragma: no cover
            evidencia = {}

    expediente_hash = (exp or {}).get("huella") or ""
    prospecto = _prospecto_referencia(db, org)

    pid = db.insert_returning_id(
        """INSERT INTO candidatos
             (candidato_id, org_nombre, estado, prospecto_id, expediente_hash,
              hash_dedup, creado_en, actualizado_en)
           VALUES (?, ?, 'detectado', ?, ?, ?, ?, ?)""",
        (cid, org, (prospecto or {}).get("id"), expediente_hash,
         hash_dedup_legacy(org), _ahora(), _ahora()),
    )
    _registrar_transicion(db, org, "", "detectado",
                          evidencia=evidencia, expediente_hash=expediente_hash)
    return {"accion": "creado", "candidato_id": cid, "id": pid,
            "estado": "detectado", "prospecto_id": (prospecto or {}).get("id"),
            "expediente_hash": expediente_hash}


def materializar_candidatos(db, exps: list[dict]) -> dict:
    """Materializa cada organización detectada como candidato independiente.

    Recorre los expedientes de BC-I ya construidos (evidencia + análisis +
    dictamen + gobernanza), materializa un candidato por organización (UPSERT
    idempotente por ``candidato_id``), refresca las referencias referenciales
    (``prospecto_id``, ``expediente_hash``, ``organizacion_id``) y devuelve un
    reporte determinista. Sin IA y sin decisión comercial.
    """
    from .observatorio import _id_map

    idm = _id_map(exps)
    creados, actualizados = 0, 0
    items = []
    for exp in exps:
        org = (exp.get("nombre") or "").strip()
        if not org:
            continue
        cid = candidato_id(org)
        expediente_hash = exp.get("huella") or ""
        prospecto = _prospecto_referencia(db, org)
        org_id = idm.get(org)

        existente = db.fetch_one(
            "SELECT * FROM candidatos WHERE candidato_id = ?", (cid,),
        )
        if existente:
            db.execute(
                """UPDATE candidatos SET
                     org_nombre = ?, organizacion_id = ?, prospecto_id = ?,
                     expediente_hash = ?, actualizado_en = ?
                   WHERE candidato_id = ?""",
                (org, org_id, (prospecto or {}).get("id"), expediente_hash,
                 _ahora(), cid),
            )
            actualizados += 1
            estado = existente["estado"]
        else:
            pid = db.insert_returning_id(
                """INSERT INTO candidatos
                     (candidato_id, org_nombre, estado, prospecto_id,
                      expediente_hash, hash_dedup, creado_en, actualizado_en)
                   VALUES (?, ?, 'detectado', ?, ?, ?, ?, ?)""",
                (cid, org, (prospecto or {}).get("id"), expediente_hash,
                 hash_dedup_legacy(org), _ahora(), _ahora()),
            )
            creados += 1
            estado = "detectado"
            _registrar_transicion(db, org, "", "detectado",
                                  evidencia=_evidencia_mejor(exp),
                                  expediente_hash=expediente_hash)

        g0 = g0_permitido(exp)
        items.append({
            "candidato_id": cid,
            "org_nombre": org,
            "organizacion_id": org_id,
            "estado": estado,
            "prospecto_id": (prospecto or {}).get("id"),
            "expediente_hash": expediente_hash,
            "g0": g0,
        })

    items.sort(key=lambda i: (i["org_nombre"],))
    return {
        "materializados": creados,
        "actualizados": actualizados,
        "total": len(items),
        "por_estado": {e: sum(1 for i in items if i["estado"] == e) for e in ESTADOS},
        "g0_permitido": sum(1 for i in items if i["g0"]["permitido"]),
        "candidatos": items,
    }


def _validar_transicion(org_nombre: str, estado_desde: str, estado_hasta: str) -> None:
    if estado_hasta not in ESTADOS:
        raise ValueError(
            f"Estado inválido: {estado_hasta}. Válidos: {ESTADOS}")
    if estado_desde not in _ESTADO_SUCESORES:
        raise ValueError(f"Estado de origen inválido: {estado_desde}")
    if estado_hasta not in _ESTADO_SUCESORES[estado_desde]:
        raise ValueError(
            f"Transición inválida: {estado_desde or 'creación'} → {estado_hasta}")


def _estado_actual(db, org_nombre: str) -> str:
    fila = db.fetch_one(
        "SELECT estado FROM candidatos WHERE candidato_id = ?",
        (candidato_id(org_nombre),),
    )
    return fila["estado"] if fila else ""


def observar(db, org_nombre: str, exp: dict | None = None,
             evidencia: dict | None = None, notas: str = "") -> dict:
    """Transición ``detectado → observado``, gateada por la Regla Cero (G0).

    Sin dictamen científico validado (veredicto VALIDADA/VALIDADA_PARCIAL e
    hipótesis no bloqueada) el candidato NO avanza: se lanza ``G0Denied`` con
    el motivo. La transición conserva la referencia a la evidencia que la
    sustenta.
    """
    cid = candidato_id(org_nombre)
    estado = _estado_actual(db, org_nombre) or "detectado"
    _validar_transicion(org_nombre, estado, "observado")

    g0 = g0_permitido(exp or {})
    if not g0["permitido"]:
        raise G0Denied(g0["motivo"])

    expediente_hash = (exp or {}).get("huella") or ""
    _registrar_transicion(db, org_nombre, estado, "observado",
                          notas=notas, evidencia=evidencia,
                          expediente_hash=expediente_hash)
    db.execute(
        "UPDATE candidatos SET estado = 'observado', actualizado_en = ? "
        "WHERE candidato_id = ?", (_ahora(), cid),
    )
    return {"candidato_id": cid, "org_nombre": org_nombre,
            "estado_desde": estado, "estado": "observado", "g0": g0}


def descartar(db, org_nombre: str, notas: str = "",
              evidencia: dict | None = None, exp: dict | None = None) -> dict:
    """Transición → ``descartado`` (decisión del operador, siempre con motivo).

    La evidencia que sustenta el descarte queda referenciada en la transición.
    Permite re-detección futura (descartado → detectado) si aparece señal nueva.
    """
    cid = candidato_id(org_nombre)
    estado = _estado_actual(db, org_nombre) or "detectado"
    _validar_transicion(org_nombre, estado, "descartado")

    expediente_hash = (exp or {}).get("huella") or ""
    _registrar_transicion(db, org_nombre, estado, "descartado",
                          notas=notas, evidencia=evidencia,
                          expediente_hash=expediente_hash)
    db.execute(
        "UPDATE candidatos SET estado = 'descartado', actualizado_en = ? "
        "WHERE candidato_id = ?", (_ahora(), cid),
    )
    return {"candidato_id": cid, "org_nombre": org_nombre,
            "estado_desde": estado, "estado": "descartado"}


def _transiciones(db, cid: str) -> list[dict]:
    filas = db.fetch_all(
        "SELECT * FROM candidato_transiciones WHERE candidato_id = ? "
        "ORDER BY id ASC", (cid,),
    )
    return [dict(f) for f in filas]


def _con_organizacion_id(candidato: dict, exps: list[dict] | None) -> dict:
    if exps:
        from .observatorio import _id_map
        candidato["organizacion_id"] = _id_map(exps).get(candidato.get("org_nombre", ""))
    else:
        candidato["organizacion_id"] = candidato.get("organizacion_id")
    return candidato


def obtener_candidato(db, org_nombre: str, exps: list[dict] | None = None) -> dict | None:
    """Detalle del candidato con la cadena referencial completa.

    organización → candidato → prospecto → expediente → evidencia.
    ``organizacion_id`` se recalcula con ``observatorio._id_map`` sobre el
    conjunto de expedientes cuando el llamador lo aporta (misma identidad que
    expone el Expediente Vivo); si no, se devuelve el snapshot persistido.
    """
    cid = candidato_id(org_nombre)
    fila = db.fetch_one(
        "SELECT * FROM candidatos WHERE candidato_id = ?", (cid,),
    )
    if not fila:
        return None
    c = dict(fila)
    c["candidato_id"] = cid
    c["etiqueta_estado"] = ESTADOS_LABELS.get(c["estado"], c["estado"])
    c["transiciones"] = _transiciones(db, cid)
    c["prospecto"] = None
    if c.get("prospecto_id"):
        p = db.fetch_one(
            "SELECT id, nombre, categoria, vertical FROM prospectos WHERE id = ?",
            (c["prospecto_id"],),
        )
        c["prospecto"] = dict(p) if p else None
    return _con_organizacion_id(c, exps)


def listar_candidatos(db, estado: str | None = None,
                      exps: list[dict] | None = None) -> dict:
    """Lista los candidatos, opcionalmente filtrados por estado."""
    if estado and estado not in ESTADOS:
        raise ValueError(f"Estado inválido: {estado}. Válidos: {ESTADOS}")
    if estado:
        filas = db.fetch_all(
            "SELECT * FROM candidatos WHERE estado = ? ORDER BY org_nombre ASC",
            (estado,),
        )
    else:
        filas = db.fetch_all(
            "SELECT * FROM candidatos ORDER BY org_nombre ASC",)
    items = []
    for f in filas:
        c = dict(f)
        c["candidato_id"] = c["candidato_id"]
        c["etiqueta_estado"] = ESTADOS_LABELS.get(c["estado"], c["estado"])
        c["transiciones"] = _transiciones(db, c["candidato_id"])
        items.append(_con_organizacion_id(c, exps))
    return {
        "total": len(items),
        "por_estado": {e: sum(1 for i in items if i["estado"] == e) for e in ESTADOS},
        "candidatos": items,
    }
