"""La app es instalable (PWA): manifest + service worker + iconos.

Base para generar el APK firmado con PWABuilder.
"""
import importlib

from fastapi.testclient import TestClient

api = importlib.import_module("hd_scraper.api.app")
cli = TestClient(api.app)


def test_manifest():
    r = cli.get("/manifest.webmanifest")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/manifest+json")
    d = r.json()
    assert d["start_url"] == "/admin" and d["display"] == "standalone"
    sizes = {i["sizes"] for i in d["icons"]}
    assert "192x192" in sizes and "512x512" in sizes  # requisito de instalabilidad


def test_service_worker_con_fetch_handler():
    r = cli.get("/sw.js")
    assert r.status_code == 200
    assert "application/javascript" in r.headers["content-type"]
    assert "addEventListener('fetch'" in r.text  # Chrome lo exige para instalar


def test_iconos_png():
    for p, n in (("/icon-192.png", 192), ("/icon-512.png", 512), ("/apple-touch-icon.png", 180)):
        r = cli.get(p)
        assert r.status_code == 200 and r.headers["content-type"] == "image/png"
        assert r.content[:8] == b"\x89PNG\r\n\x1a\n"  # firma PNG


def test_admin_enlaza_pwa():
    h = cli.get("/admin").text
    assert 'rel="manifest"' in h
    assert "serviceWorker.register" in h
    assert 'name="theme-color"' in h
