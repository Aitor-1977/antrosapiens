---
name: Field Laboratory
colors:
  surface: '#fbfaee'
  surface-dim: '#dbdbcf'
  surface-bright: '#fbfaee'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f4e8'
  surface-container: '#efeee3'
  surface-container-high: '#e9e9dd'
  surface-container-highest: '#e4e3d7'
  on-surface: '#1b1c15'
  on-surface-variant: '#414848'
  inverse-surface: '#303129'
  inverse-on-surface: '#f2f1e5'
  outline: '#717878'
  outline-variant: '#c1c8c7'
  surface-tint: '#446464'
  primary: '#173838'
  on-primary: '#ffffff'
  primary-container: '#2f4f4f'
  on-primary-container: '#9ec0bf'
  inverse-primary: '#abcdcd'
  secondary: '#496800'
  on-secondary: '#ffffff'
  secondary-container: '#c8f17a'
  on-secondary-container: '#4e6e00'
  tertiary: '#670f17'
  on-tertiary: '#ffffff'
  tertiary-container: '#87272b'
  on-tertiary-container: '#ff9f9d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c6e9e9'
  primary-fixed-dim: '#abcdcd'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#2c4c4c'
  secondary-fixed: '#c8f17a'
  secondary-fixed-dim: '#add461'
  on-secondary-fixed: '#131f00'
  on-secondary-fixed-variant: '#364e00'
  tertiary-fixed: '#ffdad8'
  tertiary-fixed-dim: '#ffb3b0'
  on-tertiary-fixed: '#410006'
  on-tertiary-fixed-variant: '#832428'
  background: '#fbfaee'
  on-background: '#1b1c15'
  surface-variant: '#e4e3d7'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Newsreader
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.7'
  body-md:
    fontFamily: Newsreader
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-lg:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.03em
  headline-lg-mobile:
    fontFamily: Newsreader
    fontSize: 28px
    fontWeight: '500'
    lineHeight: '1.2'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 8px
  margin-page: 64px
  gutter: 32px
  stack-lg: 48px
  stack-md: 24px
  stack-sm: 12px
---

## Brand & Style
The design system is a digital translation of a field scientist’s workspace—a fusion of the tactile, scholarly atmosphere of a **Moleskine notebook** and the clinical precision of a **contemporary scientific journal**. It rejects the aggressive, high-contrast tropes of modern software in favor of an **intellectual calm** and **rigorous clarity**.

The style is **Editorial Minimalism**. It prioritizes the "silent partner" interface, where the UI exists only to frame and elevate the narrative. Drawing inspiration from natural materials like linen, heavy-stock paper, and archival ink, the design system avoids all "tech" signifiers (neons, sharp glowing borders, or complex gradients) to create an environment conducive to deep thinking and patient observation.

## Colors
This design system utilizes a palette rooted in the organic and the archival. The foundation is built on **warm, parchment-like neutrals** that reduce eye strain and evoke a physical surface.

*   **Foundation:** The primary background is a soft cream (`#FDFCF0`), supported by secondary layers of muted sand and linen.
*   **Ink & Lead:** Pure black is strictly prohibited. Instead, a deep charcoal (`#1A1A1A`) is used for primary text, simulating high-quality archival ink. Secondary metadata uses a soft slate gray.
*   **Natural Accents:**
    *   **Primary (Slate Green):** A muted, deep forest slate used for structural UI elements and primary actions.
    *   **Secondary (Olive):** Used for positive states or natural categorization.
    *   **Tertiary (Terracotta):** A warm, earthy red reserved for critical highlights and callouts, ensuring visibility without "emergency" neon tones.

## Typography
The typography follows an **Editorial-First** hierarchy. It treats long-form narrative as the primary asset and UI labels as supporting metadata.

*   **Serif (Newsreader):** Used for all headlines and body text. This font provides a literary, authoritative feel. Body text should always feature **generous line heights** (1.6x - 1.7x) to emulate a well-set book page.
*   **Sans-Serif (Hanken Grotesk):** Used for the "machinery" of the UI—buttons, navigation, form labels, and data points. It is clean, contemporary, and provides a clear visual distinction from the narrative content.
*   **Letter Spacing:** Labels and headers utilize slightly wider tracking to enhance the sense of "air" and breathability within the layout.

## Layout & Spacing
The layout philosophy is defined by **expansiveness**. It avoids density in favor of focus.

*   **The Journal Grid:** A fixed-width central column for reading (max-width 720px) ensures optimal line lengths. Global layouts use a 12-column grid with wide 32px gutters.
*   **Negative Space:** Margins are intentionally large (64px+ on desktop) to simulate the edges of a physical notebook. 
*   **Rhythm:** Vertical rhythm is strictly enforced using an 8px baseline, ensuring that even as the layout scales, the relationship between narrative and metadata remains harmonious.
*   **Adaptation:** On mobile, margins reduce to 20px, but the "air" is maintained by increasing the vertical space between sections to prevent the UI from feeling cramped.

## Elevation & Depth
Depth in this design system is tactile rather than digital. It avoids the "floating" appearance of standard SaaS apps.

*   **Tonal Layering:** Depth is primarily communicated through subtle shifts in background color (e.g., a slightly darker "sand" surface resting on the "parchment" base).
*   **Paper Shadows:** When shadows are necessary (for cards or modals), they are extremely diffused and low-opacity, using a warm tint rather than gray to mimic the way a thick sheet of paper casts a shadow on a desk.
*   **Fine Outlines:** Elements are defined by thin, 1px strokes in a slightly darker version of the background color (e.g., a "muted linen" border). This provides structure without the weight of a traditional box.

## Shapes
The shape language is **Soft and Structural**. 

*   **Corner Radius:** We use a modest "Soft" setting (4px-8px). This creates a approachable feel that remains disciplined and professional. 
*   **Organic Imperfection:** Where possible, interactive elements should feel like physical objects—tabs like file folders, buttons like pressed ink stamps. 
*   **Avoidance:** Completely circular "pill" shapes are avoided for everything except the most minor tags, as they feel too "app-like." Sharp 90-degree corners are avoided for containers to maintain the organic mood.

## Components
Consistent styling of components ensures the "Field Laboratory" feels cohesive and intentional.

*   **Buttons:** Primary buttons are filled with the Slate Green (`#2F4F4F`) with white text. Secondary buttons are outlined in a 1px stroke. All buttons use the Sans-Serif label font.
*   **Cards:** Use a "Paper" style—minimal shadows, 4px border radius, and a subtle 1px border. No heavy header bars; use typography to create hierarchy within the card.
*   **Input Fields:** Ghost-style inputs with only a bottom border or a very light 4-sided stroke. Focus states should use a subtle tint change of the background rather than a glowing ring.
*   **Chips/Tags:** Small, rectangular with slightly rounded corners (2px). Used for metadata, utilizing the Sans-Serif font at a small scale.
*   **Lists:** Archival style. Use generous padding between items and thin horizontal dividers that don't span the full width, mimicking a ledger or catalog.
*   **Navigation:** Sidebars should feel like a "Table of Contents," using the Serif font for main categories and the Sans-Serif for utility links.