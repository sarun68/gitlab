"""Flask regression and real-solver integration for Lab 04."""
import json
import re
import unittest
from unittest.mock import patch

from app import app
from spice_engine import SpiceError


BASE = dict(mode='divider', vcc='12', r1='100', r2='22', rc='2.2', re='1',
            beta='100', vbe='0.7', rb='1000', rl='10', cin='10', cout='10',
            amplitude_mv='10', frequency_hz='1000', ac_start_hz='10',
            ac_stop_hz='100000000')


def payload(response):
    match = re.search(r'<script[^>]*id="simulation-data"[^>]*>(.*?)</script>',
                      response.get_data(as_text=True), re.S)
    return json.loads(match.group(1)) if match else None


class TestLab04App(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, NGSPICE_EXECUTABLE=None)
        self.client = app.test_client()

    def test_home_uses_local_assets_and_accessible_controls(self):
        response = self.client.get('/')
        text = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        for value in ('/static/app.js', '/static/style.css', 'for="analysis"',
                      'for="amplitude_mv"', 'id="run-status"', 'PN2222',
                      'not instructor-verified'):
            self.assertIn(value, text)
        self.assertNotIn('cdn.tailwindcss.com', text)

    def test_legacy_three_modes_and_missing_analysis_still_work(self):
        for mode, expected in (('divider', '1.23'), ('fixed', '1.13'), ('emitter', '1.03')):
            with self.subTest(mode=mode):
                response = self.client.post('/', data={**BASE, 'mode': mode})
                text = response.get_data(as_text=True)
                self.assertIn('Analytical', text)
                self.assertIn(expected, text)
                self.assertIn('id="analytical-results"', text)
                self.assertIsNone(payload(response))

    def test_analytical_ignores_irrelevant_hidden_values(self):
        response = self.client.post('/', data={**BASE, 'mode': 'fixed',
                                               'r1': 'not used', 're': 'not used'})
        self.assertIn('1.13', response.get_data(as_text=True))
        self.assertIn('id="analytical-results"', response.get_data(as_text=True))

    def test_dc_real_output_and_new_run_identity(self):
        first = payload(self.client.post('/', data={**BASE, 'analysis': 'dc',
                                                   'beta': 'not used', 'vbe': 'not used'}))
        self.assertIsNotNone(first)
        self.assertAlmostEqual(first['values']['ic_a'], 0.00135619456, places=9)
        self.assertEqual(first['model'], 'PN2222')
        self.assertEqual(first['status'], 'success')
        self.assertIn('ngspice-47', first['engine_version'])
        self.assertIn('Q1 collector base emitter PN2222', first['netlist'])
        second = payload(self.client.post('/', data={**BASE, 'analysis': 'dc', 're': '2'}))
        self.assertNotEqual(first['run_id'], second['run_id'])
        self.assertLess(second['values']['ic_a'], first['values']['ic_a'])

    def test_ac_and_transient_have_real_chart_series(self):
        for analysis, chart, x in (('ac', 'gain-chart', 'frequency_hz'),
                                   ('transient', 'transient-chart', 'time_s')):
            response = self.client.post('/', data={**BASE, 'analysis': analysis})
            result = payload(response)
            self.assertIsNotNone(result)
            self.assertGreater(len(result['series'][x]), 100)
            self.assertIn(f'id="{chart}"', response.get_data(as_text=True))
            self.assertIn('run_id', result)

    def test_validation_never_calls_solver_and_clears_results(self):
        for changes in ({'re': '0'}, {'vcc': 'nan'},
                        {'analysis': 'transient', 'amplitude_mv': 'inf'},
                        {'analysis': 'injected'}, {'mode': 'fixed'},
                        {'ac_start_hz': '1000', 'ac_stop_hz': '10'}):
            with self.subTest(changes=changes), patch('app.run_simulation') as engine:
                response = self.client.post('/', data={**BASE, 'analysis': 'ac', **changes})
                self.assertIn('id="error-message"', response.get_data(as_text=True))
                self.assertIsNone(payload(response))
                engine.assert_not_called()

    def test_engine_failure_after_success_has_no_stale_output(self):
        self.assertIsNotNone(payload(self.client.post('/', data={**BASE, 'analysis': 'ac'})))
        with patch('app.run_simulation', side_effect=SpiceError('test engine unavailable')):
            response = self.client.post('/', data={**BASE, 'analysis': 'ac'})
        text = response.get_data(as_text=True)
        self.assertIn('test engine unavailable', text)
        self.assertIn('id="error-message"', text)
        self.assertIsNone(payload(response))
        self.assertNotIn('id="gain-chart"', text)

    def test_nonfinite_analytical_values_and_invalid_mode_rejected(self):
        for changes in ({'beta': 'nan'}, {'vbe': '-1'}, {'mode': 'unknown'}):
            response = self.client.post('/', data={**BASE, **changes})
            self.assertIn('id="error-message"', response.get_data(as_text=True))
            self.assertNotIn('id="analytical-results"', response.get_data(as_text=True))

    def test_unsafe_tiny_analytical_values_show_error_not_http500(self):
        response = self.client.post('/', data={**BASE, 'analysis': 'analytical',
                                               'r1': '1e-200', 'r2': '1e-200', 're': '0'})
        text = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="error-message"', text)
        self.assertNotIn('id="analytical-results"', text)

    def test_initial_circuit_visibility_is_correct_without_javascript(self):
        for data, expected in ((None, 'ce'), ({**BASE, 'mode': 'fixed'}, 'fixed'),
                               ({**BASE, 'mode': 'emitter'}, 'emitter')):
            response = self.client.get('/') if data is None else self.client.post('/', data=data)
            tags = re.findall(r'<div data-circuit="([^"]+)" class="([^"]*)"',
                              response.get_data(as_text=True))
            visible = [name for name, classes in tags if 'hidden' not in classes.split()]
            self.assertEqual(visible, [expected])

    def test_blank_analytical_input_remains_blank_after_error(self):
        response = self.client.post('/', data={**BASE, 'mode': 'fixed', 'rb': ''})
        text = response.get_data(as_text=True)
        self.assertIn('id="error-message"', text)
        self.assertRegex(text, r'name="rb" id="rb" value=""')


if __name__ == '__main__':
    unittest.main()
