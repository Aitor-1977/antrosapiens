import os, subprocess

target_dir = os.path.expanduser('~/antrosapiens/android_v3/app/src/main/assets')
json_source = os.path.join(target_dir, 'public', 'datos_antrolab.json')

if os.path.exists(json_source):
    with open(json_source, 'r', encoding='utf-8') as f:
        data = f.read()
    with open(os.path.join(target_dir, 'datos_antrolab.json'), 'w', encoding='utf-8') as f:
        f.write(data)
    print("✅ JSON copiado a assets.")

html_path = os.path.join(target_dir, 'index.html')
if not os.path.exists(html_path):
    html_path = os.path.join(target_dir, 'public', 'index.html')

if os.path.exists(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    js = """<script>
    document.addEventListener("DOMContentLoaded", function() {
        fetch("datos_antrolab.json")
            .then(r => r.json())
            .then(data => {
                const corpus = data.corpus_antropologico;
                if (corpus && corpus.length > 0) {
                    const item = corpus[0];
                    const card = document.querySelector(".capa-0, [class*='capa']");
                    if (card) {
                        card.innerHTML = `
                        <div style="font-size: 0.8em; font-weight: bold; color: #15803d;">CAPA 0 — SEÑAL NEON DB</div>
                        <blockquote style="font-style: italic; margin: 8px 0;">"${item.contenido || item.fragmento_evidencia}"</blockquote>
                        <div style="font-size: 0.75em; color: #6b7280;">ID: ${item.senal_id} | Canal: ${item.canal || 'Neon DB'}</div>
                        <hr style="margin: 8px 0; border: 0; border-top: 1px dashed #ccc;">
                        <div style="font-size: 0.8em;"><strong>Discurso:</strong> ${item.discurso}</div>
                        <div style="font-size: 0.8em;"><strong>Práctica:</strong> ${item.practica_observada}</div>
                        <div style="font-size: 0.8em; color: #991b1b; margin-top: 4px;"><strong>Tensión:</strong> ${item.tipo_tension}</div>`;
                    }
                }
            });
    });
    </script>"""

    if "datos_antrolab.json" not in content:
        content = content.replace("</body>", js + "\n</body>")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Script inyectado en index.html.")

os.chdir(os.path.expanduser('~/antrosapiens/android_v3'))
subprocess.run(['./gradlew', 'assembleDebug'], check=True)
subprocess.run(['cp', 'app/build/outputs/apk/debug/app-debug.apk', '/sdcard/Download/antrosapiens-v3-debug.apk'], check=True)
print("\n🚀 APK compilada exitosamente en /sdcard/Download/antrosapiens-v3-debug.apk")
