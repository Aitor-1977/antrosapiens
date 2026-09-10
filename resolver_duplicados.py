import os
import psycopg2

try:
    url = os.environ.get("HD_DATABASE_URL")
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # Borramos los duplicados corporativos de Clip y Konfío
    cur.execute("DELETE FROM prospectos WHERE nombre IN ('Clip', 'Konfío') AND (categoria_de_organizacion = 'Corporativo' OR categoria_de_organizacion IS NULL);")
    conn.commit()
    print(f"¡Limpieza exitosa! Registros borrados: {cur.rowcount}")
    
    cur.close()
    conn.close()
except Exception as e:
    print("Error:", e)
