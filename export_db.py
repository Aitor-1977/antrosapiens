import sqlite3, json, os
db_path = os.path.expanduser("~/antrosapiens/antrolab.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("""
    SELECT 
        e.evidence_id, e.url, e.captured_at, e.titulo, e.organizacion_mencionada, e.fuente_medio, e.fragmento_textual,
        en.categoria AS enunciador_categoria,
        o.tension_valor, o.practica_observada, o.hipotesis_valor
    FROM evidencia_raw e
    LEFT JOIN enunciador en ON e.evidence_id = en.evidence_id
    LEFT JOIN observacion_evidencia oe ON e.evidence_id = oe.evidence_id
    LEFT JOIN observacion_antropologica o ON oe.observacion_id = o.observacion_id
""")
rows = cursor.fetchall()
export_data = [dict(row) for row in rows]
output_path = os.path.expanduser("~/antrosapiens/android_v3/app/src/main/assets/public/datos_antrolab.json")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({"expedientes": export_data}, f, ensure_ascii=False, indent=2)
conn.close()
print(f"-> Exportados {len(export_data)} registros a {output_path}")
