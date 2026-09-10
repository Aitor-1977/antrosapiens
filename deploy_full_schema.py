import psycopg2, os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: La variable DATABASE_URL no está configurada. Ejecuta export DATABASE_URL=... primero.")
    exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    with open("full_schema_antrolab.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()
    print("🚀 LAS 23 TABLAS DE LA ARQUITECTURA ANTROPOLÓGICA FUERON DESPLEGADAS CON ÉXITO EN NEON.")
except Exception as e:
    print(f"❌ Error al aplicar el DDL: {e}")
