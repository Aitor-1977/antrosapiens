# 0003 · Bounded Contexts (separación estricta DDD)

> Evidencia: `docs/AUDITORIA/04_CIERRE_MODELO_DOMINIO.md` §6.

## Los cuatro contextos

### BC-I · Observación Antropológica  (owner: Motor A)
- **Raíz:** Organización Observada.
- **Ciclo:** `Señal → Evidencia → Corpus → Motor A → Peritaje → DolorMap®`.
- **Lenguaje:** Evidencia, Señal, Corpus, Deuda Cultural™, Dictamen científico, Curaduría,
  Onlife (hibridación), DolorMap®, Validación, Gobernanza, deriva narrativa, colapso estructural,
  ritual competidor.
- **PROHIBIDO:** lógica comercial, CRM, ventas, cadencia, contacto.

### BC-II · Operación Comercial  (owner: RadarHD / Motor C)
- **Raíz:** Prospecto.
- **Ciclo:** `DolorMap® válido → Bitácora → Contacto → Sprint → Caso → Aprendizaje`.
- **Lenguaje:** Prospecto, Bitácora, Cadencia, Siembra, Cualificación Liminal, Decisor, SOW,
  Sprint Fundacional, Peritaje Activo, Kill Switch, Reactivación, Caso.
- **PROHIBIDO:** interpretar evidencia, ejecutar IA, generar Deuda Cultural, clasificar señales.

### BC-III · Captura & Corpus  (owner: Motor A; hoy duplicado en RadarHD)
- **Lenguaje:** Fuente, Conector, Prefiltro, Ruido, Normalización, Dedup, `corpus.v1`.
- **Estado:** frontera **violada** (RadarHD tiene captura+LLM propia). A colapsar (ver `0007`).

### BC-IV · Presentación & Navegación  (owner: RadarHD)
- **Lenguaje:** Estación, Dossier, Panel, Vista.
- **Invariante:** la vista no piensa.

## Context map (relaciones)
- **BC-I → BC-IV:** Customer/Supplier vía contrato read-only (gateway). ✅
- **BC-I → BC-II:** relación por evento (`confirmar señal`) — hoy **nominal**, debe ser
  **referencial por ID** (Prioridad 1). Candada por **Regla Cero**.
- **BC-III ⇄ BC-I:** duplicado — a colapsar.
- **BC-II → BC-I:** hoy **inexistente** — debe crearse el loop de aprendizaje.

## Separación formal (regla de merge)
Ningún módulo puede pertenecer a dos contextos. Ningún archivo de BC-II puede importar
motores de inferencia. Ningún archivo de BC-I puede importar lógica comercial. Toda mezcla
detectada es deuda que se aísla, no se tolera.
