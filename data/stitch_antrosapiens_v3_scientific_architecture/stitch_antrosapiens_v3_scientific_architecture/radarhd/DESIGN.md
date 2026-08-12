---
name: RadarHD
colors:
  surface: '#0F172A'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#F8FAFC'
  on-surface-variant: '#c5c6cd'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#8f9097'
  outline-variant: '#45474c'
  surface-tint: '#bcc7df'
  primary: '#bcc7df'
  on-primary: '#263144'
  primary-container: '#091426'
  on-primary-container: '#747f95'
  inverse-primary: '#545f74'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#e5c0a1'
  on-tertiary: '#422c16'
  tertiary-container: '#221001'
  on-tertiary-container: '#98795e'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2fc'
  primary-fixed-dim: '#bcc7df'
  on-primary-fixed: '#111c2e'
  on-primary-fixed-variant: '#3d475b'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdcc0'
  tertiary-fixed-dim: '#e5c0a1'
  on-tertiary-fixed: '#2a1704'
  on-tertiary-fixed-variant: '#5b422a'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
  clinical-mint: '#10B981'
  warning-orange: '#F59E0B'
  border-subtle: rgba(255, 255, 255, 0.1)
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-display:
    fontFamily: JetBrains Mono
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  data-code:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.08em
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  touch-target: 48px
---

## Brand & Style

This design system is engineered for **AntroSapiens V3**, a scientific anthropology instrument. The aesthetic is strictly **Clinical and Instrumental**, prioritizing data integrity and rapid interpretation over aesthetic flair. It is designed for researchers and field operatives who require high-density information environments with zero cognitive friction.

The style is characterized by a **High-Contrast Digital Interface** approach:
- **Minimalism & Precision:** Every pixel must serve a functional purpose. There is no room for decorative elements.
- **Zero Animation:** Interface transitions should be instantaneous to maintain the feel of a high-performance hardware tool.
- **Instrumental Utility:** UI components are treated as physical controls on a laboratory device, utilizing sharp edges and clear state indicators.
- **High Legibility:** Optimized for low-light environments (OLED Dark) to prevent eye strain during long-duration data analysis.

## Colors

The palette is optimized for OLED displays to maximize contrast and minimize power consumption.

- **Primary (Deep Space):** Used for structural grounding and primary navigation backgrounds.
- **Surface (OLED Dark):** The default background for all data containers.
- **Clinical Mint:** Used exclusively for "Success," "Confirmed Data," and "Active State" indicators. It represents scientific certainty.
- **Warning Orange:** Reserved for "Anomalies," "High Tension," and "Requires Attention."
- **On-Surface:** A crisp off-white to reduce the "haloing" effect common with pure white text on black backgrounds.
- **Borders:** Instead of shadows, depth is defined by 1px borders using `rgba(255, 255, 255, 0.1)`.

## Typography

The system employs a dual-font strategy to distinguish between human narrative and raw evidentiary data.

- **Inter:** Used for all UI controls, navigation, and human-readable qualitative analysis. It provides the necessary clarity for instructional text.
- **JetBrains Mono:** Used for all quantitative data, coordinate systems, timestamps, and log indices. The monospaced nature ensures that columns of numbers align perfectly for rapid scanning.
- **Hierarchy:** Use `label-caps` for all metadata headers and technical tags to distinguish them from actionable body text.

## Layout & Spacing

This design system follows a **Fixed Grid** model for data density but implements a **Thumb-Zone Navigation** strategy for mobile utility.

- **4px Base Unit:** All spacing and sizing must be multiples of 4px.
- **Thumb-Zone Controls:** Primary actions and navigation switches are located in the bottom 30% of the screen.
- **Grid:** A 12-column grid on desktop and a 4-column grid on mobile. 
- **Reflow:** On mobile, sidebars collapse into bottom-sheet drawers to keep the central "Instrument Viewport" unobstructed.
- **Scanning:** Maintain strict vertical alignment for all data lists to facilitate rapid "eye-scanning" of monospaced values.

## Elevation & Depth

In line with the clinical requirement, this system **prohibits the use of shadows**. Depth is communicated through:

- **Tonal Layering:** Background surfaces use `Primary (#091426)`, while active containers or cards use `Surface (#0F172A)`.
- **Subtle Outlines:** Every container must have a 1px border of `rgba(255, 255, 255, 0.1)`.
- **Active States:** Active or "focused" elements are indicated by a 1px solid border of `Clinical Mint` or a 100% opacity white border.
- **Visual Stacking:** Higher-level information (like modal alerts) uses a slightly lighter background hex to suggest a closer proximity to the user.

## Shapes

The shape language is strictly **Sharp (0px)**. 

- All buttons, input fields, containers, and data cells must have square corners. 
- This reinforces the "instrumental" and "hardened" nature of the software. 
- Rounding is seen as a consumer-grade aesthetic choice and is discarded here in favor of a professional, geometric structure.

## Components

- **Buttons:** Primary buttons use a solid `Clinical Mint` background with `Primary` text. Secondary buttons are outlined (1px) with `On-Surface` text. No hover transitions; state changes should be immediate.
- **Data Cells:** Used for logs. Must use `JetBrains Mono`. Row zebra-striping is permitted using `rgba(255,255,255,0.02)`.
- **Input Fields:** Bottom-aligned labels using `label-caps`. 1px border on all sides. On focus, the border changes to `Clinical Mint`.
- **Chips / Tags:** Square-edged. Technical metadata uses `JetBrains Mono`. Status tags use `Clinical Mint` (Normal) or `Warning Orange` (Alert).
- **Navigation (The "Instrument Tray"):** A persistent bottom bar containing the most frequent analytical tools. Icons should be stroke-based (1.5px weight) and lack any decorative fills.
- **Cards:** Used for grouping evidentiary findings. Must include a `label-caps` header separated by a horizontal 1px rule.