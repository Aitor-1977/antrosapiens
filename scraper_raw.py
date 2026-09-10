import sqlite3, hashlib, os, sys, urllib.request, urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime

def ingresar_evidencia(url, organizacion, fuente_medio):
    db_path = os.path.expanduser("~/antrosapiens/antrolab.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    req = urllib.request.Request(url, headers={'User-Agent': 'AntroLab/1.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print(f"Error al descargar {url}: {e}")
        return None
    soup = BeautifulSoup(html, 'html.parser')
    titulo = soup.title.string if soup.title else "Sin título"
    for script in soup(["script", "style"]):
        script.extract()
    cuerpo = soup.get_text(separator=' ', strip=True)
    hash_cuerpo = hashlib.sha256(cuerpo.encode('utf-8')).hexdigest()
    cursor.execute("SELECT COUNT(*) FROM evidencia_raw")
    count = cursor.fetchone()[0] + 1
    ev_id = f"EV-{count:04d}"
    captured_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dominio = urllib.parse.urlparse(url).netloc
    try:
        cursor.execute("""
            INSERT INTO evidencia_raw 
            (evidence_id, url, dominio, captured_at, titulo, cuerpo_disponible, organizacion_mencionada, fuente_medio, fragmento_textual, hash_contenido, metodo_captura, extracted_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'python_scraper', 'raw_scraper')
        """, (ev_id, url, dominio, captured_at, titulo, cuerpo, organizacion, fuente_medio, cuerpo[:300], hash_cuerpo))
        conn.commit()
        print(f"-> Evidencia {ev_id} registrada para {organizacion}")
    except sqlite3.IntegrityError:
        print("-> El contenido ya existe en la BD (Hash duplicado).")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python3 scraper_raw.py <URL> <ORGANIZACION> <FUENTE_MEDIO>")
        sys.exit(1)
    ingresar_evidencia(sys.argv[1], sys.argv[2], sys.argv[3])
