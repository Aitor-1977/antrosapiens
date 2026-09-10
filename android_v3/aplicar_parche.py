import os

print("=== BUSCANDO ARCHIVO HTML EN ASSETS ===")
assets_path = 'app/src/main/assets'
html_encontrado = None

for root, dirs, files in os.walk(assets_path):
    for file in files:
        if file.endswith('.html'):
            html_encontrado = os.path.join(root, file)
            break

if html_encontrado:
    print(f"-> Archivo localizado: {html_encontrado}")
    with open(html_encontrado, 'r', encoding='utf-8') as f:
        html = f.read()
    
    script_sincrono = """
    <script>
    const expedientesData = [
        {
            "organizacion": "Operadora Logística del Norte",
            "estado_comercial": "PRIORIZADO_CAMPO",
            "score": 94,
            "total_evidencias": 3,
            "razon_score": "Alta persistencia de tensión en mandos medios detectada por Motor A.",
            "evidencias": [
                {"situacion": "Conflicto operativo por turnos", "tension": "Quiebre cultural operativo", "fecha": "2026-08-25"}
            ],
            "acercamiento": {
                "por_que_contactar": "La fricción interna frena la ejecución del modelo operacional.",
                "pregunta_entrada": "¿Cómo están abordando el desgaste en la línea de supervisión?",
                "proximo_paso": "LLAMADA COMERCIAL - SPRINT $210K"
            }
        }
    ];

    document.addEventListener('DOMContentLoaded', () => {
        let htmlContent = '<div style="padding: 20px; font-family: sans-serif;">';
        htmlContent += '<h2 style="color: #2c3e50;">CASO CANDIDATO PRIORIZADO</h2>';
        expedientesData.forEach(item => {
            htmlContent += '<div style="background: #fff; padding: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid #27ae60;">';
            htmlContent += '<h3>' + item.organizacion + '</h3>';
            htmlContent += '<p><strong>Estado:</strong> ' + item.estado_comercial + ' (Score: ' + item.score + ')</p>';
            htmlContent += '<p><strong>Pregunta de Entrada:</strong> ' + item.acercamiento.pregunta_entrada + '</p>';
            htmlContent += '</div>';
        });
        htmlContent += '</div>';
        document.body.innerHTML = htmlContent;
    });
    </script>
    """
    
    if '</body>' in html:
        html_modificado = html.replace('</body>', script_sincrono + '</body>')
    else:
        html_modificado = html + script_sincrono
        
    with open(html_encontrado, 'w', encoding='utf-8') as f:
        f.write(html_modificado)
    print("-> Parche síncrono aplicado con éxito.")
else:
    print("-> Error: No se encontró ningún archivo HTML.")
