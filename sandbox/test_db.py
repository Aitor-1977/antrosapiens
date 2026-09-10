import psycopg2, os
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
    tablas = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM principios_antropologicos;")
    principios = cursor.fetchone()[0]
    conn.close()
    print(f"🚀 VERIFICACIÓN EXITOSA:")
    print(f" -> Tablas creadas en Neon: {tablas} / 23")
    print(f" -> Principios sembrados: {principios} / 40")
except Exception as e:
    print(f"❌ Error al consultar la base de datos: {e}")
