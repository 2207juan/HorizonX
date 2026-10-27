#!/usr/bin/env python3
"""Print honest A–E integration status. Offline; does not scan or connect to TVs."""
import argparse
import json
from pathlib import Path

VALID = {'verificada en televisión real', 'verificada en emulador', 'implementada pero sin probar', 'experimental', 'no compatible'}


def validate(data):
    for name, platform in data['platforms'].items():
        if set(platform['checks']) != set('ABCDE'):
            raise ValueError(name + ': missing independent acceptance checks')
        for kind, check in platform['checks'].items():
            if check['status'] not in VALID:
                raise ValueError(name + ': unknown status')
            if check['status'].startswith('verificada') and not check.get('evidence'):
                raise ValueError(name + '/' + kind + ': verification requires evidence')
        if platform.get('objective_complete') and not all(
                c['status'] == 'verificada en televisión real' for c in platform['checks'].values()):
            raise ValueError(name + ': package/browser/emulator success is not a verified main Home')


def main():
    data = json.loads((Path(__file__).parent / 'research/home-support.json').read_text())
    validate(data)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--platform', choices=list(data['platforms']))
    args = p.parse_args()
    for name, platform in data['platforms'].items():
        if args.platform and name != args.platform:
            continue
        print('\n' + name + ' — objetivo de inicio principal: pendiente')
        for kind, check in platform['checks'].items():
            print('  ' + kind + ': ' + check['status'])
        for limit in platform['limits']:
            print('  - ' + limit)


if __name__ == '__main__':
    main()
