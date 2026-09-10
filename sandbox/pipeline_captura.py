import psycopg2, os, hashlib, json
from motor_epistemico import inyectar_lectura_neon

def procesar_lote_capturas(lista_capturas):
    """
    Recibe una lista de diccionarios con datos crudos de scraping/observación
    y los procesa en la base de datos de Neon.
    """
    exitos = 0
    for item in lista_capturas:
        try:
            inyectar_lectura_neon(
                fuente_url=item.get("url", "https://antrosapiens.internal/captura"),
                organizacion_nombre=item.get("organizacion", "Hamaca Digital"),
                hecho_crudo=item["hecho_crudo"],
                discurso=item["discurso"],
                practica=item["practica"],
                friccion_descripcion=item["friccion_descripcion"],
                tipo_tension=item.get("tipo_tension", "FRICCION_OPERATIVA")
            )
            exitos += 1
        except Exception as e:
            print(f"❌ Error al procesar captura para '{item.get('organizacion')}': {e}")
    
    print(f"\n✨ Pipeline finalizado: {exitos}/{len(lista_capturas)} señales procesadas e inyectadas en Neon.")

if __name__ == "__main__":
    # Lote de prueba de señales de Capa 0 (Simulación de scraping de vacantes/operación)
    capturas_demo = [
        {
            "url": "https://linkedin.com/jobs/view/12345",
            "organizacion": "Hamaca Digital",
            "hecho_crudo": "Vacante solicita 'Project Manager con experiencia en llenar tableros Jira y coordinar mensajes urgentes por WhatsApp'.",
            "discurso": "Procesos ágiles formalizados e institucionalizados en la gestión de proyectos.",
            "practica": "Uso de WhatsApp como canal primario de gestión informal por sobre la herramienta formal.",
            "friccion_descripcion": "Saturación de comunicación asíncrona y ruptura de la trazabilidad en Jira.",
            "tipo_tension": "DEUDA_CULTURAL"
        },
        {
            "url": "https://foro-interno.com/thread/89",
            "organizacion": "Hamaca Digital",
            "hecho_crudo": "Líderes de equipo duplican reportes semanales en diapositivas porque la directiva no revisa los dashboards automáticos.",
            "discurso": "Toma de decisiones ejecutivas basada en data dashboards en tiempo real.",
            "practica": "Elaboración manual de presentaciones de alto nivel como ritual de visibilidad organizativa.",
            "friccion_descripcion": "Ritual gerencial que invalida la inversión tecnológica en analítica automática.",
            "tipo_tension": "RITUAL_ORGANIZACIONAL"
        }
    ]
    
    print("🚀 Iniciando procesamiento de lote en Pipeline de Captura...")
    procesar_lote_capturas(capturas_demo)
