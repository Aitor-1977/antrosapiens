---
name: Scientific Instrument Protocol
colors:
  surface: '#f9fbec'
  surface-dim: '#d9dbce'
  surface-bright: '#f9fbec'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f5e7'
  surface-container: '#edefe1'
  surface-container-high: '#e8e9dc'
  surface-container-highest: '#e2e4d6'
  on-surface: '#1a1d14'
  on-surface-variant: '#474740'
  inverse-surface: '#2f3228'
  inverse-on-surface: '#f0f2e4'
  outline: '#78776f'
  outline-variant: '#c8c7bd'
  surface-tint: '#5f5f55'
  primary: '#5f5f55'
  on-primary: '#ffffff'
  primary-container: '#fcfaed'
  on-primary-container: '#737369'
  inverse-primary: '#c8c7bb'
  secondary: '#5c6052'
  on-secondary: '#ffffff'
  secondary-container: '#dee1cf'
  on-secondary-container: '#606456'
  tertiary: '#80552c'
  on-tertiary: '#ffffff'
  tertiary-container: '#fff8f5'
  on-tertiary-container: '#97683d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e5e3d6'
  primary-fixed-dim: '#c8c7bb'
  on-primary-fixed: '#1b1c14'
  on-primary-fixed-variant: '#47473e'
  secondary-fixed: '#e1e4d2'
  secondary-fixed-dim: '#c5c8b7'
  on-secondary-fixed: '#191d12'
  on-secondary-fixed-variant: '#44483b'
  tertiary-fixed: '#ffdcc1'
  tertiary-fixed-dim: '#f5bb89'
  on-tertiary-fixed: '#2e1600'
  on-tertiary-fixed-variant: '#653e17'
  background: '#f9fbec'
  on-background: '#1a1d14'
  surface-variant: '#e2e4d6'
  parchment: '#FCFAED'
  parchment-dim: '#2A2D24'
  clay-accent: '#8B5E34'
  amber-accent: '#D48C00'
  olive-deep: '#3E4235'
  friccion-clay: '#6B4423'
  inference-slate: '#4A4E54'
typography:
  narrative-display:
    fontFamily: Newsreader
    fontSize: 42px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  narrative-h1:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
  narrative-body:
    fontFamily: Newsreader
    fontSize: 19px
    fontWeight: '400'
    lineHeight: 32px
  narrative-body-mobile:
    fontFamily: Newsreader
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  ui-label:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  ui-button:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.03em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  data-hash:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  touch-min: 48dp
  margin-mobile: 20px
  margin-desktop: 64px
  gutter: 16px
  rhythm: 8px
---

## Brand & Style

This design system is envisioned as a **Scientific Instrument** for high-stakes anthropological research. It rejects the ephemeral trends of modern SaaS in favor of a "Field Notebook" aesthetic that prioritizes cognitive endurance, methodological rigor, and ontological clarity. 

The design style is **Minimalist-Tactile**. It leverages a high-contrast, low-glare palette to facilitate hours of deep reading without eye fatigue. The interface is defined by functional dualism: separating human synthesis from machine inference through deliberate typographic and color shifts. The emotional response is one of authority, stillness, and intellectual focus—positioning the software as a sophisticated laboratory tool rather than a consumer application.

Key Principles:
- **Cognitive Resilience:** Every decision minimizes visual noise to preserve the researcher's focus.
- **Methodological Shielding:** Friction is intentionally introduced during "Elevation" protocols to ensure scientific rigor.
- **Ontological Separation:** Human-authored content and AI-generated metadata are visually distinct at a glance.

## Colors

The palette is strictly "Mineral," derived from organic earth tones to provide a high-contrast yet low-glare environment. 

- **Primary (Parchment):** The foundation of the light mode. It serves as the primary surface for long-form reading, reducing the "dazzle" effect of pure white.
- **Secondary (Olive Deep):** Used for structural elements, headers, and navigation to provide a grounded frame.
- **Accents (Clay/Amber):** These replace traditional "traffic light" colors. **Clay** is used for "Fricción" (friction/errors), and **Amber** for "Pausa" or "Precaución" (warnings).
- **Neutral (Parchment Dim/Deep Graphite):** The foundation for dark mode and high-density technical metadata.

