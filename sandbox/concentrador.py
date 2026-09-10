import os, json

print("=== IMPLEMENTANDO CONCENTRADOR DE EVIDENCIA (FASE 5) ===")

# Simulamos múltiples señales convergentes (salida de la Fase 4)
senales = [
    {"organizacion": "TechLogistics", "situacion": "Renuncias masivas en el área de operaciones", "tension": "Quiebre de cultura organizacional", "fecha": "2026-08-20"},
    {"organizacion": "TechLogistics", "situacion": "Sindicato de transportistas amenaza con paro", "tension": "Conflicto laboral", "fecha": "2026-08-22"},
    {"organizacion": "TechLogistics", "situacion": "Foro quejas: Clientes denuncian retrasos crónicos", "tension": "Falla operativa por falta de personal", "fecha": "2026-08-25"},
    {"organizacion": "Orla Mining", "situacion": "Sindicato exige revisión de turnos por fatiga extrema", "tension": "Conflicto laboral / Operación", "fecha": "2026-08-25"}
]

concentrador = {}

for s in senales:
    org = s["organizacion"]
    if org not in concentrador:
        concentrador[org] = {
            "organizacion": org,
            "estado_caso": "CASO CANDIDATO",
            "sintesis_situacion": "Existe una situación persistente que merece investigación.",
            "total_evidencias": 0,
            "evidencias": []
        }
    concentrador[org]["evidencias"].append(s)
    concentrador[org]["total_evidencias"] += 1

casos_candidatos = list(concentrador.values())

ruta_json = 'android_v3/app/src/main/assets/public/expedientes.json'
with open(ruta_json, 'w') as f:
    json.dump(casos_candidatos, f, ensure_ascii=False, indent=2)

print(f"-> Evidencia concentrada con éxito.")
print(f"-> Organizaciones elevadas a Caso Candidato: {len(casos_candidatos)}")
for c in casos_candidatos:
    print(f"   - {c['organizacion']}: {c['total_evidencias']} señales convergentes detectadas.")
