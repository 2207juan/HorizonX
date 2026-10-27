#!/usr/bin/env python3
"""LG installation and opt-in experimental HOME/boot integration on an ALREADY rooted TV.

No exploits, firmware changes, stock app deletion, input grabs or system partition patches.
The advanced path creates two bounded persistent Activity Manager subscriptions, based on
documented community research; command success never counts as a physical HOME test.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess
import sys

APP = 'tv.horizonx.webos'
AM = 'luna://com.webos.service.activitymanager/'
HOME_IDS = {'com.webos.app.home', 'com.webos.app.launcher', 'com.webos.app.homelauncher'}
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]


class Error(RuntimeError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def save(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2)
        return
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as f:
        os.chmod(temp, 0o600)
        json.dump(value, f, indent=2)
    os.replace(temp, path)


def parse_luna(raw):
    # SSH tty diagnostics may precede the JSON; never treat empty output/exit 0 as success.
    decoder = json.JSONDecoder()
    for pos, char in enumerate(raw):
        if char != '{':
            continue
        try:
            value, _ = decoder.raw_decode(raw[pos:])
        except ValueError:
            continue
        if isinstance(value, dict) and 'returnValue' in value:
            if value['returnValue'] is not True:
                raise Error('Luna refused operation: ' + str(value.get('errorText', value)))
            return value
    raise Error('No valid Luna response; no result can be inferred')


class TV:
    def __init__(self, host, port=22, identity=None):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.:-]*', host) or not 1 <= port <= 65535:
            raise Error('Invalid SSH destination')
        self.host = host
        self.prefix = ['ssh', '-tt', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                       '-o', 'ConnectTimeout=8', '-p', str(port)]
        if identity:
            self.prefix += ['-i', str(identity)]
        self.prefix += ['root@' + host]

    def shell(self, *args):
        r = subprocess.run(self.prefix + [shlex.join(args)], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=20)
        if r.returncode:
            raise Error(r.stderr.strip() or r.stdout.strip() or f'SSH exited {r.returncode}')
        return r.stdout.strip()

    def luna(self, uri, params):
        return parse_luna(self.shell('luna-send', '-n', '1', '-f', uri, json.dumps(params, separators=(',', ':'))))

    def identity(self):
        if self.shell('id', '-u') != '0':
            raise Error('Advanced integration requires existing root; Developer Mode is not root')
        v = self.luna('luna://com.webos.service.tv.systemproperty/getSystemInfo',
                      {'keys': ['modelName', 'firmwareVersion']})
        if not v.get('modelName') or not v.get('firmwareVersion'):
            raise Error('Model and complete firmware must be known')
        # Bind rollback to the TV, not just an IP which could be reassigned to another device.
        mac = ''
        for path in ('/sys/class/net/eth0/address', '/sys/class/net/wlan0/address'):
            try:
                candidate = self.shell('cat', path).lower()
                if re.fullmatch(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}', candidate) and candidate != '00:00:00:00:00:00':
                    mac = candidate
                    break
            except Error:
                pass
        if not mac:
            raise Error('Cannot establish a stable device identity; stop before HOME changes')
        return {'model': v['modelName'], 'firmware': v['firmwareVersion'], 'device': digest(mac)}

    def activities(self):
        result = self.luna(AM + 'list', {'details': True})
        if not isinstance(result.get('activities'), list):
            raise Error('Unsupported Activity Manager list response')
        return result['activities']

    def default_home(self):
        result = self.luna('luna://com.webos.settingsservice/getSystemSettings',
                           {'category': 'general', 'keys': ['defaultApps']})
        value = result.get('settings', {}).get('defaultApps', {}).get('home')
        if not isinstance(value, str) or not value:
            raise Error('Native defaultApps.home cannot be read; native integration refused')
        return value

    def native_capability(self):
        compositor = self.shell('cat', '/usr/lib/qml/KeyFilters/systemUi.js')
        if 'launchDefaultApp' not in compositor:
            raise Error('This compositor does not demonstrate native category routing')
        found = False
        for prefix in ('/media/developer/apps/usr/palm/applications/', '/media/cryptofs/apps/usr/palm/applications/'):
            try:
                info = json.loads(self.shell('cat', prefix + APP + '/appinfo.json'))
                found = info.get('id') == APP and 'home' in info.get('appCategory', [])
                if found:
                    break
            except (Error, ValueError):
                pass
        if not found:
            raise Error('Installed manifest must explicitly declare appCategory home')
        return digest(compositor)

    def set_home(self, target):
        self.luna('luna://com.webos.applicationManager/setDefaultApp', {'category': 'home', 'appId': target})
        if self.default_home() != target:
            raise Error('Native HOME assignment did not read back')


def activity(kind, home):
    trigger = ({'method': 'luna://com.webos.bootManager/getBootStatus', 'params': {'subscribe': True},
                'where': {'prop': ['signals', 'core-boot-done'], 'op': '=', 'val': True}} if kind == 'boot' else
               {'method': 'luna://com.webos.applicationManager/getForegroundAppInfo', 'params': {'subscribe': True},
                'where': {'prop': ['appId'], 'op': '=', 'val': home}})
    return {'name': APP + '.' + kind, 'description': 'HorizonX experimental ' + kind,
            'type': {'foreground': True, 'persist': True, 'continuous': True}, 'trigger': trigger,
            'callback': {'method': 'luna://com.webos.applicationManager/launch', 'params': {'id': APP}}}


def plan(tv, directory, native=False):
    directory = Path(directory)
    if directory.exists():
        raise Error('Choose a new backup directory; an original backup must never be overwritten')
    identity = tv.identity()
    apps = tv.luna('luna://com.webos.applicationManager/listApps', {}).get('apps')
    if not isinstance(apps, list) or APP not in [a.get('id') for a in apps]:
        raise Error('Install the LG HorizonX IPK first; Android APK does not work on webOS')
    listed = tv.luna('luna://tv.horizonx.webos.service/listApps', {}).get('apps')
    if not isinstance(listed, list) or APP not in [a.get('id') for a in listed]:
        raise Error('HorizonX discovery service is not authorized. Review Homebrew service elevation separately; no automatic escalation')
    fg = tv.luna('luna://com.webos.applicationManager/getForegroundAppInfo', {'subscribe': True})
    home = fg.get('appId')
    if home not in HOME_IDS or home not in [a.get('id') for a in apps]:
        raise Error('Open the ORIGINAL fullscreen LG Home first. Overlay Home/webOS 5 needs a separately reviewed Input Hook profile')
    boot = tv.luna('luna://com.webos.bootManager/getBootStatus', {'subscribe': True})
    if boot.get('signals', {}).get('core-boot-done') is not True:
        raise Error('Unsupported boot-status schema; cannot safely arm the boot trigger')
    activities = tv.activities()
    if any(a.get('name', '').startswith(APP + '.') for a in activities):
        raise Error('Existing HorizonX activities found; restore their original transaction first')
    native_state = None
    if native:
        if tv.default_home() != home:
            raise Error('Observed LG Home differs from defaultApps.home; stop for review')
        native_state = {'original': home, 'compositor': tv.native_capability()}
    result = {'schema': 1, 'identity': identity, 'home': home,
              'activities': [activity('boot', home), activity('home', home)], 'nonce': secrets.token_hex(16),
              'native': native_state,
              'status': 'experimental', 'requires_physical_tests': ['A', 'B', 'C', 'D', 'E']}
    directory.mkdir(parents=True, mode=0o700)
    save(directory / 'snapshot.json', {'identity': identity, 'apps': apps, 'activities': activities, 'native': native_state}, exclusive=True)
    save(directory / 'plan.json', result, exclusive=True)
    return digest(result)[:24]


def load(directory, token):
    directory = Path(directory)
    p = json.loads((directory / 'plan.json').read_text())
    snap = json.loads((directory / 'snapshot.json').read_text())
    if not secrets.compare_digest(str(token or ''), digest(p)[:24]):
        raise Error('Explicit --approve TOKEN from this plan is required')
    if p.get('schema') != 1 or p.get('identity') != snap.get('identity') or p.get('home') not in HOME_IDS or p.get('native') != snap.get('native'):
        raise Error('Invalid or changed plan/snapshot')
    if p.get('activities') != [activity('boot', p['home']), activity('home', p['home'])]:
        raise Error('Plan may only create the two bounded HorizonX subscriptions')
    if p.get('native') and (p['native'].get('original') != p['home'] or not re.fullmatch(r'[a-f0-9]{64}', p['native'].get('compositor', ''))):
        raise Error('Invalid native Home snapshot')
    return p, snap


def owns(actual, expected):
    # Runtime list entries contain additional metadata; compare the defining fields exactly.
    return all(actual.get(k) == expected[k] for k in ('name', 'trigger', 'callback'))


def remove_owned(tv, p):
    expected = {a['name']: a for a in p['activities']}
    for a in tv.activities():
        if a.get('name') not in expected:
            continue
        if not owns(a, expected[a['name']]) or not isinstance(a.get('activityId'), int):
            raise Error('Activity changed outside HorizonX; refusing to cancel somebody else\'s activity')
        tv.luna(AM + 'cancel', {'activityId': a['activityId']})
    if any(a.get('name') in expected for a in tv.activities()):
        raise Error('Cancellation not confirmed; restoration remains pending')


def activate(tv, directory, token):
    p, _ = load(directory, token)
    if tv.identity() != p['identity']:
        raise Error('Device or firmware changed since backup')
    journal = Path(directory) / 'transaction.json'
    if journal.exists():
        raise Error('Transaction already attempted. Inspect/restore it before creating a new plan')
    if any(a.get('name', '').startswith(APP + '.') for a in tv.activities()):
        raise Error('HorizonX activity state changed since plan')
    apps = tv.luna('luna://com.webos.applicationManager/listApps', {}).get('apps', [])
    if APP not in [a.get('id') for a in apps]:
        raise Error('HorizonX was removed after planning; activation refused')
    if p.get('native'):
        if tv.default_home() != p['native']['original'] or tv.native_capability() != p['native']['compositor']:
            raise Error('Native HOME or compositor changed since backup')
    state = {'status': 'applying', 'created': [], 'identity': p['identity']}
    save(journal, state, exclusive=True)  # Persist intent BEFORE the first remote write.
    try:
        for a in p['activities']:
            reply = tv.luna(AM + 'create', {'activity': a, 'start': True, 'replace': False})
            if not isinstance(reply.get('activityId'), int):
                raise Error('No activity ID; remote outcome uncertain')
            state['created'].append(reply['activityId'])
            save(journal, state)
        current = tv.activities()
        if not all(any(owns(a, expected) for a in current) for expected in p['activities']):
            raise Error('Activity readback does not match plan')
        if p.get('native'):
            tv.set_home(APP)
        state['status'] = 'implemented-unverified-on-tv'
    except Exception as exc:
        state['error'] = str(exc)
        try:
            # Reconcile by exact name AND content even if a create response was lost.
            remove_owned(tv, p)
            restore_native(tv, p)
            state['status'] = 'rolled-back'
        except Exception as rollback:
            state['status'] = 'restore-required'
            state['rollback_error'] = str(rollback)
        save(journal, state)
        raise Error('Activation failed; ' + state['status'] + ': ' + str(exc)) from exc
    save(journal, state)
    return state


def restore(tv, directory, token):
    p, _ = load(directory, token)
    if tv.identity() != p['identity']:
        raise Error('Device/firmware differs from original; recovery needs review')
    journal = Path(directory) / 'transaction.json'
    if not journal.exists():
        raise Error('No activation transaction exists for this plan')
    remove_owned(tv, p)
    restore_native(tv, p)
    save(journal, {'status': 'restored', 'identity': p['identity']})
    # LG's original app was never removed/modified. User now tests its physical Home button.


def restore_native(tv, p):
    if not p.get('native'):
        return
    current = tv.default_home()
    if current not in (APP, p['native']['original']):
        raise Error('Native Home was assigned to a third app; restore needs review')
    if current != p['native']['original']:
        tv.set_home(p['native']['original'])


def cli_tool(tool):
    local = ROOT / '.toolchain/webos-tools/node_modules/@webos-tools/cli/bin' / (tool + '.js')
    return [str(ROOT / '.toolchain/node/bin/node'), str(local)] if local.exists() else [tool]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['install', 'launch', 'status', 'home-plan', 'home-activate', 'home-restore'])
    p.add_argument('--device', help='Already paired ares device name (standard install)')
    p.add_argument('--ipk', type=Path)
    p.add_argument('--host', help='Already trusted SSH root host (advanced integration)')
    p.add_argument('--port', type=int, default=22)
    p.add_argument('--identity', type=Path)
    p.add_argument('--backup', type=Path)
    p.add_argument('--approve')
    p.add_argument('--native-home', action='store_true', help='Plan the native home category as well (experimental, strict probes)')
    args = p.parse_args()
    try:
        if args.command in ('install', 'launch'):
            if not args.device or not re.fullmatch(r'[A-Za-z0-9_.-]+', args.device):
                raise Error('Provide a paired --device NAME from ares-setup-device')
            if args.command == 'install':
                if not args.ipk or not args.ipk.is_file() or args.ipk.suffix != '.ipk':
                    raise Error('Provide the LG --ipk FILE')
                subprocess.run(cli_tool('ares-install') + ['--device', args.device, str(args.ipk.resolve())], check=True)
                print('Package installation finished. Boot and HOME have NOT been changed.')
            else:
                subprocess.run(cli_tool('ares-launch') + ['--device', args.device, APP], check=True)
            return 0
        if not args.host:
            raise Error('--host required. No discovery or automatic connection is performed')
        tv = TV(args.host, args.port, args.identity)
        if args.command == 'status':
            print(json.dumps({'identity': tv.identity(), 'activities': tv.activities()}, indent=2))
        else:
            if not args.backup:
                raise Error('--backup DIRECTORY required')
            if args.command == 'home-plan':
                token = plan(tv, args.backup, native=args.native_home)
                print('Read-only plan saved. Experimental; not a verified main Home. Approval token: ' + token)
            elif args.command == 'home-activate':
                print(json.dumps(activate(tv, args.backup, args.approve), indent=2))
                print('Subscriptions installed; physical tests A–E remain pending. Do not call this verified support.')
            else:
                restore(tv, args.backup, args.approve)
                print('HorizonX subscriptions removed. Check the original LG Home with the physical remote.')
        return 0
    except (Error, OSError, ValueError, subprocess.SubprocessError) as exc:
        print('HorizonX: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
