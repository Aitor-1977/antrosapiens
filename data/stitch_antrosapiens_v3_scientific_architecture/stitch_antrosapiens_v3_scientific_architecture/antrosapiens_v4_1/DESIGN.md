---
name: AntroSapiens V4
colors:
  surface: '#fbf9f8'
  surface-dim: '#dbd9d9'
  surface-bright: '#fbf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#eae8e7'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#45474c'
  inverse-surface: '#303030'
  inverse-on-surface: '#f2f0f0'
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
  tertiary-container: '#3a0a00'
  on-tertiary-container: '#d6603b'
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
  tertiary-fixed: '#ffdbd1'
  tertiary-fixed-dim: '#ffb59f'
  on-tertiary-fixed: '#3a0a00'
  on-tertiary-fixed-variant: '#842503'
  background: '#fbf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: '1.2'
  headline-sm:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Newsreader
    fontSize: 20px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Newsreader
    fontSize: 17px
    fontWeight: '400'
    lineHeight: '1.6'
  label-ui:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.01em
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.08em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.5'
  headline-lg-mobile:
    fontFamily: Newsreader
    fontSize: 36px
    fontWeight: '600'
    lineHeight: '1.1'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  margin-safe: 32px
  gutter: 24px
  editorial-width: 720px
  section-gap: 64px
---

## Brand & Style
The design system embodies a "Field Laboratory" aesthetic, merging the scholarly rigor of archival research with the tactile precision of high-quality stationery. The goal is to evoke the feeling of a physical workspace—an organized desk with index cards, heavy paper stock, and ink-filled pens.

The UI avoids "software" tropes in favor of editorial layouts. It utilizes a mix of **Minimalism** and **Tactile** styles, emphasizing whitespace to reduce cognitive load and using subtle borders and textures to simulate physical objects. This creates an environment that feels calm, authoritative, and permanent rather than transient or "high-tech."

## Colors
The palette is mineral and organic, strictly avoiding synthetic "neon" hues. 

- **Surface (Bone/Parchment):** Used for the primary background to simulate physical paper, reducing eye strain during long-form reading.
- **Primary (Ink/Indigo):** Used for high-contrast typography, icons, and structural strokes. It represents human-led documentation.
- **Secondary (Clinical Mint):** Used for success states, confirmed findings, and validated data points. It conveys a sense of scientific accuracy.
- **Tertiary (Sienna/Terracotta):** Reserved for tensions, alerts, or critical observations. It is an earthy alternative to standard "error red."
- **Neutral:** A range of grays with a slight warm undertone to maintain harmony with the parchment surface.

## Typography
Typography is the primary driver of hierarchy in this design system.

1.  **Newsreader (Serif):** Used for all narrative text and headings. This establishes the "editorial" tone and facilitates deep reading.
2.  **Inter (Sans-serif):** Used for functional UI elements—buttons, navigation, labels, and small metadata. It provides a modern, legible contrast to the serif body.
3.  **JetBrains Mono (Monospace):** Reserved exclusively for raw technical data, IDs, timestamps, and machine-generated logic. This creates a clear visual boundary between human interpretation and raw data.

## Layout & Spacing
The layout follows an **editorial fixed grid** philosophy. Content is centered within a 720px maximum width for optimal readability, surrounded by generous whitespace ("editorial margins").

- **Desktop:** 12-column grid with wide 32px margins. Significant vertical gaps (64px+) between major sections to prevent information density.
- **Mobile:** Single column with 20px margins. Navigation is moved to the bottom ("thumb-driven") to ensure accessibility on the go.
- **Rhythm:** All spacing units are multiples of 8px. Use large padding within containers to reinforce the "loose-leaf paper" feel.

## Elevation & Depth
This design system rejects traditional shadows in favor of **Tonal Layers** and **Low-contrast Outlines**.

- **Surfaces:** Use subtle shifts in background color (e.g., a slightly darker parchment shade) to denote different functional areas.
- **Outlines:** UI elements are defined by thin, 1px strokes in a semi-transparent Indigo (#091426 at 15% opacity). This mimics the look of a printed form or a ruled notebook.
- **Stacking:** To suggest depth without shadows, use "stacking offsets" where one index-card-style container slightly overlaps another, or use a 1px solid border with a 2px solid offset border (simulating thickness).

## Shapes
Shapes are intentionally conservative to maintain a professional and "archival" aesthetic. 

- **Containers:** Use `0.25rem` (Soft) corners for most cards and input fields to mimic the slightly worn edge of an index card.
- **Interactive Elements:** Buttons can utilize `rounded-lg` (0.5rem) to differentiate them from static containers.
- **Strictness:** Large-scale layout sections (main content blocks) should have `0` roundedness (sharp) to align with the grid and feel more architectural.

## Components
- **Buttons:** High-contrast Indigo backgrounds with White Inter text for primary actions. Secondary actions use thin borders with no fill.
- **Index Cards (Cards):** The primary container. No shadows; 1px Indigo borders; Parchment background. They should have ample internal padding (min 24px).
- **Metadata Chips:** Small, rectangular containers using JetBrains Mono. They look like "stamps" or "labels" affixed to the page.
- **Inputs:** Simple underlined fields (reminiscent of a paper form) or fully outlined boxes with subtle `rounded-sm` corners.
- **Navigation:** Bottom-docked on mobile, resembling a tabbed folder system.
- **Lists:** Bulleted with small "ink-drop" icons or simple dashes. Lines between list items are thin and low-contrast.
- **Field Notes (Special Component):** A sidebar or inset box with a slightly different paper texture/color, used for researcher observations or qualitative annotations.