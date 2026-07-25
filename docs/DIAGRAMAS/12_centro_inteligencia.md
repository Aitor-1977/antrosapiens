# Diagrama — Centro de Inteligencia

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
flowchart TB
    INV[POST /investigacion] --> XP[_construir_expedientes]
    XP --> DIC[generar_dictamen + generar_ranking]
    DIC --> AL[GET /alertas]
    DIC --> CE[GET /centro]
    XP --> DOS[GET /dossier/{org}]
    XP --> DM[GET /dolormap/{org}]
```
