"""Explicit, reversible HOME selection, including approved Google TV UI replacement."""
from __future__ import annotations
from copy import deepcopy
import datetime as dt
import re
import secrets
import time
from .adb import COMPONENT, Error, package, help_commands
from .device import identity, home as resolve_home, package_state, utc
from .transactions import same_device, same_package, confirm, token

PACKAGE = 'tv.lightos'  # Stable installation identity, public label HorizonX.
TARGET = PACKAGE + '/' + PACKAGE + '.MainActivity'
ROLE = 'android.app.role.HOME'
# These are UI entry points, never whole packages or provisioning services.
# A differing component, even in the same package, is not eligible.
PRIORITY_HOME_UI = {
    'com.google.android.apps.tv.launcherx/com.google.android.apps.tv.launcherx.home.HomeActivity',
    'com.google.android.tungsten.setupwraith/com.google.android.tungsten.setupwraith.RecoveryActivity',
}
PRIORITY_HOME_PACKAGES = {name.split('/')[0] for name in PRIORITY_HOME_UI}


def component(value):
    if not isinstance(value, str) or not COMPONENT.fullmatch(value):
        raise Error('Componente Home inválido')
    pkg, cls = value.split('/', 1)
    package(pkg)
    return pkg + '/' + (pkg + cls if cls.startswith('.') else cls)


def candidate_details(adb):
    raw = adb.shell('cmd', 'package', 'query-activities', '--brief', '--user', '0',
                    '-a', 'android.intent.action.MAIN', '-c', 'android.intent.category.HOME')
    result = {}; priority = 0
    for line in raw.splitlines():
        match = re.search(r'\bpriority=(-?\d+)\b', line)
        if match:
            priority = int(match[1])
        if COMPONENT.fullmatch(line.strip()):
            name = component(line.strip())
            if name in result and result[name] != priority:
                raise Error('Prioridades Home contradictorias: ' + name)
            result[name] = priority
            priority = 0
    if not result:
        raise Error('No se encontraron candidatos Home')
    return result


def candidates(adb):
    return sorted(candidate_details(adb))


def component_state(adb, name):
    name = component(name); pkg, cls = name.split('/', 1)
    raw = adb.shell('dumpsys', 'package', pkg)
    match = re.search(r'(?m)^\s*Package \[' + re.escape(pkg) + r'\][^\n]*:\s*\n', raw)
    if not match:
        raise Error('Sin paquete para respaldar componente: ' + name)
    block = re.split(r'(?m)^\s*Package \[', raw[match.end():], maxsplit=1)[0]
    user = re.search(r'(?ms)^\s*User 0:[^\n]*(.*?)(?=^\s*User \d+:|\Z)', block)
    if not user:
        raise Error('Sin estado de componente para usuario 0: ' + name)
    states = []
    for label, state in (('enabledComponents', 1), ('disabledComponents', 2)):
        section = re.search(r'(?m)^([ \t]*)' + label + r':\s*\n', user[1])
        if section:
            indentation = len(section[1])
            for line in user[1][section.end():].splitlines():
                if not line.strip():
                    continue
                if len(line) - len(line.lstrip()) <= indentation:
                    break
                entry = line.strip()
                if entry in (cls, '.' + cls[len(pkg)+1:], name):
                    states.append(state)
    if len(states) > 1:
        raise Error('Estado de componente contradictorio: ' + name)
    return states[0] if states else 0


def component_inverse(change):
    name = component(change['component'])
    if name not in PRIORITY_HOME_UI or change['before'] not in (0, 1):
        raise Error('Cambio de componente Home no permitido')
    return ['pm', 'default-state' if change['before'] == 0 else 'enable', '--user', '0', name]


def package_inverse(change):
    name = package(change['name'])
    if name not in PRIORITY_HOME_PACKAGES or change['before'] not in (0, 1):
        raise Error('Paquete de sustitución Home no permitido')
    return ['pm', 'default-state' if change['before'] == 0 else 'enable', '--user', '0', name]


def holders(adb):
    raw = adb.shell('cmd', 'role', 'get-role-holders', '--user', '0', ROLE)
    result = [package(line.strip()) for line in raw.splitlines() if line.strip()]
    if len(result) > 1:
        raise Error('Más de un propietario del rol Home; requiere revisión manual')
    return result


def current(adb):
    value = resolve_home(adb, 0)
    return component(value) if value else None


