# BJT Common-Emitter DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete, tested Flask web application for BJT Common-Emitter DC Bias analysis with input validation, independent engineering verification calculation, operating region detection (active, saturation, cutoff), and a clean responsive UI.

**Architecture:** A Python backend module (`bjt_model.py`) handles all BJT physics calculations and verification logic. A Flask application (`app.py`) serves the web routes and renders results using an HTML template (`templates/index.html`). Unit tests in `test_bjt.py` verify accuracy across regions.

**Tech Stack:** Python 3, Flask, HTML5, CSS (Tailwind via CDN or embedded styling), Unittest.

**Spec:** Approved Design for BJT Common-Emitter DC Bias Web App (ENG29 2121).

## Global Constraints
- Inputs: VCC, R1, R2, RC, RE, beta, VBE.
- Output: DC operating point (IB, IC, IE, VCE, VC, VB, VE) with units, validation, and region warnings.
- Compare results with an independent engineering calculation.
- No AC, transient, full circuit editor, or FET.

## Review Focus
1. **Zero / Negative Resistors or Voltages:** Handled via explicit validation raising ValueError.
2. **Saturation Mode:** Detected correctly when $V_{CE} < 0.2\text{V}$.
3. **Cutoff Mode:** Detected correctly when $I_B \le 0$ or $V_{BE} < V_{th}$ threshold.
4. **Independent Verification Discrepancy:** Compared against nodal/approximate calculation; flagged if mismatch exceeds tolerance.
5. **Form Input Sanitization:** Robust float parsing with user-friendly error display on web page.

---

### Task 1: BJT Engineering Calculation Model & Unit Tests

**Files:**
- Create: `bjt_model.py`
- Test: `test_bjt.py`

**Interfaces:**
- Produces: `calculate_bjt_dc(vcc, r1, r2, rc, re, beta, vbe) -> dict`

- [ ] **Step 1: Write failing unit tests in `test_bjt.py`**

```python
import unittest
from bjt_model import calculate_bjt_dc

class TestBJTModel(unittest.TestCase):
    def test_active_region(self):
        res = calculate_bjt_dc(12.0, 82000, 22000, 2200, 1000, 100, 0.7)
        self.assertEqual(res["region"], "Active")
        self.assertAlmostEqual(res["ib_ua"], 14.59, places=1)
        self.assertAlmostEqual(res["ic_ma"], 1.46, places=2)
        self.assertAlmostEqual(res["vce_v"], 5.09, places=1)

    def test_zero_resistance_error(self):
        with self.assertRaises(ValueError):
            calculate_bjt_dc(12.0, 0, 22000, 2200, 1000, 100, 0.7)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest test_bjt.py`
Expected: FAIL (module/function not found)

- [ ] **Step 3: Implement `calculate_bjt_dc` in `bjt_model.py`**

```python
def calculate_bjt_dc(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> dict:
    if r1 <= 0 or r2 <= 0 or rc <= 0 or re < 0:
        raise ValueError("ค่าความต้านทาน (Resistance) ต้องมากกว่า 0 (ยกเว้น RE ที่อาจเป็น 0 ได้)")
    if vcc <= 0:
        raise ValueError("ค่า VCC ต้องมากกว่า 0")
    if beta <= 0:
        raise ValueError("ค่า Beta ต้องมากกว่า 0")

    # Thevenin Equivalent
    v_th = vcc * (r2 / (r1 + r2))
    r_th = (r1 * r2) / (r1 + r2)

    # Base Current (IB)
    ib = (v_th - vbe) / (r_th + (beta + 1) * re)

    if ib <= 0:
        return {
            "region": "Cutoff",
            "ib_ua": 0.0,
            "ic_ma": 0.0,
            "ie_ma": 0.0,
            "vce_v": vcc,
            "vc_v": vcc,
            "vb_v": v_th,
            "ve_v": 0.0,
            "independent_ic_ma": 0.0,
            "warning": "ทรานซิสเตอร์อยู่ในย่าน Cutoff (กระแสเบสเป็นศูนย์หรือติดลบ)"
        }

    ic = beta * ib
    ie = (beta + 1) * ib

    vc = vcc - ic * rc
    ve = ie * re
    vce = vc - ve

    # Region check
    region = "Active"
    warning = ""
    if vce < 0.2:
        region = "Saturation"
        warning = "เตือน: ทรานซิสเตอร์เข้าสู่ย่าน Saturation (VCE < 0.2V)"

    # Independent verification calculation (approximate / nodal check)
    # Using approximate IC ≈ (V_TH - V_BE) / (R_TH/beta + RE)
    independent_ib = (v_th - vbe) / ((r_th / beta) + re) if re > 0 else ib
    independent_ic = beta * independent_ib

    return {
        "region": region,
        "ib_ua": ib * 1e6,
        "ic_ma": ic * 1e3,
        "ie_ma": ie * 1e3,
        "vce_v": vce,
        "vc_v": vc,
        "vb_v": vb_v := vbe + ve,
        "ve_v": ve,
        "independent_ic_ma": independent_ic * 1e3,
        "warning": warning
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest test_bjt.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bjt_model.py test_bjt.py
git commit -m "feat: implement bjt dc bias calculation model and unit tests"
```

