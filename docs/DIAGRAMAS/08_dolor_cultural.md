# Diagrama — Dolor Cultural (Capa 3/9)

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
flowchart LR
    KW[keywords] --> COMB{COMBINACIONES}
    COMB -->|match| DP[deuda por combinación]
    COMB -->|no| DS[deuda por señal dominante]
    DP & DS --> TD[tipo_deuda + razón]
    KW --> PROF[profundidad × vertical] --> ICP[score_icp]
    TD & ICP --> A[analizar → expediente]
```