def foreground(adb):
    raw = adb.shell('dumpsys', 'activity', 'activities')
    # Do not treat any historical ActivityRecord as evidence. Only the resumed user-0 entry counts.
    for key in ('topResumedActivity', 'mResumedActivity'):
        found = set()
        for line in raw.splitlines():
            if key in line:
                m = re.search(r'\bu0\s+([A-Za-z_][A-Za-z0-9_.]*/[A-Za-z0-9_.$]+)', line)
                if m:
                    found.add(component(m[1]))
        if found:
            return next(iter(found)) if len(found) == 1 else None
    return None


def status(adb):
    device = identity(adb)
    if device['user'] != 0:
        raise Error('La selección asistida de Inicio admite el usuario propietario 0')
    try:
        role = holders(adb) if device['sdk'] >= 29 else None
        role_error = None
    except Error as e:
        role, role_error = None, str(e)
    resolved = current(adb)
    details = candidate_details(adb)
    return {'schema': 1, 'kind': 'horizonx-home-status', 'created': utc(), 'device': device,
            'resolved_home': resolved, 'role_holders': role, 'role_error': role_error,
            'candidates': sorted(details), 'home_priorities': details, 'horizonx_selected': resolved == TARGET,
            'physical_home_tested': False, 'boot_tested': False}


def active_package(adb, name):
    state = package_state(adb, name, 0)
    disabled = adb.shell('pm', 'list', 'packages', '-d', '--user', '0').splitlines()
    if (not state['installed'] or state['hidden'] or state['suspended'] or state['enabled'] not in (0, 1)
            or 'package:' + name in disabled):
        raise Error('Inicio no disponible: ' + name)
    return state


def prepare(adb, store):
    s = status(adb)
    d = s['device']
    if not d['android_tv'] or not d['hardware_id'] or d['sdk'] < 29 or s['role_holders'] is None:
        raise Error('No se puede respaldar y restaurar el rol Home en este firmware. Usa la selección de Inicio en Ajustes; no se tocará ningún paquete.')
    before = s['resolved_home']
    if before == TARGET:
        raise Error('HorizonX ya está seleccionado. Usa home-status o una prueba Home aprobada; no se sobrescribirá el respaldo anterior.')
    if (not before or before not in s['candidates'] or 'FallbackHome' in before
            or before.startswith('com.google.android.tungsten.setupwraith/')):
        raise Error('No hay un Inicio anterior fiable para restaurar')
    if s['role_holders'] and s['role_holders'] != [before.split('/')[0]]:
        raise Error('El rol Home y su resolución no coinciden; revisa el firmware')
    if TARGET not in s['candidates']:
        raise Error('La aplicación instalada no anuncia el Home de HorizonX. Instala la APK actual antes de activar.')
    pm_commands = help_commands(adb.shell('cmd', 'package', 'help'))
    role_commands = help_commands(adb.shell('cmd', 'role', 'help'))
    required_roles = {'get-role-holders', 'clear-role-holders'}
    missing = sorted(required_roles - role_commands)
    if 'set-home-activity' not in pm_commands:
        missing.append('set-home-activity')
    if missing:
        raise Error('Faltan operaciones de selección/restauración Home: ' + ', '.join(missing))
    higher = [name for name, priority in s['home_priorities'].items()
              if priority > s['home_priorities'][TARGET]]
    unknown = set(higher) - PRIORITY_HOME_UI
    if unknown:
        raise Error('Inicio prioritario no verificado para sustitución reversible: ' + ', '.join(sorted(unknown)))
    changes = []
    if higher:
        if (adb.shell('settings', 'get', 'global', 'device_provisioned') != '1'
                or adb.shell('settings', 'get', 'secure', 'user_setup_complete') != '1'):
            raise Error('No se cambia un inicio prioritario durante la configuración inicial de Android')
        if not {'enable', 'disable-user', 'default-state'}.issubset(help_commands(adb.shell('pm', 'help'))):
            raise Error('Faltan operaciones reversibles de paquetes Home')
        for name in sorted(higher):
            state = component_state(adb, name)
            if state not in (0, 1):
                raise Error('El estado del componente Home cambió: ' + name)
            changes.append({'component': name, 'before': state, 'priority': s['home_priorities'][name]})
    package_names = {PACKAGE, before.split('/')[0]} | {n.split('/')[0] for n in higher}
    states = {p: active_package(adb, p) for p in package_names}
    for name in {c['component'].split('/')[0] for c in changes}:
        if states[name]['uid'] < 10000 or states[name]['shared_uid'] or states[name]['persistent']:
            raise Error('El inicio comparte identidad o persistencia de sistema; no se aparta: ' + name)
    package_changes = [{'name': name, 'before': states[name]['enabled']}
                       for name in sorted({c['component'].split('/')[0] for c in changes})]
    test_from = before
    if changes:
        answer = adb.shell('cmd', 'package', 'resolve-activity', '--brief', '--user', '0', '-a', 'android.settings.SETTINGS')
        choices = [component(line.strip()) for line in answer.splitlines() if COMPONENT.fullmatch(line.strip())]
        if len(choices) != 1 or choices[0].split('/')[0] == PACKAGE or choices[0] in higher:
            raise Error('No hay una pantalla de ajustes independiente para probar Home')
        test_from = choices[0]
    p = {'schema': 1, 'kind': 'horizonx-home-plan', 'id': 'home-plan-' + secrets.token_hex(8),
         'created': utc(), 'expires': (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=30)).isoformat(),
         'device': d, 'target': TARGET, 'before_home': before, 'before_holders': s['role_holders'],
         'candidates': s['candidates'], 'packages': states,
         'home_priorities': s['home_priorities'], 'home_components': [],
         'priority_ui_before': changes, 'home_packages': package_changes,
         'test_home_from': test_from,
         'operations': ['Abrir HorizonX y comprobar que inicia', 'Seleccionar el rol Home',
                        *['Deshabilitar para usuario 0 el paquete de inicio ' + c['name'] for c in package_changes],
                        'Abrir ' + test_from + ' y enviar Home para comprobar la actividad visible'],
         'preserved': 'Solo se apartan los paquetes de inicio enumerados; sus APK y datos se conservan. Sus pantallas, servicios y recomendaciones dejan de estar disponibles hasta restaurar. Android, Google Play y los paquetes de la marca no se alteran. Sin optimización adicional, red ni firmware.'}
    same_device(adb, d)
    store.save(p['id'], p)
    return p


