"""Capa 6 — Motor de Drift Narrativo: comparador determinista.

Compara dos snapshots consecutivos de la misma organización y tipo de página.
Emite Evidencias Narrativas tipificadas — cambios objetivos observados en el
discurso público. NUNCA interpreta, NUNCA genera hipótesis, NUNCA produce
Deuda Cultural™.

Tipos de cambio permitidos (cerrados):
  - posicionamiento: cambió cómo se define la organización
  - audiencia: cambió a quién se dirige
  - lenguaje: cambió el tono o vocabulario
  - identidad: cambió nombre, marca o descripción fundamental
  - concepto_nuevo: apareció un concepto antes ausente
  - concepto_eliminado: desapareció un concepto antes presente
  - contradiccion: el texto nuevo contradice al anterior
  - cambio_ontologico: cambió la categoría o marco conceptual
"""
from __future__ import annotations

import difflib
import hashlib
import logging
import re
from typing import Optional

from .db.database import get_db
from .db.models import ahora_iso

logger = logging.getLogger("hd_scraper.drift_compare")

TIPOS_CAMBIO = (
    "posicionamiento", "audiencia", "lenguaje", "identidad",
    "concepto_nuevo", "concepto_eliminado", "contradiccion", "cambio_ontologico",
)

_MARCADORES_POSICIONAMIENTO = (
    "somos", "we are", "nuestra misión", "our mission", "nos dedicamos",
    "nuestro propósito", "our purpose", "lo que hacemos", "what we do",
    "líderes en", "leaders in", "la plataforma", "the platform",
    "infraestructura", "infrastructure",
)

_MARCADORES_AUDIENCIA = (
    "para ", "for ", "dirigido a", "designed for", "nuestros clientes",
    "our customers", "empresas", "pymes", "consumidores", "usuarios",
    "latinoamérica", "latam", "global", "mercado", "market",
)

_MARCADORES_IDENTIDAD = (
    "somos ", "we are ", "nuestra marca", "our brand", "nuestro nombre",
    "fundada en", "founded in",
)


def _normalizar_para_comparar(texto: str) -> str:
    """Normalización agresiva: minúsculas, sin puntuación extra, espacios limpios."""
    t = (texto or "").lower()
    t = re.sub(r"[^\w\sáéíóúüñ]", " ", t)
    return " ".join(t.split())


def _extraer_conceptos(texto: str) -> set[str]:
    """Extrae conceptos clave (frases de 2-3 palabras que se repiten o son sustantivas)."""
    palabras = _normalizar_para_comparar(texto).split()
    stop = {"de", "la", "el", "en", "y", "a", "que", "los", "las", "un", "una",
            "del", "al", "con", "por", "para", "es", "se", "no", "su", "más",
            "the", "a", "an", "and", "or", "of", "in", "to", "for", "is", "are",
            "we", "our", "with", "on", "at", "by", "this", "that"}
    conceptos = set()
    for i in range(len(palabras) - 1):
        if palabras[i] not in stop and palabras[i + 1] not in stop:
            bigrama = f"{palabras[i]} {palabras[i+1]}"
            if len(bigrama) > 5:
                conceptos.add(bigrama)
    return conceptos


def _contiene_marcador(texto: str, marcadores: tuple[str, ...]) -> bool:
    t = texto.lower()
    return any(m in t for m in marcadores)


def _fragmentos_cambiados(antes: str, despues: str) -> list[tuple[str, str]]:
    """Identifica fragmentos que cambiaron entre dos textos (por párrafo)."""
    lineas_a = [l.strip() for l in antes.splitlines() if l.strip()]
    lineas_d = [l.strip() for l in despues.splitlines() if l.strip()]
    cambios = []
    matcher = difflib.SequenceMatcher(None, lineas_a, lineas_d)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            frag_a = "\n".join(lineas_a[i1:i2])
            frag_d = "\n".join(lineas_d[j1:j2])
            norm_a = _normalizar_para_comparar(frag_a)
            norm_d = _normalizar_para_comparar(frag_d)
            if norm_a != norm_d:
                cambios.append((frag_a, frag_d))
        elif tag == "delete":
            cambios.append(("\n".join(lineas_a[i1:i2]), ""))
        elif tag == "insert":
            cambios.append(("", "\n".join(lineas_d[j1:j2])))
    return cambios


def detectar_tipo_cambio(antes: str, despues: str) -> Optional[str]:
    """Clasifica un cambio por tipo. Solo detecta, no interpreta."""
    if not antes and despues:
        return "concepto_nuevo"
    if antes and not despues:
        return "concepto_eliminado"
    if not antes and not despues:
        return None

    a_lower = antes.lower()
    d_lower = despues.lower()

    if _contiene_marcador(a_lower, _MARCADORES_IDENTIDAD) or \
       _contiene_marcador(d_lower, _MARCADORES_IDENTIDAD):
        return "identidad"

    if _contiene_marcador(a_lower, _MARCADORES_POSICIONAMIENTO) or \
       _contiene_marcador(d_lower, _MARCADORES_POSICIONAMIENTO):
        return "posicionamiento"

    if _contiene_marcador(a_lower, _MARCADORES_AUDIENCIA) or \
       _contiene_marcador(d_lower, _MARCADORES_AUDIENCIA):
        return "audiencia"

    ratio = difflib.SequenceMatcher(
        None, _normalizar_para_comparar(antes),
        _normalizar_para_comparar(despues),
    ).ratio()
    if ratio < 0.3:
        return "cambio_ontologico"

    return "lenguaje"


