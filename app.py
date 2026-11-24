from datetime import datetime, timezone
import math
from uuid import uuid4

from flask import Flask, render_template, request
from bjt_model import calculate_bjt_dc
from spice_engine import SpiceError, SpiceParameters, run_simulation

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024


def _form_float(name: str, default: float) -> float:
    raw = request.form.get(name, str(default))
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f'{name}: กรุณากรอกตัวเลข') from None
    if not math.isfinite(value):
        raise ValueError(f'{name}: ต้องเป็นตัวเลขที่มีค่าจำกัด ไม่ใช่ NaN/Infinity')
    return value


def _analytical_result(mode):
    names = ['vcc', 'rc', 'beta', 'vbe']
    if mode == 'divider':
        names += ['r1', 'r2', 're']
    else:
        names += ['rb'] + (['re'] if mode == 'emitter' else [])
    defaults = dict(vcc=12, r1=100, r2=22, rc=2.2, re=1, beta=100, vbe=.7, rb=470)
    values = {name: _form_float(name, defaults[name]) for name in names}
    for name, value in values.items():
        if value < 0 or (value == 0 and not (name == 're' and mode == 'divider')):
            raise ValueError(f'{name}: ค่าต้องมากกว่า 0')
        if value > 1_000_000:
            raise ValueError(f'{name}: ค่าสูงเกินช่วงที่รองรับ')
        minimum = 1 if name == 'beta' else 0.001
        if value != 0 and value < minimum:
            raise ValueError(f'{name}: ค่าต่ำเกินช่วงที่รองรับ (ขั้นต่ำ {minimum})')
    result = calculate_bjt_dc(
        values['vcc'], values.get('r1', 0), values.get('r2', 0),
        values['rc'], values.get('re', 0), values['beta'], values['vbe'],
        mode=mode, rb=values.get('rb'))
    if any(not math.isfinite(value) for value in result.values()
           if isinstance(value, (int, float))):
        raise ValueError('ผลคำนวณล้นช่วงตัวเลข กรุณาปรับพารามิเตอร์')
    return result


def _spice_parameters(analysis):
    mapping = dict(vcc_v=('vcc', 12), r1_kohm=('r1', 100), r2_kohm=('r2', 22),
                   rc_kohm=('rc', 2.2), re_kohm=('re', 1), rl_kohm=('rl', 10),
                   cin_uf=('cin', 10), cout_uf=('cout', 10))
    if analysis in ('ac', 'transient'):
        mapping['frequency_hz'] = ('frequency_hz', 1000)
    if analysis == 'transient':
        mapping['amplitude_mv'] = ('amplitude_mv', 10)
    if analysis == 'ac':
        mapping.update(ac_start_hz=('ac_start_hz', 10), ac_stop_hz=('ac_stop_hz', 1e8))
    parameters = SpiceParameters(**{name: _form_float(*field)
                                    for name, field in mapping.items()})
    parameters.validate()
    return parameters


def _simulation_summary(simulation):
    if simulation['analysis'] == 'dc':
        v = simulation['values']
        return {'region': ('Forward-active (junction check)' if
                           v['vc_v'] > v['vb_v'] > v['ve_v'] else
                           'Outside forward-active — inspect bias voltages')}
    s = simulation['series']
    frequency = simulation['parameters']['frequency_hz']
    if simulation['analysis'] == 'ac':
        index = min(range(len(s['frequency_hz'])),
                    key=lambda i: abs(math.log(s['frequency_hz'][i] / frequency)))
        return {name: values[index] for name, values in s.items()}
    start = s['time_s'][-1] - 5 / frequency
    indices = [i for i, time in enumerate(s['time_s']) if time >= start]
    vin = [s['vin_v'][i] for i in indices]
    vout = [s['vout_v'][i] for i in indices]
    vin_pp = max(vin) - min(vin)
    vout_pp = max(vout) - min(vout)
    return {'vin_pp_v': vin_pp, 'vout_pp_v': vout_pp,
            'gain_pp': vout_pp/vin_pp if vin_pp > 0 else None,
            'samples': len(s['time_s'])}


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    simulation = None
    summary = None
    error = None
    form_data = {'analysis': 'dc'}

    if request.method == "POST":
        form_data = request.form.to_dict()
        form_data.setdefault('analysis', 'analytical')
        try:
            analysis = form_data['analysis']
            mode = request.form.get("mode", "divider")
            if analysis not in ('analytical', 'dc', 'ac', 'transient'):
                raise ValueError('โหมดวิเคราะห์ไม่ถูกต้อง')
            if mode not in ('divider', 'fixed', 'emitter'):
                raise ValueError('โหมดไบอัสไม่ถูกต้อง')
            if analysis == 'analytical':
                result = _analytical_result(mode)
            else:
                if mode != 'divider':
                    raise ValueError('SPICE รองรับเฉพาะ CE Voltage Divider อ้างอิง')
                simulation = run_simulation(_spice_parameters(analysis), analysis,
                                            app.config.get('NGSPICE_EXECUTABLE'))
                simulation['run_id'] = uuid4().hex
                simulation['run_time'] = datetime.now(timezone.utc).isoformat()
                summary = _simulation_summary(simulation)
        except (ValueError, SpiceError, OSError, ArithmeticError) as e:
            error = str(e)
            result = simulation = summary = None

    return render_template('index.html', result=result, simulation=simulation,
                           summary=summary, error=error, form=form_data)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False)
