import json

class CuradorAntropologico:
    """
    Motor Epistémico Capa 0: 
    Evalúa la tríada Actor + Tensión + Impacto.
    Abandona el filtrado por stopwords aisladas.
    """
    def __init__(self):
        # Mapeo de Thick Data: Tensiones organizacionales reales
        self.tensiones = {
            "repliegue": ["cierra", "cierre", "despide", "despidos", "quiebra", "retiro", "suspende"],
            "asimilacion": ["compra", "adquisición", "fusión", "absorbe", "integra"],
            "friccion": ["demanda", "multa", "regulación", "bloqueo", "investiga"],
            "simbiosis": ["alianza", "partnership", "inversión", "ronda"]
        }

    def evaluar_triada(self, actor: str, evidencia_cruda: str) -> dict:
        if not actor or not evidencia_cruda:
            return {"valida": False, "categoria": "vacío", "jerarquia": "Descartable"}

        texto = f"{actor} {evidencia_cruda}".lower()
        
        # 1. Clasificar Tensión Situacional
        tension_activa = "indefinida"
        for categoria, señales in self.tensiones.items():
            if any(s in texto for s in señales):
                tension_activa = categoria
                break
                
        # 2. Jerarquización e Impacto (Capa 0)
        if tension_activa in ["repliegue", "asimilacion"]:
            impacto = "Nivel 3: Tensión Estructural"
            es_valida = True
        elif tension_activa in ["friccion", "simbiosis"]:
            impacto = "Nivel 2: Movimiento Táctico"
            es_valida = True
        else:
            impacto = "Nivel 1: Ruido PR"
            # Se bloquea solo el ruido superficial, dejando pasar los movimientos de poder
            es_valida = False 
            
        return {
            "valida": es_valida,
            "categoria_tension": tension_activa,
            "jerarquia": impacto
        }

# Instancia global para ser consumida por el pipeline
motor_curaduria = CuradorAntropologico()
