"""Optional, journaled Android UI preferences; never packages, audio streams or network state."""
from copy import deepcopy
import datetime as dt
import math
import secrets
from .adb import Error
from .device import identity, binding, utc
from .transactions import same_device, token, confirm

KEYS=(('system','sound_effects_enabled'),('global','window_animation_scale'),('global','transition_animation_scale'))

def state(adb):
    result={}
    for namespace in ('system','global'):
        raw=adb.shell('settings','--user','0','list',namespace)
        values=dict(line.split('=',1) for line in raw.splitlines() if '=' in line)
        for space,key in KEYS:
            if space==namespace:result[key]=values.get(key)
    return result

def valid(namespace,key,value):
    if (namespace,key) not in KEYS:raise Error('Preferencia de interfaz no permitida')
    if value is None:return
    if key=='sound_effects_enabled':
        if value not in ('0','1'):raise Error('Estado de sonidos desconocido')
    else:
        try:number=float(value)
        except (TypeError,ValueError):raise Error('Escala de animación inválida')
        if not math.isfinite(number) or not 0<=number<=10:raise Error('Escala de animación fuera de rango')

def write(adb,action,value):
    valid(action['namespace'],action['key'],value)
    args=['settings','--user','0','delete' if value is None else 'put',action['namespace'],action['key']]
    if value is not None:args.append(value)
    adb.shell(*args)

def validate(record,kind):
    if record.get('schema')!=1 or record.get('kind')!=kind or not record.get('actions'):
        raise Error('Registro de interfaz inválido')
    seen=set()
    for a in record['actions']:
        valid(a['namespace'],a['key'],a['before']);valid(a['namespace'],a['key'],a['after'])
        if a['key'] in seen:raise Error('Preferencia duplicada')
        seen.add(a['key'])
        if a['key']=='sound_effects_enabled':
            if a['after']!='0':raise Error('Solo se permite silenciar efectos de Android')
        elif a['after']!='0.5':raise Error('Solo se permite la escala opcional 0.5')

def plan(adb,store,quiet=False,faster=False):
    if not quiet and not faster:raise Error('Selecciona --quiet-system o --faster-transitions')
    device=identity(adb)
    if not device['android_tv'] or device['user']!=0 or device['sdk']<26 or not device['hardware_id']:
        raise Error('Se requiere Android TV 8+, usuario 0 e identidad fiable')
    before=state(adb);actions=[]
    for namespace,key in KEYS:
        old=before[key];valid(namespace,key,old)
        if key=='sound_effects_enabled':after='0' if quiet else old
        else:after='0.5' if faster and (old is None or float(old)>.5) else old
        if old!=after:actions.append({'namespace':namespace,'key':key,'before':old,'after':after})
    if not actions:raise Error('Las preferencias seleccionadas ya están aplicadas; no hay cambios')
    result={'schema':1,'kind':'horizonx-interface-plan','id':'interface-plan-'+secrets.token_hex(8),'created':utc(),
            'expires':(dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=30)).isoformat(),'device':device,'actions':actions,
            'note':'Silencia clics de Android y/o acorta sus transiciones. No aumenta FPS, no cambia animator_duration_scale ni silencia películas. Afecta también otras pantallas del usuario 0.'}
    store.save(result['id'],result);return result

def recover(adb,store,j):
    validate(j,'horizonx-interface-transaction');errors=[];recording=[]
    def persist():
        try:store.save(j['id'],j)
        except OSError as e:recording.append(str(e))
    for a in reversed(j['actions']):
        if not a.get('attempted'):continue
        try:
            same_device(adb,j['device']);now=state(adb)[a['key']]
            if now not in (a['before'],a['after']):raise Error('Preferencia cambiada por otra operación')
            if now!=a['before']:write(adb,a,a['before'])
            if state(adb)[a['key']]!=a['before']:raise Error('No se restauró la preferencia')
        except (Error,OSError) as e:errors.append({'key':a['key'],'error':str(e)})
        persist()
    j['errors']=errors;j['status']='recovery-required' if errors or recording else 'restored';persist()
    if recording:j['status']='recovery-required';j['recording_errors']=recording
    return j

def apply(adb,store,plan_id,approval):
    with store.lock():
        p=store.load(plan_id);validate(p,'horizonx-interface-plan');confirm(token('APLICAR-INTERFAZ',p),approval)
        if dt.datetime.fromisoformat(p['expires'])<dt.datetime.now(dt.timezone.utc):raise Error('Plan de interfaz caducado')
        same_device(adb,p['device']);before=state(adb)
        if any(before[a['key']]!=a['before'] for a in p['actions']):raise Error('Las preferencias cambiaron desde el plan')
        for name in store.records('interface-transaction-'):
            old=store.load(name)
            if old.get('plan_id')==plan_id or binding(old['device'])==binding(p['device']) and old.get('status')!='restored':
                raise Error('Hay una operación de interfaz previa; revísala antes de continuar')
        j={**deepcopy(p),'kind':'horizonx-interface-transaction','id':'interface-transaction-'+secrets.token_hex(8),'plan_id':plan_id,'status':'applying'}
        store.save(j['id'],j)
        try:
            for a in j['actions']:
                same_device(adb,j['device'])
                if state(adb)[a['key']]!=a['before']:raise Error('Conflicto de interfaz')
                a['attempted']=True;store.save(j['id'],j);write(adb,a,a['after'])
                if state(adb)[a['key']]!=a['after']:raise Error('El firmware no conservó la preferencia')
            j['status']='applied';store.save(j['id'],j);return j
        except (Error,OSError,KeyboardInterrupt) as e:
            j['error']=str(e) or 'Interrumpido';return recover(adb,store,j)

def restore(adb,store,record_id,approval):
    with store.lock():
        j=store.load(record_id);validate(j,'horizonx-interface-transaction');confirm(token('RESTAURAR-INTERFAZ',j),approval)
        return recover(adb,store,j)

def inverse(record):
    validate(record,'horizonx-interface-transaction')
    return [['settings','--user','0','delete' if a['before'] is None else 'put',a['namespace'],a['key']]
            +([] if a['before'] is None else [a['before']])
            for a in reversed(record['actions']) if a.get('attempted')]
