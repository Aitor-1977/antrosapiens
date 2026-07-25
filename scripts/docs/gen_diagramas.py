#!/usr/bin/env python3
"""Generador de docs/DIAGRAMAS/*.md — diagramas Mermaid del ecosistema.

Diagramas verificados contra el código (capas, endpoints, tablas y motores
reales). Ejecutar:  python -m scripts.docs.gen_diagramas
"""
from __future__ import annotations

from pathlib import Path

DEST = Path(__file__).resolve().parents[2] / "docs" / "DIAGRAMAS"

DIAGRAMAS: dict[str, tuple[str, str]] = {
    "01_arquitectura_general": ("Arquitectura general (Motor A)", """flowchart TB
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
    C18 --> API[[API REST solo lectura · 72 endpoints]]"""),

    "02_comunicacion_motores": ("Comunicación entre motores", """sequenceDiagram
    participant F as Fuentes públicas
    participant A as Motor A (antrosapiens)
    participant R as RadarHD (Motor B+C)
    participant U as Usuario/Cliente
    F->>A: señales crudas
    A->>A: extraer, validar, clasificar (determinista), certificar
    A-->>R: GET /corpus (motor_a.corpus.v1)
    R->>U: dashboard, prospectos, seguimiento comercial
    Note over A,R: ADR-0001: Motor A piensa, B muestra, C vende"""),

    "03_flujo_evidencia": ("Flujo de evidencia", """flowchart LR
    N[Noticia/señal] --> S[connector.search]
    S --> NORM[normalize + hash_dedup]
    NORM --> KW[detectar_keywords + confianza]
    KW --> VAL{validator: contrato}
    VAL -->|ok| EV[(evidencias estado=ok)]
    VAL -->|incompleto| RJ[(rechazos)]
    VAL -->|sin fecha| NF[(evidencias no_fechado)]
    EV --> CORP[GET /corpus]"""),

    "04_pipeline_cientifico": ("Pipeline científico", """flowchart TB
    XP[_construir_expedientes] --> INF[analizar C3]
    INF --> CUR[curar C10]
    CUR --> V[validar_expediente C11]
    V --> VER{veredicto}
    VER -->|BLOQUEADA| STOP[hipótesis bloqueada]
    VER -->|VALIDADA| GOB[auditar_expediente C12]
    GOB --> MEM[guardar_version C13]
    MEM --> PUB[generar_peritaje C17]"""),

    "05_pipeline_comercial": ("Pipeline comercial (Motor C, en RadarHD)", """flowchart LR
    P[(prospecto)] --> DET[Detectado] --> CAD[cadencia_email]
    CAD --> DEC[decisores Hunter/Apify] --> EMAIL[/email-decisor/]
    EMAIL --> SEG[(seguimiento_comercial)]
    SEG --> KPI[kpisComerciales] --> TEL[telegram]
    KS[Kill Switch] -.->|corta| CAD"""),

    "06_gobernanza": ("Gobernanza (Capa 12)", """flowchart TB
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
    AUD --> T5[(certificados)]"""),

    "07_validacion": ("Validación Científica (Capa 11)", """flowchart TB
    E[Expediente] --> TZ[validar_trazabilidad]
    E --> SF[calcular_suficiencia_corpus]
    E --> SD[calcular_solidez]
    E --> CT[detectar_contradicciones]
    E --> VC[detectar_vacios]
    E --> RP[validar_reproducibilidad]
    TZ & SF & SD & CT & VC & RP --> BL[evaluar_bloqueo_hipotesis]
    BL --> CL[clasificar_veredicto]
    CL --> D[emitir_dictamen_cientifico]"""),

    "08_dolor_cultural": ("Dolor Cultural (Capa 3/9)", """flowchart LR
    KW[keywords] --> COMB{COMBINACIONES}
    COMB -->|match| DP[deuda por combinación]
    COMB -->|no| DS[deuda por señal dominante]
    DP & DS --> TD[tipo_deuda + razón]
    KW --> PROF[profundidad × vertical] --> ICP[score_icp]
    TD & ICP --> A[analizar → expediente]"""),

    "09_drift": ("Drift Narrativo (Capa 6)", """flowchart LR
    URL[sitio_web] --> SNAP[capturar_snapshot]
    SNAP --> DB[(drift_snapshots)]
    DB --> CMP[comparar consecutivos]
    CMP --> EVN[(drift_evidencias)]
    EVN --> TL[obtener_timeline]"""),

    "10_onlife": ("Onlife (Capa 7)", """flowchart LR
    ORG[org_nombre] --> G[observar_github]
    ORG --> H[observar_hackernews]
    ORG --> B[observar_blog]
    G & H & B --> S[persistir_señales]
    S --> DB[(onlife_signals)]
    DB --> P[obtener_perfil]"""),

    "11_curaduria": ("Curaduría Antropológica (Capa 10)", """flowchart TB
    EXPS[Expedientes] --> TEN[_identificar_tension]
    EXPS --> NAR[_construir_narrativa]
    EXPS --> CONV[_curar_convergencias]
    EXPS --> ORGS[_organizaciones_curadas]
    TEN & NAR & CONV & ORGS --> CUR[curar → lectura de ecosistema]"""),

    "12_centro_inteligencia": ("Centro de Inteligencia", """flowchart TB
    INV[POST /investigacion] --> XP[_construir_expedientes]
    XP --> DIC[generar_dictamen + generar_ranking]
    DIC --> AL[GET /alertas]
    DIC --> CE[GET /centro]
    XP --> DOS[GET /dossier/{org}]
    XP --> DM[GET /dolormap/{org}]"""),
}

PLANTILLA = """# Diagrama — {titulo}

> Generado por `scripts/docs/gen_diagramas.py`. Compatible con Mermaid.
> Regenerar: `python -m scripts.docs.gen_diagramas`.

```mermaid
{cuerpo}
```
"""


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for nombre, (titulo, cuerpo) in DIAGRAMAS.items():
        (DEST / f"{nombre}.md").write_text(
            PLANTILLA.format(titulo=titulo, cuerpo=cuerpo), encoding="utf-8")
    print(f"Generados {len(DIAGRAMAS)} diagramas en {DEST}")


if __name__ == "__main__":
    main()
