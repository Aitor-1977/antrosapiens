---
name: AntroSapiens V4
colors:
  surface: '#f8f9ff'
  surface-dim: '#ccdbf3'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d5e3fc'
  on-surface: '#0d1c2e'
  on-surface-variant: '#45474c'
  inverse-surface: '#233144'
  inverse-on-surface: '#eaf1ff'
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
  tertiary-container: '#1b1c14'
  on-tertiary-container: '#85847a'
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
  tertiary-fixed: '#e5e3d6'
  tertiary-fixed-dim: '#c8c7bb'
  on-tertiary-fixed: '#1b1c14'
  on-tertiary-fixed-variant: '#47473e'
  background: '#f8f9ff'
  on-background: '#0d1c2e'
  surface-variant: '#d5e3fc'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  body-reading:
    fontFamily: Newsreader
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  meta-technical:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.05em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.1em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1120px
  research-max: 720px
  gutter: 24px
  margin-mobile: 16px
  stack-sm: 12px
  stack-md: 32px
  stack-lg: 64px
---

## Brand & Style

This design system is built for ethnographic research and deep anthropological inquiry. It balances the tactile warmth of physical archives with the clinical precision of modern data science. The visual narrative centers on "The Living Archive"—a space where qualitative narratives and quantitative data intersect.

The design style is a hybrid of **Minimalism** and **Tactile Academicism**. It utilizes expansive white space to reduce cognitive load while employing subtle textures and technical mono-spacing to denote systemic rigor. The emotional response is one of intellectual calm, authority, and focused discovery.

Two distinct states govern the interface:
1.  **Standard Mode:** Balanced view for general data synthesis and structural organization.
2.  **Research Mode:** A radical reduction of UI chrome. In this mode, global navigation collapses into a minimal signature, sidebars vanish, and the typography scales to maximize readability. Interstitial noise is replaced by pure focus.

## Colors

The palette is grounded in three functional pillars:
-   **Mineral Blue (#091426):** Used for primary typography, deep structural elements, and grounding the intellectual hierarchy.
-   **Clinical Mint (#047857):** Reserved for "Organic Saturation" indicators, validated evidence, and progress markers. It represents growth and systemic health.
-   **Parchment (#FCFAED):** The foundational surface color. It provides a softer, high-legibility base compared to pure white, reducing eye strain during long-form reading.

**Organic Saturation Logic:**
Interactive elements and data visualizations utilize a shader-based gradient logic. As data density or "evidence strength" increases, the surface transitions from a desaturated Mineral Blue wash to a vibrant, deep Clinical Mint. This provides a subconscious visual cue for content richness without requiring explicit numerical labels.

## Typography

The typography system differentiates between "Narrative" and "Metadata."

-   **Newsreader** is the voice of the researcher. It is used for all long-form content, hypotheses, and titles. It brings a literary quality to the data, making the digital archive feel like a curated publication.
-   **JetBrains Mono** is the voice of the system. It is used for IDs, timestamps, technical attributes, and "Dictum" statements. Its fixed-width nature conveys precision and structural integrity.

In **Research Mode**, `body-reading` line-height increases to `32px` to optimize for maximum concentration and minimal visual friction.

## Layout & Spacing

The layout follows a **Fixed Center-Column Grid** philosophy. Content is anchored to a central axis to maintain a "manuscript" feel.

-   **Standard Layout:** 12-column grid with a 1120px max-width. Sidebars contain metadata and cross-references.
-   **Research Mode Layout:** Transitions to a single-column 720px focus area. All non-essential navigation elements fade to 0% opacity until hovered.

Spacing rhythm is strictly derived from the `8px` base unit. Narrative blocks use `stack-md` (32px) to ensure breathing room between thematic sections.

## Elevation & Depth

This design system avoids traditional drop shadows in favor of **Tonal Layers** and **Boundary Outlines**.

-   **Surface Tiers:** Depth is indicated by shifts in the Parchment value. Secondary containers use a slightly cooler tint of the base color to appear "recessed."
-   **Ghost Borders:** Interactive cards and inputs use 1px solid Mineral Blue borders at 15% opacity. This creates a clear boundary without breaking the planar nature of the parchment surface.
-   **Active State Elevation:** When an element is selected (e.g., a "Signal"), it gains a 2px solid Mineral Blue border and a soft Clinical Mint ambient glow (blur: 12px, opacity: 10%), suggesting the element is "active" or "emitting."

## Shapes

The shape language is **"Soft-Clinical."** 

Elements utilize a `0.25rem` (4px) corner radius to feel approachable yet precise. Large containers and primary buttons use the `0.5rem` (8px) `rounded-lg` token. High-contrast indicators, such as status chips or "Hypothesis" markers, remain strictly rectangular with 0px radius to denote their character as "fixed truths" or "structural points."

## Components

### Methodological Iconography
Icons must be rendered in 1.5pt stroke weight using the primary color.
-   **Signal:** A series of three varying-height vertical bars (stochastic rhythm).
-   **Evidence:** A magnifying glass intersecting a solid square.
-   **Tension:** Two opposing diagonal vectors meeting at a central point.
-   **Hypothesis:** A dashed-outline diamond (representing a malleable concept).
-   **Dictum:** A solid, bold square with a central horizontal strike (representing a settled point).

### Buttons & Inputs
-   **Primary Action:** Solid Mineral Blue with Parchment text. No roundedness (0px) to signify a firm action.
-   **Research Inputs:** Inset fields with a Mineral Blue bottom-border only. When focused, the Clinical Mint saturation shader pulses slowly in the background.

### Organic Saturation Cards
Cards containing ethnographic data do not use percentages. Instead, the background Parchment color subtly shifts toward Clinical Mint as more "Evidence" icons are nested within the card.

### Research Mode Toggle
A persistent, low-contrast utility in the bottom-right corner. It uses JetBrains Mono `label-caps` typography. When active, it turns the Clinical Mint color and dims the rest of the UI's chrome.