---
name: Agenvora
description: A pale, inspectable coordination record for agent routing, verification, and settlement.
colors:
  canvas: "#f3f4f2"
  surface: "#fafbf9"
  raised: "#fff"
  inset: "#e9ebe8"
  ink: "#151715"
  text: "#343835"
  muted: "#626964"
  line: "#d2d5d1"
  line-strong: "#9ea49f"
  action: "#ff5a1f"
  action-hover: "#e64b14"
  on-action: "#15120f"
  success: "#166a42"
  danger: "#a33126"
  code: "#171918"
  code-text: "#f3f5f2"
  code-muted: "#a8aea9"
  code-line: "#424843"
typography:
  display:
    fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif'
    fontSize: "clamp(2.625rem, 4.8vw, 4.25rem)"
    fontWeight: 600
    lineHeight: 1.04
    letterSpacing: "-0.04em"
  headline:
    fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif'
    fontSize: "clamp(2rem, 3.6vw, 3rem)"
    fontWeight: 550
    lineHeight: 1.1
    letterSpacing: "-0.035em"
  title:
    fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif'
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.015em"
  body:
    fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  lead:
    fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif'
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.65
  ui:
    fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif'
    fontSize: "0.875rem"
  button-label:
    fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif'
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.35
  label:
    fontFamily: '"SFMono-Regular", "Cascadia Code", Consolas, "Liberation Mono", monospace'
    fontSize: "0.6875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0.07em"
  code:
    fontFamily: '"SFMono-Regular", "Cascadia Code", Consolas, "Liberation Mono", monospace'
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.85
rounded:
  control: "4px"
  panel: "6px"
spacing:
  step-1: "4px"
  step-2: "8px"
  step-3: "12px"
  step-4: "16px"
  step-6: "24px"
  step-8: "32px"
  step-12: "48px"
  step-16: "64px"
  step-24: "96px"
  page-gutter: "clamp(20px, 4vw, 56px)"
components:
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "{colors.on-action}"
    typography: "{typography.button-label}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.action-hover}"
    textColor: "{colors.on-action}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.button-label}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
    height: "48px"
  button-secondary-hover:
    backgroundColor: "{colors.inset}"
    textColor: "{colors.ink}"
  input-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "12px"
  trace-panel:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
  provider-selector:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.ui}"
    padding: "24px 16px"
  provider-selector-selected:
    backgroundColor: "{colors.inset}"
    textColor: "{colors.ink}"
  stage-tab:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    typography: "{typography.ui}"
    padding: "16px 24px 20px"
    height: "66px"
  stage-tab-selected:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
  code-window:
    backgroundColor: "{colors.code}"
    textColor: "{colors.code-text}"
    typography: "{typography.code}"
    rounded: "{rounded.panel}"
---

# Design System: Agenvora

## Overview

**Creative North Star: "Trace Ledger"**

Agenvora reads as a working coordination record: a pale architectural canvas where routes, budgets, handoffs, verification, and settlement can be inspected in one calm sequence. The world is precise without becoming sterile, using compact ledgers and hairline structure to give technical evidence more authority than decoration.

The system separates human explanation from machine evidence. A restrained sans hierarchy carries propositions and guidance, while operational monospace carries code, IDs, statuses, labels, and numbers. The signature five-stage run spine connects both voices: its moving orange checkpoint makes the selected handoff legible while the adjacent ledger explains what changed.

**Key Characteristics:**

- Pale gray canvas with white and near-white evidence surfaces.
- Sans narrative hierarchy paired with operational monospace evidence.
- Flat, rule-led depth with compact 4px controls and 6px panels.
- Rare functional orange for conversion and the current run checkpoint.
- Honest illustrative diagrams, registers, code, and controls instead of decorative media.
- Responsive reflow that preserves dense evidence through contained scrolling.

## Colors

The palette is a cool, nearly neutral ledger with one high-attention action signal and two strictly semantic receipt colors.

### Primary

