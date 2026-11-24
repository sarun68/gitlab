"""Behavioral checks for the self-authored Lab 04 adapter."""
import math
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from spice_engine import (
    SpiceError, SpiceParameters, build_netlist, parse_raw, run_simulation,
)


REAL_RAW = """Title: example
Plotname: Operating Point
Flags: real
No. Variables: 2
No. Points: 1
Variables:
0 v(base) voltage
1 @q1[ic] current
Values:
0 1.9
 0.0012
"""
COMPLEX_RAW = """Title: example
Plotname: AC Analysis
Flags: complex
No. Variables: 2
No. Points: 2
Variables:
0 frequency frequency grid=3
1 v(out) voltage
Values:
0 10,0
 -1,2
1 1000,0
 -2,-0.1
"""


class TestParameters(unittest.TestCase):
    def test_reference_topology_and_model(self):
        netlist = build_netlist(SpiceParameters(), 'ac')
        for text in ('R1 vcc base 100000', 'RC vcc collector 2200',
                     'RE emitter 0 1000', 'Cin in base', 'Cout collector out',
                     'RL out 0 10000', 'Q1 collector base emitter PN2222',
                     '.ac dec 40 10 100000000', 'AC 1', '.model PN2222'):
            self.assertIn(text, netlist)
        self.assertNotIn('.control', netlist)
        self.assertNotIn('@q1[ic]', netlist)
        self.assertIn('@q1[ic]', build_netlist(SpiceParameters(), 'dc'))

    def test_reject_nonfinite_nonpositive_and_excessive_values(self):
        for field in ('vcc_v', 'r1_kohm', 'r2_kohm', 'rc_kohm', 're_kohm',
                      'rl_kohm', 'cin_uf', 'cout_uf', 'amplitude_mv', 'frequency_hz'):
            for value in (0, -1, float('nan'), float('inf'), 1e100):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        build_netlist(SpiceParameters(**{field: value}), 'dc')

    def test_reject_invalid_analysis_and_sweep(self):
        for params, analysis in ((SpiceParameters(), 'bogus'),
                                 (SpiceParameters(ac_start_hz=100, ac_stop_hz=10), 'ac'),
                                 (SpiceParameters(ac_points_per_decade=1.5), 'ac')):
            with self.assertRaises(ValueError):
                build_netlist(params, analysis)


class TestRawParser(unittest.TestCase):
    def test_real_values(self):
        result = parse_raw(REAL_RAW)
        self.assertEqual(result['v(base)'], [1.9])
        self.assertEqual(result['@q1[ic]'], [0.0012])

    def test_complex_values(self):
        result = parse_raw(COMPLEX_RAW)
        self.assertEqual(result['frequency'], [10+0j, 1000+0j])
        self.assertEqual(result['v(out)'], [-1+2j, -2-0.1j])

    def test_missing_truncated_nonfinite_and_wrong_index(self):
        for text in ('', REAL_RAW.replace('Values:', 'Bad:'),
                     REAL_RAW.replace(' 0.0012', ''),
                     REAL_RAW.replace('1.9', 'nan'),
                     REAL_RAW.replace('0 1.9', '8 1.9'),
                     REAL_RAW.replace('No. Variables: 2', 'No. Variables: 2000000')):
            with self.subTest(text=text):
                with self.assertRaises(SpiceError):
                    parse_raw(text)


class TestEngineFailures(unittest.TestCase):
    def assert_rejected_raw(self, analysis, raw, message):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'fake.exe'
            executable.touch()

            def execute(arguments, **kwargs):
                if '-b' in arguments:
                    (Path(kwargs['cwd']) / 'run.raw').write_text(raw, encoding='ascii')
                return subprocess.CompletedProcess(arguments, 0, 'ngspice-47', '')

            with patch('spice_engine.subprocess.run', side_effect=execute):
                with self.assertRaisesRegex(SpiceError, message):
                    run_simulation(SpiceParameters(), analysis, executable)

    def test_dc_derived_overflow_is_not_success(self):
        raw = REAL_RAW.replace('No. Variables: 2', 'No. Variables: 4').replace(
            '1 @q1[ic] current',
            '1 v(emitter) voltage\n2 v(collector) voltage\n3 i(@q1[ic]) current'
        ).replace(' 0.0012', ' -1e308\n 1e308\n 0.0012')
        self.assert_rejected_raw('dc', raw, 'nonfinite')

    def test_self_consistent_but_short_ac_is_not_success(self):
        raw = COMPLEX_RAW.replace('No. Variables: 2', 'No. Variables: 3').replace(
            '1 v(out) voltage', '1 v(in) voltage\n2 v(out) voltage'
        ).replace(' -1,2', ' 1,0\n -1,2').replace(' -2,-0.1', ' 1,0\n -2,-0.1')
        self.assert_rejected_raw('ac', raw, 'incomplete')

    def test_self_consistent_but_short_transient_is_not_success(self):
        raw = '''Title: short transient
Flags: real
No. Variables: 3
No. Points: 2
Variables:
0 time time
1 v(in) voltage
2 v(out) voltage
Values:
0 0
 0
 0
1 0.00001
 0.001
 -0.002
'''
        self.assert_rejected_raw('transient', raw, 'incomplete')

    def test_explicit_missing_engine(self):
        with self.assertRaisesRegex(SpiceError, 'executable'):
            run_simulation(SpiceParameters(), 'dc', executable='missing-spice-123.exe')

    def test_timeout_is_reported_and_process_uses_safe_arguments(self):
        with tempfile.TemporaryDirectory(prefix='spice path ') as directory:
            executable = Path(directory) / 'fake spice.exe'
            executable.touch()
            with patch('spice_engine.subprocess.run',
                       side_effect=subprocess.TimeoutExpired('fake', 20)) as process:
                with self.assertRaisesRegex(SpiceError, 'timed out'):
                    run_simulation(SpiceParameters(), 'dc', executable=executable)
                self.assertIsInstance(process.call_args.args[0], list)
                self.assertFalse(process.call_args.kwargs['shell'])
                self.assertEqual(process.call_args.kwargs['timeout'], 20)

    def test_failed_and_empty_runs_are_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / 'fake.exe'
            executable.touch()
            for code in (0, 1):
                with patch('spice_engine.subprocess.run', return_value=
                           subprocess.CompletedProcess([], code, '', 'failure')):
                    with self.assertRaises(SpiceError):
                        run_simulation(SpiceParameters(), 'dc', executable=executable)


if __name__ == '__main__':
    unittest.main()
