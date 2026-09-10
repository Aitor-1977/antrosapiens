"""Bootstrap del backend RadarHD (Motor A) embebido en la APK.

FASE C (Radar real): arranca la API real de hd-scraper (los mismos endpoints que
consume RadarHD) en un servidor HTTP local (127.0.0.1:8000) dentro del propio
proceso de la app Android, sobre una base SQLite local que se siembra con el
directorio curado de LATAM. La pantalla del Radar (assets/public/index.html)
consuma estos endpoints reales vía fetch.

El arranque es determinista y no depende de red: la base se inicializa con
init_schema() + asegurar_directorio_semilla() (idempotente, sin red). Los
conectores de prensa solo se usan si el operador pulsa "Ejecutar Radar" y hay
egress disponible; sin red, el directorio semilla sigue dando datos reales.
"""
from __future__ import annotations

import os
import threading
import logging

logger = logging.getLogger("hd_android.server")

API_HOST = "127.0.0.1"
API_PORT = 8000
INGEST_TOKEN = "android_v2_local"


def start_server(data_dir: str) -> dict:
    """Inicializa la base y arranca la API real en un hilo demonio.

    ``data_dir`` es el directorio de archivos internos de la app (filesDir),
    donde vive la SQLite local y los assets extra. Devuelve el estado para que
    Kotlin sepa si el arranque fue correcto.
    """
    data_dir = str(data_dir)
    os.makedirs(data_dir, exist_ok=True)

    # --- Configuración de entorno (lectura de la base local) ---------------
    os.environ["HD_DATABASE_URL"] = f"sqlite:///{os.path.join(data_dir, 'hd_scraper.db')}"
    os.environ["HD_RAW_ENABLED"] = "0"
    os.environ["HD_DATA_DIR"] = data_dir
    os.environ["HD_INGEST_TOKEN"] = INGEST_TOKEN
    # La siembra del directorio y la validación de señales no necesitan red.
    os.environ.setdefault("HD_REQUEST_TIMEOUT_S", "8")
    os.environ.setdefault("HD_MAX_RETRIES", "1")

    try:
        from hd_scraper.api.app import app as hd_app
        from fastapi.middleware.cors import CORSMiddleware
        from starlette.middleware.base import BaseHTTPMiddleware

        # CORS abierto: el WebView (origen file:// / null) consume el servidor local.
        hd_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Private Network Access (PNA): desde Android 10+/Chromium, un fetch
        # desde un contexto no seguro (file://) hacia el loopback 127.0.0.1
        # (red privada) se bloquea salvo que la respuesta incluya
        # "Access-Control-Allow-Private-Network: true" —tanto en la respuesta
        # real como en el preflight OPTIONS que dispara la cabecera
        # "x-ingest-token". Sin esto el WebView falla con "Failed to fetch"
        # aunque el servidor local esté vivo.
        class PrivateNetworkMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                resp = await call_next(request)
                resp.headers["Access-Control-Allow-Private-Network"] = "true"
                return resp

        hd_app.add_middleware(PrivateNetworkMiddleware)

        # Calienta la base (init_schema + semilla) antes de servir tráfico.
        from hd_scraper.db.database import get_db
        get_db()

        import uvicorn
        config = uvicorn.Config(
            hd_app,
            host=API_HOST,
            port=API_PORT,
            log_level="info",
            access_log=False,
        )
        server = uvicorn.Server(config)
        t = threading.Thread(target=server.run, daemon=True, name="hd-api")
        t.start()
        logger.info("API RadarHD local en http://%s:%s", API_HOST, API_PORT)
        return {"ok": True, "host": API_HOST, "port": API_PORT}
    except Exception as exc:  # pragma: no cover - el arranque jamás tumba la app
        logger.exception("Fallo al arrancar la API local: %s", exc)
        return {"ok": False, "error": str(exc)}
