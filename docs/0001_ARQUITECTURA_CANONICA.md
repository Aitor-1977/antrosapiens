# 0001 · Arquitectura Canónica de Referencia

> Detalle y evidencia: `docs/AUDITORIA/02_MODELO_MENTAL_CTO.md` y
> `03_ESPECIFICACION_CANONICA.md`.

## Columna de la plataforma (una sola)
```
Captura de evidencia ─┐
Normalización         ├─►  MOTOR A (Antrosapiens) — única inferencia, determinista, gobernada
Corpus (motor_a.corpus.v1)                 │  API read-only + contratos versionados
                                           ▼
                                   GATEWAY (motor-a.gateway.ts) — frontera única A→B/C
                                           ▼
                     RADARHD — consume · compone (Motor C) · opera · registra
                       ├─ DolorMap®  (síntesis del peritaje de A) → GATE (Regla Cero)
                       ├─ Bitácora   (avance metodológico + comercial)
                       └─ Sprint Fundacional (decisión humana; congela el foco)
```

## Reglas de la arquitectura
1. **Dirección única** de integración: A publica, RadarHD consume. RadarHD **nunca**
   escribe en A ni comparte su base de datos.
2. **Contrato versionado con candado:** un tag desconocido rompe el consumo (nunca se
   ingieren formas desconocidas).
3. **La vista no piensa:** cero lógica de dominio (inferencia) en componentes React.
4. **Regla Cero:** la operación comercial (BC-II) está candada por el peritaje científico
   (BC-I). Ver `0000` y `0005`.

## Estado actual vs objetivo (resumen)
- **Sano hoy:** corpus, gateway, operación, Bitácora, Sprint, contrato read-only.
- **Deuda viva (ver `0007`):** inferencia duplicada (LLM en RadarHD + React), captura
  duplicada, costura BC-I↔BC-II **nominal (por nombre)**, falta de gate DolorMap y de
  loop de aprendizaje hacia A.

## Adaptador temporal declarado
`expedientes.service.ts` es un **adaptador de compatibilidad** (Fase 3): mapea el Dossier
de Motor A a la forma `ExpedienteVivo` que consumen los servicios comerciales. Es puente
temporal, no deuda permanente; muere cuando los consumidores hablen la forma nativa de A.
