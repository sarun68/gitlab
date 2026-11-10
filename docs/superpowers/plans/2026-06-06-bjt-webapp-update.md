# BJT Common-Emitter UI Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the BJT DC Bias app to a 3-column UI layout, add units, and update the engineering model to handle kΩ resistor inputs.

**Architecture:** Use CSS Grid for the new 3-column layout. Update `bjt_model.py` to handle kΩ input conversion.

**Tech Stack:** Python 3, Flask, Tailwind CSS.

**Spec:** Approved Update Design for BJT Common-Emitter DC Bias Web App.

## Global Constraints
- Input resistors (R1, R2, RC, RE) are now in kΩ (must be multiplied by 1000).
- UI must follow 3-column grid structure.
- Output units must be formatted correctly.

## Review Focus
1. **kΩ Conversion Error:** Ensuring all four resistor inputs are properly scaled in the model.
2. **UI Grid Layout:** Verification of 3-column responsiveness.
3. **Unit Consistency:** Ensuring labels in UI match the new kΩ expectation.

---

### Task 1: Update Engineering Model for kΩ Inputs

**Files:**
- Modify: `bjt_model.py`
- Modify: `test_bjt.py`

**Interfaces:**
- Consumes: Inputs in kΩ.
- Produces: Correct DC bias results.

- [ ] **Step 1: Write failing test with kΩ inputs in `test_bjt.py`**

```python
import unittest
from bjt_model import calculate_bjt_dc

class TestBJTModel(unittest.TestCase):
    def test_kohms_input(self):
        # Using 82, 22, 2.2, 1.0 (kΩ equivalents)
        # Should yield same results as 82000, 22000, 2200, 1000
        res = calculate_bjt_dc(12.0, 82.0, 22.0, 2.2, 1.0, 100, 0.7)
        self.assertAlmostEqual(res["ib_ua"], 15.53, places=1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_bjt.py`
Expected: FAIL (values will differ significantly due to current code interpreting 82 as 82 ohms)

- [ ] **Step 3: Implement scaling logic in `bjt_model.py`**

```python
def calculate_bjt_dc(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> dict:
    # Scale kΩ to Ω
    r1, r2, rc, re = r1 * 1000, r2 * 1000, rc * 1000, re * 1000
    # ... rest of the existing logic ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_bjt.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add bjt_model.py test_bjt.py
git commit -m "feat: scale resistor inputs to kohms"
```

---

### Task 2: Update UI to 3-Column Layout

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: Update `templates/index.html`**

Use Tailwind's `grid-cols-3` to implement the 3-column layout. Place the inputs in the first column, an image placeholder in the second, and the result table in the third.

- [ ] **Step 2: Verify UI visually**

Run: `python app.py` and check the browser.

- [ ] **Step 3: Commit**

```bash
git add templates/index.html
git commit -m "ui: update to 3-column layout"
```
EOF
