# Diagrama — Arquitectura general (Motor A)

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
flowchart TB
    C0[Capa 0 · Captura/Ingesta] --> C1[Capa 1 · Normalización]
    C1 --> C2[(Capa 2 · evidencias)]
    C2 --> C3[Capa 3 · Inferencia analizar]
    C3 --> C9[Capa 9 · DolorMap]
    C9 --> C10[Capa 10 · Curaduría]
    C10 --> C11[Capa 11 · Validación Científica]
    C11 --> C12[Capa 12 · Gobernanza]
    C12 --> C13[Capa 13 · Memoria]
    C13 --> C14[Capa 14 · Comparador]
    C14 --> C15[Capa 15 · Predictivo]
    C15 --> C16[Capa 16 · Observatorio]
    C16 --> C17[Capa 17 · Publicador]
    C17 --> C18[Capa 18 · Sistema Operativo]
    C18 --> API[[API REST solo lectura · 72 endpoints]]
```
