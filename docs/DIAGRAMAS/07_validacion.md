# Diagrama — Validación Científica (Capa 11)

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
flowchart TB
    E[Expediente] --> TZ[validar_trazabilidad]
    E --> SF[calcular_suficiencia_corpus]
    E --> SD[calcular_solidez]
    E --> CT[detectar_contradicciones]
    E --> VC[detectar_vacios]
    E --> RP[validar_reproducibilidad]
    TZ & SF & SD & CT & VC & RP --> BL[evaluar_bloqueo_hipotesis]
    BL --> CL[clasificar_veredicto]
    CL --> D[emitir_dictamen_cientifico]
```