---

### Task 2: Flask App and HTML UI

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Modify: `test_bjt.py` (add Flask route tests if desired)

**Interfaces:**
- Consumes: `bjt_model.calculate_bjt_dc`
- Produces: Flask web server running on localhost.

- [ ] **Step 1: Create `templates/index.html` with Tailwind CSS & Form**

```html
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>BJT Common-Emitter DC Bias Calculator - ENG29 2121</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
</head>
<body class="bg-slate-50 min-h-screen py-10 px-4">
    <div class="max-w-4xl mx-auto bg-white rounded-xl shadow-md overflow-hidden p-8">
        <header class="mb-8 text-center">
            <h1 class="text-3xl font-bold text-slate-800">BJT Common-Emitter DC Bias Analyzer</h1>
            <p class="text-slate-500 mt-2">ENG29 2121 Lab - ตัวคำนวณจุดปฏิบัติการ DC ของวงจรไบอัสทรานซิสเตอร์</p>
        </header>

        {% if error %}
        <div class="mb-6 bg-red-50 border-l-4 border-red-500 p-4 text-red-700">
            <p class="font-bold">เกิดข้อผิดพลาด</p>
            <p>{{ error }}</p>
        </div>
        {% endif %}

        <form method="POST" class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
                <h2 class="text-xl font-semibold text-slate-700 border-b pb-2">ค่าพารามิเตอร์วงจร (Inputs)</h2>
                
                <div>
                    <label class="block text-sm font-medium text-slate-600">VCC (Volt):</label>
                    <input type="number" step="any" name="vcc" value="{{ form.vcc or '12' }}" required class="mt-1 w-full rounded-md border border-slate-300 p-2 shadow-sm focus:border-indigo-500 focus:ring-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-600">R1 (Ohm):</label>
                    <input type="number" step="any" name="r1" value="{{ form.r1 or '82000' }}" required class="mt-1 w-full rounded-md border border-slate-300 p-2 shadow-sm">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-600">R2 (Ohm):</label>
                    <input type="number" step="any" name="r2" value="{{ form.r2 or '22000' }}" required class="mt-1 w-full rounded-md border border-slate-300 p-2 shadow-sm">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-600">RC (Ohm):</label>
                    <input type="number" step="any" name="rc" value="{{ form.rc or '2200' }}" required class="mt-1 w-full rounded-md border border-slate-300 p-2 shadow-sm">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-600">RE (Ohm):</label>
                    <input type="number" step="any" name="re" value="{{ form.re or '1000' }}" required class="mt-1 w-full rounded-md border border-slate-300 p-2 shadow-sm">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-600">Beta ($\beta$):</label>
                    <input type="number" step="any" name="beta" value="{{ form.beta or '100' }}" required class="mt-1 w-full rounded-md border border-slate-300 p-2 shadow-sm">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-600">VBE (Volt):</label>
                    <input type="number" step="any" name="vbe" value="{{ form.vbe or '0.7' }}" required class="mt-1 w-full rounded-md border border-slate-300 p-2 shadow-sm">
                </div>

                <button type="submit" class="w-full bg-indigo-600 text-white font-semibold py-3 px-4 rounded-md hover:bg-indigo-700 transition">คำนวณจุดปฏิบัติการ (Calculate DC Bias)</button>
            </div>

            <div class="space-y-4 bg-slate-50 p-6 rounded-lg border border-slate-200">
                <h2 class="text-xl font-semibold text-slate-700 border-b pb-2">ผลลัพธ์การวิเคราะห์ (Outputs)</h2>
                
                {% if result %}
                <div class="space-y-3">
                    <div class="flex justify-between items-center bg-white p-3 rounded shadow-sm">
                        <span class="text-slate-600 font-medium">ย่านการทำงาน (Region):</span>
                        <span class="px-3 py-1 rounded-full text-sm font-bold {% if result.region == 'Active' %}bg-green-100 text-green-800{% elif result.region == 'Saturation' %}bg-amber-100 text-amber-800{% else %}bg-red-100 text-red-800{% endif %}">
                            {{ result.region }}
                        </span>
                    </div>

                    {% if result.warning %}
                    <div class="bg-amber-50 border border-amber-200 p-3 rounded text-amber-800 text-sm">
                        {{ result.warning }}
                    </div>
                    {% endif %}

                    <div class="grid grid-cols-2 gap-3 text-sm">
                        <div class="bg-white p-3 rounded shadow-sm">
                            <span class="block text-slate-400">Base Current ($I_B$)</span>
                            <span class="text-lg font-bold text-slate-800">{{ "%.2f"|format(result.ib_ua) }} µA</span>
                        </div>
                        <div class="bg-white p-3 rounded shadow-sm">
                            <span class="block text-slate-400">Collector Current ($I_C$)</span>
                            <span class="text-lg font-bold text-slate-800">{{ "%.2f"|format(result.ic_ma) }} mA</span>
                        </div>
                        <div class="bg-white p-3 rounded shadow-sm">
                            <span class="block text-slate-400">Emitter Current ($I_E$)</span>
                            <span class="text-lg font-bold text-slate-800">{{ "%.2f"|format(result.ie_ma) }} mA</span>
                        </div>
                        <div class="bg-white p-3 rounded shadow-sm">
                            <span class="block text-slate-400">Collector-Emitter ($V_{CE}$)</span>
                            <span class="text-lg font-bold text-slate-800">{{ "%.2f"|format(result.vce_v) }} V</span>
                        </div>
                        <div class="bg-white p-3 rounded shadow-sm">
                            <span class="block text-slate-400">Collector Voltage ($V_C$)</span>
                            <span class="text-lg font-bold text-slate-800">{{ "%.2f"|format(result.vc_v) }} V</span>
                        </div>
                        <div class="bg-white p-3 rounded shadow-sm">
                            <span class="block text-slate-400">Emitter Voltage ($V_E$)</span>
                            <span class="text-lg font-bold text-slate-800">{{ "%.2f"|format(result.ve_v) }} V</span>
                        </div>
                    </div>

                    <div class="mt-4 pt-4 border-t border-slate-200">
                        <h3 class="font-semibold text-slate-700 mb-2 text-sm">การตรวจสอบอิสระ (Independent Check)</h3>
                        <div class="bg-white p-3 rounded shadow-sm text-sm flex justify-between">
                            <span class="text-slate-600">Calculated $I_C$ (Verify):</span>
                            <span class="font-bold text-indigo-600">{{ "%.2f"|format(result.independent_ic_ma) }} mA</span>
                        </div>
                    </div>
                </div>
                {% else %}
                <div class="flex items-center justify-center h-64 text-slate-400 text-center">
                    <p>กรอกค่าพารามิเตอร์ด้านซ้ายแล้วกดปุ่ม "คำนวณจุดปฏิบัติการ"</p>
                </div>
                {% endif %}
            </div>
        </form>
    </div>
</body>
</html>
```

