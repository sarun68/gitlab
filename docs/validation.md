# Lab 04 validation — 2026-11-24

## Environment and provenance

- Windows x64; Python **3.12.7**, Flask **3.1.3**, ngspice **47** console.
- Local URL: `http://127.0.0.1:5000/`. Actual Playwright MCP tools were used:
  navigate, snapshot, select, fill, click, evaluate, resize, screenshot, console.
- Model: **PN2222**, official ngspice example; [source/provenance](../models/README.md).
  Self-authored starter, **not instructor-verified**. Approval for using this
  substitute in the course is still a human/instructor decision.
- Model SHA-256: `372bc60e9e920164d79639743b5778ab39b736cbbb8aa6c840eaa2fded2d91f9`.
- Fixture: VCC=12 V, R1/R2=100/22 kΩ, RC/RE/RL=2.2/1/10 kΩ,
  Cin=Cout=10 µF, temperature 27 °C, no emitter bypass. Generator input before
  Cin; output across RL after Cout. Initial transient 10 mV peak at 1 kHz.
- AC: 10 Hz–100 MHz, 40 points/decade, excitation 1 V, actual **281** samples.
  Transient: 20 periods, actual **2008** samples, graph last five periods (**501**
  samples). Data are adaptive solver samples, not invented sine curves.

## Browser acceptance B1–B8

All PASS entries below represent actions executed with real browser tools, not
inferred from source or screenshot appearance alone. Core checks ran before the
last hardening pass; corrected phase/mobile behavior and a fresh DC run were
verified afterward. Screenshots may have different run IDs from earlier snapshots
because baseline analyses were re-run after fixes with the same input fixture.

| Case | Method / Input | Expected / Reference | Observed | Evidence | Status |
|---|---|---|---|---|---|
| B1 · Regression | Select Analytical DC; Divider R1/R2=100/22, Fixed RB=1000, Emitter RB=1000/RE=1 (kΩ), β=100, VBE=.7 V | Original Lab 3 values remain | Divider IC=1.23 mA, VCE=8.05 V; Fixed 1.13 mA / 9.51 V; Emitter 1.03 mA / 8.71 V. All Active | `captures/B1-divider.yml`, `B1-fixed.yml`, `B1-emitter.yml`; original module unchanged | **PASS** |
| B2 · DC SPICE | Select SPICE DC; reference fixture; click Run | Actual `.op`, PN2222, success and correct measurement units | VB=2.015763451 V, VE=1.364230727 V, VC=9.016769239 V, VCE=7.652538512 V, IC=1.356194560 mA; CE diagram visible, model/netlist/log available | `captures/B2-dc.yml`, `B2-browser-data.json`, `lab04-dc-desktop.png` | **PASS** |
| B3 · Change RE | Change only RE 1→2 kΩ, click Run | Operating point changes and run is new | IC 1.356194560→0.718933121 mA; VCE 7.652538512→8.971366040 V; different run ID. Before submission, old result hidden and Inputs changed shown | `captures/B3-re2.yml`; baseline/new run IDs in snapshots | **PASS** |
| B4 · AC | Restore RE=1 kΩ, select SPICE AC, click Run | Actual magnitude/phase vs log Hz | 281 gain/phase points; at 1000 Hz gain=1.757779687 V/V, 4.899288828 dB, phase=−179.873340144°. Raw complex magnitudes match chart arrays with max absolute error **0**. One phase wrap split into two polylines, retaining all 281 samples | `captures/B4-browser-data.json`, `B4-ac-final.yml`, `lab04-ac-desktop.png` | **PASS** |
| B5 · Transient | Select Transient, 10 mV peak / 1000 Hz, click Run | Actual input/output traces, time and voltage units, approximately inverted steady state | 2008 raw points; last 501 displayed. Vin Vpp=.019996904972 V, Vout Vpp=.035149729855 V; average Vin×Vout=−.000087712887275 V² in final five periods; agrees with small-signal AC gain within 5% | `captures/B5-browser-data.json`, `B5-transient.yml`, `lab04-transient-desktop.png` | **PASS** |
| B6 · Change Source | Change amplitude 10→20 mV peak, Run; then frequency 1000→2000 Hz, Run | Actual waveform changes, not fixed trace | Vin Vpp .0199969→.0399938 V; Vout Vpp .0351497→.070299 V, about 2×. At 2 kHz simulated end time .020→.010 s (20 periods fixed), new run IDs | `captures/B6-browser-data.json`, `B6-amplitude20.yml`; browser tool evaluation | **PASS** |
| B7 · Invalid/fail | Following successful run, enter RE=0 and click Run | Visible error, no stale success/plot | Error names re_kohm and allowed range; Error status, no `simulation-data` element and zero chart SVGs. Recovery RE=1 ran successfully. Engine-not-found/timeout/failure paths additionally covered by unittest (not claimed as browser tests) | `captures/B7-invalid.yml`, `lab04-error.png`; `test_app.py`, `test_spice_engine.py` | **PASS** |
| B8 · UI | Resize AC and Transient to desktop 1280×900, tablet 768×1024, phone 390×844; switch modes and keyboard Tab | Readable controls/units/plots, no clipped important content | Initial mobile axis text about 6.4 px: **failed**, fixed responsive viewBox and rechecked at **13 px**. No horizontal overflow. Mobile button height 48.39 px; labels associated; keyboard focus solid 3 px; final console 0 errors/warnings | `captures/B8-mobile.yml`, `lab04-ac-mobile.png`, `lab04-transient-mobile.png`, `lab04-console.log` | **PASS after fix** |

