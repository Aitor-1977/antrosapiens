import os, json

print("=== IMPLEMENTANDO MÓDULO DE ACERCAMIENTO (FASE 8) ===")
ruta_json = 'android_v3/app/src/main/assets/public/expedientes.json'

with open(ruta_json, 'r') as f:
    casos = json.load(f)

for caso in casos:
    org = caso.get("organizacion", "")
    trens = [e.get("tension", "") for e in caso.get("evidencias", []) if e.get("tension") != "NO DETERMINADO"]
    tension_dom = trens[0] if trens else "Tensión organizacional no especificada"
    
    # Inyección de la estrategia de acercamiento comercial
    caso["acercamiento"] = {
        "por_que_contactar": f"Se detectó la tensión '{tension_dom}' afectando la continuidad operativa.",
        "que_sabemos": [e.get("situacion", "") for e in caso.get("evidencias", [])],
        "que_no_sabemos": "Grado de impacto directo en la rotación de mandos medios y margen operativo.",
        "hipotesis_conversacion": "La fricción entre supervisión y personal operativo está bloqueando la ejecución del modelo de entrega.",
        "pregunta_entrada": f"¿Cómo están abordando en {org} la fricción en mandos medios derivada de los cambios recientes de turnos?",
        "proximo_paso": "AGENDAR LLAMADA EXPLORATORIA -> PROSPECTAR SPRINT FUNDACIONAL ($210,000 MXN)"
    }
    caso["estado_embudo"] = "PROSPECTOR_LISTO"

with open(ruta_json, 'w') as f:
    json.dump(casos, f, ensure_ascii=False, indent=2)

print("-> Estrategia de acercamiento inyectada en todos los Casos Candidatos.")
print("\nEjemplo de ficha de contacto generada para el top prospecto:")
top = casos[0]
print(f"Organización: {top['organizacion']}")
print(f"Pregunta de Entrada: {top['acercamiento']['pregunta_entrada']}")
print(f"Próximo Paso: {top['acercamiento']['proximo_paso']}")
