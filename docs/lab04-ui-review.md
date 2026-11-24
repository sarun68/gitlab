# Lab 04 UI refinement — Impeccable polish and audit

Date: 2026-11-24. Surface: existing `templates/index.html`, engineering **Operate**
mode, not a marketing page. Scope: preserve Lab 3 calculations and bias diagrams,
add usable SPICE controls, readable plots and trustworthy state/provenance.

## Method and tool provenance

- Installed with `npx --yes impeccable install --providers=opencode --scope=project`
  (`DO_NOT_TRACK=1`). Project skill is `.opencode/skills/impeccable`.
- Loaded the native `impeccable` skill, executed its `context --target
  templates/index.html` once, read polish / operate / craft-floor guidance.
- No existing PRODUCT.md/DESIGN.md; used the actual incumbent implementation and
  rendered before screenshot as refinement context. No replacement visual-world
  design and no full dual-agent `/impeccable critique` report is claimed.
- Actual source scan: `impeccable.cmd detect --json templates/index.html`.
  Exit **2**, two warnings. The scanner could not resolve Jinja's `url_for`
  stylesheet expression, so CSS-dependent findings are incomplete.
- Actual rendered browser checks: Playwright MCP, 1280×900, 768×1024, 390×844;
  screenshot inspection, keyboard focus, labels, computed sizes/contrast/overflow,
  invalid input recovery, chart/run-data correspondence and downloads.

## Before → changes

Baseline screenshot: [Lab 3 desktop](captures/lab03-before-desktop.png).

- Long single-column fields made repeated runs slow; grouped component/source
  inputs in a compact two-column input panel, retaining a one-column mobile page.
- There was no distinction between analytical/SPICE provenance; added explicit
  analysis labels, model disclaimer, units, measurement references and run ID/time.
- Added Ready/Running/Success/Error/Inputs changed states. Changing inputs hides
  old results; failure responses do not contain old chart data.
- Removed the Tailwind runtime CDN dependency in favor of local CSS and JS.
- Added native labels and visible focus, a skip link, local responsive SVG plots,
  solid Vin/dashed Vout (not color alone), JSON export and expandable evidence.
- Actual mobile test found axis labels shrunk to about **6.4 px**. Responsive
  viewBox rendering and resize redraw corrected them to **13 px**, without
  altering solver arrays or recomputing the circuit in the browser.
- Final review found principal phase was connected across a ±180° jump. Split
  into two polylines: **281 total samples retained**, no false connecting segment.

## Mechanical findings and rendered cross-check

| Source detector finding | Actual browser evidence | Disposition |
|---|---|---|
| `flat-type-hierarchy`: inferred body/h1/h2/h3 all 16 px | Computed body 16, h1 29.6, h2 18.4, h3 16 px | Inaccurate because linked Jinja CSS was not loaded by source scanner |
| `monotonous-spacing`: inferred about 8 px everywhere | Panel padding 24 px, field gap 14×12 px, panel gaps 20 px, section spacing 20–24 px | Same source-scanning limitation; not taken as proof of a rendered defect |

Do not interpret this as a clean source scan or a comprehensive accessibility
certification. The CLI returned warnings, not zero findings.

Rendered contrast checks from the current CSS colors:
body ink/white **12.67:1**, muted text/paper **5.86:1**, white/action **7.06:1**.
Keyboard focus on Bias select: solid **3 px** outline. Mobile Run button height
**48.39 px**; active numeric/select controls have associated labels. Actual page
scrollWidth did not exceed viewport width at the three tested sizes.
Final page console: **0 errors, 0 warnings** (`captures/lab04-console.log`).

## After evidence

- [SPICE DC desktop](captures/lab04-dc-desktop.png)
- [AC desktop](captures/lab04-ac-desktop.png) / [AC mobile](captures/lab04-ac-mobile.png)
- [Transient desktop](captures/lab04-transient-desktop.png) /
  [Transient mobile](captures/lab04-transient-mobile.png)
- [Invalid input](captures/lab04-error.png)

Scope limits: not a screen-reader-user study or an exhaustive WCAG audit; no
native iOS/Android apps; browser viewport testing is not physical-device testing.
Before/after captures may come from repeated baseline runs with distinct run IDs;
numeric input fixture and actual engineering values are recorded in validation.
