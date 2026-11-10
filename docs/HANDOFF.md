# Handoff / Holdout Notes — BJT Common-Emitter DC Bias Web App

## Project
- Repo: C:\Users\B6826123\Desktop\gitlab (origin: https://github.com/sarun68/gitlab.git, branch main)
- Course: ENG29 2121 lab
- Deliverable: Flask web app for BJT Common-Emitter DC Bias analysis (no AC/transient/FET/circuit editor)

## Current state (verified)
- Python 3.12.7, Flask 3.1.3, git 2.56.0
- Tests: `python -m unittest discover` -> 4 tests pass (2 BJT + 2 electrical)
- App runs: `python app.py` -> http://127.0.0.1:5000/ (GET 200, POST computes correctly)
- Last verified POST (VCC=12, R1=82, R2=22, RC=2.2, RE=1.0 kΩ, beta=100, VBE=0.7) -> Active, IB=15.53 µA, IC=1.55 mA, VCE=7.01 V
- Uncommitted .superpowers/ ledger left untracked (tooling state)

## Files
- bjt_model.py: engineering logic (kΩ->Ω scaling, Thevenin, region detection, independent check)
- app.py: Flask routes, form handling, validation errors shown in UI
- templates/index.html: 3-column Tailwind UI (inputs / circuit image / results)
- static/: circuit.png, circuit.svg, style.css
- test_bjt.py: 2 tests (active region, kΩ input)

## Known limitations / open items
1. Image viewing not available to this model: column-2 image swap (user's UI change request) NOT done. Uploaded images in Temp/opencode/uploads (4 variants). To apply, copy chosen image to static/circuit.png and update templates if needed; keep other parts unchanged.
2. No design spec doc under docs/superpowers/specs (only plans). Brainstorming design approval step was not formally recorded.
3. pytest not installed; using unittest.
4. VBE not validated as positive; VCEsat threshold hardcoded 0.2 V.
5. Independent check uses approximate formula (R_TH/beta + RE); documented as approximate.

## If continuing with another model
- Read this file + docs/superpowers/plans/* first.
- Do not re-run design unless asked; implementation exists and tests pass.
- Preferred next steps: apply image swap (needs image-capable model or user description), then final commit + push.
- Git user configured: katang <b6826123@g.sut.ac.th>.
PY