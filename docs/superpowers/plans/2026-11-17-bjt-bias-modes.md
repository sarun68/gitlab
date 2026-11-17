# เพิ่มโหมด Fixed Bias / Emitter Bias — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่มโหมด Fixed Bias และ Emitter Bias (แหล่งจ่ายเดียว) ในแอป Flask เดิม โดยผลลัพธ์ของ Voltage Divider ต้องคงเดิมทุกค่า

**Architecture:** แยกสูตรของแต่ละโหมดเป็นฟังก์ชันใน `bjt_model.py` แล้วใช้ `calculate_bjt_dc()` เป็น dispatcher เลือกฟังก์ชันตาม `mode` ทุกโหมดคืน dict คีย์/หน่วยชุดเดียวกัน ฝั่ง UI เพิ่ม dropdown เลือกโหมด ซ่อน/แสดงอินพุตตามโหมด และสลับวงจร SVG 3 แบบ

**Tech Stack:** Python 3.12, Flask 3.1, Jinja2, Tailwind CSS (CDN), SVG

**Spec:** ตารางโหมด/อินพุต/ตำแหน่งตัวต้านทานที่ผู้ใช้ให้มา + โครง Flask จาก Lab 2 (`B6826123-sarunporn-G1-lab2.pdf`)

## สิ่งที่อ่านจากโครงเดิม (Lab 2)

- `app.py`: route `/` รับ GET/POST, อ่านค่าจาก `request.form.get(...)`, เรียก `calculate_bjt_dc(...)`, ส่ง `result/error/form` ให้ template
- `bjt_model.py`: ฟังก์ชันเดียวสำหรับ Voltage Divider — แปลง kΩ→Ω, ทำ Thevenin, คำนวณ IB/IC/IE/VC/VE/VCE, ตรวจ Active/Saturation/Cutoff, คืน dict
- `templates/index.html`: ฟอร์ม 3 คอลัมน์ (Inputs / SVG / Results), ตารางผลลัพธ์ใช้คีย์ `vb_v, ve_v, vc_v, vce_v, ib_ua, ic_ma, ie_ma`
- Lab 2 PDF เน้นลำดับ ฟอร์ม → Flask (`request.form.get`) → dict → Jinja2 และการเตือน Region/Warning; **ไม่มีสมการไบอัสในไฟล์** จึงใช้ตารางที่ผู้ใช้ให้เป็นแหล่งสมการ

## Global Constraints

- ผลลัพธ์ Voltage Divider ต้องเหมือนเดิมทุกค่า (IB=15.53 µA, IC=1.55 mA, VCE=7.01 V สำหรับค่า default)
- ตัวต้านทานใน UI เป็น kΩ; แปลงเป็น Ω ภายในโมเดล
- ทุกโหมดคืน dict คีย์และหน่วยชุดเดียวกัน
- **ไม่แก้ `test_bjt.py` และไม่เพิ่ม unittest ใหม่** — ตรวจรับงานผ่าน Browser ด้วยตารางของผู้ใช้
- ไม่แตะ `electrical.py`, `static/*`, และส่วนอื่นที่ไม่เกี่ยวข้อง

## ไฟล์ที่จะเปลี่ยน

| ไฟล์ | การเปลี่ยนแปลง |
|------|----------------|
| `bjt_model.py` | เพิ่มฟังก์ชันแยกต่อโหมด + helper สร้างผลลัพธ์ + dispatcher |
| `app.py` | อ่าน `mode`, `rb`; ส่งเข้า dispatcher; เก็บค่าฟอร์ม; แสดง error |
| `templates/index.html` | dropdown โหมด, ซ่อน/แสดงอินพุต, SVG 3 แบบ, JS อัปเดตป้าย, error block |
| `test_bjt.py` | **ไม่แก้** (ใช้เป็น regression ของ Divider) |

## Interfaces

