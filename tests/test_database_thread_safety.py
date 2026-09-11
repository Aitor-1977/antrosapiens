"""Concurrencia sobre la conexión compartida (2026-09-11).

Causa raíz real del timeout intermitente en producción, diagnosticada tras
descartar Neon/vercel.json: los endpoints de `hd_scraper/api/app.py` son
`def` síncronos, así que Starlette los corre en hilos del threadpool. Todos
comparten `_db_singleton` (`hd_scraper/db/database.py:get_db`), una única
conexión. psycopg (y sqlite3 con `check_same_thread=False`, usado aquí para
poder probarlo sin Postgres) no son seguros para uso concurrente de la misma
conexión desde varios hilos sin sincronización: dos `execute()` simultáneos
pueden entrelazar el protocolo de wire y dejarla en un estado corrupto.

Este test golpea la MISMA instancia de `Database` desde muchos hilos a la
vez. Sin el `threading.Lock` por instancia (`Database._lock`), esto debería
fallar de forma intermitente (excepciones de sqlite3 por acceso concurrente,
o un conteo final que no cuadra). Con el lock, cada operación queda
serializada y el resultado es siempre consistente.
"""
import threading

from hd_scraper.db.models import ahora_iso


def test_muchos_hilos_escribiendo_a_la_vez_no_corrompen_la_conexion(db):
    n_hilos = 24
    errores: list[Exception] = []

    def _escribir(i: int) -> None:
        try:
            db.execute(
                "INSERT INTO rechazos (connector, motivo, payload_json, creado_en) "
                "VALUES (?, ?, ?, ?)",
                (f"hilo-{i}", "prueba_concurrencia", "{}", ahora_iso()),
            )
        except Exception as exc:  # se recoge, no se relanza: se afirma después
            errores.append(exc)

    hilos = [threading.Thread(target=_escribir, args=(i,)) for i in range(n_hilos)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    assert not errores, f"{len(errores)} hilo(s) fallaron: {errores[:3]}"
    fila = db.fetch_one(
        "SELECT COUNT(*) AS n FROM rechazos WHERE motivo = 'prueba_concurrencia'")
    assert fila["n"] == n_hilos


def test_lecturas_y_escrituras_concurrentes_no_bloquean_para_siempre(db):
    """Mezcla execute()/fetch_one()/fetch_all() concurrentes: si el lock no
    cubriera alguna operación, esta prueba podría colgarse (deadlock) o
    lanzar una excepción de sqlite3 por acceso concurrente."""
    n_hilos = 16
    errores: list[Exception] = []

    def _trabajar(i: int) -> None:
        try:
            db.execute(
                "INSERT INTO rechazos (connector, motivo, payload_json, creado_en) "
                "VALUES (?, ?, ?, ?)",
                (f"mix-{i}", "prueba_mixta", "{}", ahora_iso()),
            )
            db.fetch_one("SELECT COUNT(*) AS n FROM rechazos")
            db.fetch_all("SELECT id FROM rechazos LIMIT 5")
        except Exception as exc:
            errores.append(exc)

    hilos = [threading.Thread(target=_trabajar, args=(i,)) for i in range(n_hilos)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=10)

    assert not any(h.is_alive() for h in hilos), "algún hilo quedó colgado"
    assert not errores, f"{len(errores)} hilo(s) fallaron: {errores[:3]}"
