# ENG29 2121 · Lab 04 — ชุดส่งงาน

- **นักศึกษา:** B6826123 ศรัณย์พร รัตตสุพร
- **Repository:** https://github.com/sarun68/gitlab
- **Branch:** `lab04-spice-starter`
**Commit SHA:** ใช้ SHA ของ local commit ที่รวมชุดงานนี้ ตรวจด้วย `git rev-parse HEAD`
และคัดลอกลงช่องส่งงาน ไม่ใช้ SHA ของ Lab 3 แทน

> การสร้าง local commit ไม่ได้แปลว่าอัปโหลด GitHub แล้ว ต้อง push branch หรือ
> merge ตามที่เจ้าของเลือกก่อน TA จึงจะเปิดไฟล์จาก GitHub ได้
> โมเดล PN2222 เป็นตัวอย่างที่นำมาจัดทำ Starter Kit เอง ไม่ใช่ชุดรับรองของผู้สอน

## Submission checklist และลิงก์หลักฐาน

| รายการในใบงาน | สิ่งที่เตรียมไว้ | สถานะ |
|---|---|---|
| GitHub URL / Commit SHA | URL ด้านบน; ตรวจ SHA ด้วย `git rev-parse HEAD` | ต้องเผยแพร่ commit ไป GitHub ก่อนส่ง |
| Flask App, DC/AC/Transient และ DC Bias 3 แบบ | `app.py`, `bjt_model.py`, `spice_engine.py`, `templates/index.html`, `static/` | ทำแล้ว; 30 tests ผ่าน |
| README ติดตั้ง/รัน | [README.md](../README.md), [requirements.txt](../requirements.txt), [Starter guide](starter-kit.md) | เตรียมแล้ว |
| B1–B8, วิธีตรวจ, ผลจริง, ที่มา, ข้อจำกัด | [validation.md](validation.md) | ตรวจจริงด้วย Playwright MCP; บันทึก NOT RUN แยกไว้ |
| UI ก่อน/หลัง และ Impeccable | [UI review](lab04-ui-review.md), [ก่อน](captures/lab03-before-desktop.png), [หลัง](captures/lab04-dc-desktop.png) | เตรียมแล้ว; ระบุข้อจำกัด detector ตามจริง |
| กราฟจาก Browser จริง | [AC desktop](captures/lab04-ac-desktop.png), [Transient desktop](captures/lab04-transient-desktop.png), [AC mobile](captures/lab04-ac-mobile.png), [Transient mobile](captures/lab04-transient-mobile.png) | เตรียมแล้ว |
| ตัวอย่างข้อมูลและที่มาของกราฟ | [DC JSON](captures/B2-browser-data.json), [AC JSON](captures/B4-browser-data.json), [Transient JSON](captures/B5-browser-data.json) | มี run ID, netlist, raw output, log และโมเดล |
| บันทึก AI 3–5 บรรทัด | หัวข้อด้านล่าง | ไม่อ้างว่านักศึกษาตรวจเองแล้ว |

## วิธีสาธิตให้ TA

```cmd
python -m pip install -r requirements.txt
ngspice_con --version
python -m unittest discover
python app.py
```

เปิด `http://127.0.0.1:5000/`:

1. เลือก Analytical DC สาธิต Divider / Fixed / Emitter ตามค่า B1 ใน validation.
2. เลือก SPICE DC ใช้ค่าตั้งต้น แล้วเปลี่ยน RE 1→2 kΩ เพื่อแสดงผลที่เปลี่ยนจริง.
3. คืน RE=1 เลือก AC ดู magnitude/phase และเปิด Run evidence เทียบ netlist/log.
4. เลือก Transient ที่ 10 mV peak, 1 kHz แล้วเปลี่ยนเป็น 20 mV หรือ 2 kHz.
5. ใส่ RE=0 ให้เห็น Error และไม่มีกราฟเก่าค้าง จากนั้นแก้กลับเพื่อสาธิต recovery.
6. กด Download run JSON และลองหน้าจอมือถือ ดูหน่วย จุดวัด และป้าย model/source.

Windows ใช้ `ngspice_con.exe` ไม่ใช่ตัว GUI; หาก PATH ไม่พบให้ตั้ง
`NGSPICE_EXECUTABLE` ตาม README ก่อนเปิด Flask. ไม่ต้องลง ngspice ด้วย pip.

## แนวคำตอบคำถามรายบุคคล 5 ข้อ

คำตอบนี้อธิบายโค้ดที่ทำไว้ ใช้ทบทวนและทดลองเองก่อนตอบ TA ไม่ใช่หลักฐานว่า
นักศึกษาสาธิตหรือเข้าใจแล้ว

### 1. Python ส่งอะไรให้ ngspice และรับผลกลับมาอย่างไร?

Flask รับค่าจากฟอร์ม ตรวจตัวเลข/ช่วง แล้วส่ง `SpiceParameters` ให้ adapter.
Adapter สร้างไฟล์ข้อความ **netlist** `circuit.cir` ระบุชิ้นส่วน จุดต่อ โมเดล
PN2222 และคำสั่ง `.op`, `.ac` หรือ `.tran` ในโฟลเดอร์ชั่วคราวแยกแต่ละรอบ.
เรียก ngspice ด้วย `subprocess.run` แบบ argument list, `shell=False`, timeout
20 วินาที โดยสั่ง `-b -o run.log -r run.raw circuit.cir`.
เมื่อจบ ตรวจ exit code/ไฟล์ แล้วอ่าน log และ ASCII raw แปลงเป็นตัวเลขหรือ
complex vectors ก่อนส่งผล/arrays/หน่วยให้ Jinja และกราฟ SVG ใน Browser.

