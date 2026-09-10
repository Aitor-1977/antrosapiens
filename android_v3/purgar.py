import json, glob, os
candidatos = glob.glob('../**/expedientes.json', recursive=True) + glob.glob('expedientes.json')
ruta = candidatos[0] if candidatos else None
print('Leyendo desde:', ruta)

with open(ruta, 'r') as f:
    data = json.load(f)

filtrados = []
for x in data:
    if isinstance(x, dict):
        org = str(x.get('organizacion', '')).lower()
    else:
        org = str(x).lower()
    
    if not any(c in org for c in ['rappi', 'ualá', 'uala', 'mercadolibre', 'nubank']):
        filtrados.append(x)

os.makedirs('app/src/main/assets/public', exist_ok=True)
with open('app/src/main/assets/public/expedientes.json', 'w') as f:
    json.dump(filtrados, f, ensure_ascii=False)
print('Total limpios guardados en assets:', len(filtrados))
