import os, json

print("=== IMPLEMENTANDO FILTRO ANTROPOLÓGICO (FASE 4) ===")

# Simulamos la ingesta de un scraping bruto para pasarle el filtro
scraping_bruto = [
    {"titular": "Sindicato de Orla Mining exige revisión de turnos por fatiga extrema", "fuente": "Prensa Local", "url": "http://ejemplo.com/1"},
    {"titular": "Rappi anuncia crecimiento del 35% en el Q3", "fuente": "Comunicado Corporativo", "url": "http://ejemplo.com/2"},
    {"titular": "Renuncias masivas en el área de operaciones de TechLogistics", "fuente": "Foro Empleados", "url": "http://ejemplo.com/3"}
]

corpus_filtrado = []

for item in scraping_bruto:
    texto = item.get("titular", "").lower()
    
    # 1. Filtro de exclusión (Vanity metrics y corporativos)
    if any(corp in texto for corp in ["rappi", "ualá", "mercadolibre", "crecimiento", "unicornio", "ronda de inversión"]):
        continue # Descartar señal débil
        
    # 2. Detección de Tensión y Actores
    tension = "NO DETERMINADO"
    actores = "NO DETERMINADO"
    posicion = "NO DETERMINADO"
    
    if "sindicato" in texto or "huelga" in texto or "fatiga" in texto:
        tension = "Conflicto laboral / Operación"
        actores = "Trabajadores sindicalizados"
        posicion = "Actor afectado"
    elif "renuncia" in texto or "rotación" in texto:
        tension = "Quiebre de cultura organizacional"
        actores = "Personal operativo"
        posicion = "Ex-empleados / Operativos"
        
    # 3. Construcción de la Señal Antropológica
    senal = {
        "fuente": item.get("fuente", "NO DETERMINADO"),
        "url": item.get("url", "NO DETERMINADO"),
        "fecha": "2026-08-25",
        "organizacion": item.get("titular", "").split()[0:2], # Simplificación para el demo
        "persona_citada": "NO DETERMINADO",
        "cargo": "NO DETERMINADO",
        "posicion_enunciador": posicion,
        "tipo_senal": "Alerta Cultural",
        "situacion": item.get("titular", ""),
        "tension": tension,
        "actores": actores,
        "practica": "NO DETERMINADO",
        "consecuencia": "Posible interrupción operativa",
        "evidencia_textual": item.get("titular", "")
    }
    # Formatear el nombre de la organización
    senal["organizacion"] = " ".join(senal["organizacion"]).title()
    corpus_filtrado.append(senal)

# Guardar el corpus procesado
ruta_json = 'android_v3/app/src/main/assets/public/expedientes.json'
with open(ruta_json, 'w') as f:
    json.dump(corpus_filtrado, f, ensure_ascii=False, indent=2)

print(f"-> Filtro aplicado. Señales útiles retenidas: {len(corpus_filtrado)}")
print("-> Vanity metrics y corporativos descartados.")
