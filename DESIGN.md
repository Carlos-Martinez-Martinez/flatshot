---
version: "alpha"
name: "FlatShot Desktop"
description: "Compact local production UI for batch product-image processing."
colors:
  primary: "#0e8469"
  secondary: "#0f172a"
  accent: "#0e8469"
  background: "#f5f7f8"
  surface: "#ffffff"
  text: "#0f172a"
  muted: "#64748b"
  border: "#d9e1e7"
darkColors:
  background: "#18181b"
  surface: "#27272a"
  text: "#f4f4f5"
  muted: "#d4d4d8"
  border: "#3f3f46"
brandTones:
  default: "green"
  options:
    - "green"
    - "blue"
    - "indigo"
    - "violet"
    - "coral"
    - "amber"
typography:
  h1:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "22px"
    fontWeight: "700"
    lineHeight: "1.15"
    letterSpacing: "0px"
  h2:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "18px"
    fontWeight: "700"
    lineHeight: "1.15"
    letterSpacing: "0px"
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "14px"
    fontWeight: "400"
    lineHeight: "1.4"
    letterSpacing: "0px"
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: "600"
    lineHeight: "1.4"
    letterSpacing: "0px"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "8px 14px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.sm}"
    padding: "8px 12px"
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "8px 14px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
    padding: "{spacing.sm}"
  caption:
    textColor: "{colors.muted}"
    typography: "{typography.label}"
  divider:
    backgroundColor: "{colors.border}"
    height: "1px"
---

## Overview

FlatShot Desktop should feel compact, professional, and production-oriented. The interface supports a repeated local workflow: import batch, choose preset, adjust look, review exceptions, configure export, process.

## Colors

Use the existing light neutral surface system with teal as the operational accent. Secondary text must remain legible on white and small badges must meet normal text contrast. Error, warning, and success states must use semantic tokens and not rely on color alone.

Dark mode is an explicit user preference, not an automatic redesign. Reuse existing semantic token names with scoped overrides, keep the background neutral gray rather than green-tinted, and preserve real output colors such as white preview/export backgrounds.

The brand accent is user-selectable and independent of light/dark mode. Keep the default teal available, but allow blue, indigo, violet, coral, and amber variants by overriding the same primary/accent tokens rather than creating parallel color systems.

Interface preferences such as theme and brand tone belong in a dedicated preferences menu. Export format dialogs must stay focused on output configuration.

The preferences surface is for application interface behavior only: theme, brand tone, density, reduced motion, onboarding recents, thumbnail size, file-name display, and local preference cleanup. Export profiles, destinations, file formats, image presets, and processing parameters must remain in their existing workflow surfaces.

## Typography

Use system UI fonts explicitly. Keep dense application text at 13px to 14px, reserve 18px to 22px text for panel and modal headings, and keep letter spacing at 0px.

## Layout

Prefer dense but organized work surfaces over marketing layout. The primary screen should keep batch, preview, current preset, adjustments, export readiness, and process action accessible. Responsive variants must preserve access to inspector and export controls.

## Elevation & Depth

Use borders and restrained shadows for separation. Focus rings must be visible. Modals use a dimmed backdrop and one elevated panel; avoid nested visual cards unless the child is a repeated item or true tool surface.

## Shapes

Use 8px radius for buttons and compact controls, 12px to 16px for panels and dialogs, and pill radius only for badges or segmented status chips.

## Components

Buttons need at least 36px interactive height. Forms use compact labels, clear disabled states, and stable control dimensions. Modals should preserve focus behavior, support reduced motion, and avoid layout shifts while opening or closing.

The topbar preferences gear may expose fast theme and brand controls, but deeper options open a dedicated preferences modal. Keep the modal dense and sectioned; avoid turning it into another export or preset editor.

Preferences are arranged top-to-bottom by category. Each preference row keeps the label and supporting information on the left, with one clear control or action on the right: toggles for enable/disable settings, selects for option sets, and buttons only for explicit local actions.

## Do's and Don'ts

- Do: keep image processing and export behavior separate from UI presentation.
- Do: use existing CSS modules and tokens before adding new visual rules.
- Do: keep paths, filenames, and status messages truncated in dense panels.
- Do: implement theme variants by overriding existing semantic tokens instead of adding parallel token families.
- Don't: introduce frameworks or new dependencies for UI polish.
- Don't: hide critical preset, adjustment, or export controls without a responsive alternative.
