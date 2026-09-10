import psycopg2, os, hashlib

def inyectar_lectura_neon(fuente_url, organizacion_nombre, hecho_crudo, discurso, practica, friccion_descripcion, tipo_tension="FRICCION_OPERATIVA"):
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL no está configurada.")
        return

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # 1. Obtener Organización Semilla
    cursor.execute("SELECT id FROM organizaciones WHERE nombre = %s;", (organizacion_nombre,))
    org_row = cursor.fetchone()
    if not org_row:
        print(f"❌ Organización '{organizacion_nombre}' no encontrada.")
        return
    org_id = org_row[0]

    # 2. Registrar Situación
    cursor.execute("""
        INSERT INTO situaciones (nombre, organizacion_id, descripcion)
        VALUES (%s, %s, %s) RETURNING id;
    """, (f"Situación de Fricción: {organizacion_nombre}", org_id, friccion_descripcion))
    situacion_id = cursor.fetchone()[0]

    # 3. Registrar Fuente (Capa 0)
    hash_c = hashlib.sha256(hecho_crudo.encode()).hexdigest()
    cursor.execute("""
        INSERT INTO fuentes (url, dominio, tipo_fuente, hash_contenido)
        VALUES (%s, 'web', 'scraping_antropologico', %s)
        ON CONFLICT (hash_contenido) DO UPDATE SET url = EXCLUDED.url
        RETURNING id;
    """, (fuente_url, hash_c))
    fuente_id = cursor.fetchone()[0]

    # 4. Registrar Señal
    cursor.execute("""
        INSERT INTO senales_antropologicas 
        (fuente_id, situacion_id, contenido, fragmento_evidencia, tipo_enunciador, posicion_enunciador, canal)
        VALUES (%s, %s, %s, %s, 'Actor Operativo', 'Enunciador Situado', 'Web / Scraping')
        RETURNING id;
    """, (fuente_id, situacion_id, hecho_crudo, hecho_crudo))

    # 5. Registrar Tensión Relacional
    cursor.execute("""
        INSERT INTO tensiones (situacion_id, discurso, practica_observada, descripcion, tipo_tension, nivel_confianza)
        VALUES (%s, %s, %s, %s, %s, 0.90);
    """, (situacion_id, discurso, practica, friccion_descripcion, tipo_tension))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Lectura Antropológica inyectada exitosamente en Neon para '{organizacion_nombre}'.")

if __name__ == "__main__":
    print("Motor Epistémico Neon preparado.")


# FILTRO DE EXCLUSION DE FALSAS ENTIDADES (MOTOR A)
STOPWORDS_ORGANIZACION = {"cierra", "abre", "anuncia", "compra", "vende", "lanza", "prepara"}
NOMBRES_PERSONAS_COMUNES = {"armando", "carlos", "maria", "jose", "ana", "luis", "juan"}

def es_entidad_valida(nombre: str) -> bool:
    if not nombre: return False
    limpio = nombre.strip().lower()
    if limpio in STOPWORDS_ORGANIZACION or limpio in NOMBRES_PERSONAS_COMUNES: return False
    if len(limpio) < 2 or limpio.isdigit(): return False
    return True
