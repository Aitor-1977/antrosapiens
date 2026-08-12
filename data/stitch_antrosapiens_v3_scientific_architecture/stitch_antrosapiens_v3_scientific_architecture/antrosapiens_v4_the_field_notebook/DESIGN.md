---
name: 'AntroSapiens V4: The Field Notebook'
colors:
  surface: '#fdf9ee'
  surface-dim: '#dddacf'
  surface-bright: '#fdf9ee'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f7f3e8'
  surface-container: '#f1eee3'
  surface-container-high: '#ece8dd'
  surface-container-highest: '#e6e2d8'
  on-surface: '#1c1c15'
  on-surface-variant: '#404944'
  inverse-surface: '#31312a'
  inverse-on-surface: '#f4f1e6'
  outline: '#707974'
  outline-variant: '#bfc9c3'
  surface-tint: '#2b6954'
  primary: '#003527'
  on-primary: '#ffffff'
  primary-container: '#064e3b'
  on-primary-container: '#80bea6'
  inverse-primary: '#95d3ba'
  secondary: '#904d00'
  on-secondary: '#ffffff'
  secondary-container: '#fe932c'
  on-secondary-container: '#663500'
  tertiary: '#212f42'
  on-tertiary: '#ffffff'
  tertiary-container: '#374559'
  on-tertiary-container: '#a4b2ca'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b0f0d6'
  primary-fixed-dim: '#95d3ba'
  on-primary-fixed: '#002117'
  on-primary-fixed-variant: '#0b513d'
  secondary-fixed: '#ffdcc3'
  secondary-fixed-dim: '#ffb77d'
  on-secondary-fixed: '#2f1500'
  on-secondary-fixed-variant: '#6e3900'
  tertiary-fixed: '#d5e3fd'
  tertiary-fixed-dim: '#b9c7e0'
  on-tertiary-fixed: '#0d1c2f'
  on-tertiary-fixed-variant: '#3a485c'
  background: '#fdf9ee'
  on-background: '#1c1c15'
  surface-variant: '#e6e2d8'
typography:
  display-lg:
    fontFamily: Newsreader
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Newsreader
    fontSize: 32px
    fontWeight: '500'
    lineHeight: '1.2'
  headline-lg-mobile:
    fontFamily: Newsreader
    fontSize: 28px
    fontWeight: '500'
    lineHeight: '1.2'
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
  label-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0.05em
  caption:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.4'
  mono-code:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  margin-page: 4rem
  margin-mobile: 1.25rem
  gutter: 2rem
  stack-compact: 0.75rem
  stack-loose: 2.5rem
---

## Brand & Style

The design system is built upon the **Tactile / Skeuomorphic** movement, reimagined for a modern digital interface. It evokes the intimacy of a physical researcher's notebook—a space for rigorous observation, spontaneous sketches, and lifelong inquiry. The UI should feel organic, grounded, and quiet, prioritizing the "hand-written" quality of long-form thought over clinical digital precision.

The emotional response is one of **focused presence and intellectual warmth**. It mimics the physical experience of paper and ink, using wide margins and subtle textures to reduce cognitive load and encourage deep work.

## Colors

The palette is derived from natural materials—paper, ink, and earth pigments. 

- **Primary (Forest Green):** Used for primary actions and "inked" stamps of approval.
- **Secondary (Ochre):** Used for highlighting, annotations, and "sticky note" callouts.
- **Surface (Cream/Linen/Warm Gray):** These represent the physical substrates. Use **Cream (#FFFBF0)** as the base canvas for writing, and **Linen (#F3F4F6)** for sidebar or secondary organizational areas.
- **Text (Graphite):** Avoid pure black. Graphite provides a softer, more natural contrast against the cream background.

## Typography

The typography system mirrors the hierarchy of a published academic journal or a well-kept field diary.

- **Newsreader** is used for all narrative content to provide an authoritative yet literary feel. Its optical sizing at larger scales should emphasize its elegant, sharp serifs.
- **Inter** handles the functional UI layer—metadata, labels, and navigation—ensuring legibility in dense organizational areas.
- **JetBrains Mono** is reserved for technical data, coordinates, timestamps, and "marginalia" where precision is required.

## Layout & Spacing

The layout philosophy follows a **Fixed Grid** model centered on a "Single Page" metaphor. 

- **The Main Well:** Content should be constrained to a readable width (max 720px) to simulate the width of a physical book.
- **The Margins:** Generous horizontal gutters are used for "marginalia"—comments, dates, and icons that sit outside the main text flow.
- **Indentation:** Use a rigorous indentation system (32px increments) to show "threaded" relationships between notes, rather than using heavy borders or boxes.
- **Breakpoints:** On mobile, margins collapse to 20px, and marginalia move into an expandable "drawer" or fold directly into the vertical stack.

## Elevation & Depth

This design system avoids digital shadows in favor of **Tonal Layers** and **Tactile Overlays**.

- **Surface Stacking:** Depth is created by layering Cream surfaces on top of Warm Gray backgrounds. A thin, 1px stroke (Graphite at 10% opacity) should be used to define paper edges.
- **The "Pinned" Effect:** Elements that need to float (like floating action buttons) should use a subtle, slightly colored "contact shadow" (Ochre-tinted) to suggest they are pinned or taped to the page rather than floating in 3D space.
- **Translucency:** Use minimal backdrop blurs for overlaying menus to suggest vellum or tracing paper.

## Shapes

Shapes should feel organic and slightly irregular. While the digital environment requires precision, use **Soft (0.25rem)** corners for cards and containers to mimic the slightly rounded corners of a well-worn notebook. 

Buttons and interactive labels should use a **Pill-shape** to contrast against the rectangular nature of the page, making them feel like stickers or physical tabs.

## Components

- **Buttons:** Primary buttons use the Forest Green fill with white text. Secondary buttons are "Ghost" style with a Graphite border, feeling like a penciled outline.
- **Pinned Notes:** Use a slightly rotated (1-2 degree) container with an Ochre top-border to represent a sticky note or a pinned observation.
- **Threaded Relationships:** Use thin vertical lines (Graphite, 15% opacity) to connect parent and child observations, simulating a hand-drawn organizational tree.
- **Input Fields:** Instead of boxes, use a single bottom-border (1px Graphite) to simulate a ruled line on a page.
- **Chips & Tags:** Small, pill-shaped elements with a Linen background and Graphite text. They should look like stamped labels.
- **The "Artifact" Card:** A container with a very subtle paper texture background and a slightly deckled edge (simulated via CSS mask or subtle border-radius variation) for highlighted research findings.