```python
# bjt_model.py
def calculate_fixed_bias(vcc, rb, rc, beta, vbe) -> dict
def calculate_emitter_bias(vcc, rb, re, rc, beta, vbe) -> dict
def calculate_voltage_divider_bias(vcc, r1, r2, rc, re, beta, vbe) -> dict

# dispatcher — คง signature เดิมไว้เพื่อให้ test เดิมเรียกแบบ positional ได้
def calculate_bjt_dc(vcc, r1, r2, rc, re, beta, vbe,
                     mode="divider", rb=None) -> dict
```

- `mode` รับ `"divider"` (ค่าเริ่มต้น), `"fixed"`, `"emitter"`
- ถ้าไม่ส่ง `mode` → Divider เหมือนเดิม
- `rb` ส่งเป็น keyword จาก `app.py`

## Dict ที่คืนทุกโหมด (คีย์/หน่วยตรงกัน)

| Key | หน่วย | ความหมาย |
|-----|-------|----------|
| `region` | — | `"Active"` / `"Saturation"` / `"Cutoff"` |
| `ib_ua` | µA | กระแสฐาน |
| `ic_ma` | mA | กระแสคอลเลกเตอร์ |
| `ie_ma` | mA | กระแสอีมิตเตอร์ |
| `vce_v` | V | แรงดัน collector–emitter |
| `vc_v` | V | แรงดัน collector เทียบกราวด์ |
| `vb_v` | V | แรงดันฐานเทียบกราวด์ |
| `ve_v` | V | แรงดันอีมิตเตอร์เทียบกราวด์ |
| `independent_ic_ma` | mA | ค่าตรวจสอบ (Divider ใช้สูตรเดิม; โหมดใหม่ = `ic_ma`) |
| `warning` | — | ข้อความเตือน |

## สูตรแต่ละโหมด

| โหมด | IB | จุดต่ออุปกรณ์ |
|------|----|----------------|
| Fixed Bias | `IB = (VCC − VBE) / RB` | RB: VCC→Base, Emitter→Ground ตรง |
| Emitter Bias | `IB = (VCC − VBE) / (RB + (β+1)·RE)` | RB: VCC→Base, RE: Emitter→Ground |
| Voltage Divider | `VTH = VCC·R2/(R1+R2)`, `RTH = R1∥R2`<br>`IB = (VTH − VBE) / (RTH + (β+1)·RE)` | R1: VCC→Base, R2: Base→Ground, RE: Emitter→Ground |

**สูตรร่วมทุกโหมด**

```
IC = β·IB
IE = (β+1)·IB
VC = VCC − IC·RC
VE = IE·RE          (Fixed: RE = 0 → VE = 0)
VCE = VC − VE
VB = VBE + VE
```

- `IB <= 0` → `Cutoff` (คืน IB=IC=IE=0, VE=0; VB = VTH สำหรับ Divider, VB = VCC สำหรับ Fixed/Emitter)
- `VCE < 0.2 V` → `Saturation` พร้อม warning
- นอกนั้น → `Active`

## การแปลงหน่วย

- **อินพุต:** `RB`, `R1`, `R2`, `RC`, `RE` เป็น kΩ → คูณ 1000 ที่ต้นฟังก์ชันของแต่ละโหมด
  - Fixed: `rb *= 1000`, `rc *= 1000`
  - Emitter: `rb *= 1000`, `re *= 1000`, `rc *= 1000`
  - Divider: `r1, r2, rc, re = r1*1000, r2*1000, rc*1000, re*1000` (เหมือนเดิม)
- **ไม่แปลง:** `VCC`, `VBE` เป็น V อยู่แล้ว; `beta` เป็น dimensionless
- **เอาต์พุต:** แปลงเฉพาะตอนสร้าง dict — `ib_ua = ib*1e6`, `ic_ma = ic*1e3`, `ie_ma = ie*1e3`; แรงดันคงเป็น V

## การตรวจอินพุตตามโหมด

| โหมด | เงื่อนไข |
|------|----------|
| Common | `VCC > 0`, `RC > 0`, `beta > 0` (ข้อความเดิม) |
| Fixed | `RB > 0` |
| Emitter | `RB > 0`, `RE > 0` |
| Divider | `R1 > 0`, `R2 > 0`, `RE >= 0` (เหมือนเดิมทุกข้อความ) |
| โหมดไม่ถูกต้อง | `ValueError("โหมดไม่ถูกต้อง")` |