**Constraint:** Pure white (`#FFFFFF`) and pure black (`#000000`) are prohibited to maintain the "analog instrument" feel. All feedback must remain within the mineral spectrum; do not use green for success or red for errors.

## Typography

Typography is used ontologically to distinguish between human thought and machine calculation.

1.  **Newsreader (Human Judgment):** Reserved for narrative text, field notes, synthesis, and human-led analysis. It conveys the authority of a published monograph.
2.  **JetBrains Mono (Technical Inference):** Used for all AI-generated suggestions, metadata, SHA-256 hashes, and technical identifiers.
3.  **Inter (UI Framework):** Used for functional labels, button text, and system-level navigation to provide a neutral, legible interface layer.

**Core Constraint:** All narrative body text must be constrained to a **maximum line width of 65 characters**. This ensures optimal cognitive resilience and prevents tracking errors during long-form analysis.

## Layout & Spacing

The layout is built for **Ergonomía Android**, prioritizing the "Thumb Zone."

- **Bottom-Anchored Navigation:** All primary methodological transitions (Observation, Description, Analysis, Theory) are located at the bottom of the screen.
- **Fixed Grid:** A 4-column grid for mobile and a 12-column grid for tablet/desktop. On desktop, the central narrative column remains fixed at the 65-character width, with sidebars reserved for "Ariadne's Thread" (traceability) and metadata.
- **Interactive Targets:** Every interactive element must maintain a minimum surface area of **48dp** to ensure precision in field conditions.
- **The Crystallization Cycle:** The layout follows a linear-evolutionary progression. High-level synthesis (N3) is visually distinct from raw signal capture (N0), with increased spacing and "elevation" as data matures.

## Elevation & Depth

Elevation in the design system is a functional metaphor for **Scientific Maturity**.

- **Organic Saturation:** Instead of aggressive shadows, depth is conveyed through "saturation shaders." As a Signal (N0) is elevated to Evidence (N1), its container gains a subtle tonal shift and a soft, diffused shadow to represent its "weight" in the corpus.
- **Tonal Layering:** Surfaces are stacked using the Parchment palette. The most "raw" data sits on the lowest tier (Parchment Dim), while validated "Dictamen" (reports) sit on the highest, most vibrant Parchment tier.
- **Ariadne's Thread:** A lateral visual trail (a subtle vertical line or path) connects a synthesis node back to its source signals, providing constant depth-of-origin.
- **Soft Shadows:** Shadows should be low-opacity, using a tint of the `Olive Deep` or `Clay` colors rather than pure gray, appearing as a natural "bleed" on a physical page.

## Shapes

The shape language is **Soft & Mineral**. 

- **Subtle Rounding:** A base roundedness of 0.25rem (Soft) is used for cards and input fields to reference the slightly rounded edges of a physical field journal.
- **Nodal Geometry:** "Tension Nodes" and "Knots" within the mesh layout use circular forms to imply organic connection points.
- **The "Seal":** The "Seal Report" action uses a distinct circular or hexagonal container to mimic a physical stamped gesture, implying the immutability of the final research phase.

## Components

### Narrative Cards
Large containers for Newsreader text. They must include a "Source Trace" (Ariadne’s Thread) in the margin and use JetBrains Mono for the underlying SHA-256 hash identity.

### Methodological Navigation
Bottom-anchored bar using abstract, glyph-based icons for the four stages:
1. **Observation:** Open eye/lens.
2. **Description:** Horizontal ledger lines.
3. **Analysis:** Intersecting nodes.
4. **Theory:** Solidified crystal/diamond.

### Alerts & Feedback
- **Zero Pop-ups:** All feedback must be inline or via bottom toasts.
- **Lab Language:** Avoid "Error." Use "Sincronización en Pausa" (Sync Paused) or "Fricción de Datos" (Data Friction).
- **Auto-Fade:** Success messages (e.g., "Captura Exitosa") must fade within 2 seconds without user intervention.

### Buttons & Interaction
Interactive areas must be at least 48dp. Buttons use the `Inter` typeface and `Olive Deep` background with `Parchment` text. When a researcher "Elevates" a signal, the transition should feel heavy and deliberate (the "Physical Stamping" gesture).

### Input Fields
Stylized as "Scientific Notes" (Bloc Científico). They use horizontal rules for text entry rather than boxed containers where possible, reinforcing the field note metaphor.