"""Self-authored Lab 04 ngspice adapter; no Flask or third-party dependencies."""
from dataclasses import asdict, dataclass, fields
import hashlib
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


MODEL_PATH = Path(__file__).resolve().parent / 'models' / 'PN2222.mod'
MODEL_SOURCE = ('https://github.com/ngspice/ngspice/blob/master/'
                'examples/tclspice/tcl-testbench1/PN2222.mod')


class SpiceError(RuntimeError):
    """A missing solver, unsuccessful run, or invalid solver output."""


@dataclass(frozen=True)
class SpiceParameters:
    vcc_v: float = 12
    r1_kohm: float = 100
    r2_kohm: float = 22
    rc_kohm: float = 2.2
    re_kohm: float = 1
    rl_kohm: float = 10
    cin_uf: float = 10
    cout_uf: float = 10
    amplitude_mv: float = 10
    frequency_hz: float = 1000
    ac_start_hz: float = 10
    ac_stop_hz: float = 100_000_000
    ac_points_per_decade: int = 40
    transient_periods: int = 20

    def validate(self):
        limits = {
            'vcc_v': (0.1, 100), 'amplitude_mv': (0.001, 5000),
            'frequency_hz': (1, 1_000_000), 'ac_start_hz': (0.1, 1e9),
            'ac_stop_hz': (0.1, 1e9), 'ac_points_per_decade': (10, 200),
            'transient_periods': (10, 100),
        }
        for field in fields(self):
            value = getattr(self, field.name)
            lower, upper = limits.get(field.name, (0.001, 1_000_000))
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or not lower <= value <= upper):
                raise ValueError(f'{field.name} must be finite and within [{lower}, {upper}]')
        if self.ac_start_hz >= self.ac_stop_hz:
            raise ValueError('ac_start_hz must be less than ac_stop_hz')
        for name in ('ac_points_per_decade', 'transient_periods'):
            if int(getattr(self, name)) != getattr(self, name):
                raise ValueError(f'{name} must be an integer')


def build_netlist(parameters: SpiceParameters, analysis: str) -> str:
    parameters.validate()
    if analysis not in ('dc', 'ac', 'transient'):
        raise ValueError('analysis must be dc, ac, or transient')
    p = parameters
    fmt = lambda value: format(value, '.12g')
    step = 1 / p.frequency_hz / 100
    directives = {
        'dc': '.op',
        'ac': (f'.ac dec {int(p.ac_points_per_decade)} '
               f'{fmt(p.ac_start_hz)} {fmt(p.ac_stop_hz)}'),
        'transient': (f'.tran {fmt(step)} '
                      f'{fmt(p.transient_periods / p.frequency_hz)} 0 {fmt(step)}'),
    }
    return '\n'.join([
        'Lab04 self-authored CE reference - not instructor verified',
        '* Vin: generator before Cin. Vout: RL node after Cout. No bypass capacitor.',
        '.temp 27',
        f'VCC vcc 0 DC {fmt(p.vcc_v)}',
        f'VIN in 0 DC 0 AC 1 SIN(0 {fmt(p.amplitude_mv / 1000)} {fmt(p.frequency_hz)})',
        f'R1 vcc base {fmt(p.r1_kohm * 1000)}',
        f'R2 base 0 {fmt(p.r2_kohm * 1000)}',
        f'RC vcc collector {fmt(p.rc_kohm * 1000)}',
        f'RE emitter 0 {fmt(p.re_kohm * 1000)}',
        f'RL out 0 {fmt(p.rl_kohm * 1000)}',
        f'Cin in base {fmt(p.cin_uf * 1e-6)}',
        f'Cout collector out {fmt(p.cout_uf * 1e-6)}',
        'Q1 collector base emitter PN2222',
        MODEL_PATH.read_text(encoding='ascii').strip(),
        '.save v(base) v(emitter) v(collector) v(in) v(out)'
        + (' @q1[ic]' if analysis == 'dc' else ''),
        directives[analysis], '.end', '',
    ])


