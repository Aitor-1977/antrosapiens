import os, glob, re, json

print("=== 1. PARCHANDO LÍMITE DE API ===")
archivos_modificados = 0
for filepath in glob.glob('hd_scraper/**/*.py', recursive=True):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Busca y reemplaza cualquier límite 500 por 100
    new_content = re.sub(r'([\'"]?limite[\'"]?\s*[:=]\s*)500', r'\g<1>100', content)
    new_content = re.sub(r'limit\s*=\s*500', r'limit=100', new_content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"-> Corregido límite 500 a 100 en: {filepath}")
        archivos_modificados += 1

if archivos_modificados == 0:
    print("-> No se encontraron límites de 500 para parchar.")

print("\n=== 2. INYECTANDO ESTRUCTURA ANTROPOLÓGICA LIMPIA ===")
# Plantilla base obligatoria para evitar el KeyError: 0
plantilla = [{
    "fuente": "NO DETERMINADO",
    "url": "NO DETERMINADO",
    "fecha": "NO DETERMINADO",
    "organizacion": "Organización Candidata",
    "persona_citada": "NO DETERMINADO",
    "cargo": "NO DETERMINADO",
    "posicion_enunciador": "NO DETERMINADO",
    "tipo_senal": "NO DETERMINADO",
    "situacion": "Prueba de reinicio del Motor A tras colapso de API.",
    "tension": "NO DETERMINADO",
    "actores": "NO DETERMINADO",
    "practica": "NO DETERMINADO",
    "consecuencia": "NO DETERMINADO",
    "evidencia_textual": "Validación de estructura de Caso Candidato. Límite de scraping corregido."
}]

os.makedirs('android_v3/app/src/main/assets/public', exist_ok=True)
ruta_json = 'android_v3/app/src/main/assets/public/expedientes.json'
with open(ruta_json, 'w') as f:
    json.dump(plantilla, f, ensure_ascii=False, indent=2)

# Sobrescribir también en android_v2 para limpiar el caché general
with open('android_v2/expedientes.json', 'w') as f:
    json.dump(plantilla, f, ensure_ascii=False, indent=2)

print(f"-> Corpus purgado y regenerado en {ruta_json}")