---

### Task 1: แยกสูตรใน `bjt_model.py`

**Files:**
- Modify: `bjt_model.py`

**Interfaces:**
- Produces: `calculate_fixed_bias`, `calculate_emitter_bias`, `calculate_voltage_divider_bias`, `calculate_bjt_dc` ตาม signature ด้านบน

- [ ] **Step 1: ย้ายโค้ด Divider เดิมไปเป็น `calculate_voltage_divider_bias(vcc, r1, r2, rc, re, beta, vbe)`**

คงลำดับเดิมทั้งหมด: แปลง kΩ → ตรวจ `r1/r2/rc > 0`, `re >= 0`, `vcc > 0`, `beta > 0` → Thevenin → IB → cutoff → IC/IE/VC/VE/VCE → region → `independent_ic_ma` สูตรเดิม

- [ ] **Step 2: เพิ่ม `_build_result(...)` สำหรับสร้าง dict ชุดเดียวกัน**

พารามิเตอร์ที่ต้องใช้: `vcc, beta, rc, re, ib, vbe, vb_cutoff, independent_ic`
- ถ้า `ib <= 0` → คืน cutoff dict (ใช้ `vb_cutoff`)
- ถ้าไม่ใช่ → คำนวณ IC/IE/VC/VE/VCE, ตรวจ `vce < 0.2`, คืน dict 10 คีย์
- ถ้า `independent_ic is None` → ใช้ `ic` (สำหรับ Fixed/Emitter)

- [ ] **Step 3: เพิ่ม `calculate_fixed_bias`**

```python
rb = rb * 1000
rc = rc * 1000
if rb <= 0: raise ValueError("ค่า RB ต้องมากกว่า 0")
# ... ตรวจ VCC, RC, beta ...
ib = (vcc - vbe) / rb
return _build_result(vcc, beta, rc, 0.0, ib, vbe, vb_cutoff=vcc, independent_ic=None)
```

- [ ] **Step 4: เพิ่ม `calculate_emitter_bias`**

```python
rb = rb * 1000
re = re * 1000
rc = rc * 1000
if rb <= 0: raise ValueError("ค่า RB ต้องมากกว่า 0")
if re <= 0: raise ValueError("ค่า RE ต้องมากกว่า 0")
# ... ตรวจ VCC, RC, beta ...
ib = (vcc - vbe) / (rb + (beta + 1) * re)
return _build_result(vcc, beta, rc, re, ib, vbe, vb_cutoff=vcc, independent_ic=None)
```

- [ ] **Step 5: เพิ่ม dispatcher `calculate_bjt_dc`**

```python
def calculate_bjt_dc(vcc, r1, r2, rc, re, beta, vbe, mode="divider", rb=None):
    if mode == "fixed":
        if rb is None: raise ValueError("กรุณากรอกค่า RB")
        return calculate_fixed_bias(vcc, rb, rc, beta, vbe)
    if mode == "emitter":
        if rb is None: raise ValueError("กรุณากรอกค่า RB")
        return calculate_emitter_bias(vcc, rb, re, rc, beta, vbe)
    if mode == "divider":
        return calculate_voltage_divider_bias(vcc, r1, r2, rc, re, beta, vbe)
    raise ValueError("โหมดไม่ถูกต้อง")
```

- [ ] **Step 6: ตรวจ regression ด้วย test เดิม**

Run: `python -m unittest discover`
Expected: `Ran 4 tests ... OK`

- [ ] **Step 7: ตรวจค่า Divider ตรงเดิม (ไม่เพิ่ม unittest)**

Run:
```powershell
python -c "from bjt_model import calculate_bjt_dc; r=calculate_bjt_dc(12,82,22,2.2,1,100,0.7); print(r['region'], r['ib_ua'], r['ic_ma'], r['vce_v'])"
```
Expected: `Active 15.53... 1.55... 7.01...`