### 2. เหตุใดกราฟ `.ac` และ `.tran` จึงไม่ใช่สิ่งเดียวกัน?

`.ac` วิเคราะห์สัญญาณเล็กรอบ DC operating point กวาดความถี่ เพื่อดู magnitude
และ phase ของ `Vout/Vin`; แกนนอนเป็น Hz. ในงานนี้ AC excitation ตั้ง 1 V
เพื่อหา transfer ratio ไม่ใช่คลื่นเวลาขนาด 1 V ที่นำไปทดสอบ clipping.
`.tran` จำลองแรงดันตามเวลาโดยใช้แหล่ง `SIN` จริงที่ระบุ mV peak และ Hz;
แกนนอนเป็นเวลา และเห็น startup/การกลับเฟส/ความบิดเบือนเมื่อสัญญาณใหญ่ได้.
จึงไม่ควรนำ Vpp ratio ของคลื่นบิดเบือนมาอ้างว่าเท่ากับ small-signal AC gain.

### 3. เปลี่ยน Amplitude แล้วกราฟไม่เปลี่ยน ควรตรวจตรงไหนก่อน?

ตรวจว่าเลือก **Transient** และกด Run ใหม่แล้ว ไม่ใช่ดูผล AC ซึ่งเป็น
small-signal analysis. จากนั้นตรวจค่า `amplitude_mv` ที่ฟอร์มส่งและ
`parameters` ของ JSON ว่าถูกแปลง mV→V และอยู่ใน `SIN(0 amplitude frequency)`
ของ netlist จริงหรือไม่. เปรียบเทียบ run ID, raw output และ arrays ก่อนดู
การวาดกราฟ เพื่อแยกปัญหาฟอร์ม/adapter ออกจากปัญหาหน้าเว็บหรือผลเก่าค้าง.
ค่าอ้างอิงที่ทดสอบ: เพิ่ม 10→20 mV แล้ว Vout Vpp ประมาณ .03515→.07030 V.

### 4. Impeccable เปลี่ยนอะไรได้ และไม่ควรเปลี่ยนอะไร?

ใช้ตรวจ/ปรับการจัดกลุ่มอินพุต ลำดับข้อมูล ตัวอักษร สี/contrast หน่วย
labels/focus สถานะ error/loading และ responsive layout ได้. ในงานนี้ใช้
polish guidance กับ UI เดิมและตรวจ rendered browser จริง.
ไม่ควรเปลี่ยนสมการ/โมเดลวงจรหรือข้อมูลผลรันเพื่อให้หน้าจอสวย ไม่เปลี่ยน
กราฟจริงเป็นเส้นตัวอย่าง ไม่ซ่อน engine error และไม่อ้างว่า detector ผ่าน
หมดเมื่อเครื่องมือรายงาน warning. รายละเอียดอยู่ใน `lab04-ui-review.md`.

### 5. รู้ได้อย่างไรว่า Bode Plot เป็นผลจำลองจริง ไม่ใช่ Mock Data?

ตรวจสายข้อมูลตั้งแต่ netlist ที่มี `.ac` → log/`run.raw` จาก ngspice → arrays
ที่ parser อ่าน → JSON ของ run เดียวกัน → polyline ที่ใช้ arrays นั้น.
มี run ID, engine version, model SHA-256 และ inputs กำกับ. ในหลักฐาน B4
มี 281 จุด; คำนวณ magnitude จาก complex raw output แล้วตรงกับ arrays ของ
กราฟทุกจุด (max absolute error 0). ที่ 1 kHz ได้ประมาณ 1.75778 V/V,
4.89929 dB และ −179.87334°. Screenshot เพียงอย่างเดียวไม่พิสูจน์ที่มาของข้อมูล.

## บันทึกการใช้ AI (4 บรรทัด)

1. AI สร้าง adapter/Starter CLI และเลือก PN2222 จากตัวอย่าง ngspice พร้อมแหล่งอ้างอิง
2. AI เชื่อม Flask เพิ่มกราฟจริงและหลักฐานผลรัน โดยคง Analytical DC Bias 3 แบบ
3. AI รัน unittest และ Playwright MCP บันทึกผลจริงและข้อจำกัดใน validation
4. นักศึกษายังต้องทดลอง/ตรวจเอง และให้ผู้สอนยอมรับโมเดลก่อนส่ง ไม่อ้างว่าขั้นนี้เสร็จแล้ว

## สิ่งที่ยังต้องยืนยันก่อนส่ง

- อัปโหลด commit ที่เลือกไป GitHub แล้วส่ง URL/Commit SHA ที่ TA เข้าถึงได้.
- ตรวจด้วยตนเองตามขั้นตอนข้างต้นและอธิบายที่มาของผลให้ได้.
- ขอผู้สอนยอมรับ PN2222 ตัวอย่างแทน Starter Kit ของรายวิชา.
- ไม่รวม `.venv`, `.env`, token/API key, โปรแกรม ngspice ทั้งชุด หรือ cache
  ชั่วคราวใน commit; เก็บเฉพาะหลักฐานตัวอย่างที่ระบุวิธีสร้างซ้ำ.
