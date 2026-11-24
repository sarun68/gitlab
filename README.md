# ENG29 2121 · Lab 04 — BJT CE Amplifier Simulator

Flask app ต่อยอดจาก Lab 3: คง Analytical DC Bias ทั้ง **Fixed / Emitter /
Voltage Divider** และเพิ่ม **ngspice DC / AC / Transient** สำหรับ CE Voltage
Divider อ้างอิงหนึ่งวงจร พร้อมกราฟ SVG จากข้อมูลที่ Solver รันจริง

**Model: PN2222 จากตัวอย่าง ngspice — ชุดที่เราจัดทำเอง ไม่ใช่
Instructor-verified Starter Kit** ควรให้ผู้สอนยืนยันก่อนใช้ส่งแทนชุดรายวิชา
แหล่งที่มาและข้อจำกัด: [models/README.md](models/README.md)

## Run locally

ทดสอบด้วย Python 3.12.7, Flask 3.1.3, ngspice 47 (Windows x64 console)

```cmd
cd /d C:\Users\B6826123\Desktop\gitlab
python -m pip install -r requirements.txt
ngspice_con --version
python app.py
```

เปิด **http://127.0.0.1:5000/** แล้วเลือก Analysis และกด **Run Simulation**
ปิด Server ด้วย Ctrl+C ใน Terminal ที่ใช้รัน ใช้บน localhost เท่านั้น ไม่ใช่
production deployment; debug mode ปิดเป็นค่าเริ่มต้น

### Install/configure ngspice

