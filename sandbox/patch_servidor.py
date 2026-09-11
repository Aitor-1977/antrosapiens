import sys
import os

# Asegurar que la raíz del proyecto esté en el path de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sandbox.motor_epistemico import motor_curaduria

def procesar_evidencia_entrante(actor: str, raw_text: str) -> dict:
    """
    Intercepta la señal cruda antes de escribir en base de datos.
    Exige la tríada Actor + Tensión + Impacto.
    """
    dictamen = motor_curaduria.evaluar_triada(actor, raw_text)
    
    evaluacion_estructural = {
        "organizacion": actor,
        "estado": "ACTIVA" if dictamen.get("valida", False) else "BLOQUEADA",
        "categoria_tension": dictamen.get("categoria_tension", "indefinida").upper(),
        "jerarquia": dictamen.get("jerarquia", "Nivel 1: Ruido PR"),
        "razon_score": (
            f"Señal Estructural Validada: {dictamen.get('categoria_tension', '').upper()} | {dictamen.get('jerarquia', '')}"
            if dictamen.get("valida", False)
            else "Descartado (Nivel 1): Ruido superficial sin tensión organizacional."
        )
    }
    
    return evaluacion_estructural

# Prueba rápida del parche local
test_res = procesar_evidencia_entrante("Frubana", "anunció cierre de operaciones de su red logística")
print("✔️ Módulo de parche de servidor cargado correctamente.")
print("Resultado de prueba:", test_res)