def check_versions(adb, record):
    for name, before in record['packages'].items():
        attempted = any(c['name'] == name and c.get('attempted') for c in record.get('home_packages', []))
        now = package_state(adb, name, 0) if attempted else active_package(adb, name)
        if not same_package(before, now) or now['enabled'] != (3 if attempted else before['enabled']):
            raise Error('La instalación o el estado del launcher cambió: ' + name)


def verify_visible(adb, wait=time.sleep, expected=TARGET):
    for n in range(20):
        if foreground(adb) == expected:
            return True
        if n < 19:
            wait(.2)
    return False


def verify_selection(adb, expected_home, expected_holders, wait=time.sleep):
    # Role callbacks and activity resolution may settle on different system threads.
    for n in range(20):
        if holders(adb) == expected_holders and current(adb) == expected_home:
            return True
        if n < 19:
            wait(.2)
    return False


def inverse(record):
    if record.get('kind') != 'horizonx-home-transaction' or record.get('target') != TARGET:
        raise Error('Diario Home inválido')
    component(record['before_home'])
    if record['before_holders'] not in ([], [record['before_home'].split('/')[0]]):
        raise Error('Estado previo del rol inválido')
    commands = [component_inverse(c) for c in reversed(record.get('home_components', [])) if c.get('attempted')]
    commands += [package_inverse(c) for c in reversed(record.get('home_packages', [])) if c.get('attempted')]
    if record['before_holders']:
        return commands + [['cmd', 'package', 'set-home-activity', '--user', '0', record['before_home']]]
    return commands + [['cmd', 'role', 'clear-role-holders', '--user', '0', ROLE]]


