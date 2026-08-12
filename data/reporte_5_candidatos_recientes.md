# Reporte · 5 Candidatos Comerciales recientes

**Fecha de corrida:** 2026-08-11 19:26 UTC
**Entorno:** local (Termux · Linux)
**Base de datos:** `~/antrosapiens/data/hd_scraper.db` (SQLite)
**Directorio temporal:** `~/antrosapiens/data/` (regla de entorno: prohibido `/tmp`; `TMPDIR`/`TMP`/`TEMP` redirigidos en runtime)
**Conectores de ingesta:** `google_news` (+ enriquecimiento `rss_fijos`, `gdelt`)

---

## 1. Resumen de la ingesta (`run_once`, modo autónomo)

- Objetivos barridos por defecto: **52** organizaciones del directorio semilla curado (VC · Startup · Incubadora · Corporativo).
- Evidencias escritas: **3589** · `estado=ok` (consumibles por la API) · **0 rechazadas** · **0 duplicadas**.
- 52/52 organizaciones del directorio con evidencia captada.

## 2. Materialización de Candidatos Comerciales (BC-I → BC-II)

- Candidatos materializados: **52** (uno por organización detectada con evidencia), por `candidato_id` determinista (sha256 del nombre normalizado).
- Prospectos vinculados: **52** de 52 (identidad referencial `organización → candidato → prospecto → expediente → evidencia`).
- Estados: `detectado`: 47 · `observado`: 5.
- **Regla Cero (G0):** `g0_permitido = 5`. Solo los candidatos con dictamen `VALIDADA`/`VALIDADA_PARCIAL` pueden avanzar a `observado`; el resto queda bloqueado por la ciencia.

## 3. Los 5 Candidatos Comerciales recientes

Ordenados por la **señal más reciente** capturada (`fecha_publicacion` máxima de la evidencia).

| # | Organización | Categoría | Escala | Scoring | Score ICP | Dictamen (G0) | Evidencias | Última señal |
|---|--------------|-----------|--------|---------|-----------|----------------|------------|--------------|
| 1 | **Angel Ventures** | VC | 11-50 | B | 65 | BLOQUEADA | 43 | 2026-08-11 |
| 2 | **Arca Continental** | Corporativo | 501+ | B | 65 | BLOQUEADA | 95 | 2026-08-11 |
| 3 | **BBVA México** | Corporativo | 501+ | A | 99 | BLOQUEADA | 98 | 2026-08-11 |
| 4 | **Clara** | Startup | 201-500 | A | 100 | **VALIDADA** (G0 ✓) | 102 | 2026-08-11 |
| 5 | **Clip** | Startup | 501+ | B | 65 | BLOQUEADA | 99 | 2026-08-11 |

### Detalle por candidato

**1. Angel Ventures** — `id=104` · `candidato_id=0239a873…96578d`
- Estado: `detectado` · Prospecto id: `7` · Dictamen: `BLOQUEADA` · G0: `False`.
- Expediente: `a1632261dc8c16f32e7fc26da643b5c0708b3b0b823f34667ff8b5bfc42b5c82`.
- Mejor evidencia (confianza 1.0): *«José Manuel Moller vende su porcentaje en startup Fracción y lidera ronda en su empresa Algramo - Diario Financiero»* — Diario Financiero.
  - URL: https://news.google.com/rss/articles/CBMirgFBVV95cUxNM2RBSk5oTmpCazVXLWRLaXJLa1VRZjNIQkUxR1c3SjU0ai1IMTNsQVJTeUVBU0wzUlRzZ2ozZXlSOVpieWFqTkRRb0k3VHpPcWZKOE41VUVzcmx5X09SOGZ0LTFPdnhSQVhBbllYb0t5UTlVNllyVUNGMEJLbzE1V2ZEYWRidEplN3hBdWNUUWZGYVhfV2hYODI4Tk1yeWFsNXQxNjZvclJKa0VyYVE?oc=5

