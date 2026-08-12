---
name: AntroSapiens V4
colors:
  surface: '#fcfaed'
  surface-dim: '#dcdace'
  surface-bright: '#fcfaed'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f4e7'
  surface-container: '#f0eee1'
  surface-container-high: '#eae9dc'
  surface-container-highest: '#e5e3d6'
  on-surface: '#1b1c14'
  on-surface-variant: '#45474c'
  inverse-surface: '#303129'
  inverse-on-surface: '#f3f1e4'
  outline: '#75777d'
  outline-variant: '#c5c6cd'
  surface-tint: '#545f74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#111c2e'
  on-primary-container: '#7a849b'
  inverse-primary: '#bcc7df'
  secondary: '#006c4e'
  on-secondary: '#ffffff'
  secondary-container: '#97f5cc'
  on-secondary-container: '#007353'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#1a1b22'
  on-tertiary-container: '#83838c'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2fc'
  primary-fixed-dim: '#bcc7df'
  on-primary-fixed: '#111c2e'
  on-primary-fixed-variant: '#3d475b'
  secondary-fixed: '#97f5cc'
  secondary-fixed-dim: '#7bd8b1'
  on-secondary-fixed: '#002115'
  on-secondary-fixed-variant: '#00513a'
  tertiary-fixed: '#e3e1ec'
  tertiary-fixed-dim: '#c6c5cf'
  on-tertiary-fixed: '#1a1b22'
  on-tertiary-fixed-variant: '#46464e'
  background: '#fcfaed'
  on-background: '#1b1c14'
  surface-variant: '#e5e3d6'
typography:
  narrative-display:
    fontFamily: Newsreader
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 48px
    letterSpacing: -0.02em
  narrative-display-mobile:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 38px
  narrative-body:
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
  ui-control:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  technical-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  technical-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  touch-target: 48px
  margin-mobile: 20px
  margin-tablet: 40px
  gutter: 16px
  thumb-zone-bottom: 120px
---

## Brand & Style
The design system for this scientific instrument is rooted in the "Digital Parchment" philosophy—a marriage of archival preservation and clinical precision. It rejects the hyper-stimulating tropes of commercial software in favor of a quiet, mineral aesthetic that respects the cognitive load of anthropological field research.

The UI should evoke the feeling of an authoritative field journal: tactile, permanent, and intellectually rigorous. It utilizes a **Modern-Editorial** style with a focus on high-quality typography and intentional "void" space. Visual flourishes are limited to subtle grain textures and high-precision technical linework, ensuring the observer’s focus remains entirely on the subject and the data.

## Colors
The palette is derived from natural mineral sources and archival materials to reduce eye strain during extended observation periods.

- **Parchment (#FCFAED):** The primary surface. It provides a warm, low-glare background that feels more organic than pure white.
- **Parchment Dim (#F2EFE0):** Used for secondary surfaces, recessed areas, or "dimmed" modes for low-light fieldwork.
- **Mineral Blue (#091426):** The color of narrative and judgment. Used for primary text, deep ink-like headers, and decisive UI actions.
- **Clinical Mint (#047857):** Reserved strictly for technical inference, AI metadata, and system-generated annotations. It signifies "machine logic" as distinct from "human observation."
- **Mineral Gray (#71717A):** Used for structural elements, borders, and tertiary metadata that does not require immediate focus.

Avoid all "traffic light" color systems. Error states should be communicated through iconography (e.g., the *Fracture* glif) or weight changes rather than red/green/yellow indicators.

## Typography
Typography is the core of this system, establishing a clear hierarchy between human insight and technical data.

- **Newsreader (Serif):** Used for the "Human Narrative." Any text that represents observation, field notes, or anthropological conclusions must be set in this serif to maintain an editorial tone.
- **Inter (Sans):** Used for "The Instrument." UI controls, buttons, and system navigation are set in Inter to provide a neutral, functional contrast to the narrative.
- **JetBrains Mono (Monospace):** Used for "The Evidence." Hashes, coordinates, timestamps, and AI-generated metadata use this font to signify raw, unprocessed information.

**Line Length:** Narrative text must never exceed 65 characters per line to ensure optimal legibility and focus.

## Layout & Spacing
The layout follows a 4px baseline grid. On Android devices, the "Thumb Zone" (the bottom 40% of the screen) is prioritized for all frequent interactive elements.

- **Grid:** A 12-column fluid grid for tablet; 4-column for mobile.
- **Margins:** Generous 20px margins on mobile to avoid edge-bleeding and provide a "framed" archival look.
- **Touch Targets:** A strict minimum of 48x48dp for all interactive elements, regardless of visual size.
- **Ergonomics:** Primary navigation and data entry triggers are anchored to the bottom-right or bottom-center to accommodate one-handed operation during active observation.

## Elevation & Depth
This design system avoids shadows in favor of **Tonal Layering** and **Mineral Outlines**. 

- **Surface Tiers:** Depth is created by placing Parchment (#FCFAED) elements on Parchment Dim (#F2EFE0) backgrounds.
- **The Ink Line:** Structural separation is achieved via 1px solid lines in Mineral Gray or 0.5px "Hairlines" in Mineral Blue.
- **The Etched State:** Active or pressed states should appear "etched" into the surface (subtle inner border) rather than lifted above it.
- **Glassmorphism:** Use only for temporary analytical overlays, employing a heavy backdrop blur (20px+) with a Mineral Blue tint at 5% opacity.

## Shapes
The shape language is "Soft-Technical." Elements use a subtle 4px (0.25rem) radius to feel approachable but precise. 

- **Hard Corners:** Used for technical data containers and "evidence blocks" to imply rigidity and facts.
- **Soft Corners:** Used for narrative inputs and human-centric cards to imply fluidity and interpretation.
- **Abstract Glifs:** Icons are not literal representations. Use geometric metaphors:
    - *Pulse:* Frequency of interaction.
    - *Anchor:* A fixed point of observation.
    - *Zigzag:* Non-linear progression/deviation.
    - *Fracture:* A point of contention or system error.

## Components
- **Primary Action Buttons:** Solid Mineral Blue with Inter-Medium text in Parchment. No gradients. 48dp height minimum.
- **Analytical Chips:** Outlined in Clinical Mint with JetBrains Mono text. These represent system tags or machine-inferred categories.
- **Narrative Input:** Minimalist fields with a single bottom-border (1px Mineral Blue). When focused, the border weight increases to 2px.
- **Observation Cards:** Parchment-colored containers with a 1px Mineral Gray border. Headers are Newsreader SemiBold; metadata is JetBrains Mono.
- **The "Anchor" FAB:** A square floating action button (4dp radius) located in the thumb zone for initiating a new observation.
- **Data Lists:** High-density rows with hairline separators. No chevrons; use weight changes in the typography to indicate "drill-down" capability.
- **Absence of Progress:** Instead of bars, use the *Pulse* glif in a slow, rhythmic opacity fade to indicate background processing—respecting the slow nature of anthropological work.