def restore_internal(adb, store, j, wait=time.sleep):
    errors = []
    recording_errors = []
    def persist():
        try:
            store.save(j['id'], j)
        except OSError as e:
            recording_errors.append(str(e))
    try:
        same_device(adb, j['device'])
        # Updating/reinstalling HorizonX must not remove the way back. Only the
        # original Home's identity is needed to restore its selection.
        original = j['before_home'].split('/')[0]
        old = j['packages'][original]
        actual = package_state(adb, original, 0)
        if not actual['installed'] or actual['hidden'] or actual['suspended']:
            raise Error('Inicio original no disponible para restaurar')
        if any(actual[k] != old[k] for k in ('uid', 'signatures')):
            raise Error('La identidad del inicio original cambió; requiere revisión')
        now_role, now_home = holders(adb), current(adb)
        before_role, before_home = j['before_holders'], j['before_home']
        # Preserve changes made by the user or by another administrator.
        planned = j.get('home_components', [])
        for change in planned:
            component_inverse(change)
        # After aparting the first UI, another planned higher-priority UI may surface
        # before its own disable command (or a timeout) completes.
        package_pending = [c for c in j.get('home_packages', []) if c.get('attempted')]
        for change in j.get('home_packages', []):
            package_inverse(change)
        surfaced = ({c['component'] for c in planned} if any(c.get('attempted') for c in planned) else set())
        if package_pending:
            surfaced |= {c['component'] for c in j.get('priority_ui_before', [])}
        own_home_states = {before_home, TARGET} | surfaced
        if now_role not in (before_role, [PACKAGE]) or now_home not in own_home_states:
            raise Error('Otro inicio fue seleccionado; no se sobrescribirá la elección externa')
        pending = [c for c in j.get('home_components', []) if c.get('attempted')]
        for change in pending:
            component_inverse(change)  # Validate allowlist/state before any restore mutation.
            pkg = change['component'].split('/')[0]
            actual = active_package(adb, pkg)
            if any(actual[k] != j['packages'][pkg][k] for k in ('uid', 'signatures')):
                raise Error('La identidad del componente Home cambió: ' + pkg)
            if component_state(adb, change['component']) not in (change['before'], 2):
                raise Error('Estado externo de componente Home; requiere revisión: ' + change['component'])
        for change in package_pending:
            actual = package_state(adb, change['name'], 0)
            if not actual['installed'] or actual['hidden'] or actual['suspended']:
                raise Error('El paquete Home no está disponible para restaurar')
            if any(actual[k] != j['packages'][change['name']][k] for k in ('uid', 'signatures')):
                raise Error('La identidad del paquete Home cambió')
            if actual['enabled'] not in (change['before'], 3):
                raise Error('Estado externo de paquete Home; requiere revisión: ' + change['name'])
        if now_role != before_role or now_home != before_home or pending or package_pending:
            if not j.get('selection_attempted'):
                raise Error('No hay un cambio Home propio que restaurar')
            j['status'] = 'restoring'; persist()
            for change in reversed(pending):
                if component_state(adb, change['component']) != change['before']:
                    adb.shell(*component_inverse(change))
                if component_state(adb, change['component']) != change['before']:
                    raise Error('El componente Home no se restauró: ' + change['component'])
            for change in reversed(package_pending):
                if package_state(adb, change['name'], 0)['enabled'] != change['before']:
                    adb.shell(*package_inverse(change))
                if package_state(adb, change['name'], 0)['enabled'] != change['before']:
                    raise Error('El paquete Home no se restauró: ' + change['name'])
            if holders(adb) != before_role or current(adb) != before_home:
                if before_role:
                    adb.shell('cmd', 'package', 'set-home-activity', '--user', '0', before_home)
                else:
                    adb.shell('cmd', 'role', 'clear-role-holders', '--user', '0', ROLE)
            if not verify_selection(adb, before_home, before_role, wait):
                raise Error('El firmware no conservó el rol/resolución Home anteriores')
        j['status'] = 'restored'
    except (Error, OSError) as e:
        errors.append(str(e)); j['status'] = 'recovery-required'
    j['finished'] = utc(); j['errors'] = errors; persist()
    if recording_errors:
        j['recording_errors'] = recording_errors; j['status'] = 'recovery-required'
    return j