**2. Arca Continental** — `id=105` · `candidato_id=010ccd40…c66b30`
- Estado: `detectado` · Prospecto id: `51` · Dictamen: `BLOQUEADA` · G0: `False`.
- Expediente: `dd878669afa488d19d13726aeeb80d4f8f1041f018d82e336d3c240980f660d6`.
- Mejor evidencia (confianza 1.0): *«Arca Continental lanza el programa Somos Locales en alianza con la UANL - Reporte Indigo»* — Reporte Indigo.
  - URL: https://news.google.com/rss/articles/CBMiygFBVV95cUxPTXdueWt3ZFgyOHRhVTc0NEZOQ0tSLU11UUZISjNvNDZJcE51VU5TWVRrUXlTRU5uZDc5NU45NFNhRkNacVVFS09iaEZGZWFQbU9iTkpPMTlBaHhoTEl5MFNzLWY3UlQzc0JaQmhQRFYyNnRKTDcyM0VKcWNWajd4ZFp5bUZvVGJOOFZ4TzRRRGFPZkxMcnAwRWVmdXd2WlJPM09QVjFxbmF6QlI2VEdkSXI5MjNkLVUtMzlaVW9vMzhBQUtCblpWcmVB0gHPAUFVX3lxTE5XQ0VYV2Y1YW5GRVBtM3FFMnRUek9lLU5JVVNLekhwd1p4SDJCcm1iWFhRSXFacWZLZXZfeHRfZngzOXZrUi0yNWJsMjNTNDRaV25rb2ZGT0x3QmlXR3dnNmlSQ1VRdnp6ODZaVTZKMG9XajczcFh6SHJvV3RZVEZ5dU5oc1NOUW5Oc1I4R2FzSGhPRnFGWmxIb0lxXzRnMXlGQXNVTmUwOWE0Vi1Bc2k0SF93MGVXMkVOVVBJeEdnNHdBd0dUbUVpWC1lYk16NA?oc=5

**3. BBVA México** — `id=106` · `candidato_id=d9867778…66c96e`
- Estado: `detectado` · Prospecto id: `49` · Dictamen: `BLOQUEADA` · G0: `False`.
- Expediente: `dfef4d0792b6ff599613262fa7a187f16afe9c739f11a2c1787ebee0175aa42a`.
- Mejor evidencia (confianza 1.0): *«BBVA México y la AMAV firman alianza para digitalizar cobros y financiar a 500 agencias de viajes - BBVA»* — BBVA.
  - URL: https://news.google.com/rss/articles/CBMizwFBVV95cUxNQ0hTczdxc1dXLUl3OFY1eUZseHZzazBVM1NCbUZnOHd6RHZCc0pWVU5LWktMcHlTN3puZW9nSi1aaDl5NGxqcDhSYVZfM09LZGFvTEt4Yk1Pdmdlb1VjLVRsWVBBZm1lR2hSaXpSZE1fNEp6M2p1aUxTemZfTkZLTmpKRFRUTzIxQk1VYjlPUXVzNUgtRnVZTTJIbGxLdVRpamt3VmJsdk9ORVZSbkdNelREMkNkUDNRcVh4Sld2c3JRcFhtVzNUWG5vWm02YUU?oc=5

**4. Clara** — `id=110` · `candidato_id=6e613b93…4c52f0`
- Estado: `observado` · Prospecto id: `17` · Dictamen: `VALIDADA` · G0: `True`.
- Expediente: `4c4dc988c86c9d55883af9770be1f9fefa23c692383c649263c8a9e222149cab`.
- Mejor evidencia (confianza 1.0): *«CLARA BRUGADA ENTREGA 87 OBRAS ESTRATÉGICAS EN COYOACÁN Y TLALPAN RUMBO AL MUNDIAL DE FÚTBOL; DESTACA INVERSIÓN POR 260 MILLONES DE PESOS Y AFIRMA: “¡CUMPLIMOS LO PROMETIDO!” - Secretaría de Obras y Servicios de la CDMX.»* — Secretaría de Obras y Servicios de la CDMX..
  - URL: https://news.google.com/rss/articles/CBMi1wFBVV95cUxPeldqZFRHNVhjaFNEeWswd1lPX3RpdVYya0tudUgzNjljVXlDekN0Y1RFSl9haU1BTnV3ZzFQd3p6T1NnclBPaW5xeDNNYW1RZC0xdTNUWERWdVQ2RzlTOEoyUG5HdFdpcThkU0hHYU9ubzdiajFkSDdxM0NXSUxCSlM3RWdqclc4WWRraVVJNm9aSDRhd3k3WU43M2lmc1UxekJoMHVIc010THdqR1Q3RmJ3WWZBSXN6dmpBZHJLRW02RnpaY1hHNXZPUlB5QjFzdzVfYUhJVQ?oc=5

