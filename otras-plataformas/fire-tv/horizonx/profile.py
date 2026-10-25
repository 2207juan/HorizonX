"""Optional native Google TV profile mirror. No credentials, OAuth tokens or images in releases."""
import datetime as dt
import hashlib,json,re,secrets,time
from pathlib import Path
import xml.etree.ElementTree as ET
from .adb import Error
from .device import identity,package_state,home,utc
from .transactions import token,confirm,same_device,RESTORE_COMMAND
from . import volume

NATIVE='com.google.android.apps.tv.launcherx'
CHOOSER=NATIVE+'/com.google.android.apps.tv.launcherx.profile.chooser.ProfileChooserActivity'
EMAIL=re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',re.I)

def volume_enabled(adb):
    services=(volume.settings(adb)['enabled_accessibility_services'] or '').split(':')
    return any(c in services for c in (volume.COMPONENT,'tv.lightos/.VolumeDisplayService'))

def account_hash(name):return hashlib.sha256(name.strip().lower().encode('utf-8')).hexdigest()

def account_hashes(adb):
    raw=adb.shell('dumpsys','account')
    users=re.split(r'(?m)^User UserInfo\{',raw)
    current=next((section for section in users if section.startswith('0:')),None)
    if current is None:raise Error('No se pudo identificar la lista de cuentas del usuario 0')
    return sorted({account_hash(name) for name in re.findall(r'Account \{name=([^,\n]+), type=com\.google\}',current)})

def choose_native_avatar(xml,known,selected=None):
    root=ET.fromstring(xml[xml.find('<'):]);candidates=[]
    for node in root.iter('node'):
        if node.get('package')!=NATIVE or node.get('clickable')!='true':continue
        description=node.get('content-desc','');emails=EMAIL.findall(description)
        if len(emails)!=1:continue
        hashed=account_hash(emails[0])
        if hashed not in known:continue
        bounds=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.get('bounds',''))
        if not bounds:continue
        x,y,right,bottom=map(int,bounds.groups());width=right-x;height=bottom-y
        # The public Google TV chooser uses a portrait photo with its caption underneath.
        # Unknown layouts are rejected instead of capturing an unrelated region.
        if not 64<=width<=700 or not width<=height<=width*1.7:continue
        name=description[:description.find(emails[0])].strip(' ,:;\n\t')
        if not name or len(name)>120:continue
        size=round(width*.70);offset=(width-size)//2
        candidates.append({'accountHash':hashed,'displayName':name,'crop':{'x':x+offset,'y':y+offset,'size':size},'focused':node.get('focused')=='true',
                           'current':any(s in description.lower() for s in ('cuenta actual','current account'))})
    unique={c['accountHash']:c for c in candidates}
    if selected:return unique.get(selected)
    if len(unique)==1:return next(iter(unique.values()))
    current=[c for c in unique.values() if c['current']]
    return current[0] if len(current)==1 else None

def plan(adb,store,selected=None):
    _,digest=volume.artifact();device=identity(adb)
    if not device['android_tv'] or device['sdk']<26 or device['user']!=0 or not device.get('hardware_id'):raise Error('Se requiere Android TV 8+, usuario 0')
    if volume_enabled(adb):raise Error('Pausa primero el puente con volume-restore; el selector nativo necesita una captura autorizada de UI')
    system=adb.shell('pm','list','packages','-s','--user','0',NATIVE).splitlines()
    if 'package:'+NATIVE not in system:raise Error('Este dispositivo no tiene el selector nativo Google TV compatible; no se inventará una foto')
    accounts=account_hashes(adb)
    if not accounts:raise Error('No hay cuentas de Google en el usuario actual')
    if selected and selected not in accounts:raise Error('La cuenta seleccionada no está presente')
    result={'schema':1,'kind':'horizonx-profile-plan','id':'profile-plan-'+secrets.token_hex(8),'created':utc(),
            'expires':(dt.datetime.now(dt.timezone.utc)+dt.timedelta(minutes=30)).isoformat(),'device':device,'home':home(adb,0),
            'native_before':package_state(adb,NATIVE,0),'accounts':accounts,'selected':selected,'helper_sha256':digest,
            'note':'Abre temporalmente el selector nativo Google TV y sincroniza solo el nombre y avatar de la cuenta actual. Puede habilitar temporalmente su app de inicio y devuelve exactamente su estado previo. No inicia sesión, no cambia la cuenta ni almacena credenciales. La foto es una copia privada, no una conexión OAuth en tiempo real; ejecuta otra sincronización después de cambiarla en Google.'}
    store.save(result['id'],result);return result

def validate(record,kind):
    if record.get('schema')!=1 or record.get('kind')!=kind or record.get('native_before',{}).get('name')!=NATIVE:raise Error('Registro de perfil inválido')
    if record['native_before'].get('enabled') not in RESTORE_COMMAND:raise Error('Estado nativo inválido')
    if not record.get('accounts') or not all(re.fullmatch('[a-f0-9]{64}',h) for h in record['accounts']):raise Error('Cuentas del registro inválidas')
    if kind.endswith('transaction') and not re.fullmatch('/data/local/tmp/horizonx-profile-[a-f0-9]{32}',record.get('remote','')):raise Error('Ruta de perfil inválida')