def parse_raw(text: str) -> dict:
    """Parse a single real/complex ASCII ngspice plot with strict shape checks."""
    try:
        lines = text.splitlines()
        header = {}
        variable_line = lines.index('Variables:')
        values_line = lines.index('Values:')
        for line in lines[:variable_line]:
            if ':' in line:
                key, value = line.split(':', 1)
                header[key.strip()] = value.strip()
        count = int(header['No. Variables'])
        points = int(header['No. Points'])
        if not 1 <= count <= 100 or not 1 <= points <= 100_000:
            raise ValueError('unsupported raw dimensions')
        flags = header['Flags'].split()
        if 'complex' not in flags and 'real' not in flags:
            raise ValueError('unsupported raw flags')
        names = []
        for index, line in enumerate(lines[variable_line + 1:values_line]):
            tokens = line.split()
            if len(tokens) < 3 or int(tokens[0]) != index:
                raise ValueError('invalid variable definition')
            names.append(tokens[1].lower())
        if len(names) != count or len(set(names)) != count:
            raise ValueError('invalid variable count/names')
        data = [line.strip() for line in lines[values_line + 1:] if line.strip()]
        if len(data) != count * points:
            raise ValueError('truncated or extra raw values')
        result = {name: [] for name in names}
        for point in range(points):
            for index, name in enumerate(names):
                token = data[point * count + index]
                if index == 0:
                    point_index, token = token.split(maxsplit=1)
                    if int(point_index) != point:
                        raise ValueError('incorrect point index')
                if 'complex' in flags:
                    real, imag = token.split(',')
                    value = complex(float(real), float(imag))
                    finite = math.isfinite(value.real) and math.isfinite(value.imag)
                else:
                    value = float(token)
                    finite = math.isfinite(value)
                if not finite:
                    raise ValueError('nonfinite raw data')
                result[name].append(value)
        return result
    except (ValueError, KeyError, IndexError, OverflowError) as error:
        raise SpiceError(f'Invalid ASCII raw output: {error}') from error


def find_executable(executable=None) -> Path:
    """Respect explicit configuration; otherwise prefer the Windows console build."""
    configured = executable or os.environ.get('NGSPICE_EXECUTABLE')
    candidates = [configured] if configured else (
        ['ngspice_con.exe'] if os.name == 'nt' else ['ngspice'])
    if not configured and os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        candidates.append(Path(os.environ['LOCALAPPDATA']) /
                          'Programs/ngspice-47/Spice64/bin/ngspice_con.exe')
    for candidate in candidates:
        resolved = shutil.which(str(candidate))
        path = Path(resolved or candidate).expanduser()
        if path.is_file():
            return path.resolve()
    raise SpiceError('ngspice executable not found; configure NGSPICE_EXECUTABLE '
                     '(use ngspice_con.exe on Windows)')


def _environment(executable: Path) -> dict:
    env = os.environ.copy()
    env['SPICE_ASCIIRAWFILE'] = '1'
    resources = executable.parent.parent / 'share' / 'ngspice'
    if (resources / 'scripts' / 'spinit').is_file():
        env['SPICE_LIB_DIR'] = str(resources)
        env['SPICE_SCRIPTS'] = str(resources / 'scripts')
    return env


def _run(arguments, directory, environment):
    try:
        return subprocess.run(arguments, cwd=directory, env=environment, shell=False,
                              capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=20)
    except subprocess.TimeoutExpired as error:
        raise SpiceError('ngspice timed out after 20 seconds') from error
    except OSError as error:
        raise SpiceError(f'Could not launch ngspice executable: {error}') from error


