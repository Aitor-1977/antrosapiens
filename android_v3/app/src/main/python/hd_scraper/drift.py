"""Capa 6 — Motor de Drift Narrativo: captura de snapshots.

Descarga páginas públicas de una organización, limpia el HTML, extrae texto
y almacena snapshots versionados. NO interpreta, NO genera hipótesis, NO
calcula Deuda Cultural™. Su única responsabilidad es capturar el discurso
público tal cual está en un momento dado.

Flujo:  Sitio web → HTTP GET → BeautifulSoup → texto limpio → snapshot.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Callable, Optional

from bs4 import BeautifulSoup

from .db.database import get_db
from .db.models import ahora_iso

logger = logging.getLogger("hd_scraper.drift")

TIPOS_PAGINA = (
    "homepage", "about", "mision", "propuesta_valor", "manifiesto",
)

ESTADOS_NO_OBSERVABLE = (
    "no_observable", "spa", "error_http", "timeout",
    "contenido_vacio", "wayback", "bloqueado", "robots",
)

RUTAS_POR_TIPO: dict[str, tuple[str, ...]] = {
    "homepage": ("",),
    "about": ("about", "about-us", "nosotros", "quienes-somos", "conocenos"),
    "mision": ("mision", "mission", "proposito", "purpose"),
    "propuesta_valor": ("servicios", "services", "solucion", "soluciones", "solutions", "productos", "products"),
    "manifiesto": ("manifiesto", "manifesto", "valores", "values", "cultura", "culture"),
}


def _limpiar_html(html: str) -> str:
    """Extrae texto visible de HTML, eliminando scripts, estilos y navegación."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript",
                     "iframe", "svg", "form", "button"]):
        tag.decompose()
    texto = soup.get_text(separator="\n", strip=True)
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    return "\n".join(lineas)


def _hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _normalizar_url(base: str, ruta: str) -> str:
    base = base.rstrip("/")
    if not base.startswith("http"):
        base = "https://" + base
    if ruta:
        return f"{base}/{ruta}"
    return base


def capturar_pagina(
    url: str,
    http_get: Callable[[str], str],
) -> dict:
    """Descarga una URL y devuelve texto limpio + estado.

    Retorna {"texto": str, "estado": "ok"|<estado_no_observable>, "url": str}.
    Nunca lanza: los errores se capturan como estados no observables.
    """
    try:
        html = http_get(url)
    except Exception as exc:
        msg = str(exc).lower()
        if "timeout" in msg or "timed out" in msg:
            estado = "timeout"
        elif "403" in msg or "forbidden" in msg:
            estado = "bloqueado"
        elif "404" in msg or "not found" in msg:
            estado = "error_http"
        elif "robot" in msg:
            estado = "robots"
        else:
            estado = "error_http"
        logger.info("Drift: no observable %s — %s (%s)", url, estado, exc)
        return {"texto": "", "estado": estado, "url": url}

    texto = _limpiar_html(html)
    if not texto or len(texto) < 20:
        return {"texto": "", "estado": "contenido_vacio", "url": url}
    if any(marca in html.lower() for marca in (
        "window.__next_data__", "window.__nuxt__", "id=\"__next\"",
        "id=\"app\"", "<noscript>you need to enable javascript",
        "please enable javascript",
    )) and len(texto) < 100:
        return {"texto": "", "estado": "spa", "url": url}

    return {"texto": texto, "estado": "ok", "url": url}