- [ ] **Step 8: Commit**

```bash
git add bjt_model.py
git commit -m "feat: add fixed and emitter bias calculations"
```

---

### Task 2: อัปเดต `app.py`

**Files:**
- Modify: `app.py`

**Interfaces:**
- Consumes: `calculate_bjt_dc(..., mode=..., rb=...)`

- [ ] **Step 1: อ่าน `mode` และ `rb` จากฟอร์ม**

```python
mode = request.form.get("mode", "divider")
rb_raw = request.form.get("rb", "")
rb = float(rb_raw) if rb_raw not in ("", None) else None
```

- [ ] **Step 2: เรียก dispatcher พร้อม keyword**

```python
result = calculate_bjt_dc(vcc, r1, r2, rc, re, beta, vbe, mode=mode, rb=rb)
```

- [ ] **Step 3: เก็บค่าฟอร์มเพื่อให้ dropdown/อินพุตคงอยู่หลัง POST**

```python
form_data = request.form.to_dict()
```

- [ ] **Step 4: ตรวจด้วย Flask test client (ไม่ใช่ unittest ใหม่)**

Run:
```powershell
python -c "from app import app; c=app.test_client(); r=c.post('/', data={'mode':'fixed','vcc':'12','rb':'470','rc':'2.2','beta':'100','vbe':'0.7'}); print(r.status_code, 'Active' in r.data.decode())"
```
Expected: `200 True`

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: pass bias mode and RB from form"
```

---

### Task 3: อัปเดต `templates/index.html`

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: เพิ่ม dropdown โหมดที่หัวคอลัมน์ Inputs**

```html
<select name="mode" id="mode" class="w-full border p-2 rounded">
  <option value="divider" {% if (form.mode or 'divider') == 'divider' %}selected{% endif %}>Voltage Divider Bias</option>
  <option value="fixed" {% if form.mode == 'fixed' %}selected{% endif %}>Fixed Bias</option>
  <option value="emitter" {% if form.mode == 'emitter' %}selected{% endif %}>Emitter Bias</option>
</select>
```

- [ ] **Step 2: ติด `data-mode` ให้อินพุตตามตาราง**

- `RB` (default `470`) → `data-mode="fixed emitter"`
- `RE` → `data-mode="emitter divider"`
- `R1`, `R2` → `data-mode="divider"`
- `VCC`, `RC`, `Beta`, `VBE` → แสดงทุกโหมด (ไม่ต้องมี `data-mode`)

- [ ] **Step 3: เพิ่ม JS ซ่อน/แสดงอินพุตตามโหมด**

```js
const modeSelect = document.getElementById('mode');
function applyMode() {
  const mode = modeSelect.value;
  document.querySelectorAll('[data-mode]').forEach(el => {
    el.classList.toggle('hidden', !el.dataset.mode.split(' ').includes(mode));
  });
  document.querySelectorAll('[data-circuit]').forEach(el => {
    el.classList.toggle('hidden', el.dataset.circuit !== mode);
  });
}
modeSelect.addEventListener('change', applyMode);
applyMode();
```

- [ ] **Step 4: เก็บ SVG Divider เดิมไว้ใน `data-circuit="divider"` และเพิ่มอีก 2 วงจร**

- `data-circuit="fixed"`: VCC ด้านบน → RB ลงมาที่ Base, RC ลงมาที่ Collector, Q1 NPN, Emitter ต่อลง Ground ตรง (ไม่มี RE)
- `data-circuit="emitter"`: เหมือน Fixed แต่มี RE ระหว่าง Emitter กับ Ground
- ป้ายค่าทุกวงจรใช้ `data-bind="vcc|rb|r1|r2|rc|re|beta"` แทน id เฉพาะ

- [ ] **Step 5: แทน `updateSvg` เดิมด้วย `refreshLabels`**

```js
const labelMap = {
  vcc: v => `Vcc = ${v} V`,
  rb:  v => `RB = ${v} kΩ`,
  r1:  v => `R1 = ${v} kΩ`,
  r2:  v => `R2 = ${v} kΩ`,
  rc:  v => `RC = ${v} kΩ`,
  re:  v => `RE = ${v} kΩ`,
  beta:v => `Q1 NPN (β = ${v})`,
};
function refreshLabels() {
  document.querySelectorAll('[data-bind]').forEach(el => {
    const input = document.getElementById(el.dataset.bind);
    if (input) el.textContent = labelMap[el.dataset.bind](input.value);
  });
}
document.querySelectorAll('input').forEach(i => i.addEventListener('input', refreshLabels));
modeSelect.addEventListener('change', refreshLabels);
refreshLabels();
```

- [ ] **Step 6: เพิ่ม error block และแสดงชื่อโหมดในคอลัมน์ Results**

```html
{% if error %}
<div class="bg-red-50 border border-red-200 text-red-800 p-3 rounded text-sm">{{ error }}</div>
{% endif %}
```

- [ ] **Step 7: ตรวจว่า Divider เดิมยังแสดงผลเหมือนเดิม**

Run: เปิด `http://127.0.0.1:5000` → เลือก Voltage Divider Bias → กดคำนวณ
Expected: ตารางเดิม VB=2.27, VE=1.57, VC=8.58, VCE=7.01, IB=15.53, IC=1.55, IE=1.57

