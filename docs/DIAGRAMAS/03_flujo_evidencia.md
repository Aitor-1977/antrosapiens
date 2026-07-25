# Diagrama — Flujo de evidencia

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
flowchart LR
    N[Noticia/señal] --> S[connector.search]
    S --> NORM[normalize + hash_dedup]
    NORM --> KW[detectar_keywords + confianza]
    KW --> VAL{validator: contrato}
    VAL -->|ok| EV[(evidencias estado=ok)]
    VAL -->|incompleto| RJ[(rechazos)]
    VAL -->|sin fecha| NF[(evidencias no_fechado)]
    EV --> CORP[GET /corpus]
```