def _extract_result(vectors: dict, analysis: str, parameters: SpiceParameters) -> dict:
    try:
        if analysis == 'dc':
            vb, ve, vc, ic = (vectors[name][0] for name in
                             ('v(base)', 'v(emitter)', 'v(collector)', 'i(@q1[ic])'))
            if any(len(values) != 1 for values in vectors.values()):
                raise ValueError('DC output must have exactly one point')
            if any(not math.isfinite(value) for value in (vb, ve, vc, ic, vc-ve)):
                raise ValueError('nonfinite derived DC result')
            return {'values': {'vb_v': vb, 've_v': ve, 'vc_v': vc,
                               'vce_v': vc-ve, 'ic_a': ic},
                    'units': {'vb_v': 'V', 've_v': 'V', 'vc_v': 'V',
                              'vce_v': 'V', 'ic_a': 'A'}}
        if analysis == 'ac':
            frequency = [v.real for v in vectors['frequency']]
            gain = [out / vin for out, vin in zip(vectors['v(out)'], vectors['v(in)'])]
            magnitude = [abs(v) for v in gain]
            if any(v <= 0 for v in magnitude):
                raise ValueError('zero AC magnitude')
            result = {'series': {'frequency_hz': frequency,
                                 'gain_v_per_v': magnitude,
                                 'gain_db': [20*math.log10(v) for v in magnitude],
                                 'phase_deg': [math.degrees(math.atan2(v.imag, v.real))
                                               for v in gain]},
                      'units': {'frequency_hz': 'Hz', 'gain_v_per_v': 'V/V',
                                'gain_db': 'dB', 'phase_deg': 'degrees'}}
            scale = frequency
        else:
            result = {'series': {'time_s': vectors['time'], 'vin_v': vectors['v(in)'],
                                 'vout_v': vectors['v(out)']},
                      'units': {'time_s': 's', 'vin_v': 'V', 'vout_v': 'V'}}
            scale = vectors['time']
        if len(scale) < 2 or any(b <= a for a, b in zip(scale, scale[1:])):
            raise ValueError('non-increasing or insufficient scale points')
        if analysis == 'ac':
            count = math.floor(parameters.ac_points_per_decade * math.log10(
                parameters.ac_stop_hz / parameters.ac_start_hz) + 1e-9) + 1
            if len(scale) != count or any(not math.isclose(value,
                    parameters.ac_start_hz * 10**(index / parameters.ac_points_per_decade),
                    rel_tol=1e-7) for index, value in enumerate(scale)):
                raise ValueError('incomplete or inconsistent AC sweep')
        elif (not math.isclose(scale[0], 0, abs_tol=1e-12)
              or not math.isclose(scale[-1],
                                  parameters.transient_periods / parameters.frequency_hz,
                                  rel_tol=1e-7, abs_tol=1e-12)):
            raise ValueError('incomplete or inconsistent transient time range')
        for values in result['series'].values():
            if any(not math.isfinite(value) for value in values):
                raise ValueError('nonfinite derived result')
        return result
    except (KeyError, IndexError, ValueError, ZeroDivisionError, TypeError) as error:
        raise SpiceError(f'Unexpected {analysis} output: {error}') from error


def run_simulation(parameters: SpiceParameters, analysis: str, executable=None) -> dict:
    """Run one analysis in isolation, returning actual outputs plus provenance."""
    netlist = build_netlist(parameters, analysis)
    engine = find_executable(executable)
    env = _environment(engine)
    with tempfile.TemporaryDirectory(prefix='lab04 spice ') as directory:
        folder = Path(directory)
        (folder / 'circuit.cir').write_text(netlist, encoding='ascii')
        process = _run([str(engine), '-b', '-o', 'run.log', '-r', 'run.raw',
                        'circuit.cir'], directory, env)
        log = process.stdout + process.stderr
        if (folder / 'run.log').is_file():
            log += (folder / 'run.log').read_text(encoding='utf-8', errors='replace')
        if process.returncode != 0:
            raise SpiceError(f'ngspice failed (exit {process.returncode}):\n{log[-4000:]}')
        if not (folder / 'run.raw').is_file():
            raise SpiceError(f'ngspice produced no raw output:\n{log[-4000:]}')
        raw_text = (folder / 'run.raw').read_text(encoding='ascii', errors='replace')
        result = _extract_result(parse_raw(raw_text), analysis, parameters)
        version = _run([str(engine), '--version'], directory, env)
        if version.returncode != 0:
            raise SpiceError('ngspice version check failed')
    result.update({
        'status': 'success', 'analysis': analysis, 'parameters': asdict(parameters),
        'engine': str(engine), 'engine_version': version.stdout.strip(),
        'model': 'PN2222', 'model_source': MODEL_SOURCE,
        'model_sha256': hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
        'instructor_verified': False, 'temperature_c': 27,
        'input_reference': 'generator node in, before Cin',
        'output_reference': 'load node out, after Cout',
        'netlist': netlist, 'log': log, 'raw_text': raw_text,
    })
    return result