def comparar(snapshot_anterior: dict, snapshot_actual: dict) -> list[dict]:
    """Compara dos snapshots y emite evidencias narrativas.

    Solo compara snapshots del mismo org_nombre y tipo_pagina.
    Retorna lista de evidencias narrativas (sin persistir).
    """
    if snapshot_anterior["org_nombre"] != snapshot_actual["org_nombre"]:
        return []
    if snapshot_anterior["tipo_pagina"] != snapshot_actual["tipo_pagina"]:
        return []

    texto_antes = snapshot_anterior.get("texto", "")
    texto_despues = snapshot_actual.get("texto", "")

    norm_antes = _normalizar_para_comparar(texto_antes)
    norm_despues = _normalizar_para_comparar(texto_despues)
    if norm_antes == norm_despues:
        return []

    evidencias = []
    cambios = _fragmentos_cambiados(texto_antes, texto_despues)

    for frag_antes, frag_despues in cambios:
        if len((frag_antes or "") + (frag_despues or "")) < 10:
            continue

        tipo = detectar_tipo_cambio(frag_antes, frag_despues)
        if tipo is None:
            continue

        if tipo == "concepto_nuevo":
            descripcion = f"Apareció: {frag_despues[:200]}"
        elif tipo == "concepto_eliminado":
            descripcion = f"Desapareció: {frag_antes[:200]}"
        else:
            descripcion = f"Cambió ({tipo})"

        evidencias.append({
            "org_nombre": snapshot_actual["org_nombre"],
            "tipo_cambio": tipo,
            "tipo_pagina": snapshot_actual["tipo_pagina"],
            "fragmento_antes": (frag_antes or "")[:500],
            "fragmento_despues": (frag_despues or "")[:500],
            "descripcion": descripcion,
            "snapshot_anterior_id": snapshot_anterior["id"],
            "snapshot_actual_id": snapshot_actual["id"],
        })

    conceptos_antes = _extraer_conceptos(texto_antes)
    conceptos_despues = _extraer_conceptos(texto_despues)
    nuevos = conceptos_despues - conceptos_antes
    eliminados = conceptos_antes - conceptos_despues

    for c in sorted(nuevos)[:5]:
        evidencias.append({
            "org_nombre": snapshot_actual["org_nombre"],
            "tipo_cambio": "concepto_nuevo",
            "tipo_pagina": snapshot_actual["tipo_pagina"],
            "fragmento_antes": "",
            "fragmento_despues": c,
            "descripcion": f"Concepto nuevo: «{c}»",
            "snapshot_anterior_id": snapshot_anterior["id"],
            "snapshot_actual_id": snapshot_actual["id"],
        })

    for c in sorted(eliminados)[:5]:
        evidencias.append({
            "org_nombre": snapshot_actual["org_nombre"],
            "tipo_cambio": "concepto_eliminado",
            "tipo_pagina": snapshot_actual["tipo_pagina"],
            "fragmento_antes": c,
            "fragmento_despues": "",
            "descripcion": f"Concepto eliminado: «{c}»",
            "snapshot_anterior_id": snapshot_anterior["id"],
            "snapshot_actual_id": snapshot_actual["id"],
        })

    return evidencias


def persistir_evidencias(evidencias: list[dict]) -> int:
    """Guarda las evidencias narrativas en la base de datos. Retorna nuevas."""
    db = get_db()
    ahora = ahora_iso()
    nuevas = 0
    for ev in evidencias:
        dedup = hashlib.sha256(
            f"{ev['org_nombre']}|{ev['tipo_cambio']}|{ev['tipo_pagina']}|"
            f"{ev['snapshot_anterior_id']}|{ev['snapshot_actual_id']}|"
            f"{ev.get('fragmento_antes','')}".encode()
        ).hexdigest()[:32]

        cur = db.execute(
            """INSERT INTO drift_evidencias
                 (org_nombre, tipo_cambio, tipo_pagina, fragmento_antes,
                  fragmento_despues, descripcion, snapshot_anterior_id,
                  snapshot_actual_id, hash_dedup, detectado_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (hash_dedup) DO NOTHING""",
            (ev["org_nombre"], ev["tipo_cambio"], ev["tipo_pagina"],
             ev.get("fragmento_antes", ""), ev.get("fragmento_despues", ""),
             ev["descripcion"],
             ev["snapshot_anterior_id"], ev["snapshot_actual_id"],
             dedup, ahora),
        )
        if getattr(cur, "rowcount", 0):
            nuevas += 1
    return nuevas