ngspice เป็นโปรแกรมภายนอก ไม่ใช่ pip dependency:
[Official download](https://ngspice.sourceforge.io/download.html)
บน Windows ให้แตกแพ็กเกจ 64-bit ทั้งโฟลเดอร์ไว้ในตำแหน่งที่เขียนได้ แล้วใช้
`Spice64/bin/ngspice_con.exe` ไม่ใช่ GUI `ngspice.exe`

ถ้า PATH ยังไม่พบ ให้ตั้งใน CMD ก่อนเปิด Flask:

```cmd
set "NGSPICE_EXECUTABLE=%LOCALAPPDATA%\Programs\ngspice-47\Spice64\bin\ngspice_con.exe"
python app.py
```

Adapter ค้นหาตัว console จาก PATH หรือ per-user ngspice 47 location บน Windows
และกำหนดตำแหน่ง `spinit` จาก executable ให้ subprocess โดยอัตโนมัติเมื่อพบ
`share/ngspice` บน Linux ใช้คำสั่ง `ngspice`; ไม่ได้ทดสอบ Linux/macOS ในรอบนี้
หากเปลี่ยน environment ให้รีสตาร์ต Flask ไม่ต้องติดตั้งแบบ admin

## Use the app

- **Analytical DC:** เลือก Bias ได้ 3 แบบ ใช้สูตรเดิมใน `bjt_model.py`.
- **SPICE DC:** แสดง VB, VE, VC, VCE (V) และ IC (mA) จาก `.op`.
- **SPICE AC:** กราฟ magnitude (dB) / phase (degrees) กับ logarithmic Hz,
  และค่า magnitude (V/V) ที่จุดตัวอย่างใกล้ความถี่ที่ระบุ.
- **SPICE Transient:** ปรับ mV **peak** และ Hz; จำลอง 20 คาบ แสดง 5 คาบท้าย,
  Vin/Vout (V) กับเวลา (ms) และค่า peak-to-peak.
- เมื่อแก้ค่า ผลเก่าถูกซ่อนและสถานะเปลี่ยนเป็น Inputs changed จนกดรันใหม่.
- Error/Timeout/Engine ไม่พบ จะไม่มีกราฟเก่าพร้อม Success.
- **Run evidence:** ดู Model SHA-256, engine version, netlist และ log;
  Download run JSON มีพารามิเตอร์, arrays, raw output, run ID และเวลา.

Reference: VCC 12 V, R1/R2 100/22 kΩ, RC/RE/RL 2.2/1/10 kΩ,
Cin/Cout 10/10 µF, PN2222, 27 °C, no emitter bypass; Vin อยู่ก่อน Cin,
Vout อยู่หลัง Cout คร่อม RL. ไม่มีการส่งพารามิเตอร์ไปยังบริการภายนอก

## Verify and reproduce

```cmd
python -m unittest discover -v
python starter_kit.py --output "%TEMP%\opencode\lab04-new-run"
```

เลือก output directory ที่ยังไม่มีอยู่ ชุด unittest ใช้ Python stdlib ไม่ต้องลง
pytest; integration tests เรียก ngspice จริง ส่วน tests ของ failure paths ใช้
mock เฉพาะ timeout/solver failure การรันบนเครื่องที่ไม่มี solver จะไม่ผ่าน
Flask real-engine tests จนกว่าจะติดตั้ง/กำหนด executable

- [B1–B8 validation](docs/validation.md) — ผล Playwright MCP จริงและข้อจำกัด
- [Submission checklist และแนวคำตอบ 5 ข้อ](docs/SUBMISSION.md)
- [UI polish/audit](docs/lab04-ui-review.md) — ก่อน/หลัง Impeccable และ mobile fix
- [Starter API, units, model and CLI](docs/starter-kit.md)
- [Screenshots and sample browser data](docs/captures/)

## Structure

```text
app.py                    Flask validation / analysis dispatch / result summary
bjt_model.py              Original Lab 3 analytical calculations (unchanged)
spice_engine.py            Netlist / safe subprocess / ASCII raw parser
starter_kit.py             Standalone evidence CLI
models/PN2222.mod          Sourced numerical BJT model
templates/index.html      Shared form, original bias SVGs, CE reference, evidence
static/style.css          Local responsive CSS (no Tailwind CDN)
static/app.js             Controls, status, real-array SVG plots, JSON export
test_app.py               Flask regression and real-engine route tests
test_spice*.py            Adapter/parser failures and real-engine tests
docs/validation.md        Actual browser B1–B8 evidence
```

Model parameters differ from constant beta/VBE assumptions in Analytical.
Different results are expected; do not force them to match. AC is small-signal;
transient Vpp ratio at large amplitudes is not automatically an AC gain.
Phase is principal angle −180…180°, with graph segments split at wrap jumps.
Cutoff frequencies are not automatically reported. See the handout for scope.

## Submission status

- Repository: https://github.com/sarun68/gitlab.git
- Student: B6826123 ศรัณย์พร รัตตสุพร
- Working branch: `lab04-spice-starter`
- ตรวจ final local commit SHA ด้วย `git rev-parse HEAD`; การมี local commit
  ไม่ได้แปลว่า push แล้ว ต้องเผยแพร่ commit นั้นไป GitHub ก่อนส่ง TA.
  อย่าใช้ SHA ของ Lab 3 แทนชุดงาน Lab 04 นี้.
- Human review of the model choice and personal demonstration are still needed.

Project-scoped Impeccable tooling can be installed again with
`npx impeccable install --providers=opencode --scope=project`.
The local downloaded skill is not application runtime code and is excluded
from the submission commit; the UI review/evidence is included.

## AI assistance disclosure (4 lines)

1. AI สร้าง adapter, starter CLI และนำโมเดลตัวอย่าง PN2222 มาพร้อมแหล่งอ้างอิง
2. AI เชื่อม Flask และเพิ่มกราฟ/สถานะ/หลักฐาน โดยคงสูตร Analytical เดิม
3. AI รัน unittest, ngspice และ Playwright MCP แล้วบันทึกสิ่งที่เห็นจริง
4. การตรวจด้วยตนเองและการอนุมัติโมเดลโดยนักศึกษา/ผู้สอนยังต้องทำ ไม่ได้อ้างว่าเสร็จแล้ว
