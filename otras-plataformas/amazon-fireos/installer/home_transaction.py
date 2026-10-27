"""Explicit, reversible Fire OS accessibility activation. No launcher is disabled.

This prepares the existing Android implementation; it does not prove boot or Home on Fire TV.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import re

SERVICE = 'tv.lightos/tv.lightos.HorizonService'
STARTUP = 'content://tv.lightos.fire.startup'


class HomeError(RuntimeError):
    pass


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def write(path, value, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dest = path if exclusive else path.with_suffix(path.suffix + '.tmp')
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC), 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(value, f, indent=2)
    if not exclusive:
        os.replace(dest, path)


def startup(a, optional=False):
    try:
        raw = a.shell('content','call','--uri',STARTUP,'--method','status')
    except Exception:
        if optional:
            return None  # Legacy Android APK has no Fire-specific runtime.
        raise
    revision = re.search(r'\brevision=(\d+)\b', raw)
    flags = {k: re.search(r'\b'+k+r'=(true|false)\b', raw) for k in ('boot','home')}
    if not revision or revision[1] != '1' or not all(flags.values()):
        if optional:
            return None
        raise HomeError('Fire startup provider response missing or unsupported')
    return {k: v[1] == 'true' for k,v in flags.items()}


def setstartup(a, flags):
    a.shell('content','call','--uri',STARTUP,'--method','configure',
            '--extra','boot:b:'+str(flags['boot']).lower(),'--extra','home:b:'+str(flags['home']).lower())
    if startup(a) != flags:
        raise HomeError('Fire startup policy did not read back')


def identity(a):
    if 'amazon.hardware.fire_tv' not in a.shell('pm', 'list', 'features'):
        raise HomeError('Not an Android-based Fire TV; Vega cannot use this procedure')
    values = {k: a.shell('getprop', k) for k in ('ro.product.model', 'ro.build.fingerprint', 'ro.serialno', 'ro.build.version.sdk')}
    if not all(values.values()) or int(values['ro.build.version.sdk']) < 26:
        raise HomeError('Unknown device identity or unsupported Fire OS')
    # Retain a stable hash, never publish the hardware serial.
    values['ro.serialno'] = fingerprint(values['ro.serialno'])
    return values


def setting(a, key):
    return a.shell('settings', 'get', 'secure', key)


def services(value):
    return [s for s in value.split(':') if s and s != 'null']


def setvalue(a, key, value):
    if value == 'null':
        a.shell('settings', 'delete', 'secure', key)
    else:
        a.shell('settings', 'put', 'secure', key, value)
    if setting(a, key) != value:
        raise HomeError('Setting did not read back: ' + key)


def plan(a, path):
    ident = identity(a)
    if 'package:' not in a.shell('pm', 'path', 'tv.lightos'):
        raise HomeError('Install the APK before preparing Home activation')
    policy = startup(a, optional=True)
    if policy is None:
        raise HomeError('Install the FireOS-specific APK first; the legacy Android APK cannot provide the new startup/restore policy')
    p = {'schema': 1, 'identity': ident, 'service': SERVICE, 'nonce': secrets.token_hex(16),
         'services': setting(a, 'enabled_accessibility_services'),
         'enabled': setting(a, 'accessibility_enabled'), 'status': 'planned',
         'startup': policy,
         'physical_tests': {k: 'experimental' for k in 'BCDE'}}
    write(path, p, exclusive=True)
    return fingerprint(p)[:24]


def load(a, path, token):
    p = json.loads(Path(path).read_text())
    if not secrets.compare_digest(str(token or ''), fingerprint(p)[:24]):
        raise HomeError('Provide --approve TOKEN from this immutable Home plan')
    if p.get('schema') != 1 or p.get('service') != SERVICE or identity(a) != p['identity']:
        raise HomeError('Plan identity/firmware differs; stop for review')
    return p


def activate(a, path, token):
    p = load(a, path, token)
    if p.get('startup') is None:
        raise HomeError('Legacy plan cannot activate reliable boot policy; prepare a new FireOS-specific plan')
    journal = Path(str(path) + '.transaction.json')
    if journal.exists():
        raise HomeError('Activation already attempted; restore/review before retrying')
    if setting(a, 'enabled_accessibility_services') != p['services'] or setting(a, 'accessibility_enabled') != p['enabled']:
        raise HomeError('Accessibility changed after planning')
    if p.get('startup') is not None and startup(a) != p['startup']:
        raise HomeError('Fire startup preferences changed after planning')
    current = services(p['services'])
    if SERVICE not in current:
        current.append(SERVICE)
    write(journal, {'status': 'applying'}, exclusive=True)
    try:
        setvalue(a, 'enabled_accessibility_services', ':'.join(current))
        setvalue(a, 'accessibility_enabled', '1')
        if p.get('startup') is not None:
            setstartup(a, {'boot': True, 'home': True})
        # Readback proves only settings, not that the OEM bound/delivered accessibility events.
        write(journal, {'status': 'implemented-unverified-on-tv'})
    except Exception as exc:
        try:
            restore(a, path, token)
        except Exception as rollback:
            write(journal, {'status': 'restore-required', 'error': str(exc), 'rollback_error': str(rollback)})
        raise


def restore(a, path, token):
    p = load(a, path, token)
    journal = Path(str(path) + '.transaction.json')
    if not journal.exists():
        raise HomeError('No activation transaction to restore')
    if p.get('startup') is not None:
        setstartup(a, p['startup'])
    current = services(setting(a, 'enabled_accessibility_services'))
    # Remove only what we added. Preserve services enabled by the owner after activation.
    if SERVICE not in services(p['services']):
        current = [s for s in current if s != SERVICE]
    desired = ':'.join(current)
    if current == services(p['services']):
        desired = p['services']  # Preserve absent/null versus empty original settings.
    setvalue(a, 'enabled_accessibility_services', desired)
    if not current:
        setvalue(a, 'accessibility_enabled', p['enabled'])
    write(journal, {'status': 'restored'})
