
# FILTRO DE EXCLUSION INTELIGENTE (MOTOR A)
STOPWORDS_ORGANIZACION = {"cierra", "abre", "anuncia", "compra", "vende", "lanza", "prepara"}
NOMBRES_PERSONAS_COMUNES = {"armando", "carlos", "maria", "jose", "ana", "luis", "juan"}

def es_entidad_valida(nombre: str) -> bool:
    if not nombre: return False
    limpio = nombre.strip().lower()
    
    # Solo bloquea si la entidad EXTRAÍDA es exactamente el verbo o la stopword aislada, 
    # permitiendo que organizaciones como Frubana pasen aunque la noticia hable de cierres.
    if limpio in STOPWORDS_ORGANIZACION or limpio in NOMBRES_PERSONAS_COMUNES: 
        return False
        
    if len(limpio) < 2 or limpio.isdigit(): 
        return False
        
    return True
