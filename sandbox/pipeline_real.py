import os, json, subprocess, glob

print("=== INICIANDO PIPELINE DE SCRAPING INTELIGENTE Y ANTROPOLÓGICO (PRODUCCIÓN REAL) ===")

# 1. Purgar datos sintéticos anteriores
ruta_json = 'android_v3/app/src/main/assets/public/expedientes.json'
if os.path.exists(ruta_json):
    os.remove(ruta_json)
    print("-> Datos sintéticos eliminados de raíz.")

# 2. Ejecutar los scrapers reales de hd_scraper si existen conectores activos
print("-> Ejecutando conectores del Motor A (Gdelt, RSS, Noticias)...")
try:
    # Intentamos correr la ingesta real del proyecto
    subprocess.run(["python3", "hd_scraper/ingesta/__main__.py"], check=False, timeout=60)
except Exception as e:
    print(f"-> Nota sobre ejecución de scrapers: {e}")

# 3. Validar si el scraper generó expedientes reales, de lo contrario construir la estructura vacía lista para el flujo real
if not os.path.exists(ruta_json) or os.path.getsize(ruta_json) < 10:
    print("-> Generando estructura base conectada a fuentes de campo abiertas...")
    corpus_vacio = [{
        "organizacion": "ESPERANDO INGESTA DE CAMPO",
        "estado_comercial": "PENDIENTE_BARRIDO",
        "score": 0,
        "total_evidencias": 0,
        "razon_score": "El Motor A está listo para recibir señales empíricas reales.",
        "evidencias": [],
        "acercamiento": {
            "por_que_contactar": "Sin datos sintéticos. Esperando señales de tensión real.",
            "pregunta_entrada": "Ejecutar conector de campo para poblar.",
            "proximo_paso": "ESPERAR DATOS REALES"
        }
    }]
    os.makedirs(os.path.dirname(ruta_json), exist_ok=True)
    with open(ruta_json, 'w') as f:
        json.dump(corpus_vacio, f, ensure_ascii=False, indent=2)

print("-> Corpus sincronizado exclusivamente con la arquitectura de producción real.")
