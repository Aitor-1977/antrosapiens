# Diagrama — Pipeline científico

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
flowchart TB
    XP[_construir_expedientes] --> INF[analizar C3]
    INF --> CUR[curar C10]
    CUR --> V[validar_expediente C11]
    V --> VER{veredicto}
    VER -->|BLOQUEADA| STOP[hipótesis bloqueada]
    VER -->|VALIDADA| GOB[auditar_expediente C12]
    GOB --> MEM[guardar_version C13]
    MEM --> PUB[generar_peritaje C17]
```
