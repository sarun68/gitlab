"""Run all three reference analyses and preserve reproducible evidence."""
import argparse
import json
from pathlib import Path

from spice_engine import SpiceError, SpiceParameters, run_simulation


def create_evidence(output: Path, parameters: SpiceParameters, executable=None) -> dict:
    output = Path(output)
    parameters.validate()
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    for analysis in ('dc', 'ac', 'transient'):
        folder = output / analysis
        folder.mkdir()
        try:
            result = run_simulation(parameters, analysis, executable)
        except (SpiceError, ValueError) as error:
            (folder / 'error.txt').write_text(str(error), encoding='utf-8')
            raise
        for key, filename in (('netlist', 'circuit.cir'), ('log', 'run.log'),
                              ('raw_text', 'run.raw')):
            (folder / filename).write_text(result[key], encoding='utf-8')
        summary = {key: value for key, value in result.items()
                   if key not in ('netlist', 'log', 'raw_text')}
        (folder / 'result.json').write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False),
            encoding='utf-8')
        results[analysis] = summary
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New directory for artifacts; existing paths are not overwritten')
    parser.add_argument('--executable', help='Explicit ngspice executable path')
    parser.add_argument('--amplitude-mv', type=float, default=10)
    parser.add_argument('--frequency-hz', type=float, default=1000)
    parser.add_argument('--re-kohm', type=float, default=1)
    args = parser.parse_args()
    parameters = SpiceParameters(amplitude_mv=args.amplitude_mv,
                                 frequency_hz=args.frequency_hz, re_kohm=args.re_kohm)
    try:
        results = create_evidence(args.output, parameters, args.executable)
    except (SpiceError, ValueError, OSError) as error:
        parser.exit(1, f'Error: {error}\n')
    print('Self-authored starter; NOT instructor verified. Model: PN2222.')
    print('DC:', json.dumps(results['dc']['values']))
    for mode in ('ac', 'transient'):
        series = results[mode]['series']
        print(f'{mode}: {len(next(iter(series.values())))} data points')
    print(f'Evidence: {args.output.resolve()}')


if __name__ == '__main__':
    main()
