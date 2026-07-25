# Diagrama — Onlife (Capa 7)

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
flowchart LR
    ORG[org_nombre] --> G[observar_github]
    ORG --> H[observar_hackernews]
    ORG --> B[observar_blog]
    G & H & B --> S[persistir_señales]
    S --> DB[(onlife_signals)]
    DB --> P[obtener_perfil]
```
