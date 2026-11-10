def calculate_bjt_dc(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> dict:
    # Scale kΩ to Ω
    r1, r2, rc, re = r1 * 1000, r2 * 1000, rc * 1000, re * 1000

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
    independent_ib = (v_th - vbe) / ((r_th / beta) + re) if re > 0 else ib
    independent_ic = beta * independent_ib

    return {
        "region": region,
        "ib_ua": ib * 1e6,
        "ic_ma": ic * 1e3,
        "ie_ma": ie * 1e3,
        "vce_v": vce,
        "vc_v": vc,
        "vb_v": vbe + ve,
        "ve_v": ve,
        "independent_ic_ma": independent_ic * 1e3,
        "warning": warning
    }
