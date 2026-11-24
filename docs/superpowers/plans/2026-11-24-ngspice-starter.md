# ngspice Starter Implementation Plan

> **For agentic workers:** Use executing-plans to implement task-by-task.

**Goal:** A reproducible self-authored DC/AC/transient CE starter kit.
**Architecture:** Sourced model, standard-library Python adapter, separate CLI.
**Tech Stack:** Python 3.12, unittest, ngspice 47 console.
**Spec:** `docs/superpowers/specs/2026-11-24-ngspice-starter-design.md`

## Global Constraints
- Preserve existing Lab 3 app, calculations and tests.
- No instructor-verification claim, invented traces or arbitrary transistor parameters.
- Run subprocess argument lists, shell=False, timeout=20, isolated work directories.
- No commit/push or package installation for this increment.

## Review Focus
- Nonfinite and excessive source/sweep values must be rejected before execution.
- Explicit executable configuration must fail clearly, not silently choose another.
- Missing, truncated and nonfinite raw output must never report success.
- Paths with spaces and working-directory changes must not break model/init loading.
- Amplitude/frequency/RE changes must alter actual simulation results.

### Task 1: Adapter and sourced model
Files: `spice_engine.py`, `models/PN2222.mod`, `models/README.md`, `test_spice_engine.py`.
Interfaces: `SpiceParameters`, `SpiceError`, `build_netlist`, `parse_raw`,
`run_simulation(parameters, analysis, executable=None)`.
- [x] Write failing unittest cases: valid defaults, invalid/nonfinite/bounded input,
  model/topology, real/complex raw parsing, bad output, unavailable engine, timeout.
- [x] Run tests and confirm missing-module failure.
- [x] Implement the adapter/model, preserving the sourced parameters.
- [x] Run adapter tests and original regression suite.

### Task 2: CLI, evidence and documentation
Files: `starter_kit.py`, `test_spice_integration.py`, `docs/starter-kit.md`.
Interfaces: CLI `python starter_kit.py --output <new-directory>` invokes all modes.
- [x] Write integration tests for DC physical ordering, gain/phase, source scaling,
  frequency change, RE change and small-signal AC/transient agreement.
- [x] Run and observe failure before completing missing interfaces.
- [x] Implement CLI and artifact writing; refuse to overwrite existing directories.
- [x] Run real simulations and save reproducible evidence outside Git.
- [x] Document setup, provenance, units, limitations and Flask handoff.
- [x] Review diff and report verified outcomes and remaining Lab 04 integration work.