def activate(adb, store, plan_id, approval, wait=time.sleep):
    with store.lock():
        p = store.load(plan_id)
        if p.get('kind') != 'horizonx-home-plan' or p.get('target') != TARGET:
            raise Error('No es un plan Home válido')
        confirm(token('ACTIVAR-INICIO', p), approval)
        if dt.datetime.fromisoformat(p['expires']) < dt.datetime.now(dt.timezone.utc):
            raise Error('Plan caducado; vuelve a preparar la activación')
        same_device(adb, p['device']); check_versions(adb, p)
        if holders(adb) != p['before_holders'] or current(adb) != p['before_home'] or candidates(adb) != p['candidates']:
            raise Error('Inicio cambió desde la preparación')
        if 'home_priorities' in p and candidate_details(adb) != p['home_priorities']:
            raise Error('Las prioridades Home cambiaron desde el respaldo')
        for change in p.get('home_components', []):
            component_inverse(change)
            if component_state(adb, change['component']) != change['before']:
                raise Error('Un componente Home cambió desde el respaldo')
        for change in p.get('home_packages', []):
            package_inverse(change)
            if package_state(adb, change['name'], 0)['enabled'] != change['before']:
                raise Error('Un paquete Home cambió desde el respaldo')
        for name in store.records('home-transaction-'):
            prior = store.load(name)
            if prior.get('plan_id') == plan_id:
                raise Error('El plan ya fue utilizado')
            if prior['device']['hardware_id'] == p['device']['hardware_id'] and prior.get('status') != 'restored':
                raise Error('Hay una selección Home propia pendiente; revisa su diario antes de continuar')
        j = {**deepcopy(p), 'kind': 'horizonx-home-transaction', 'id': 'home-transaction-' + secrets.token_hex(8),
             'plan_id': plan_id, 'status': 'prepared', 'selection_attempted': False,
             'physical_home_tested': False, 'boot_tested': False}
        store.save(j['id'], j)
        try:
            j['status'] = 'starting'; store.save(j['id'], j)
            out = adb.shell('am', 'start', '-W', '--user', '0', '-n', TARGET)
            if not re.search(r'^Status:\s*ok\s*$', out, re.M) or re.search(r'^Error', out, re.M) or not verify_visible(adb, wait):
                raise Error('HorizonX no inició correctamente; el inicio predeterminado se conserva')
            same_device(adb, j['device']); check_versions(adb, j)
            if holders(adb) != j['before_holders'] or current(adb) != j['before_home']:
                raise Error('Inicio cambió durante la comprobación')
            j['selection_attempted'] = True; j['status'] = 'selecting'; store.save(j['id'], j)
            adb.shell('cmd', 'package', 'set-home-activity', '--user', '0', TARGET)
            # Android rejects shell component changes on non-test packages. This
            # explicit Home plan names the two UI packages; the optimizer stays separate.
            for change in j.get('home_components', []):
                same_device(adb, j['device'])
                if holders(adb) != [PACKAGE]:
                    raise Error('No se aparta el inicio anterior sin el rol Home de HorizonX')
                if component_state(adb, change['component']) != change['before']:
                    raise Error('El componente Home cambió durante la activación')
                change['attempted'] = True; j['status'] = 'selecting-home-components'; store.save(j['id'], j)
                adb.shell('pm', 'disable', '--user', '0', change['component'])
                if component_state(adb, change['component']) != 2:
                    raise Error('El firmware no apartó la actividad Home: ' + change['component'])
            for change in j.get('home_packages', []):
                same_device(adb, j['device'])
                if holders(adb) != [PACKAGE]:
                    raise Error('No se aparta el inicio anterior sin el rol de HorizonX')
                actual = active_package(adb, change['name'])
                if not same_package(j['packages'][change['name']], actual) or actual['enabled'] != change['before']:
                    raise Error('El paquete Home cambió durante la activación')
                change['attempted'] = True; j['status'] = 'selecting-home-packages'; store.save(j['id'], j)
                adb.shell('pm', 'disable-user', '--user', '0', change['name'])
                if package_state(adb, change['name'], 0)['enabled'] != 3:
                    raise Error('El firmware no apartó el paquete Home: ' + change['name'])
            if not verify_selection(adb, TARGET, [PACKAGE], wait):
                j['selection_observed'] = {'resolved_home': current(adb), 'role_holders': holders(adb)}
                store.save(j['id'], j)
                raise Error('El firmware no conservó la selección HorizonX: Home=' + str(j['selection_observed']['resolved_home'])
                            + '; rol=' + str(j['selection_observed']['role_holders']))
            j['status'] = 'testing-home'; store.save(j['id'], j)
            # Test from a different app. Sending Home while already in HorizonX
            # would falsely pass on firmware that ignores the key entirely.
            test_from = j.get('test_home_from', j['before_home'])
            out = adb.shell('am', 'start', '-W', '--user', '0', '-n', test_from)
            if not re.search(r'^Status:\s*ok\s*$', out, re.M) or not verify_visible(adb, wait, test_from):
                raise Error('No se pudo preparar una prueba Home independiente')
            adb.shell('input', 'keyevent', 'KEYCODE_HOME'); wait(.35)
            if not verify_visible(adb, wait) or current(adb) != TARGET or holders(adb) != [PACKAGE]:
                raise Error('Home no mostró HorizonX; la activación se revierte')
            same_device(adb, j['device']); check_versions(adb, j)
            j['status'] = 'activated'; j['finished'] = utc(); j['injected_home_verified'] = True
            store.save(j['id'], j)
            return j
        except (Error, OSError, KeyboardInterrupt) as e:
            j['error'] = str(e) or 'Interrumpido'
            try:
                store.save(j['id'], j)
            except OSError:
                pass
            result = restore_internal(adb, store, j, wait)
            result['outcome'] = 'activation-failed'
            try:
                store.save(j['id'], result)
            except OSError:
                result['status'] = 'recovery-required'
            return result


def restore(adb, store, record_id, approval):
    with store.lock():
        j = store.load(record_id)
        if j.get('kind') != 'horizonx-home-transaction' or j.get('target') != TARGET:
            raise Error('Diario Home inválido')
        confirm(token('RESTAURAR-INICIO', j), approval)
        return restore_internal(adb, store, j)
