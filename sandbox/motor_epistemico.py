import json

class CuradorAntropologico:
    def __init__(self):
        self.tensiones = {
            "repliegue": ["cierra", "cierre", "despide", "despidos", "quiebra", "retiro", "suspende"],
            "asimilacion": ["compra", "adquisición", "fusión", "absorbe", "integra"],
            "friccion": ["demanda", "multa", "regulación", "bloqueo", "investiga"],
            "simbiosis": ["alianza", "partnership", "inversión", "ronda"]
        }

    def evaluar_triada(self, actor: str, evidencia_cruda: str) -> dict:
        if not actor or not evidencia_cruda:
            return {"valida": False, "categoria_tension": "vacío", "jerarquia": "Nivel 1: Ruido PR"}

        texto = f"{actor} {evidencia_cruda}".lower()
        
        tension_activa = "indefinida"
        for categoria, señales in self.tensiones.items():
            if any(s in texto for s in señales):
                tension_activa = categoria
                break
                
        if tension_activa in ["repliegue", "asimilacion"]:
            impacto = "Nivel 3: Tensión Estructural"
            es_valida = True
        elif tension_activa in ["friccion", "simbiosis"]:
            impacto = "Nivel 2: Movimiento Táctico"
            es_valida = True
        else:
            impacto = "Nivel 1: Ruido PR"
            es_valida = False 
            
        return {
            "valida": es_valida,
            "categoria_tension": tension_activa,
            "jerarquia": impacto
        }

motor_curaduria = CuradorAntropologico()
