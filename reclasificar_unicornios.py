import os
import psycopg2

url = os.environ.get("HD_DATABASE_URL")
conn = psycopg2.connect(url)
cur = conn.cursor()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'prospectos';")
cols = [r[0] for r in cur.fetchall()]

col_org = 'organizacion' if 'organizacion' in cols else 'nombre'
col_cat = 'categoria_de_organizacion' if 'categoria_de_organizacion' in cols else 'categoria'
if 'foco' in cols and col_cat == 'categoria': 
    col_cat = 'foco'

# Actualizamos a Startup a los unicornios que quedaron atrapados como Corporativo
query = f"UPDATE prospectos SET {col_cat} = 'Startup' WHERE {col_org} IN ('Rappi', 'Ualá') AND {col_cat} = 'Corporativo';"
cur.execute(query)
conn.commit()

print(f"¡Listo! Se actualizaron {cur.rowcount} registros de Corporativo a Startup.")

cur.close()
conn.close()
