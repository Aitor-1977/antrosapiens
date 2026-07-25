# Diagrama — Drift Narrativo (Capa 6)

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
flowchart LR
    URL[sitio_web] --> SNAP[capturar_snapshot]
    SNAP --> DB[(drift_snapshots)]
    DB --> CMP[comparar consecutivos]
    CMP --> EVN[(drift_evidencias)]
    EVN --> TL[obtener_timeline]
```
