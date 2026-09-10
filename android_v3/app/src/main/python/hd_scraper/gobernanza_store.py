"""Persistencia de la Capa 12 — Gobernanza Científica.

Separada a propósito de ``gobernanza.py`` (que es 100% puro): aquí vive el único
código que escribe en las tablas de gobernanza. NO calcula nada nuevo: almacena
lo que las funciones puras ya produjeron. La escritura es **idempotente y
determinista** (select-then-insert por hash/id), portable entre SQLite y
PostgreSQL sin sintaxis de UPSERT específica de motor.
"""
from __future__ import annotations

import json

from .db.models import ahora_iso


def _existe(db, tabla: str, columna: str, valor: str) -> bool:
    row = db.fetch_one(f"SELECT 1 FROM {tabla} WHERE {columna} = ? LIMIT 1", (valor,))
    return row is not None


def persistir_versionado(db, registros: list[dict]) -> int:
    """Registra versiones de componentes (única por componente+hash)."""
    ahora = ahora_iso()
    n = 0
    for r in registros:
        comp, h = r.get("componente", ""), r.get("hash", "")
        ya = db.fetch_one(
            "SELECT 1 FROM versionado_modelo WHERE componente = ? AND hash_contenido = ? LIMIT 1",
            (comp, h))
        if ya is None:
            db.execute(
                "INSERT INTO versionado_modelo (componente, version, hash_contenido, "
                "registrado_en) VALUES (?, ?, ?, ?)",
                (comp, r.get("version", ""), h, ahora))
            n += 1
    return n


def persistir_huella(db, org: str, huella: dict) -> bool:
    """Guarda la huella digital (única por hash). Devuelve True si insertó."""
    if _existe(db, "huellas_digitales", "hash", huella.get("hash", "")):
        return False
    db.execute(
        "INSERT INTO huellas_digitales (org_nombre, huella_id, hash, version, "
        "versiones_json, hashes_json, fecha, creado_en) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (org, huella.get("id", ""), huella.get("hash", ""), huella.get("version", ""),
         json.dumps(huella.get("versiones", {}), ensure_ascii=False),
         json.dumps(huella.get("hashes", {}), ensure_ascii=False),
         huella.get("fecha", "") or ahora_iso(), ahora_iso()))
    return True


def persistir_bitacora(db, org: str, hash_expediente: str, bitacora: dict) -> int:
    """Registra las decisiones de la bitácora (idempotente por hash_expediente)."""
    if _existe(db, "bitacora_decisiones", "hash_expediente", hash_expediente):
        return 0
    ahora = ahora_iso()
    n = 0
    for d in bitacora.get("decisiones", []):
        db.execute(
            "INSERT INTO bitacora_decisiones (org_nombre, hash_expediente, tipo, regla, "
            "resultado, detalle, version_algoritmo, registrado_en) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (org, hash_expediente, d.get("tipo", ""), d.get("regla", ""),
             d.get("resultado", ""), d.get("detalle", ""),
             d.get("version_algoritmo", ""), ahora))
        n += 1
    return n


def persistir_auditoria(db, org: str, auditoria: dict) -> bool:
    """Guarda la auditoría (única por hash del expediente)."""
    resumen = auditoria.get("resumen", {})
    h = resumen.get("hash", "")
    if _existe(db, "auditoria_expedientes", "hash_expediente", h):
        return False
    db.execute(
        "INSERT INTO auditoria_expedientes (org_nombre, hash_expediente, veredicto, "
        "integra, consistente, reproducible, auditoria_json, creado_en) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (org, h, resumen.get("veredicto", ""),
         1 if resumen.get("integra") else 0,
         1 if resumen.get("consistente") else 0,
         1 if resumen.get("reproducible") else 0,
         json.dumps(auditoria, ensure_ascii=False), ahora_iso()))
    return True


def persistir_certificado(db, org: str, certificado: dict) -> bool:
    """Guarda el certificado (único por certificado_id)."""
    cid = certificado.get("certificado_id", "")
    if _existe(db, "certificados", "certificado_id", cid):
        return False
    db.execute(
        "INSERT INTO certificados (org_nombre, certificado_id, hash, version, estado, "
        "veredicto, nivel_evidencia, nivel_confianza, solidez, suficiencia, firma_motor, "
        "fecha, certificado_json, creado_en) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (org, cid, certificado.get("hash", ""), certificado.get("version", ""),
         certificado.get("estado", ""), certificado.get("veredicto", ""),
         certificado.get("nivel_evidencia", ""), certificado.get("nivel_confianza", ""),
         certificado.get("solidez", 0), certificado.get("suficiencia", 0),
         certificado.get("firma_motor", ""), certificado.get("fecha", "") or ahora_iso(),
         json.dumps(certificado, ensure_ascii=False), ahora_iso()))
    return True


def persistir_gobernanza(db, org: str, auditoria: dict) -> dict:
    """Persiste todo el paquete de gobernanza de una auditoría (idempotente).

    Reúne huella, versionado, bitácora, auditoría y certificado en una sola
    transacción lógica. Reejecutarlo no duplica filas.
    """
    huella = (auditoria.get("huellas_digitales") or [{}])[0]
    hash_exp = auditoria.get("resumen", {}).get("hash", "")
    return {
        "versionado": persistir_versionado(db, auditoria.get("versionado", [])),
        "huella": persistir_huella(db, org, huella),
        "bitacora": persistir_bitacora(db, org, hash_exp, auditoria.get("bitacora", {})),
        "auditoria": persistir_auditoria(db, org, auditoria),
        "certificado": persistir_certificado(db, org, auditoria.get("certificado", {})),
    }