## Independent data checks and hardening

1. Loaded saved browser JSON, parsed each embedded `raw_text` independently of
   the adapter parser, compared frequency and complex gain, and real time/Vin/Vout
   arrays: AC magnitude max error **0** (281 samples); B5/B6 real arrays match
   exactly (2008 samples each). This proves data correspondence, not physical
   manufacturer validation of every PN2222 model parameter.
2. Actual real-solver unittest compares AC and transient gain, near-180° phase,
   source amplitude/frequency changes and DC RE response. Legacy four tests remain.
3. Independent code review found extreme tiny analytical inputs could underflow
   and cause HTTP 500. Added failing regression and lower bounds/handled arithmetic
   error path; now returns normal Error with no result.
4. Browser regression proved the old phase chart drew across ±180°; final check
   reports **1 wrap / 2 segments / 281 samples**, no false segment.
5. Added server-rendered initial schematic visibility and blank-value preservation
   regressions so no-JS/invalid-input recovery does not silently show wrong data.
6. Final unit/integration suite: **30 tests, all PASS**, command
   `python -m unittest discover -v`. Some engine-failure tests use mocks by design;
   successful SPICE integration tests invoke the real ngspice executable.
7. Download run JSON button clicked in Playwright; a JSON file downloaded
   successfully. It contains the same run ID, parameters and actual series/raw.

## Limitations / NOT RUN

- Physical hardware/device measurement validation: **NOT RUN**.
- Instructor acceptance of substitute PN2222 model: **not yet obtained**.
- Full Lab 3 A1–A5 were not all rerun in browser in this increment; B1 reran all
  three bias modes. Older A1–A5 evidence is retained below as history.
- Full screen-reader-user study, other browser engines and physical phones:
  **NOT RUN**. Playwright viewport tests are not device certification.
- Impeccable skill loaded and used for polish; source detector returned two
  CSS-resolution-limited warnings, not a clean scan. See
  [UI review](lab04-ui-review.md) for exact method and rendered cross-checks.
- No automatic cutoff-frequency estimate; principal phase remains wrapped.
- Analytical beta/VBE approximation and PN2222 are different models; they are
  intentionally not forced to match, and the old analytical independent estimate
  is not used as the SPICE reference.