def recover(adb,store,j):
    validate(j,'horizonx-profile-transaction');same_device(adb,j['device']);errors=[]
    if j.get('enable_attempted'):
        try:
            now=package_state(adb,NATIVE,0);before=j['native_before']
            if now['enabled'] not in (before['enabled'],1):raise Error('El estado del inicio nativo cambió externamente')
            if now['enabled']!=before['enabled']:adb.shell('pm',RESTORE_COMMAND[before['enabled']],'--user','0',NATIVE)
            if package_state(adb,NATIVE,0)['enabled']!=before['enabled']:raise Error('No se restauró el estado nativo')
        except (Error,OSError) as error:errors.append(str(error))
    if home(adb,0)!=j['home']:errors.append('El Home actual difiere del respaldo')
    if not errors:
        adb.shell('input','keyevent','KEYCODE_HOME')
        # Only our random, mode-700 capture directory. No recursive deletion or untrusted paths.
        for name in ('accounts.json','metadata.json','screen.png','screen.xml','bridge.jar'):adb.optional('rm','-f',j['remote']+'/'+name)
        adb.optional('rmdir',j['remote'])
    j['errors']=errors;j['status']='recovery-required' if errors else 'synced' if j.get('photo_imported') else 'restored';store.save(j['id'],j);return j

def sync(adb,store,plan_id,approval):
    with store.lock():
        p=store.load(plan_id);validate(p,'horizonx-profile-plan');confirm(token('SINCRONIZAR-PERFIL',p),approval)
        if dt.datetime.fromisoformat(p['expires'])<dt.datetime.now(dt.timezone.utc):raise Error('Plan de perfil caducado')
        same_device(adb,p['device']);helper,digest=volume.artifact()
        if digest!=p['helper_sha256'] or package_state(adb,NATIVE,0)!=p['native_before'] or account_hashes(adb)!=p['accounts'] or home(adb,0)!=p['home']:raise Error('El estado cambió desde el plan')
        if volume_enabled(adb):raise Error('El puente de volumen se activó después del plan; páusalo primero')
        for name in store.records('profile-transaction-'):
            old=store.load(name)
            if old.get('plan_id')==plan_id:raise Error('Este plan de perfil ya se utilizó')
            if old.get('device',{}).get('hardware_id')==p['device']['hardware_id'] and old.get('status') not in ('synced','restored'):raise Error('Recupera primero la sincronización anterior')
        j={**p,'kind':'horizonx-profile-transaction','id':'profile-transaction-'+secrets.token_hex(8),'plan_id':plan_id,
           'remote':'/data/local/tmp/horizonx-profile-'+secrets.token_hex(16),'status':'prepared'};store.save(j['id'],j)
        try:
            adb.shell('mkdir','-m','700',j['remote']);adb.command('push',helper,j['remote']+'/bridge.jar')
            if p['native_before']['enabled'] not in (0,1):
                j['enable_attempted']=True;store.save(j['id'],j);adb.shell('pm','enable','--user','0',NATIVE)
            j['ui_attempted']=True;store.save(j['id'],j)
            adb.shell('am','start','-W','-n',CHOOSER,'-a','com.google.android.gms.account.ProfilePickerDelegation')
            candidate=None
            for _ in range(8):
                adb.shell('uiautomator','dump','--compressed',j['remote']+'/screen.xml')
                focused='\n'.join(line for line in adb.shell('dumpsys','window').splitlines() if 'mCurrentFocus=' in line)
                if 'profile.chooser.ProfileChooserActivity' not in focused:raise Error('El selector nativo no está visible; no se capturará otra pantalla')
                candidate=choose_native_avatar(adb.shell('cat',j['remote']+'/screen.xml'),p['accounts'],p['selected'])
                if candidate:break
                time.sleep(.4)
            if not candidate:raise Error('No se pudo identificar una foto vinculada a la cuenta actual')
            # Focus changes brightness only; never click/select a Google account or alter it.
            if not candidate['focused']:
                adb.shell('input','keyevent','KEYCODE_DPAD_UP');time.sleep(.2)
                adb.shell('uiautomator','dump','--compressed',j['remote']+'/screen.xml')
                refreshed=choose_native_avatar(adb.shell('cat',j['remote']+'/screen.xml'),p['accounts'],candidate['accountHash'])
                if refreshed:candidate=refreshed
            metadata={'schema':1,'accountHash':candidate['accountHash'],'displayName':candidate['displayName'],'source':'native-google-tv','sourcePackage':NATIVE,'crop':candidate['crop']}
            local=store.root/(j['id']+'-metadata.json');local.write_text(json.dumps(metadata,ensure_ascii=False));local.chmod(0o600)
            try:adb.command('push',local,j['remote']+'/metadata.json')
            finally:local.unlink(missing_ok=True)
            adb.shell('screencap','-p',j['remote']+'/screen.png')
            result=adb.shell('env','CLASSPATH='+j['remote']+'/bridge.jar','app_process','/system/bin','tv.horizonx.bridge.ProfileBridge','import',j['remote'])
            if 'PROFILE_IMPORTED' not in result:raise Error('No se confirmó la importación del perfil')
            j['photo_imported']=True;j['selected_account_hash']=candidate['accountHash'];store.save(j['id'],j)
        except (Error,OSError,ValueError,ET.ParseError,KeyboardInterrupt) as error:j['error']=str(error) or 'Interrumpido';store.save(j['id'],j)
        return recover(adb,store,j)

def restore_native(adb,store,record_id,approval):
    with store.lock():
        j=store.load(record_id);validate(j,'horizonx-profile-transaction');confirm(token('RECUPERAR-PERFIL-NATIVO',j),approval);return recover(adb,store,j)
