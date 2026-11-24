# Lab 04 web integration

User authorized continuing from the working self-authored starter into the
remaining Lab 04 Flask integration, real charts and browser acceptance.

## Approach
Extend the existing Flask route and Jinja form rather than create a new app or
introduce React. Reuse `bjt_model.py` unchanged, original bias diagrams and input
names, `spice_engine.py` and the sourced PN2222 model. Add an analysis selector
for Analytical DC, SPICE DC, AC and transient; SPICE only supports the CE divider
reference. Alternative separate frontend/service adds unnecessary deployment
and dependencies; static SVG plots driven by real returned arrays avoid a CDN.

## Behavior
Preserve analytical Fixed/Emitter/Divider and existing POST requests (missing
analysis means analytical). GET defaults to the handout's CE DC reference.
Validate only active fields, reject nonfinite/nonpositive input and invalid
mode/analysis before running. Use 64 KB request limit and existing timeout and
isolated working directories. Solver failure or invalid input clears results;
no stale success. Changing inputs marks output stale, hides previous results;
submission displays Running and prevents double submission.

Show VB/VE/VC/VCE/IC for SPICE DC. AC: two SVG plots, logarithmic Hz axis,
gain dB and principal phase degrees plus actual sampled numeric gain in V/V.
Transient: generator Vin and load Vout (V) against time (ms), last five periods
by default, indicate startup exclusion. Real solver arrays are embedded with
Jinja tojson; JS only projects coordinates and changes display windows.
Each result has unique run ID/time, model source/hash, netlist and log; JSON
download includes actual numeric data. Clearly label SPICE vs analytical and
self-authored non-instructor-verified model. Do not silently force agreement
between constant-beta analytical model and historical PN2222 model.

## UI and verification
Responsive engineering dashboard reusing circuit SVGs, with local CSS and JS,
explicit labels/units, accessible status/error, keyboard focus and readable
graphs. Save original desktop screenshot before changes. Install/load project-
scoped Impeccable if available, critique/polish/audit actual running UI without
changing physics. Log any installation limitation truthfully.
Run unit/integration tests, real browser B1–B8 using Playwright MCP, verify plot
arrays against solver output and RE/source changes, save desktop/mobile captures
and update validation and README. Preserve prior Lab 3 validation history.
Do not push or overwrite unrelated user files. Remain on lab04-spice-starter;
commit only after scope/verification and user instruction are clear.
