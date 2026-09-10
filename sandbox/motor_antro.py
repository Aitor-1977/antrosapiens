import sqlite3, os

def procesar_observacion(evidence_id, categoria_enunciador, actor, situacion, tension, practica, hipotesis):
    db_path = os.path.expanduser("~/antrosapiens/antrolab.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT organizacion_mencionada FROM evidencia_raw WHERE evidence_id = ?", (evidence_id,))
    row = cursor.fetchone()
    if not row:
        print(f"ERROR: No existe evidencia cruda con ID {evidence_id}.")
        return
    organizacion = row[0]
    cursor.execute("INSERT OR REPLACE INTO enunciador (evidence_id, categoria, posicion_declarada) VALUES (?, ?, ?)", (evidence_id, categoria_enunciador, actor))
    obs_id = f"OBS-{evidence_id}"
    cursor.execute("""
        INSERT OR REPLACE INTO observacion_antropologica 
        (observacion_id, organizacion, actor_involucrado, situacion_detectada, tension_valor, practica_observada, hipotesis_valor, nivel_confianza)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Alto')
    """, (obs_id, organizacion, actor, situacion, tension, practica, hipotesis))
    cursor.execute("INSERT OR REPLACE INTO observacion_evidencia (observacion_id, evidence_id) VALUES (?, ?)", (obs_id, evidence_id))
    conn.commit()
    conn.close()
    print(f"-> Observación {obs_id} creada y vinculada a {evidence_id}")

if __name__ == "__main__":
    ev_id = input("ID de Evidencia (ej. EV-0001): ")
    enunciador = input("Enunciador: ")
    actor = input("Actor involucrado: ")
    sit = input("Situación detectada: ")
    tens = input("Tensión: ")
    pract = input("Práctica / Ritual: ")
    hip = input("Hipótesis: ")
    procesar_observacion(ev_id, enunciador, actor, sit, tens, pract, hip)


# FILTRO DE EXCLUSION DE FALSAS ENTIDADES (MOTOR A)
STOPWORDS_ORGANIZACION = {"cierra", "abre", "anuncia", "compra", "vende", "lanza", "prepara"}
NOMBRES_PERSONAS_COMUNES = {"armando", "carlos", "maria", "jose", "ana", "luis", "juan"}

def es_entidad_valida(nombre: str) -> bool:
    if not nombre: return False
    limpio = nombre.strip().lower()
    if limpio in STOPWORDS_ORGANIZACION or limpio in NOMBRES_PERSONAS_COMUNES: return False
    if len(limpio) < 2 or limpio.isdigit(): return False
    return True
