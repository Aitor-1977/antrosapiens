# Diagrama — Gobernanza (Capa 12)

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
flowchart TB
    EXP[Expediente + Validación] --> H[generar_huella_digital]
    H --> INT[validar_integridad]
    H --> CON[verificar_consistencia]
    H --> CERT[emitir_certificado + firma_motor]
    H --> BIT[generar_bitacora]
    H --> AUD[auditar_expediente]
    AUD --> T1[(versionado_modelo)]
    AUD --> T2[(huellas_digitales)]
    AUD --> T3[(bitacora_decisiones)]
    AUD --> T4[(auditoria_expedientes)]
    AUD --> T5[(certificados)]
```
