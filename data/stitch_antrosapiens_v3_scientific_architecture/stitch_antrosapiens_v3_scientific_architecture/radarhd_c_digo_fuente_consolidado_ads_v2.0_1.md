# RadarHD OS | Código Fuente Consolidado (ADS v2.0 - Cuaderno de Campo)

Este documento constituye el blueprint técnico oficial para la implementación del Sistema Operativo Antropológico RadarHD, bajo los principios de rigor metodológico y separación estricta de inferencias.

## 1. Arquitectura de Diseño (Tailwind Config)

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'surface': '#f9f9f7', // Mineral Gray
        'on-surface': '#1e293b',
        'primary': '#091426',
        'secondary': '#d0e1fb',
        'outline-variant': 'rgba(0,0,0,0.06)', // Membranas sutiles
        'clinical-mint': '#047857',
        'motor-a-gray': '#64748B', // Inferencia de IA
      },
      fontFamily: {
        'sans': ['Inter', 'sans-serif'], // Narrativa y UI
        'mono': ['JetBrains Mono', 'monospace'], // Metadatos y Motor A
      },
      borderRadius: {
        'ads-card': '16px',
        'ads-action': '8px',
      }
    },
  },
}
```

---

## 2. Flujo Metodológico: Investigar → Expediente → Motor A → DolorMap® → Sprint
El sistema opera como una secuencia inmutable de rigor. Ningún hallazgo puede certificarse sin haber transitado por las estaciones previas.

### Estación Actual: Estación Maestra (Capa 0)
**Source:** `{{DATA:SCREEN:SCREEN_168}}`

```html
{{DATA:SCREEN:SCREEN_168}}
```

---

## 3. Protocolo de Inferencia (Motor A vs Peritaje)
La IA (Motor A) actúa únicamente como fuente de señales y reducción de ruido. El peritaje (juicio experto) se registra en bloques de narrativa humana inmutables. 

- **Motor A Logs:** Siempre en JetBrains Mono, prefijados con `[SCAN]`, `[LOG]` o `[ALERT]`.
- **Peritaje Humano:** En Inter, tipografía de alta legibilidad, firmado con ID del Investigador.

---
*Este documento es la única fuente de verdad para la inyección de código en entornos de desarrollo RadarHD.*
