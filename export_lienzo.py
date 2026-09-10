import psycopg2, json, os
from decimal import Decimal

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no está configurada.")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
    SELECT 
        s.id AS senal_id, s.contenido, s.fragmento_evidencia, s.tipo_enunciador, 
        s.posicion_enunciador, s.canal, s.fecha_observacion,
        t.discurso, t.practica_observada, t.tipo_tension, t.descripcion AS tension_descripcion, t.nivel_confianza,
        o.nombre AS organizacion
    FROM senales_antropologicas s
    LEFT JOIN situaciones sit ON s.situacion_id = sit.id
    LEFT JOIN organizaciones o ON sit.organizacion_id = o.id
    LEFT JOIN tensiones t ON sit.id = t.situacion_id
""")

columns = [desc[0] for desc in cursor.description]
rows = cursor.fetchall()

export_data = []
for row in rows:
    item = dict(zip(columns, row))
    for k, v in item.items():
        if hasattr(v, 'isoformat'):
            item[k] = v.isoformat()
        elif isinstance(v, Decimal):
            item[k] = float(v)
    export_data.append(item)

output_path = os.path.expanduser("~/antrosapiens/android_v3/app/src/main/assets/public/datos_antrolab.json")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"corpus_antropologico": export_data}, f, ensure_ascii=False, indent=2)

cursor.close()
conn.close()
print(f"✅ Corpus exportado exitosamente desde Neon ({len(export_data)} registros) a {output_path}")
