# Lab 04 — Self-authored ngspice Starter Kit

**ชุดนี้จัดทำเอง ไม่ใช่ Instructor-verified Starter Kit**
ควรให้ผู้สอนยืนยันว่าใช้ PN2222 ตัวอย่างนี้แทนโมเดลของรายวิชาได้
การทดสอบด้านล่างเป็นการทดสอบ Engine ไม่ใช่ผลตรวจรับเว็บ B1–B8
เอกสารนี้เริ่มจาก milestone Starter Kit แยกจากเว็บ ต่อมามีการเชื่อม Flask แล้ว
ดูวิธีใช้เว็บและผลตรวจรับล่าสุดที่ [README](../README.md) และ
[validation](validation.md); สูตร DC Bias ทั้งสามแบบยังคงเดิม

## Files

- `spice_engine.py`: validate parameters, generate netlist, run solver, parse ASCII raw data.
- `models/PN2222.mod`: original numerical model parameters from ngspice examples.
- `models/README.md`: model source, attribution and limitations.
- `starter_kit.py`: run DC/AC/transient and save traceable output artifacts.
- `test_spice_engine.py`, `test_spice_integration.py`: unit and real-engine checks.

## Setup and run (Windows CMD)

Use Python 3.12 and ngspice 47 console. The kit needs no pip packages.
From the project directory:

```cmd
cd /d C:\Users\B6826123\Desktop\gitlab
python -m unittest discover -v
python starter_kit.py --output "%TEMP%\opencode\lab04-my-first-run"
```

Choose a **new** output directory for each run; the CLI refuses to overwrite
existing directories. Failed analyses leave `error.txt` and exit nonzero.
No error is replaced by a fake success result. If one analysis fails, earlier
analysis artifacts may exist; that does not mean all three analyses succeeded.

Discovery prefers `ngspice_con.exe` from PATH on Windows, then the per-user
ngspice 47 location installed in this session. On Linux it uses `ngspice`.
For another installation explicitly configure:

```cmd
set "NGSPICE_EXECUTABLE=%LOCALAPPDATA%\Programs\ngspice-47\Spice64\bin\ngspice_con.exe"
python starter_kit.py --output "%TEMP%\opencode\lab04-another-run"
```

You can instead pass `--executable "C:\path with spaces\ngspice_con.exe"`.
An invalid explicit path causes an error, not silent fallback. On Windows
do not use the GUI `ngspice.exe` for a console subprocess. The adapter derives
the `share/ngspice` resource directory from the executable where present,
sets `SPICE_LIB_DIR`/`SPICE_SCRIPTS` for that subprocess, and requests ASCII
output with `SPICE_ASCIIRAWFILE=1`. It does not modify global environment settings.

## Circuit, measurements and units

| Input | Baseline |
|---|---|
| VCC | 12 V |
| R1 / R2 | 100 / 22 kohm |
| RC / RE / RL | 2.2 / 1 / 10 kohm |
| Cin / Cout | 10 / 10 uF |
| Model / temperature | PN2222 / 27 degrees C |
| Generator | 10 mV **peak**, 1 kHz |
| AC sweep | 10 Hz–100 MHz, 40 points/decade, AC 1 V |
| Transient | 20 periods, maximum timestep = period/100 |

R1 is VCC-to-base; R2 is base-to-ground; RC is VCC-to-collector;
RE is emitter-to-ground. Q1 terminals are collector/base/emitter.
The source connects to the base through Cin; Cout connects the collector to
the output, with RL from output to ground. **No emitter bypass capacitor.**

`Vin` is the generator node `in` before Cin, not the base voltage.
`Vout` is node `out` across RL after Cout, not DC collector voltage.
AC gain is `V(out)/V(in)`; magnitude is V/V, dB is `20*log10(magnitude)`.
Phase uses the principal angle [-180, 180] degrees; it is not unwrapped.
DC `ic_a` is Q1's collector current, positive into the collector.

Transient data includes startup. For steady-state comparisons use the final
five periods, not the first cycle. Changing frequency keeps the displayed
number of periods fixed, so total simulation time changes too.

## Outputs and traceability

Each `dc/`, `ac/`, `transient/` directory contains:

- `circuit.cir`: actual netlist including the exact model.
- `run.log`: solver diagnostics.
- `run.raw`: real ASCII solver data, not fabricated chart points.
- `result.json`: numeric results/arrays, units, parameters, references,
  actual executable/version, model source and model SHA-256.

The process uses an argument list, `shell=False`, a 20-second timeout per
invocation and a unique temporary working directory per simulation. Inputs
must be finite and within documented bounds in `SpiceParameters.validate`;
RE=0, nonpositive values, NaN, infinity, inverted sweeps and fractional point
counts are rejected. Missing/truncated output and failed processes raise
`SpiceError`; missing initialization files remain visible in the saved log.

Try parameter changes in separate output directories:

```cmd
python starter_kit.py --re-kohm 2 --output "%TEMP%\opencode\lab04-re2"
python starter_kit.py --amplitude-mv 20 --output "%TEMP%\opencode\lab04-20mv"
python starter_kit.py --frequency-hz 2000 --output "%TEMP%\opencode\lab04-2khz"
```

## Verified observations (2026-11-24)

Python 3.12.7 / ngspice 47, baseline above:

| Quantity | Actual result |
|---|---|
| VB | 2.015763451 V |
| VE | 1.364230727 V |
| VC | 9.016769239 V |
| VCE | 7.652538512 V |
| IC | 1.356194560 mA |
| Gain at 1 kHz | 1.757779687 V/V (4.899288828 dB) |
| Phase at 1 kHz | -179.873340144 degrees |
| AC / transient points | 281 / 2008 |

Observed model SHA-256:
`372bc60e9e920164d79639743b5778ab39b736cbbb8aa6c840eaa2fded2d91f9`.
These numbers document an actual run; they are not constants used by the adapter.
The real-engine tests check RE sensitivity, near-inverted phase, small-signal
AC/transient gain agreement within 5%, approximate output doubling at 20 mV,
and time-axis change at 2 kHz. Results may vary slightly by solver/platform.

Baseline artifacts from this session are stored outside Git:
`C:\Users\B6826123\AppData\Local\Temp\opencode\lab04-starter-evidence-20261124-174851`.
Temporary evidence is not permanent submission material; regenerate/copy a
selected sample when preparing the final Lab 04 submission.

## Flask interface — now integrated in app.py

```python
from spice_engine import SpiceParameters, SpiceError, run_simulation

# Form validation must convert numeric strings before constructing parameters.
parameters = SpiceParameters(re_kohm=1, amplitude_mv=10, frequency_hz=1000)
result = run_simulation(parameters, "ac")
# result["series"] supplies chart data; no analytical substitute is used.
```

For Flask, keep `bjt_model.py` and the three existing analytical modes;
dispatch only the CE reference SPICE analyses to this adapter. Catch both
`ValueError` and `SpiceError` and clear old plots on errors. Show source units,
model and run provenance. Do not compare the model's Bf=255.9 directly against
the analytical calculator's constant beta=100 as if they were identical.
The original analytical "independent" approximation is not used to validate
this starter's solver data.

The later web milestone integrates this interface with Flask, actual SVG plots,
Impeccable polish, B1–B8 browser evidence and submission documentation. Those
checks are recorded separately in `docs/validation.md`, not inferred from this
starter's CLI tests. Instructor acceptance of the model, human demonstration,
commit and push remain pending user review.
