import os
import psycopg2

try:
    url = os.environ.get("HD_DATABASE_URL")
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # Buscamos tablas disponibles para evitar adivinar el nombre exacto
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tablas = [r[0] for r in cur.fetchall()]
    print("Tablas encontradas:", tablas)
    
    tabla_obj = 'prospectos' if 'prospectos' in tablas else ('prospecto' if 'prospecto' in tablas else tablas[0])
    
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tabla_obj}';")
    cols = [r[0] for r in cur.fetchall()]
    
    col_org = 'organizacion' if 'organizacion' in cols else ('nombre' if 'nombre' in cols else cols[0])
    col_cat = 'categoria_de_organizacion' if 'categoria_de_organizacion' in cols else 'categoria'
    
    query = f"DELETE FROM {tabla_obj} WHERE {col_org} IN ('Clip', 'Konfío') AND {col_cat} = 'Corporativo';"
    cur.execute(query)
    conn.commit()
    print(f"¡Éxito! Filas corporativas eliminadas de '{tabla_obj}': {cur.rowcount}")
    
    cur.close()
    conn.close()
except Exception as e:
    print("Error:", e)