def capturar_snapshot(
    org_nombre: str,
    sitio_web: str,
    http_get: Callable[[str], str],
    tipos: tuple[str, ...] | None = None,
) -> list[dict]:
    """Captura snapshots de las páginas públicas de una organización.

    Para cada tipo de página intenta varias rutas conocidas; guarda el primer
    resultado exitoso. Retorna la lista de snapshots creados (o no observables).
    """
    db = get_db()
    tipos_a_capturar = tipos or TIPOS_PAGINA
    resultados = []

    for tipo in tipos_a_capturar:
        if tipo not in RUTAS_POR_TIPO:
            continue

        capturado = None
        for ruta in RUTAS_POR_TIPO[tipo]:
            url = _normalizar_url(sitio_web, ruta)
            resultado = capturar_pagina(url, http_get)
            if resultado["estado"] == "ok":
                capturado = resultado
                break

        if capturado is None:
            ultimo = capturar_pagina(_normalizar_url(sitio_web, RUTAS_POR_TIPO[tipo][0]), http_get)
            snapshot = _guardar_snapshot(
                db, org_nombre, tipo, ultimo["url"], "",
                estado=ultimo["estado"],
            )
            resultados.append(snapshot)
            continue

        hash_contenido = _hash_texto(capturado["texto"])
        existente = db.fetch_one(
            "SELECT id FROM drift_snapshots "
            "WHERE org_nombre = ? AND tipo_pagina = ? AND hash_contenido = ? "
            "ORDER BY capturado_en DESC LIMIT 1",
            (org_nombre, tipo, hash_contenido),
        )
        if existente:
            resultados.append({
                "org_nombre": org_nombre, "tipo_pagina": tipo,
                "estado": "sin_cambios", "hash": hash_contenido,
            })
            continue

        snapshot = _guardar_snapshot(
            db, org_nombre, tipo, capturado["url"], capturado["texto"],
            estado="ok", hash_contenido=hash_contenido,
        )
        resultados.append(snapshot)

    return resultados


def _guardar_snapshot(
    db, org_nombre: str, tipo_pagina: str, url: str, texto: str,
    estado: str = "ok", hash_contenido: str = "",
) -> dict:
    """Persiste un snapshot y devuelve su representación."""
    ahora = ahora_iso()
    if not hash_contenido and texto:
        hash_contenido = _hash_texto(texto)
    sid = db.insert_returning_id(
        """INSERT INTO drift_snapshots
             (org_nombre, tipo_pagina, url, texto, hash_contenido,
              estado_observable, capturado_en)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (org_nombre, tipo_pagina, url, texto, hash_contenido, estado, ahora),
    )
    return {
        "id": sid, "org_nombre": org_nombre, "tipo_pagina": tipo_pagina,
        "url": url, "estado": estado, "hash": hash_contenido,
        "capturado_en": ahora,
    }


def obtener_snapshot_anterior(
    org_nombre: str, tipo_pagina: str, excluir_id: int,
) -> Optional[dict]:
    """Devuelve el snapshot inmediatamente anterior (solo estado 'ok')."""
    db = get_db()
    row = db.fetch_one(
        "SELECT * FROM drift_snapshots "
        "WHERE org_nombre = ? AND tipo_pagina = ? AND id < ? "
        "AND estado_observable = 'ok' "
        "ORDER BY id DESC LIMIT 1",
        (org_nombre, tipo_pagina, excluir_id),
    )
    return dict(row) if row else None


def obtener_timeline(org_nombre: str) -> dict:
    """Devuelve el timeline completo de drift para una organización."""
    db = get_db()
    snapshots = db.fetch_all(
        "SELECT id, org_nombre, tipo_pagina, url, hash_contenido, "
        "estado_observable, capturado_en FROM drift_snapshots "
        "WHERE org_nombre = ? ORDER BY capturado_en DESC",
        (org_nombre,),
    )
    evidencias = db.fetch_all(
        "SELECT * FROM drift_evidencias "
        "WHERE org_nombre = ? ORDER BY detectado_en DESC",
        (org_nombre,),
    )
    return {
        "org_nombre": org_nombre,
        "snapshots": [dict(s) for s in snapshots],
        "evidencias": [dict(e) for e in evidencias],
        "total_snapshots": len(snapshots),
        "total_evidencias": len(evidencias),
    }