- [ ] **Step 8: Commit**

```bash
git add templates/index.html
git commit -m "feat: add bias mode selector and three circuit diagrams"
```

---

### Task 4: ตรวจรับผ่าน Browser ด้วยตารางของผู้ใช้

**Files:** ไม่มี (verification only)

- [ ] **Step 1: รันเซิร์ฟเวอร์**

Run: `python app.py`
Open: `http://127.0.0.1:5000`

- [ ] **Step 2: Divider regression**

ใส่ VCC=12, R1=82, R2=22, RC=2.2, RE=1.0, β=100, VBE=0.7
Expected: `Active`, IB=15.53 µA, IC=1.55 mA, IE=1.57 mA, VB=2.27 V, VE=1.57 V, VC=8.58 V, VCE=7.01 V

- [ ] **Step 3: Fixed Bias sanity check**

ใส่ VCC=12, RB=470, RC=2.2, β=100, VBE=0.7
Expected (ประมาณ): IB≈24.04 µA, IC≈2.40 mA, IE≈2.43 mA, VE=0 V, VB=0.70 V, VC=VCE≈6.71 V

- [ ] **Step 4: Emitter Bias sanity check**

ใส่ VCC=12, RB=470, RE=1.0, RC=2.2, β=100, VBE=0.7
Expected (ประมาณ): IB≈19.79 µA, IC≈1.98 mA, IE≈2.00 mA, VE≈2.00 V, VB≈2.70 V, VC≈7.65 V, VCE≈5.65 V

- [ ] **Step 5: เทียบกับตารางจริงของผู้ใช้**

กรอกค่าตามใบงาน/ตารางของผู้ใช้ทีละแถว แล้วเทียบผลทุกคอลัมน์
หากไม่ตรง ให้รายงานค่า expected vs actual ก่อนแก้

## Out of Scope

- ไม่เพิ่ม unittest ใหม่ (ตามคำสั่งผู้ใช้)
- ไม่แก้ `electrical.py`, `static/*`
- ไม่ทำ AC/transient analysis

## จุดที่ต้องยืนยันก่อนลงโค้ด

1. **RC ยังเป็นอินพุตร่วมทุกโหมด** (จำเป็นสำหรับ VC/VCE) — ตารางระบุเฉพาะ "อินพุตเพิ่ม" จึงตีความว่า RC เป็นอินพุตพื้นฐานเดิม
2. ค่า default ของ RB = 470 kΩ และ RE = 1.0 kΩ ใช้ได้หรือไม่
3. สูตรทั้งสามตรงกับใบงาน/ตารางของผู้ใช้หรือไม่ (โดยเฉพาะ Emitter Bias ที่ใช้ `RB + (β+1)RE`)