- Remote publication and final submission SHA: **pending user choice**. A local
  commit does not mean the GitHub repository already contains the changes;
  verify the selected commit was pushed before submitting its SHA.

---

## Archived Lab 3 validation (previous session, preserved unchanged)

| กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน | เห็นจริง | วิธีตรวจ | สถานะ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A1 · โหมดเดิม** | Divider · $R_1 = 100\text{ k}\Omega$, $R_2 = 22\text{ k}\Omega$, $R_E = 1\text{ k}\Omega$ | ผลต้องตรงกับเมื่อรัน Lab 2 ก่อนแก้ และเทียบได้กับค่าอ้างอิงเดิม<br>$I_C = 1.23\text{ mA}$ · $V_{CE} = 8.05\text{ V}$ | $I_C = \mathbf{1.23\text{ mA}}$ · $V_{CE} = \mathbf{8.05\text{ V}}$ | Playwright MCP: เปิด http://127.0.0.1:5000/ → ใส่ R1=100, R2=22, RE=1 → กดคำนวณ → อ่าน snapshot | ✅ PASS |
| **A2 · Fixed** | Fixed · $R_B = 1\text{ M}\Omega$ | คำนวณได้โดยไม่ต้องกรอก $R_E$<br>$I_C = 1.13\text{ mA}$ · $V_{CE} = 9.51\text{ V}$ | $I_C = \mathbf{1.13\text{ mA}}$ · $V_{CE} = \mathbf{9.51\text{ V}}$ | Playwright MCP: เปิด http://127.0.0.1:5000/ → เลือกโหมด Fixed → ใส่ RB=1000 kΩ, RC=2.2, β=100, VBE=0.7 → กดคำนวณ → อ่าน snapshot | ✅ PASS |
| **A3 · Emitter** | Emitter · $R_B = 1\text{ M}\Omega$, $R_E = 1\text{ k}\Omega$ | มีช่องและใช้ค่า $R_E$<br>$I_C = 1.03\text{ mA}$ · $V_{CE} = 8.71\text{ V}$ | $I_C = \mathbf{1.03\text{ mA}}$ · $V_{CE} = \mathbf{8.71\text{ V}}$ | Playwright MCP: เปิด http://127.0.0.1:5000/ → เลือกโหมด Emitter → ใส่ RB=1000 kΩ, RE=1 kΩ, RC=2.2, β=100, VBE=0.7 → กดคำนวณ → อ่าน snapshot | ✅ PASS |
| **A4 · เปลี่ยนค่าเดียว** | Emitter · เหมือน A3 แต่เปลี่ยน $R_E$ เป็น $2\text{ k}\Omega$ | $I_C$ จะลดลงจาก A3 (เหลือ $0.94\text{ mA}$, $V_{CE} = 8.03\text{ V}$) เพราะ $R_E$ มากขึ้น ทำให้แรงดันตกคร่อม $R_E$ สูงขึ้นและกระแส $I_B$ ลดลง | $I_C = \mathbf{0.94\text{ mA}}$ · $V_{CE} = \mathbf{8.03\text{ V}}$ | Playwright MCP: เปิด http://127.0.0.1:5000/ → เลือกโหมด Emitter → ใส่ RB=1000 kΩ, RE=2 kΩ, RC=2.2, β=100, VBE=0.7 → กดคำนวณ → อ่าน snapshot | ✅ PASS |
| **A5 · อินพุตผิด** | Fixed · $R_B = 0$ | มีข้อความให้แก้ $R_B$ เว็บไม่ล่ม และไม่แสดงผลเดิมเป็นผลของรอบนี้ | ค่า RB ต้องมากกว่า 0 · ไม่มีตารางผลลัพธ์ | Playwright MCP: เปิด http://127.0.0.1:5000/ → เลือกโหมด Fixed → ใส่ RB=0 → กดคำนวณ → อ่าน snapshot | ✅ PASS |
