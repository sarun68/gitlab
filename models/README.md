# PN2222 model provenance

`PN2222.mod` is copied from the official ngspice example:

- https://github.com/ngspice/ngspice/blob/master/examples/tclspice/tcl-testbench1/PN2222.mod
- Raw source: https://raw.githubusercontent.com/ngspice/ngspice/master/examples/tclspice/tcl-testbench1/PN2222.mod
- Also present in the installed ngspice 47 distribution at
  `Spice64/examples/tclspice/tcl-testbench1/PN2222.mod`.
- Checked on 2026-11-24; numerical model parameters and original attribution
  (Fairchild, pid=19, TO92, 88-09-07 bam) retained. Only indentation normalized.

This is a historical simulation example, not a newly manufacturer-validated
model, not an instructor-specified model, and not a guarantee for every real
PN2222 device. Bf=255.9 is a model parameter, not the constant beta=100 used
by the existing analytical calculator. Do not force their DC results to match.
Every run records the local model's SHA-256 so the exact parameters are traceable.
