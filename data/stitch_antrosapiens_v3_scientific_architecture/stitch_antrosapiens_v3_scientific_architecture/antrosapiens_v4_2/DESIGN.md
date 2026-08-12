---
name: AntroSapiens V4
colors:
  surface: '#fcfaed'
  surface-dim: '#dcdacf'
  surface-bright: '#fcfaed'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f4e8'
  surface-container: '#f0eee2'
  surface-container-high: '#eae8dd'
  surface-container-highest: '#e5e3d7'
  on-surface: '#1b1c15'
  on-surface-variant: '#414848'
  inverse-surface: '#303129'
  inverse-on-surface: '#f3f1e5'
  outline: '#717878'
  outline-variant: '#c1c8c7'
  surface-tint: '#446464'
  primary: '#173838'
  on-primary: '#ffffff'
  primary-container: '#2f4f4f'
  on-primary-container: '#9ec0bf'
  inverse-primary: '#abcdcd'
  secondary: '#ac3400'
  on-secondary: '#ffffff'
  secondary-container: '#fd6b36'
  on-secondary-container: '#5d1900'
  tertiary: '#293347'
  on-tertiary: '#ffffff'
  tertiary-container: '#404a5e'
  on-tertiary-container: '#afbad2'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c6e9e9'
  primary-fixed-dim: '#abcdcd'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#2c4c4c'
  secondary-fixed: '#ffdbd0'
  secondary-fixed-dim: '#ffb59d'
  on-secondary-fixed: '#390c00'
  on-secondary-fixed-variant: '#832600'
  tertiary-fixed: '#d8e2fc'
  tertiary-fixed-dim: '#bcc7df'
  on-tertiary-fixed: '#111c2e'
  on-tertiary-fixed-variant: '#3d475b'
  background: '#fcfaed'
  on-background: '#1b1c15'
  surface-variant: '#e5e3d7'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Newsreader
    fontSize: 28px
    fontWeight: '500'
    lineHeight: 36px
  title-md:
    fontFamily: Newsreader
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Newsreader
    fontSize: 19px
    fontWeight: '400'
    lineHeight: 32px
  body-md:
    fontFamily: Newsreader
    fontSize: 17px
    fontWeight: '400'
    lineHeight: 28px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  technical-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  margin-page: 4rem
  margin-mobile: 1.5rem
  gutter: 2rem
  stack-xl: 3rem
  stack-md: 1.5rem
  stack-sm: 0.75rem
---

## Brand & Style

The design system is a "Scientific Instrument" crafted for long-form research and high-stakes evidentiary review. It balances the timeless authority of a prestigious scientific journal with the precision of a modern laboratory interface. The aesthetic is "Academic Minimalism," prioritizing focus, legibility, and a sense of archival permanence.

The visual direction follows a **Tactile / Editorial** approach. It evokes the feeling of a heavy oak desk layered with cotton-bound reports and index cards. This is achieved through subtle paper textures, ample white space (margins), and a deliberate hierarchy that separates human narrative from technical machine data. The emotional response is one of calm, focused authority and intellectual rigor.

## Colors

The palette is rooted in natural, archival materials to reduce eye strain during long-form reading. 

- **Primary (Mineral Green):** Used for primary actions, validated states, and core branding. It represents stability and natural observation.
- **Secondary (Terracotta):** Reserved for "critical tensions"—warnings, high-priority anomalies, or contrasting data points that require immediate attention.
- **Background Tiers:** The UI uses `background_parchment` as the global base. `background_ivory` is used for elevated surface elements like cards, while `neutral_color_hex` (Sand) provides a structured contrast for sidebar or utility areas.
- **Ink & Slate:** All primary narrative text is set in `text_ink` for maximum contrast, while `text_slate` handles secondary metadata and UI labels.

## Typography

The typography system is the core of this design system, optimized for "deep reading" and evidentiary clarity.

- **Newsreader:** Utilized for all narrative content, evidence reports, and editorial headers. It features high x-height and optimized legibility for long-form prose.
- **Inter:** Used strictly for the "instrument" interface—buttons, navigation, input labels, and tooltips. It provides a functional, neutral counterpoint to the serif narrative.
- **JetBrains Mono:** Used for machine-generated data, AI inferences, timestamps, and metadata. This provides a clear "visual signature" that distinguishes machine output from human input.

**Scaling:** Large headlines should decrease in size on mobile but maintain their serif elegance. Body text (19px) is intentionally large to mimic the comfort of a printed book.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy for content, centering long-form reports within generous margins to simulate the experience of a physical manuscript.

- **Desktop:** 12-column grid with wide 4rem (64px) margins. The central reading column is restricted to a maximum width of 720px for optimal line length.
- **Gutter & Rhythm:** A consistent 8px base unit is used, but spacing is generous (stack-xl) between major sections to allow the content to "breathe."
- **Sidebars:** Analytical tools and machine data are positioned in persistent sidebars or "margin notes" to keep the primary narrative focused.
- **Mobile:** Transition to a single-column fluid layout with 1.5rem margins. All large serif headlines scale down to prevent awkward wrapping.

## Elevation & Depth

This design system avoids aggressive shadows in favor of **Tonal Layers** and **Low-Contrast Outlines**.

- **Surfaces:** Depth is communicated by color shifting from the base Parchment (#FBFAEE) to the elevated Ivory (#FFFDF5).
- **Shadows:** When necessary for separation (e.g., active modals or floating index cards), use "Ambient Shadows"—ultra-diffused, 4% opacity ink-tinted shadows with no sharp edges.
- **Borders:** UI components like input fields and card separators use thin (1px) Slate (#475569) borders at 15% opacity, resembling faint pencil lines on paper.
- **Machine Data Separation:** AI and machine-driven elements are often contained in slightly recessed Sand (#F2F0E4) containers to distinguish them from the "elevated" human narrative.

## Shapes

The shape language is refined and "Soft." It avoids the coldness of sharp corners but rejects the playfulness of heavy rounding.

- **Standard Elements:** Buttons, inputs, and small cards use a 0.25rem (4px) radius.
- **Large Components:** Sections or report containers use `rounded-lg` (0.5rem) to suggest the soft edges of a stack of paper.
- **Interactive Elements:** Checkboxes and radio buttons maintain the 4px soft radius to feel like manual stamps or index card notches.

## Components

- **Buttons:** Primary buttons are Mineral Green with White text. Secondary buttons use a Slate outline. Ghost buttons are reserved for utility functions.
- **Report Cards:** Ivory background, subtle 4px rounding, and a top-border accent of Mineral Green for "Verified" or Terracotta for "Under Review."
- **Index Chips:** Small, Inter-based labels used for categorizing evidence. They use a Sand background with Ink text.
- **Input Fields:** Styled like traditional forms; underline-only for a minimalist look, or a full 1px border for "data entry" modes.
- **Separators:** Use a subtle "Horizontal Rule" style—thin, centered lines that don't touch the edges of the container, mimicking editorial breaks.
- **Machine Inference Blocks:** Always use JetBrains Mono and a Sand (#F2F0E4) background to signify the non-human origin of the data.
- **Annotations:** Floating "margin notes" that appear next to the serif text, using smaller Inter typography and Slate text.