**5. Clip** — `id=111` · `candidato_id=f7770b7d…ee0173`
- Estado: `detectado` · Prospecto id: `15` · Dictamen: `BLOQUEADA` · G0: `False`.
- Expediente: `b1bbdf189807191a7af8e7df6f472dcedcc0dec3bdc5a5e064964ab91bd64812`.
- Mejor evidencia (confianza 1.0): *«CMF presenta los Clip Pro, sus primeros auriculares 'open-ear' con diseño de 'clip on' y autonomía de hasta 32,5 horas - infobae.com»* — infobae.com.
  - URL: https://news.google.com/rss/articles/CBMi-AFBVV95cUxQcnB6UFpRSzV2SGZUTWlrLUxvX0pqbkZpVmllTzZXYTBCZGo1elJjSU82ZGNSMktBTGd0SV9GWUJjSFVMNXhpdzJ6M1R2bmt0S3F4cEZOZ1NHcV9mTW5qTFdFTklRWV91OVYzOFdnT1dHeVdYUkxkeTlkQ2JKN2VPYlNYQWpGWDlEOFdheEVIbk5oclhHZXlKZ2x5UHo5Y3VsWmZfRjJwNFI0SFl1NXdZVFJ0emNSQzYwa19tdzJMazV2eVNQeWlmSHBCZDAtRWxxOTlQQzFXRnhzUEJLa2ZxdVRPSHJKd0Uxdll4OXVVNkJzaG8ybDgxddIBkwJBVV95cUxOX1RBQnVpMThSSG43WS0tT0pxWDRHenRQODg1Szc4cjBXZXJyYXBicE9ZcXVoT3psLThFdGFaeDl1SUs1SHRvOTNlZWVTNDhod25zOGhseWM2MDlmTnhCSDQ4cWJOYU9aODRiZEV0bjJiWS1tMEZERHZsX0dEbTJuSGRhd0xtdmZESldDekZEdjhTSy1aTGQ5SnlmNHVRNUFHM1l0LXhDb3lFWlZsb2ZVZ0ZxZjREVFBBXy1rR3ZYdmRjOUFZTnhfcDBSNlVNMlh0dUdTclU5NFl0MHdxZ3dERHUzVFp4MnEyb0M5bWh3YTlBVmVKTGhxWUpKc1lHczVKaE5hRlc0OFZaQURfZm1mbl9ldw?oc=5

---

## 4. Notas de trazabilidad y calidad

- **Regla Cero activa:** los candidatos con dictamen `BLOQUEADA`/`SIN_HIPOTESIS` permanecen en `detectado`; solo avanzan los de dictamen validado. La decisión de qué hacer con los observados corresponde al operador vía RadarHD (Motor B); Motor A solo registra la detección y la observación.
- **Ruido por homonimia:** las señales de *Cometa* (cometa astronómico) y *Clara* (Clara Brugada) son coincidencias léxicas del nombre exacto, no actividad de la organización. Es extracción objetiva de la fuente (búsqueda exacta por nombre); la interpretación/descartado no es de este motor.
- **Corroboración independiente:** GDELT y RSS fijos aportan dominios reales de medios; sin ellos, todas las notas de Google News compartirían el dominio agregador `news.google.com` y contarían como una sola fuente para la Validación Científica (Capa 11).
- **Determinismo:** cada `candidato_id` y `expediente_hash` es reproducible (mismo insumo ⇒ mismo resultado). Re-materializar no duplica filas ni transiciones.
- **Cadena referencial verificable** con `python -m scripts.trazabilidad` (solo lectura).

*Fin del reporte.*
