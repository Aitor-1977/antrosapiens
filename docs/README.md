# Documentación — Ecosistema Hamaca Digital

> Índice maestro. **Toda** la documentación técnica vive aquí (ADR-0004),
> versionada y verificada contra el código. Punto de entrada para auditoría,
> onboarding y reconstrucción total.

## Empezar aquí
- **[README_TECNICO.md](./README_TECNICO.md)** — qué es, instalar, ejecutar, tests, deploy.
- **[GUIA_RECONSTRUCCION_TOTAL.md](./GUIA_RECONSTRUCCION_TOTAL.md)** — reconstruir el ecosistema desde cero.
- **[DOCUMENTACION_MAESTRA.md](./DOCUMENTACION_MAESTRA.md)** — documento maestro de Motor A (23 secciones).

## Ecosistema y fronteras
- **[ARQUITECTURA_ECOSISTEMA.md](./ARQUITECTURA_ECOSISTEMA.md)** — 3 motores, 6 diagramas, estado 1.0.
- **[FRONTERAS_MOTORES.md](./FRONTERAS_MOTORES.md)** — responsabilidad definitiva (A piensa, B muestra, C vende).
- **[CANON_OPERATIVO_RADARHD.md](./CANON_OPERATIVO_RADARHD.md)** — documento canónico del uso metodológico de RadarHD (Motor B/C).
- **[CONTRATOS_API.md](./CONTRATOS_API.md)** — contrato `motor_a.corpus.v1` y superficies API.
- **[ROADMAP_ARQUITECTONICO.md](./ROADMAP_ARQUITECTONICO.md)** — plan de cutover a Arquitectura 1.0.

## Inventarios (verificados)
- **[INVENTARIO_ENDPOINTS.md](./INVENTARIO_ENDPOINTS.md)** — 121 endpoints (72 A + 49 RadarHD).
- **[INVENTARIO_TABLAS.md](./INVENTARIO_TABLAS.md)** — 34 tablas (20 A + 14 RadarHD).
- **[INVENTARIO_COMPONENTES.md](./INVENTARIO_COMPONENTES.md)** — módulos, engines, servicios, componentes.

## Decisiones de arquitectura (ADR)
- **[ADR/ADR_0001_ARQUITECTURA_1_0.md](./ADR/ADR_0001_ARQUITECTURA_1_0.md)** — Motor A piensa, B muestra, C vende.
- **[ADR/ADR_0002_CAPAS_CIENTIFICAS.md](./ADR/ADR_0002_CAPAS_CIENTIFICAS.md)** — la inferencia vive solo en Motor A.
- **[ADR/ADR_0003_GOBERNANZA.md](./ADR/ADR_0003_GOBERNANZA.md)** — versionado, hashes, auditoría, reproducibilidad.
- **[ADR/ADR_0004_DOCUMENTACION.md](./ADR/ADR_0004_DOCUMENTACION.md)** — la documentación vive en el repo.

## Capas (0–18)
Una ficha por capa en **[CAPAS/](./CAPAS/)**:
[00](./CAPAS/CAPA_00.md) · [01](./CAPAS/CAPA_01.md) · [02](./CAPAS/CAPA_02.md) ·
[03](./CAPAS/CAPA_03.md) · [04](./CAPAS/CAPA_04.md) · [05](./CAPAS/CAPA_05.md) ·
[06](./CAPAS/CAPA_06.md) · [07](./CAPAS/CAPA_07.md) · [08](./CAPAS/CAPA_08.md) ·
[09](./CAPAS/CAPA_09.md) · [10](./CAPAS/CAPA_10.md) · [11](./CAPAS/CAPA_11.md) ·
[12](./CAPAS/CAPA_12.md) · [13](./CAPAS/CAPA_13.md) · [14](./CAPAS/CAPA_14.md) ·
[15](./CAPAS/CAPA_15.md) · [16](./CAPAS/CAPA_16.md) · [17](./CAPAS/CAPA_17.md) ·
[18](./CAPAS/CAPA_18.md)

## Diagramas (Mermaid)
En **[DIAGRAMAS/](./DIAGRAMAS/)**: arquitectura general, comunicación entre
motores, flujo de evidencia, pipeline científico, pipeline comercial, gobernanza,
validación, dolor cultural, drift, onlife, curaduría, centro de inteligencia.

## Gobernanza documental
- **[CHANGELOG.md](./CHANGELOG.md)** — historial reconstruido desde Git.
- **[INCONSISTENCIAS.md](./INCONSISTENCIAS.md)** — control de calidad y hallazgos.

## Documentación de contexto (preexistente)
[captura_inteligente.md](./captura_inteligente.md) ·
[evidencia_produccion.md](./evidencia_produccion.md) ·
[perfil_prospecto_hd.md](./perfil_prospecto_hd.md) ·
[validacion_produccion.md](./validacion_produccion.md)

## Regenerar documentación
```bash
python -m scripts.docs.gen_capas       # docs/CAPAS/CAPA_00..18.md
python -m scripts.docs.gen_diagramas   # docs/DIAGRAMAS/*.md
```