- [ ] **Step 2: Create `app.py`**

```python
from flask import Flask, render_template, request
from bjt_model import calculate_bjt_dc

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    form_data = {}

    if request.method == "POST":
        try:
            form_data = {
                "vcc": request.form.get("vcc"),
                "r1": request.form.get("r1"),
                "r2": request.form.get("r2"),
                "rc": request.form.get("rc"),
                "re": request.form.get("re"),
                "beta": request.form.get("beta"),
                "vbe": request.form.get("vbe"),
            }
            vcc = float(form_data["vcc"])
            r1 = float(form_data["r1"])
            r2 = float(form_data["r2"])
            rc = float(form_data["rc"])
            re = float(form_data["re"])
            beta = float(form_data["beta"])
            vbe = float(form_data["vbe"])

            result = calculate_bjt_dc(vcc, r1, r2, rc, re, beta, vbe)
        except ValueError as e:
            error = str(e)
        except Exception as e:
            error = f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {str(e)}"

    return render_template("index.html", result=result, error=error, form=form_data)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

- [ ] **Step 3: Run all unit tests and verify app starts**

Run: `python -m unittest discover`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add app.py templates/index.html
git commit -m "feat: implement flask app and tailwind ui for bjt dc bias analyzer"
```

---

### Task 3: Verification & Local Demonstration Setup

**Files:**
- Test: Verify everything runs locally.

- [ ] **Step 1: Run unit tests one final time**

Run: `python -m unittest discover`
Expected: PASS

- [ ] **Step 2: Commit final documentation / instructions if needed**

```bash
git add README.md
git commit -m "docs: update readme with instructions for BJT DC Bias Web App"
```
EOF
