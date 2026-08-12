# Arquitectura AntroSapiens V3: El Instrumento de Indagación Antropológica

## 1. Declaración de Identidad (Ontología del Producto)
AntroSapiens **no es una aplicación de noticias**. Es una **Estación Científica de Campo** móvil. Su propósito es la reducción de ruido y la cristalización de evidencia para la toma de decisiones críticas.

### El Perfil del Investigador (Persona)
- **Rol:** Antropólogo Senior.
- **Entorno:** Sesiones de +3 horas en dispositivos móviles, a menudo bajo fatiga cognitiva o estrés.
- **Necesidad:** Rigor metodológico, trazabilidad absoluta y minimización de carga cognitiva.

---

## 2. Nueva Arquitectura Cognitiva
Sustitución del paradigma lineal "Noticia → Chatbot" por un flujo circular de validación científica:

1.  **Pregunta:** El disparador de la investigación (foco).
2.  **Corpus (Motor A):** Captura bruta de señales (RSS, GDELT, PDF, Web).
3.  **Curación (Motor B):** Normalización, deduplicación y detección de tensiones.
4.  **Evidencia:** El átomo inmutable de verdad.
5.  **Tensiones/Contradicciones:** Visualización de la incertidumbre.
6.  **Hipótesis:** Construcción de sentido humano apoyado por IA.
7.  **Interpretación (Motor C):** Capa de análisis (DolorMap®, Deuda Cultural).
8.  **Dictamen / Informe:** Salida final de alto valor.

---

## 3. Modelo de Motores (Sinfonía Operativa)

| Motor | Función | Salida | Carácter |
| :--- | :--- | :--- | :--- |
| **Motor A (Indagación)** | Descubrimiento ciego. | Corpus Bruto | Técnico/Monoespaciado |
| **Motor B (Rigor)** | Limpieza, clasificación y mapeo. | Corpus Estructurado | Invisible/Funcional |
| **Motor C (Interpretación)** | Generación de hipótesis y riesgos. | Dictamen | Narrativo/Experto |

---

## 4. Rediseño de UX/UI (Principios V3)

### Navegación Basada en Estado, no en Módulos
Eliminación de pestañas "Noticias", "Favoritos", "Perfil". 
**Navegación:** `Inicio (Radar) → Evidencia → Tensiones → Hipótesis → Dictamen`.

### Interfaz de Instrumento Científico
- **Modo Obscuro (OLED):** Para reducir fatiga visual en sesiones largas.
- **Tipografía Diferenciada:** 
    - `JetBrains Mono` para datos crudos y logs de Motor A.
    - `Inter` para narrativa y peritaje humano.
- **Acciones con una sola mano:** Controles en la zona inferior (zona de pulgar).
- **Cero Distracción:** Eliminación de animaciones "vivas". Transiciones secas y funcionales.

---

## 5. Sistemas Específicos

### Sistema de Evidencia (El Átomo)
Cada pieza de información se presenta con:
- **Índice de Certeza:** Visualización de la incertidumbre (Principio 7).
- **Rastro de Origen:** Botón inmediato a la fuente original (Principio 2).
- **Auditoría:** Quién y cuándo validó esta evidencia (Principio 3).

### Sistema de Incertidumbre (Visualización)
Los vacíos de información o contradicciones entre fuentes no se ocultan; se destacan como "Nodos de Tensión" que requieren intervención humana o más indagación del Motor A.

### Persistencia y Offline (Modo Campo)
- Estrategia *Offline-First*. Toda la base de datos local se sincroniza en ráfagas.
- Marcado rápido y selección de texto optimizada para "captura de campo".

---

## 6. Arquitectura de Estados de la Investigación
La pantalla principal es un **Dashboard de Salud Metodológica**:
- % de cobertura del Corpus.
- Nivel de contradicción detectado (Tensiones).
- Calidad metodológica (Alta/Media/Baja).
- Preguntas abiertas vs. Hipótesis cerradas.

---

## 7. Plan de Implementación (Fases)

### Fase 1: Cimiento Metodológico
- Implementación de la nueva configuración Tailwind (RadarHD Design System).
- Creación de la estructura de navegación de "Flujo de Indagación".
- Pantalla de Inicio: Estado de la Investigación.

### Fase 2: El Alambique (Motores A & B)
- Interfaz de visualización de Corpus Estructurado.
- Sistema de tarjetas de Evidencia con trazabilidad.
- Herramientas de resaltado y notas de campo.

### Fase 3: La Síntesis (Motor C)
- Módulo de DolorMap® y Deuda Cultural.
- Generador de Hipótesis y visualización de Tensiones.
- Exportación de Dictámenes e Informes Científicos.

---

**Documento generado por Stitch para el Laboratorio de Antropología de la Innovación de Hamaca Digital.**
**,data_type: