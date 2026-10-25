"""Explicit capability-checked volume UI delegation. Audio, keys and safety warnings stay native."""
import datetime as dt
import hashlib
import json
import re
import secrets
import shlex
import time
from pathlib import Path
from .adb import Error
from .device import identity,utc
from .store import load_json
from .transactions import same_device,token,confirm

COMPONENT='tv.lightos/tv.lightos.VolumeDisplayService'
KEYS=('enabled_accessibility_services','accessibility_enabled')
BASE=Path(__file__).resolve().parents[1]

def boot(adb):
    value=adb.shell('cat','/proc/sys/kernel/random/boot_id').strip()
    if not re.fullmatch('[a-f0-9-]{36}',value):raise Error('No se pudo identificar el arranque')
    return value

def artifact():
    helper=BASE/'assets/horizonx-volume-bridge.jar'
    release=load_json(BASE/'release.json')
    digest=hashlib.sha256(helper.read_bytes()).hexdigest()
    if digest!=release.get('volume_bridge_sha256'):raise Error('El puente no corresponde a la distribución')
    return helper,digest

def settings(adb):
    result={key:adb.shell('settings','--user','0','get','secure',key) for key in KEYS}
    return {key:None if value=='null' else value for key,value in result.items()}

def restricted(adb):
    raw=adb.shell('cmd','appops','get','--user','0','tv.lightos','ACCESS_RESTRICTED_SETTINGS')
    match=re.search(r'ACCESS_RESTRICTED_SETTINGS: (allow|deny|ignore|default|foreground)',raw)
    if match:return match[1]
    if 'No operations' in raw:return 'default'
    raise Error('No se pudo leer el permiso restringido de HorizonX')

def secure(adb,key,value):
    if key not in KEYS:raise Error('Preferencia no permitida')
    args=['settings','--user','0','delete' if value is None else 'put','secure',key]
    if value is not None:args.append(value)
    adb.shell(*args)

def plan(adb,store):
    helper,digest=artifact();device=identity(adb)
    if not device['android_tv'] or device['sdk']<26 or device['user']!=0 or not device.get('hardware_id'):
        raise Error('Se requiere Android TV 8+ y usuario 0; las capacidades del firmware se comprobarán antes de activar')
    before=settings(adb)
    if any(c in (before['enabled_accessibility_services'] or '').split(':') for c in (COMPONENT,'tv.lightos/.VolumeDisplayService')):
        raise Error('El servicio ya está configurado; restaura su sesión anterior antes de reactivar')
    p={'schema':1,'kind':'horizonx-volume-plan','id':'volume-plan-'+secrets.token_hex(8),'created':utc(),
       'expires':(dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=30)).isoformat(),'device':device,
       'before':before,'restricted_before':restricted(adb),'helper_sha256':digest,'boot_id':boot(adb),
       'note':'Permite una superposición sin lectura de pantalla ni captura de teclas. Comprueba las APIs de respaldo y una vista previa ADJUST_SAME antes de dejar activo el indicador multimedia; conserva el controlador original y sus avisos. Requiere reactivar desde PC después de reiniciar. Un proceso guardián queda en la TV; el PC puede desconectarse. Si sincronizaste el perfil, comprueba periódicamente que la cuenta siga presente para no mostrar su foto después de eliminarla.'}
    store.save(p['id'],p);return p

def validate(j,kind):
    if j.get('schema')!=1 or j.get('kind')!=kind or set(j.get('before',{}))!=set(KEYS):raise Error('Registro de volumen inválido')
    if j.get('restricted_before') not in ('allow','deny','ignore','default','foreground'):raise Error('Permiso original inválido')
    if not re.fullmatch('[a-f0-9-]{36}',j.get('boot_id','')):raise Error('Arranque del registro inválido')
    if kind.endswith('transaction'):
        session=j.get('session','')
        if not re.fullmatch('[a-f0-9]{32}',session) or j.get('remote')!='/data/local/tmp/horizonx-volume-'+session:raise Error('Ruta de sesión inválida')

def status(adb,j):
    validate(j,'horizonx-volume-transaction');same_device(adb,j['device'])
    if j['boot_id']!=boot(adb):
        return {'ready':False,'stopped':True,'restored':False,'different_controller_preserved':True,'restore_error':False,'log':'Nueva sesión de arranque: no se reactiva ni se sustituye el controlador actual','rebooted':True}
    ready=adb.optional('cat',j['remote']+'/ready').get('value','')
    stopped=adb.optional('cat',j['remote']+'/stopped').get('value','')
    log=adb.optional('cat',j['remote']+'/bridge.log').get('value','')
    return {'ready':ready.startswith('ACTIVE '),'stopped':stopped.startswith('STOPPED'),
            'restored':'RESTORED original volume controller' in log,
            'different_controller_preserved':'UNCHANGED another controller is current' in log,
            'restore_error':'RESTORE_REQUIRED' in log,'log':log[-2000:]}

def recover(adb,store,j):
    validate(j,'horizonx-volume-transaction');same_device(adb,j['device']);errors=[]
    if j.get('launch_attempted') and j.get('boot_id')==boot(adb):
        adb.shell('touch',j['remote']+'/stop')
        state=status(adb,j)
        for _ in range(25):
            if state['stopped'] or not state['ready'] and (state['restored'] or state['different_controller_preserved']):break
            time.sleep(.2);state=status(adb,j)
        # A failure before registration may never create ready/stopped; preserve diagnostic state.
        if not (state['stopped'] or not state['ready'] and (state['restored'] or state['different_controller_preserved'])) or state['restore_error']:
            j['status']='recovery-required';j['error']='El guardián no confirmó el cierre; no se retiran permisos con el controlador pendiente';j['bridge_status']=state
            store.save(j['id'],j);return j
        j['bridge_status']=state
    current=settings(adb)
    if j.get('permissions_attempted'):
        services=(current['enabled_accessibility_services'] or '').split(':')
        remaining=[s for s in services if s and s not in (COMPONENT,'tv.lightos/.VolumeDisplayService')]
        old=j['before']['enabled_accessibility_services']
        value=old if remaining==[s for s in (old or '').split(':') if s] else ':'.join(remaining) or None
        secure(adb,'enabled_accessibility_services',value)
        if not remaining:secure(adb,'accessibility_enabled',j['before']['accessibility_enabled'])
        mode=restricted(adb)
        if mode not in ('allow',j['restricted_before']):errors.append('El permiso restringido cambió externamente')
        elif mode!=j['restricted_before']:adb.shell('cmd','appops','set','--user','0','tv.lightos','ACCESS_RESTRICTED_SETTINGS',j['restricted_before'])
    j['status']='recovery-required' if errors else 'restored';j['errors']=errors;store.save(j['id'],j);return j

def activate(adb,store,plan_id,approval):
    with store.lock():
        p=store.load(plan_id);validate(p,'horizonx-volume-plan');confirm(token('ACTIVAR-BURBUJA',p),approval)
        if dt.datetime.fromisoformat(p['expires'])<dt.datetime.now(dt.timezone.utc):raise Error('Plan de volumen caducado')
        same_device(adb,p['device']);helper,digest=artifact()
        if digest!=p['helper_sha256'] or settings(adb)!=p['before'] or restricted(adb)!=p['restricted_before'] or boot(adb)!=p['boot_id']:raise Error('El estado cambió desde el plan')
        for name in store.records('volume-transaction-'):
            other=store.load(name)
            if other.get('device',{}).get('hardware_id')==p['device']['hardware_id'] and other.get('status')!='restored':raise Error('Hay una sesión previa; restáurala primero')
        session=secrets.token_hex(16)
        j={**p,'kind':'horizonx-volume-transaction','id':'volume-transaction-'+secrets.token_hex(8),'plan_id':plan_id,
           'session':session,'remote':'/data/local/tmp/horizonx-volume-'+session,'status':'prepared'}
        store.save(j['id'],j)
        try:
            adb.shell('mkdir','-m','700',j['remote'])
            adb.command('push',helper,j['remote']+'/bridge.jar')
            probe=adb.shell('env','CLASSPATH='+j['remote']+'/bridge.jar','app_process','/system/bin','tv.horizonx.bridge.VolumeBridge','status')
            if f"sdk={p['device']['sdk']} uid=2000 native_controller=true" not in probe:raise Error('Controlador original o API de respaldo no disponibles')
            j['permissions_attempted']=True;store.save(j['id'],j)
            adb.shell('cmd','appops','set','--user','0','tv.lightos','ACCESS_RESTRICTED_SETTINGS','allow')
            services=[s for s in (p['before']['enabled_accessibility_services'] or '').split(':') if s]
            secure(adb,'enabled_accessibility_services',':'.join([*services,COMPONENT]));secure(adb,'accessibility_enabled','1')
            time.sleep(1)
            j['launch_attempted']=True;store.save(j['id'],j)
            command=shlex.join(['env','CLASSPATH='+j['remote']+'/bridge.jar','app_process','/system/bin','tv.horizonx.bridge.VolumeBridge','start',j['remote'],session])
            # All substituted paths derive from the validated random session, never shell fragments.
            adb.shell('sh','-c','nohup '+command+' >'+shlex.quote(j['remote']+'/bridge.log')+' 2>&1 </dev/null &')
            state=status(adb,j)
            for _ in range(30):
                if state['ready'] or state['stopped']:break
                time.sleep(.2);state=status(adb,j)
            if not state['ready'] or state['restore_error']:raise Error('No se activó la burbuja: '+state['log'])
            j['status']='active';j['bridge_status']=state;store.save(j['id'],j);return j
        except (Error,OSError,KeyboardInterrupt) as error:
            j['error']=str(error) or 'Interrumpido';store.save(j['id'],j);return recover(adb,store,j)

def restore(adb,store,record_id,approval):
    with store.lock():
        j=store.load(record_id);validate(j,'horizonx-volume-transaction');confirm(token('RESTAURAR-BURBUJA',j),approval)
        return recover(adb,store,j)
