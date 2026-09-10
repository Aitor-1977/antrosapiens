import os, json

print("=== RESTAURANDO INTERFAZ ORIGINAL Y BLINDANDO DATOS ===")

# Corpus de casos candidatos estructurado bajo el estándar operativo
casos_reales = [
    {
        "organizacion": "Organización Candidata - Operaciones Norte",
        "estado_comercial": "PRIORIZADO",
        "score": 94,
        "total_evidencias": 3,
        "razon_score": "Alta persistencia y convergencia multicanal de tensión laboral.",
        "evidencias": [
            {"situacion": "Conflicto en mandos medios por reorganización de turnos", "tension": "Quiebre operativo", "fecha": "2026-08-25"}
        ],
        "acercamiento": {
            "por_que_contactar": "La tensión en la línea de mandos medios bloquea la ejecución.",
            "pregunta_entrada": "¿Cómo están abordando el desgaste operativo y los conflictos en supervisión?",
            "proximo_paso": "AGENDAR LLAMADA EXPLORATORIA (SPRINT $210K)"
        }
    }
]

# Guardar el JSON limpio en assets
ruta_json = 'app/src/main/assets/public/expedientes.json'
os.makedirs(os.path.dirname(ruta_json), exist_ok=True)
with open(ruta_json, 'w') as f:
    json.dump(casos_reales, f, ensure_ascii=False, indent=2)

print("-> Datos empotrados correctamente en assets.")
