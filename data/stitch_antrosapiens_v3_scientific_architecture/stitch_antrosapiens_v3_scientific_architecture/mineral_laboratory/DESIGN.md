---
name: Mineral Laboratory
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#3d4947'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#6d7a77'
  outline-variant: '#bcc9c6'
  surface-tint: '#006a61'
  primary: '#00685f'
  on-primary: '#ffffff'
  primary-container: '#008378'
  on-primary-container: '#f4fffc'
  inverse-primary: '#6bd8cb'
  secondary: '#9b4500'
  on-secondary: '#ffffff'
  secondary-container: '#fd8a42'
  on-secondary-container: '#682c00'
  tertiary: '#585d5c'
  on-tertiary: '#ffffff'
  tertiary-container: '#717574'
  on-tertiary-container: '#f9fdfb'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#89f5e7'
  primary-fixed-dim: '#6bd8cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#ffdbca'
  secondary-fixed-dim: '#ffb68e'
  on-secondary-fixed: '#331200'
  on-secondary-fixed-variant: '#763300'
  tertiary-fixed: '#dfe3e1'
  tertiary-fixed-dim: '#c3c7c6'
  on-tertiary-fixed: '#181c1c'
  on-tertiary-fixed-variant: '#434847'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '500'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  headline-md:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '400'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  technical-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: -0.01em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
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
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 16px
  margin: 24px
  max-width: 1280px
---

## Brand & Style

This design system is a minimalist digital instrument designed for intensive data distillation and high-precision cognitive work. The brand personality is clinical, disciplined, and calm, evoking the atmosphere of a modern clean-room laboratory. It prioritizes clarity and speed of comprehension over decorative flourish.

The design style is **Minimalist with Structural Precision**. It avoids standard shadows in favor of "membrane" borders—ultra-fine lines that define boundaries without adding visual weight. The aesthetic is "warm clinical," balancing sterile efficiency with soft neutral tones to prevent user fatigue during long periods of data analysis.

The interface should feel like a high-end sensor readout: intentional, stable, and reactive. Every pixel serves a functional purpose in the hierarchy of evidence-based reasoning.

## Colors

The palette is rooted in mineral and clinical tones.
- **Primary (Clinical Teal):** Used for focus actions, success states, and primary navigational paths. It represents the "active" state of an instrument.
- **Secondary (Clay):** Reserved for "Inference" markers, warnings, or secondary data points that require cognitive attention without the urgency of a primary action.
- **Backgrounds (Pearl & Chalk):** `Pearl Gray` is the primary application background to reduce glare. `Chalk` is used for elevated surface containers to create subtle contrast. `Cool Mint` provides a soft tint for high-density data zones.
- **Text (Deep Charcoal):** Used for all high-contrast reading to ensure maximum legibility against the light backgrounds.

## Typography

The typographic system utilizes a tripartite structure to distinguish between different types of information:
- **Newsreader (Serif):** Used for "Evidence," editorial content, and high-level headers. Its literary quality adds authority and a human touch to clinical data.
- **Inter (Sans):** The primary workhorse for UI labels, body text, and general navigation. It ensures clarity and neutrality.
- **JetBrains Mono (Monospace):** Used for "Technical Data," metadata, and sensor readings. Its fixed-width nature aids in comparing numerical values and provides a precise, lab-instrument feel.

Use `label-caps` for table headers and categorizations to create a distinct visual "metadata" layer.

## Layout & Spacing

This design system uses a **Fixed Grid** model for analytical views to ensure predictable eye-tracking, and a **Fluid Grid** for content-heavy dashboard views.

- **Baseline Grid:** A strict 4px spacing rhythm. All components, margins, and padding must be multiples of 4.
- **Column System:** A 12-column grid on desktop (1280px max) with 16px gutters.
- **Information Density:** High. Use minimal vertical padding within data tables (`8px`) to allow for maximum "at-a-glance" data visibility.
- **Mobile Adaptation:** On mobile, the grid collapses to a single column with 16px side margins. Typography scales down (e.g., `headline-lg` becomes `headline-lg-mobile`) to maintain proportions.

## Elevation & Depth

To maintain the "Mineral Laboratory" aesthetic, depth is communicated through **Membrane Layers** rather than traditional shadows.

- **Membrane Borders:** Surfaces are separated by 1px solid borders in a slightly darker shade of the background (e.g., `#E2E8F0`). 
- **Tonal Stepping:** Depth is achieved by placing `Chalk` (#FFFFFF) surfaces on top of a `Pearl Gray` (#F9F9F7) base.
- **Backdrop Blur:** For transient elements like modals or dropdowns, use a subtle 8px backdrop blur (Glassmorphism) with a `Cool Mint` tint to simulate laboratory glass. 
- **Zero Shadows:** Shadows are strictly prohibited except for the highest level of the Z-axis (e.g., global modals), where a very soft, non-directional #1E293B at 5% opacity may be used to provide separation.

## Shapes

The shape language is **Soft (0.25rem)**. This provides a subtle "finished" feel to the clinical interface without appearing too consumer-grade or playful. 

- **Standard Elements:** Buttons, inputs, and small containers use `rounded` (4px).
- **Large Containers:** Content cards or sections use `rounded-lg` (8px).
- **Exceptions:** Technical data tags or status "chips" may use `rounded-xl` (12px) to distinguish them from actionable buttons.

## Components

- **Buttons:** Primary buttons use `Clinical Teal` with white text. Secondary buttons use a `Membrane Border` with `Deep Charcoal` text. No gradients.
- **Input Fields:** Flat backgrounds (#FFFFFF) with a 1px border. On focus, the border transitions to `Clinical Teal`. Use `JetBrains Mono` for numeric inputs.
- **Chips & Tags:** Small, low-height components using the `Cool Mint` background. Text is `label-caps` in `Clinical Teal` for high-precision categorization.
- **Cards:** No shadows. Defined by a 1px border and a slight color shift to `Chalk`. Used to group "Evidence" clusters.
- **Lists:** Clean lines with 1px horizontal separators. Use `Inter` for primary labels and `JetBrains Mono` for secondary metrics aligned to the right.
- **Evidence vs. Inference:** 
    - **Evidence:** Presented in `Newsreader` font within `Clinical Teal` bordered containers.
    - **Inference:** Presented in `Inter` font within `Clay` tinted containers or with a `Clay` left-accent border.
- **Data Tables:** High density. Zebra striping using `Pearl Gray` and `White`. Cell text uses `technical-data` tokens.