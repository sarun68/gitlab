def analyze_dc(voltage_v, resistance_ohm):
    if resistance_ohm == 0:
        raise ValueError("ค่าความต้านทาน (Resistance) ต้องไม่เท่ากับ 0")
    
    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}


if __name__ == "__main__":
    try:
        # รับค่าจากผู้ใช้งาน
        v = float(input("ป้อนค่าแรงดันไฟฟ้า (Volt): "))
        r = float(input("ป้อนค่าความต้านทาน (Ohm): "))
        
        result = analyze_dc(v, r)
        print("\n--- ผลลัพธ์การคำนวณ ---")
        print(f"กระแสไฟฟ้า (Current): {result['current_a']:.2f} แอมป์ (A)")
        print(f"กำลังไฟฟ้า (Power): {result['power_w']:.2f} วัตต์ (W)")
        
    except ValueError as e:
        print(f"เกิดข้อผิดพลาด: {e}")
