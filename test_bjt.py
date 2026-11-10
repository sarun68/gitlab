import unittest
from bjt_model import calculate_bjt_dc

class TestBJTModel(unittest.TestCase):
    def test_active_region(self):
        res = calculate_bjt_dc(12.0, 82.0, 22.0, 2.2, 1.0, 100, 0.7)
        self.assertEqual(res["region"], "Active")
        self.assertAlmostEqual(res["ib_ua"], 15.53, places=1)
        self.assertAlmostEqual(res["ic_ma"], 1.55, places=2)
        self.assertAlmostEqual(res["vce_v"], 7.01, places=1)

    def test_kohms_input(self):
        # Using 82, 22, 2.2, 1.0 (kΩ equivalents)
        # Should yield same results as 82000, 22000, 2200, 1000
        res = calculate_bjt_dc(12.0, 82.0, 22.0, 2.2, 1.0, 100, 0.7)
        self.assertAlmostEqual(res["ib_ua"], 15.53, places=1)

if __name__ == "__main__":
    unittest.main()
