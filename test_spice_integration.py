"""Real solver checks; skipped only when the ngspice executable is absent."""
from dataclasses import replace
import math
from pathlib import Path
import tempfile
import unittest

from spice_engine import SpiceError, SpiceParameters, find_executable, run_simulation
from starter_kit import create_evidence


class TestRealSpice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.executable = find_executable()
        except SpiceError as error:
            raise unittest.SkipTest(str(error))
        cls.params = SpiceParameters()

    def run_spice(self, mode, params=None):
        return run_simulation(params or self.params, mode, self.executable)

    def test_dc_physical_ordering_and_re_change(self):
        dc = self.run_spice('dc')
        values = dc['values']
        self.assertGreater(values['vc_v'], values['vb_v'])
        self.assertGreater(values['vb_v'], values['ve_v'])
        self.assertGreater(values['ve_v'], 0)
        self.assertGreater(values['ic_a'], 0)
        self.assertAlmostEqual(values['vce_v'], values['vc_v']-values['ve_v'])
        changed = self.run_spice('dc', replace(self.params, re_kohm=2))
        self.assertLess(changed['values']['ic_a'], values['ic_a'])
        self.assertIn('PN2222', dc['netlist'])
        self.assertIn('ngspice-47', dc['engine_version'])
        self.assertNotIn('can\'t find the initialization', dc['log'])

    def test_ac_and_transient_consistency_and_source_change(self):
        ac = self.run_spice('ac')['series']
        index = min(range(len(ac['frequency_hz'])),
                    key=lambda i: abs(ac['frequency_hz'][i]-1000))
        self.assertGreater(ac['gain_v_per_v'][index], 1)
        self.assertLess(abs(abs(ac['phase_deg'][index])-180), 15)
        tran = self.run_spice('transient')['series']

        def steady(series):
            cutoff = series['time_s'][-1] - 5 / self.params.frequency_hz
            return [(i, o) for t, i, o in zip(series['time_s'], series['vin_v'],
                                            series['vout_v']) if t >= cutoff]

        pairs = steady(tran)
        amplitude = lambda numbers: (max(numbers)-min(numbers))/2
        vin = [v[0] for v in pairs]
        vout = [v[1] for v in pairs]
        gain = amplitude(vout)/amplitude(vin)
        self.assertAlmostEqual(gain/ac['gain_v_per_v'][index], 1, delta=0.05)
        self.assertLess(sum(i*o for i, o in pairs), 0)
        changed = self.run_spice('transient', replace(self.params, amplitude_mv=20))['series']
        changed_out = [v[1] for v in steady(changed)]
        self.assertAlmostEqual(amplitude(changed_out)/amplitude(vout), 2, delta=0.1)
        changed_frequency = self.run_spice('transient', replace(self.params, frequency_hz=2000))
        self.assertAlmostEqual(changed_frequency['series']['time_s'][-1],
                               tran['time_s'][-1]/2, delta=1e-8)

    def test_evidence_artifacts_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='starter evidence ') as directory:
            target = Path(directory) / 'new results'
            results = create_evidence(target, self.params, self.executable)
            self.assertEqual(set(results), {'dc', 'ac', 'transient'})
            for mode in results:
                for name in ('result.json', 'circuit.cir', 'run.log', 'run.raw'):
                    self.assertTrue((target / mode / name).is_file())
            with self.assertRaises(FileExistsError):
                create_evidence(target, self.params, self.executable)


if __name__ == '__main__':
    unittest.main()