- **Checkpoint Orange** (`action`, #ff5a1f): Primary conversion buttons and the current-stage checkpoint only.
- **Pressed Orange** (`action-hover`, #e64b14): Hover and active feedback for orange actions while preserving readable dark text.

### Secondary

- **Verified Green** (`success`, #166a42): Completed stages, verified receipts, and successful outcomes.
- **Error Red** (`danger`, #a33126): Validation errors and failure feedback only.

### Neutral

- **Canvas Fog** (`canvas`, #f3f4f2): The page-wide architectural ground.
- **Evidence Paper** (`surface`, #fafbf9): Inset headers, selected tabs, diagram beds, and quiet evidence regions.
- **Raised White** (`raised`, #fff): Trace panels, calculators, nodes, and fields that sit above the canvas without shadow.
- **Ledger Inset** (`inset`, #e9ebe8): Hover states, footer ground, inactive meter tracks, and grouped regions.
- **Protocol Ink** (`ink`, #151715): Primary text, focus outlines, quantitative bars, and the strongest structural contrast.
- **Action Ink** (`on-action`, #15120f): Text and icons on orange actions.
- **Body Graphite** (`text`, #343835): Explanatory copy.
- **Quiet Graphite** (`muted`, #626964): Metadata, tertiary labels, and supporting notes.
- **Hairline** (`line`, #d2d5d1): Internal dividers and low-emphasis boundaries.
- **Strong Rule** (`line-strong`, #9ea49f): Panel outlines, major totals, and structural separators.
- **Code Well** (`code`, #171918): The sole dark evidence surface.
- **Code Paper** (`code-text`, #f3f5f2): Primary code and dark-surface focus.
- **Code Metadata** (`code-muted`, #a8aea9): Secondary code labels and annotations.
- **Code Rule** (`code-line`, #424843): Dark-surface dividers and outlined copy control.

### Named Rules

**The Rare Signal Rule.** Orange marks only primary conversion and the current-stage checkpoint; it never decorates a background, chart, or ambient surface.

**The Semantic Receipt Rule.** Green means completed or verified and red means error; neither color is used as a second brand accent.

## Typography

**Display Font:** Segoe UI (with Apple system, BlinkMacSystemFont, Helvetica Neue, and sans-serif fallbacks)  
**Body Font:** Segoe UI (with Apple system, BlinkMacSystemFont, Helvetica Neue, and sans-serif fallbacks)  
**Label/Mono Font:** SFMono-Regular (with Cascadia Code, Consolas, Liberation Mono, and monospace fallbacks)

**Character:** The sans voice is direct, compact, and editorial enough to carry a public protocol narrative. Monospace enters only when fixed-width rhythm improves auditability, so labels and evidence feel operational without turning the whole page into a terminal.

### Hierarchy

- **Display** (600, `clamp(2.625rem, 4.8vw, 4.25rem)`, 1.04): Hero proposition only, balanced and capped at a readable measure.
- **Headline** (550, `clamp(2rem, 3.6vw, 3rem)`, 1.1): Chapter and closing statements.
- **Title** (600, 1.25rem, 1.3): Inspector titles, principle headings, and dialog headings.
- **Lead** (400, 1.125rem, 1.65): Hero explanation on wide screens; it returns to body size where space tightens.
- **Body** (400, 1rem, 1.6): Product explanation and form content, generally held near 43–60 characters per line by its container.
- **UI** (400–600, 0.875rem, 1.6 default / 1.35 for buttons): Navigation, selectors, buttons, and dense interface copy.
- **Label** (400, 0.6875rem, 1.5, 0.07em tracking): Uppercase operational categories, run IDs, and register headings.
- **Code** (400, 0.8125rem, 1.85): Copyable protocol examples and machine-readable evidence.

### Named Rules

**The Two-Voice Rule.** Sans carries narrative and interaction hierarchy; monospace is reserved for code, IDs, statuses, labels, and numeric evidence.

## Layout

The system uses a centered 1240px maximum content width, fluid page gutters (`clamp(20px, 4vw, 56px)`), and a 4px spacing rhythm expressed as 4, 8, 12, 16, 24, 32, 48, 64, and 96px steps. Chapters use 96px vertical separation on wide screens and 64px on mobile. Hero and editorial sections favor unequal split grids so evidence and explanation remain visibly related rather than becoming a repeated card grid.

At 1100px the workbench inspector moves below its map and wide provider layouts compact. At 900px the hero, editorial splits, economics, and final call to action become single-column. At 760px navigation collapses, the page gutter fixes at 20px, registers reflow, and the five-stage rail and route map remain complete inside explicit horizontal scrollers. At 360px actions stack and the smallest quantitative grids reduce to two columns. The trace itself retains a 520px stage rail and 680px route map so its information model is never compressed into illegibility.

### Named Rules

**The Evidence-First Rule.** Show the proposition with an honest illustrative trace, then expose the five-stage run before deeper explanation and conversion.

**The Preserve-the-Run Rule.** Reflow prose and registers on small screens, but contain and horizontally scroll the complete route topology.

## Elevation & Depth

The system is flat and uses no shadows. Depth comes from the Canvas Fog, Evidence Paper, Raised White, and Ledger Inset surface sequence; 1px Hairline and Strong Rule boundaries; and a single Code Well contrast surface. The access dialog uses a dark translucent scrim for modal separation, but the dialog itself remains an unshadowed, ruled panel.

### Named Rules

**The Flat Ledger Rule.** No component uses a shadow; establish depth with tonal surfaces, 1px rules, dark code contrast, and the dialog scrim.

## Shapes

Geometry is restrained and functional. Interactive controls use a 4px radius, bounded panels use a 6px radius, and rules are consistently 1px. Tiny square markers reinforce the trace language: the run spine uses a 7px checkpoint and the active route node uses a 6px marker. Circles, large capsules, and soft floating cards do not belong to this system.

### Named Rules

**The Measured Corner Rule.** Controls use 4px corners and bounded panels use 6px corners; do not inflate them into soft cards or pills.

## Components

### Buttons

- **Shape:** Compact rectangular control with a 4px corner, at least 48px tall for primary page actions and 44px in compact navigation contexts.
- **Primary:** Checkpoint Orange background with Action Ink text, a matching border, and 10px by 18px padding.
- **Hover / Focus:** Orange actions move to Pressed Orange; every action uses a visible 2px Protocol Ink outline with a 3px offset. Dark code controls use Code Paper for the outline.
- **Secondary / Text:** Secondary buttons are transparent with a Strong Rule border and fill with Ledger Inset on hover. Text controls stay underlined and use a 44px minimum target without decorative chrome.

### Cards / Containers

- **Corner Style:** Evidence panels use 6px corners; nested goals, nodes, and controls use 4px corners.
- **Background:** Raised White for primary evidence, Evidence Paper for headers and selected states, and Ledger Inset for quiet grouping.
- **Shadow Strategy:** None; refer to the flat depth model above.
- **Border:** Strong Rule for the outside frame, Hairline for internal divisions.
- **Internal Padding:** 16–24px, composed from the 4px spacing rhythm.

### Inputs / Fields

- **Style:** Evidence Paper fill, Strong Rule border, 4px radius, 12px padding, and readable 1rem sans input text.
- **Focus:** The global 2px Protocol Ink focus outline sits 3px outside the control; fields retain a visible text caret.
- **Error / Disabled:** Error Red replaces the field border and is paired with inline explanatory text. Disabled copy controls retain their shape and show a waiting cursor while work completes.

### Navigation

The header is a flat sticky canvas with a Hairline lower rule. Links use muted 0.875rem sans text, a minimum 44px target, and an underline plus ink shift for hover/current state. At 760px the menu button appears in DOM order and reveals full-width 48px rows; Escape closes the menu and restores the toggle.

### Provider Selector

Provider choices form a ruled register rather than pills. Each cell uses a sans provider name and monospace capability label; hover and selected states fill with Ledger Inset, while a 2px Protocol Ink bar marks the selected provider without introducing another accent.

### Five-Stage Run Spine

The signature component has five ordered tabs—Plan, Route, Execute, Verify, Settle—linked by a 1px spine. One 7px orange checkpoint moves between stages over the 200ms state transition; earlier nodes show completed text in Verified Green, and the selected node gains a dark rule plus a small orange marker. The inspector updates the stage title, handoff, evidence, route, and route note in the same panel. Its run ID and data are explicitly illustrative.

### Budget Register

The calculator pairs three 44px range controls with a monospace settlement total, a strong total rule, neutral quantitative bars, and immediate explanatory output. Tracks, bars, and the settlement unit remain neutral; orange is not used for generic quantitative data.

### Code Window

The code preview is the only dark surface. It uses Code Paper and Code Metadata, keyboard-operable file tabs, a bordered copy control with 44px minimum height, and persistent success or recovery feedback. The example remains explicitly illustrative and horizontally scrollable when required.

### Motion & Accessibility

Control color feedback uses 120ms; checkpoint and quantitative state changes use 200ms with `cubic-bezier(0, 0, .2, 1)`. Motion explains state only—there are no entrance reveals or loops. Under `prefers-reduced-motion: reduce`, transitions, animation, and smooth scrolling resolve immediately without removing the final state. Semantic controls, associated tab panels, live feedback, inline errors, dialog focus containment/restoration, a skip link, readable contrast, and text alongside semantic color are required.

### Named Rules

**The Honest Evidence Rule.** Traces, budgets, protocol code, and token allocation must remain labeled as illustrative or proposed wherever the implementation does so; never convert them into live-network proof.

## Do's and Don'ts

### Do:

- **Do** reserve orange for primary conversion and the selected run checkpoint.
- **Do** set narrative and interaction hierarchy in sans while keeping code, IDs, statuses, labels, and numeric evidence in monospace.
- **Do** build spacing from the implemented 4px rhythm and use 4px control corners with 6px panel corners.
- **Do** preserve all five stages and contain the complete route map with horizontal scrolling on narrow screens.
- **Do** expose visible focus, keyboard relationships, readable semantic text, and immediate final states under reduced motion.
- **Do** identify illustrative traces, estimates, examples, and proposed economics honestly.

### Don't:

- **Don't** add shadows, gradients, glass, decorative grids, atmospheric glows, or floating card effects.
- **Don't** fabricate customer proof, performance metrics, compatibility, or live-network claims.
- **Don't** enlarge established radii into soft cards or use pills as a default container.
- **Don't** hide, truncate, or collapse route and register data merely to fit a smaller viewport.
- **Don't** rely on orange, green, or red as the sole indicator of state.
- **Don't** turn `$AGNV` into token-first spectacle; keep utility and proposed allocation inside the same evidence-led system.
