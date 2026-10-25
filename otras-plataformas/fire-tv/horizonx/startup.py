"""Optional foreground warm-start measurement; separate approval because it opens the launcher."""
import secrets
from .adb import Error
from .device import identity, utc
from .transactions import confirm, token, same_device
from .metrics import number

def plan(adb, store):
    d = identity(adb)
    if not d.get('hardware_id') or not d.get('android_tv') or d.get('user') != 0:
        raise Error('No se puede preparar la prueba para este dispositivo')
    if 'package:tv.lightos' not in adb.shell('pm','list','packages','--user','0','tv.lightos').splitlines():
        raise Error('Instala primero la aplicación cuando decidas probarla')
    p = {'schema':1,'kind':'horizonx-startup-plan','id':'startup-plan-'+secrets.token_hex(8),
         'created':utc(),'device':d,'note':'Abre HorizonX una vez, sin detener procesos. Mide apertura o reanudación; no es arranque en frío ni latencia física del mando.'}
    store.save(p['id'],p)
    return p

def measure(adb, store, plan_id, approval):
    with store.lock():
        p = store.load(plan_id)
        if p.get('kind') != 'horizonx-startup-plan':raise Error('Plan de prueba inválido')
        confirm(token('ABRIR-PARA-MEDIR',p),approval)
        same_device(adb,p['device'])
        j={**p,'kind':'horizonx-startup-measurement','id':'startup-'+secrets.token_hex(8),'status':'prepared'}
        store.save(j['id'],j)
        try:
            out=adb.shell('am','start','-W','--user','0','-n','tv.lightos/.MainActivity')
            j['status']='measured'
            j['total_time_ms']=number(r'^TotalTime:\s*(\d+)',out,int)
            j['wait_time_ms']=number(r'^WaitTime:\s*(\d+)',out,int)
            j['this_time_ms']=number(r'^ThisTime:\s*(\d+)',out,int)
            j['launch_state']=next((line.split(':',1)[1].strip() for line in out.splitlines() if line.startswith('LaunchState:')),None)
        except Error as e:
            j['status']='unavailable';j['error']=str(e)
        store.save(j['id'],j)
        return j
