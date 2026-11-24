/* Display solver data only: no circuit solver or placeholder waveform here. */
(() => {
    'use strict';
    const form = document.getElementById('bias-form');
    const analysis = document.getElementById('analysis');
    const mode = document.getElementById('mode');
    const status = document.getElementById('run-status');
    const button = document.getElementById('run-button');
    const names = {divider: 'Voltage Divider Bias', fixed: 'Fixed Bias', emitter: 'Emitter Bias'};
    const numericLabels = {vcc: 'Vcc', r1: 'R1', r2: 'R2', rb: 'RB', rc: 'RC', re: 'RE'};

    function applyMode() {
        const analytical = analysis.value === 'analytical';
        for (const option of mode.options) option.disabled = !analytical && option.value !== 'divider';
        if (!analytical) mode.value = 'divider';
        document.querySelectorAll('[data-mode], [data-analysis]').forEach(element => {
            const modeMatch = !element.dataset.mode || element.dataset.mode.split(' ').includes(mode.value);
            const analysisMatch = !element.dataset.analysis || element.dataset.analysis.split(' ').includes(analysis.value);
            const visible = modeMatch && analysisMatch;
            element.hidden = !visible;
            element.querySelectorAll('input,select').forEach(input => { input.disabled = !visible; });
        });
        document.querySelectorAll('[data-circuit]').forEach(element => {
            element.classList.toggle('hidden', element.dataset.circuit !== (analytical ? mode.value : 'ce'));
        });
        document.getElementById('mode-label').textContent = names[mode.value];
        button.textContent = analytical ? 'Calculate Analytical DC' : 'Run Simulation';
        document.querySelectorAll('[data-bind]').forEach(element => {
            const key = element.dataset.bind;
            const value = document.getElementById(key).value;
            element.textContent = key === 'beta' ? `Q1 NPN (β = ${value})` :
                `${numericLabels[key]} = ${value} ${key === 'vcc' ? 'V' : 'kΩ'}`;
        });
    }

    function markStale() {
        document.querySelectorAll('.run-content').forEach(element => { element.hidden = true; });
        const error = document.getElementById('error-message');
        if (error) error.hidden = true;
        status.className = 'status stale';
        status.textContent = 'Inputs changed · กรุณารันใหม่';
    }

    form.addEventListener('input', () => { applyMode(); markStale(); });
    form.addEventListener('change', () => { applyMode(); markStale(); });
    form.addEventListener('submit', () => {
        status.className = 'status running';
        status.textContent = 'Running · กำลังคำนวณ…';
        document.querySelectorAll('.run-content').forEach(element => { element.hidden = true; });
        button.disabled = true;
        button.textContent = 'Running…';
    });
    window.addEventListener('pageshow', () => { button.disabled = false; applyMode(); });
    applyMode();

    const dataElement = document.getElementById('simulation-data');
    if (!dataElement) return;
    const result = JSON.parse(dataElement.textContent);
    document.getElementById('download-json').addEventListener('click', () => {
        const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], {type: 'application/json'}));
        const link = document.createElement('a');
        link.href = url;
        link.download = `ngspice-${result.analysis}-${result.run_id.slice(0, 12)}.json`;
        link.click();
        URL.revokeObjectURL(url);
    });

    const ns = 'http://www.w3.org/2000/svg';
    function node(svg, tag, attributes, text) {
        const element = document.createElementNS(ns, tag);
        for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
        if (text !== undefined) element.textContent = text;
        svg.append(element);
        return element;
    }
    const tickLabel = value => {
        if (value === 0) return '0';
        return Math.abs(value) < .001 || Math.abs(value) >= 10000 ? value.toExponential(0) : Number(value.toPrecision(3)).toString();
    };

    function draw(id, x, traces, xLabel, yLabel, log = false) {
        const svg = document.getElementById(id);
        const width = Math.max(300, Math.round(svg.getBoundingClientRect().width));
        const height = 290, left = 66, right = 24, top = 26, bottom = 60;
        svg.replaceChildren();
        svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
        svg.dataset.points = String(x.length);
        svg.dataset.runId = result.run_id;
        const tx = value => log ? Math.log10(value) : value;
        const minX = tx(x[0]), maxX = tx(x[x.length - 1]);
        const ys = traces.flatMap(trace => trace.values);
        let minY = Math.min(...ys), maxY = Math.max(...ys);
        const pad = (maxY - minY) * .12 || .01;
        minY -= pad; maxY += pad;
        const px = value => left + (tx(value) - minX) / (maxX - minX) * (width - left - right);
        const py = value => height - bottom - (value - minY) / (maxY - minY) * (height - top - bottom);
        for (let i = 0; i <= 4; i++) {
            const y = minY + (maxY - minY) * i / 4;
            node(svg, 'line', {x1: left, x2: width-right, y1: py(y), y2: py(y), stroke: '#dce5ed'});
            node(svg, 'text', {x: left-10, y: py(y)+4, 'text-anchor': 'end', class: 'chart-tick'}, tickLabel(y));
            const scaleX = minX + (maxX - minX) * i / 4;
            const rawX = log ? 10**scaleX : scaleX;
            node(svg, 'text', {x: px(rawX), y: height-bottom+24, 'text-anchor': 'middle', class: 'chart-tick'}, tickLabel(rawX));
        }
        node(svg, 'line', {x1: left, x2: width-right, y1: height-bottom, y2: height-bottom, stroke: '#7c8fa1'});
        node(svg, 'text', {x: width/2, y: height-12, 'text-anchor': 'middle', class: 'chart-axis-label'}, xLabel);
        node(svg, 'text', {x: left, y: 16, class: 'chart-axis-label'}, yLabel);
        for (const trace of traces) {
            const segments = [[]];
            trace.values.forEach((value, index) => {
                if (trace.wrapped && index > 0 && Math.abs(value - trace.values[index-1]) > 180) segments.push([]);
                segments.at(-1).push({value, index});
            });
            for (const segment of segments) {
                const points = segment.map(({value, index}) => `${px(x[index]).toFixed(2)},${py(value).toFixed(2)}`).join(' ');
                const line = node(svg, 'polyline', {points, class: 'chart-line', stroke: trace.color,
                    'stroke-dasharray': trace.dashed ? '7 4' : 'none', 'data-trace': trace.name,
                    'data-start-index': segment[0].index, 'data-end-index': segment.at(-1).index});
                node(line, 'title', {}, `${trace.name}: ${segment.length} actual solver samples`);
            }
        }
    }

    function renderPlots() {
      if (result.analysis === 'ac') {
        const series = result.series;
        draw('gain-chart', series.frequency_hz, [{name: 'gain_db', values: series.gain_db, color: '#4d42cd'}], 'Frequency (Hz, log)', 'Gain (dB)', true);
        draw('phase-chart', series.frequency_hz, [{name: 'phase_deg', values: series.phase_deg, color: '#007568', wrapped: true}], 'Frequency (Hz, log)', 'Phase (degrees)', true);
      } else if (result.analysis === 'transient') {
        const series = result.series;
        const cutoff = series.time_s.at(-1) - 5 / result.parameters.frequency_hz;
        const start = series.time_s.findIndex(value => value >= cutoff);
        draw('transient-chart', series.time_s.slice(start).map(value => value * 1000), [
            {name: 'vin_v', values: series.vin_v.slice(start), color: '#007568'},
            {name: 'vout_v', values: series.vout_v.slice(start), color: '#a84c12', dashed: true},
        ], 'Time (ms)', 'Voltage (V)');
      }
    }
    renderPlots();
    let resizePending = false;
    window.addEventListener('resize', () => {
        if (resizePending) return;
        resizePending = true;
        requestAnimationFrame(() => { renderPlots(); resizePending = false; });
    });
})();
