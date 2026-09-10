import os, json

print("=== IMPLEMENTANDO PRIORIZACIÓN COMERCIAL (FASES 6 Y 7) ===")
ruta_json = 'android_v3/app/src/main/assets/public/expedientes.json'

with open(ruta_json, 'r') as f:
    casos = json.load(f)

for caso in casos:
    evidencias = caso.get("evidencias", [])
    total_evidencias = caso.get("total_evidencias", 0)
    
    # Cálculo de score base (simulando las variables comerciales de HD)
    score = 40 # Base por existir como caso
    
    # Premiamos la persistencia y convergencia
    score += (total_evidencias * 15)
    
    # Asignamos la justificación comercial
    if total_evidencias >= 3:
        score += 15 # Bono de urgencia
        razon = "Alta persistencia y convergencia multicanal. Tensión validada."
        estado = "PRIORIZADO"
    else:
        razon = "Evidencia inicial aislada. Requiere mayor monitoreo."
        estado = "VALIDADO"
        
    caso["score"] = min(score, 99) # Tope de 99
    caso["razon_score"] = razon
    caso["estado_comercial"] = estado

# Ordenar los prospectos de mayor a menor score para el ranking
casos.sort(key=lambda x: x.get("score", 0), reverse=True)

with open(ruta_json, 'w') as f:
    json.dump(casos, f, ensure_ascii=False, indent=2)

print(f"-> Priorización ejecutada. Ranking de Casos Candidatos:")
for c in casos:
    print(f"   [ {c['score']} pts ] {c['organizacion']} | {c['estado_comercial']} | {c['razon_score']}")
