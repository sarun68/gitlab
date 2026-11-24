# Self-authored Lab 04 SPICE starter

The user authorized creating our own starter after confirming the handout
contains no downloadable kit/model. This is not instructor-verified material.

## Scope and approach
Build a standalone Python standard-library adapter and CLI before integrating
Flask. Preserve all existing Lab 3 files and tests. Reuse the PN2222 model from
the official ngspice examples, with its original parameter values and attribution.
Alternative: invent a generic model (less traceable); wait for the instructor's
kit (not available). The selected engineering approach is the sourced PN2222.

Circuit: NPN voltage-divider CE, VCC=12 V, R1=100 kohm, R2=22 kohm,
RC=2.2 kohm, RE=1 kohm, RL=10 kohm, Cin=Cout=10 uF, no emitter bypass.
Input is the ideal generator node before Cin; output is across RL after Cout.
Transient source defaults to 10 mV peak, 1 kHz. AC excitation is 1 V.
Default AC sweep: 10 Hz to 100 MHz, 40 points/decade. Transient uses 20
periods with maximum timestep period/100; steady-state checks use the last 5.

## Interfaces and integrity
`SpiceParameters` holds explicit-unit numeric fields. `run_simulation(parameters,
analysis, executable=None)` accepts `dc`, `ac`, `transient`, returns values/series,
units, engine/model provenance, netlist, raw output and log. Reject nonfinite,
nonpositive or excessive inputs before launching. Run argument lists with
shell=False, timeout=20 seconds, unique temporary working directory and ASCII
raw output; parse numeric data, including complex AC vectors. Never substitute
synthetic results. Resolve an explicit executable or NGSPICE_EXECUTABLE first,
then console executable on Windows; find installation resources from executable.
Distinguish missing engine, failed run, timeout and malformed/missing output.

CLI writes per-analysis JSON, circuit.cir, run.raw and run.log to an explicitly
selected new output directory. No GUI, Flask changes, browser verification,
instructor certification, commit/push or dependency installation in this increment.
Do not claim AC/transient correctness solely from screenshots: test real outputs,
input changes, phase inversion and small-signal consistency.
