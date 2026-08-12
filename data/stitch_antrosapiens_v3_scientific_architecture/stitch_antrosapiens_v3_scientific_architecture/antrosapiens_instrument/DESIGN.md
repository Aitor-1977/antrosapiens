---
name: AntroSapiens Instrument
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
  surface-tint: '#545f73'
  primary: '#091426'
  on-primary: '#ffffff'
  primary-container: '#1e293b'
  on-primary-container: '#8590a6'
  inverse-primary: '#bcc7de'
  secondary: '#436653'
  on-secondary: '#ffffff'
  secondary-container: '#c2e9d2'
  on-secondary-container: '#476a58'
  tertiary: '#041528'
  on-tertiary: '#ffffff'
  tertiary-container: '#1a2a3e'
  on-tertiary-container: '#8191a9'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e3fb'
  primary-fixed-dim: '#bcc7de'
  on-primary-fixed: '#111c2d'
  on-primary-fixed-variant: '#3c475a'
  secondary-fixed: '#c5ebd4'
  secondary-fixed-dim: '#a9cfb9'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#2c4e3d'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#fcfaed'
  on-background: '#1b1c14'
  surface-variant: '#e5e3d6'
  parchment: '#FCFAED'
  ink-blue: '#1E293B'
  stone-blue: '#475569'
  moss-green: '#2D4F3E'
  terracotta-alert: '#991B1B'
  amber-question: '#D97706'
  slate-text: '#334155'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
  headline-md-mobile:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  body-reading:
    fontFamily: Newsreader
    fontSize: 20px
    fontWeight: '400'
    lineHeight: 32px
  body-reading-mobile:
    fontFamily: Newsreader
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  mono-technical:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  mono-label:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  metadata:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  margin-mobile: 24px
  margin-desktop: 64px
  gutter: 16px
  visual-silence: 48px
  touch-target: 48px
---

## Brand & Style
The design system embodies the **Scientific Instrument** aesthetic. It moves away from the ephemeral nature of SaaS and toward the permanence of a physical artifact—a high-end field notebook or a museum archive. The brand personality is academic, rigorous, and mineral, designed to facilitate deep focus during four-hour inquiry sessions.

### Design Movement: Physical Minimalism
The style is a blend of **Minimalism** and **Tactile Skeuomorphism 2.0**. It rejects neon accents and "business intelligence" gauges in favor of:
- **Parchment and Paper:** Surfaces that mimic the physical weight and texture of organic materials.
- **Academic Rigor:** A layout that prioritizes the "Escalera del Rigor" (Ladder of Rigor), where every digital element feels like a curated object (a file, a card, or a thread).
- **Mineral Calm:** An atmosphere that reduces eye strain through low-contrast transitions and a natural, desaturated palette.
- **Editorial Focus:** Strictly capped column widths (65ch) and generous white space ("Visual Silence") to ensure cognitive clarity.

## Colors
The palette is rooted in **Mineral Tones**, avoiding absolute blacks to maintain a soft, ink-on-paper feel.

- **Surface (Neutral):** `Parchment` (#FCFAED) is the primary background for all workspaces, providing a warm, non-glare surface.
- **Primary Content (Ink):** `Ink Blue` (#1E293B) is used for human-authored text, providing the highest hierarchy of authority.
- **Secondary (Mineral):** `Moss Green` and `Stone Blue` are used for organizational elements and AI-generated suggestions (Motor A/B).
- **Functional Tensions:** `Terracotta` (#991B1B) is reserved for methodological alerts or critical contradictions. `Amber` is used for "Open Questions" and gaps in data.
- **Text Tones:** Body text should utilize `Slate Text` to maintain a calm reading experience over long durations.

## Typography
The system employs a **Strict Duality** to differentiate the source of knowledge.

- **Newsreader (Serif):** Used for "Human Knowledge." This includes the main corpus, anthropologist notes, field journals, and final dictums. It is the voice of the investigator.
- **JetBrains Mono (Monospace):** Used for "Machine Inference." This includes technical IDs (SHA-256), AI-generated tags, logs, and metadata. It represents the analytical "engine."

**Constraints:**
- **Reading Comfort:** All long-form text blocks must be capped at a maximum width of **65 characters** (approx. 520px - 600px depending on font size).
- **Rhythm:** Line heights are intentionally generous (1.6x for body) to facilitate a scholarly, unhurried reading pace.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model centered on the "Focus Column." 

- **The Focus Column:** The central reading area is fixed at a 65ch width, centered on the screen.
- **Generous Margins:** A minimum margin of 24px is required on mobile to allow for one-handed thumb navigation. Desktop margins expand to 64px+ to create "Visual Silence."
- **Organic Grid:** While the text follows a grid, UI "objects" (index cards, tags) may have subtle 1-2 degree rotations to mimic a physical desk arrangement.
- **Interaction Targets:** All touchable elements must adhere to a minimum **48dp target**, specifically optimized for Android's one-handed reachability.

## Elevation & Depth
Depth is used to represent **Methodological Progress**, not just visual layering.

- **Tonal Layering:** Surfaces do not use heavy dropshadows. Instead, depth is achieved by stacking "paper" layers. A field note (higher rigor) sits physically on top of a signal (raw data).
- **Soft Shadows:** When used, shadows are "Ambient" and organic—wide blur radius, low opacity (5-10%), and tinted with `Ink Blue` rather than gray.
- **Ariadne’s Thread:** Relationships between objects are shown via "Cordeles" (thin, low-opacity lines) that visually link evidence to hypotheses, suggesting a flat but interconnected physical plane.
- **The "Seal":** Final peritajes (reports) use a subtle textured overlay to indicate they are "locked" and immutable.

## Shapes
Shapes mimic the artifacts of a laboratory.

- **Base Corner Radius:** Use **4px (Soft)** for index cards and buttons, echoing the cut of a physical Moleskine or archival folder.
- **Paper Tags:** Small metadata tags (labels) use 2px radius or sharp corners to feel like adhesive labels.
- **Prohibited:** No fully circular "pill" buttons or large-radius "bubble" cards. The geometry should feel professional and sturdy.

## Components

### The Evidence Card (Ficha)
- **Background:** Slightly brighter than the parchment surface (#FFFFFF).
- **Border:** 1px solid `Stone Blue` at 10% opacity.
- **Content:** Headline in `Newsreader`, technical metadata (SHA-256) in `JetBrains Mono` at the bottom right.

### The Scientific Button
- **Style:** Text-based with a subtle underline or a "pressed paper" effect. 
- **Active State:** A tint shift to `Moss Green` for "Validate" actions or `Terracotta` for "Reject."
- **Touch Target:** Always 48dp height.

### Input Fields (Field Notes)
- **Style:** Minimalist. No bounding box. A single horizontal baseline (like a ruled notebook).
- **Typography:** Switches to `Newsreader` as soon as the user starts typing, signaling "Human Entry."

### The "Ariadne" Connector
- **Visual:** A 1px dashed line connecting cards. 
- **Semantic Color:** Green for "Reinforces," Red for "Contradicts," Blue for "Qualifies."

### Lists & Indexes
- **Style:** Numbered lists using `JetBrains Mono` for the numerals, emphasizing the archival nature of the data. 
- **Spacing:** High vertical padding (16px+) between list items to prevent mis-taps.