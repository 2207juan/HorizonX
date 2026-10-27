"""Experimental native Home on explicitly scoped Tizen firmware with EXISTING root.

No exploit or SDK command-execution workaround. Uses a pinned, manually installed bounded
helper through trusted SSH. All Home/startup originals are journaled and restored via APIs.
"""
from pathlib import Path
import hashlib,json,os,re,secrets,shlex,subprocess

TARGET='HrznXTV001.HorizonX'
STOCK='com.samsung.tv.csfs'
KEYS=('db/appfw/home_appid','db/appfw/startup_appid','db/appfw/booting_appid_backup','db/first_screen/type')
# Firmware-specific precedents from source inspection; no HorizonX physical certification.
PROFILES={
 'frame-tizen9-2130':'T-KSU2EDUABC-0090-2130.0',
 's90d-tizen9-2130':'T-PTMDAKUC-0090-2130.0',
 'u8000f-1300.9':'T-KSU2EFAKUC-0090-1300.9',
}

class Error(RuntimeError):pass

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(p,v,exclusive=False):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p if exclusive else p.with_suffix(p.suffix+'.tmp')
 fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|(os.O_EXCL if exclusive else os.O_TRUNC),0o600)
 with os.fdopen(fd,'w') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
 if not exclusive:os.replace(tmp,p)

def validate_snapshot(v):
 if not isinstance(v,dict) or set(v)!={'home','strings','auto','boot_supported'}:raise Error('Incomplete native snapshot')
 valid=lambda x:isinstance(x,str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,160}',x)
 if not valid(v['home']) or type(v['auto']) is not int or v['auto'] not in (0,1) or type(v['boot_supported']) is not int or v['boot_supported'] not in (0,1):raise Error('Invalid native Home values')
 if not isinstance(v['strings'],dict) or set(v['strings'])!=set(KEYS) or not all(valid(x) for x in v['strings'].values()):raise Error('Missing typed startup values')
 return v

def parse(raw):
 values={}
 for line in raw.splitlines():
  if '=' not in line:continue
  k,v=line.split('=',1)
  if k in values:raise Error('Duplicate native protocol field')
  values[k]=v
 expected={'HX_NATIVE_HOME','home','auto','boot_supported',*KEYS}
 if set(values)!=expected or values['HX_NATIVE_HOME']!='1':raise Error('Native helper protocol missing/unsupported')
 try:return validate_snapshot({'home':values['home'],'strings':{k:values[k] for k in KEYS},'auto':int(values['auto']),'boot_supported':int(values['boot_supported'])})
 except (TypeError,ValueError) as e:raise Error('Malformed native snapshot') from e

class SSH:
 def __init__(self,host,helper,sha256,port=22,key=None):
  if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.:-]*',host) or not 1<=port<=65535:raise Error('Invalid SSH destination')
  if not re.fullmatch(r'/[A-Za-z0-9_./-]{1,180}',helper) or '..' in helper.split('/') or not re.fullmatch(r'[a-f0-9]{64}',sha256):raise Error('Provide the absolute helper path and published SHA256')
  self.prefix=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-p',str(port)]
  if key:self.prefix+=['-i',str(key)]
  self.prefix+=['root@'+host];self.helper=helper;self.sha256=sha256
 def shell(self,*args):
  r=subprocess.run(self.prefix+[shlex.join(args)],capture_output=True,text=True,timeout=20,stdin=subprocess.DEVNULL)
  if r.returncode:raise Error(r.stderr.strip() or r.stdout.strip() or 'SSH refused')
  if len(r.stdout)>65536:raise Error('Oversized SSH response')
  return r.stdout.strip()
 def identity(self,profile):
  if self.shell('id','-u')!='0':raise Error('Existing root is required; no privilege escalation is attempted')
  if self.shell('uname','-m')!='armv7l':raise Error('Only the built ARMv7 helper ABI is prepared')
  self.shell('test','-x','/lib/ld-linux.so.3')
  prd=self.shell('cat','/etc/prd_info.ini')
  versions=re.findall(r'^Version=([^;\r\n]+);?\s*$',prd,re.M)
  if PROFILES.get(profile) not in versions:raise Error('Unreviewed firmware/profile; no writes permitted')
  self.shell('test','!','-L',self.helper)
  if self.shell('stat','-c','%u:%a',self.helper) not in ('0:700','0:755'):raise Error('Helper must be root-owned and not writable by other users')
  if self.shell('sha256sum',self.helper).split()[0]!=self.sha256:raise Error('Remote helper differs from approved binary')
  mac=None
  for device in ('eth0','wlan0'):
   try:v=self.shell('cat','/sys/class/net/'+device+'/address').lower()
   except Error:continue
   if re.fullmatch(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}',v) and v!='00:00:00:00:00:00':mac=v;break
  if not mac:raise Error('Cannot bind backup to a physical device')
  return {'device':digest(mac),'firmware':PROFILES[profile],'prd_sha256':digest(prd),'profile':profile,'architecture':'armv7l','helper_sha256':self.sha256}
 def snapshot(self):return parse(self.shell(self.helper,'query'))
 def set(self,field,value,key=None):
  args=(field,key,str(value)) if key else (field,str(value))
  return parse(self.shell(self.helper,*args))

def plan(tv,path,profile):
 if profile not in PROFILES:raise Error('Select a reviewed firmware profile')
 ident=tv.identity(profile);original=validate_snapshot(tv.snapshot())
 if original['home']!=STOCK:raise Error('Original Home is not the reviewed Samsung Home; refuse to replace another launcher')
 if original['boot_supported']!=1:raise Error('Installed HorizonX is not eligible for boot according to the TV')
 p={'schema':1,'target':TARGET,'identity':ident,'original':original,'nonce':secrets.token_hex(16),'status':'planned-experimental','requires_existing_root':True,'requires_physical_checks':list('ABCDE')}
 save(path,p,exclusive=True);return digest(p)[:24]

def load(tv,path,token):
 p=json.loads(Path(path).read_text())
 if not secrets.compare_digest(str(token or ''),digest(p)[:24]):raise Error('Explicit --approve token required')
 if p.get('schema')!=1 or p.get('target')!=TARGET or p.get('original',{}).get('home')!=STOCK:raise Error('Invalid plan')
 validate_snapshot(p['original'])
 if tv.identity(p['identity']['profile'])!=p['identity']:raise Error('Device, firmware, helper or identity changed')
 return p

def desired(p):return {'home':TARGET,'strings':{k:TARGET for k in KEYS},'auto':1,'boot_supported':p['original']['boot_supported']}

def restore(tv,path,token):
 p=load(tv,path,token);journal=Path(str(path)+'.transaction.json')
 if not journal.exists():raise Error('No activation journal; nothing is assumed')
 before=validate_snapshot(tv.snapshot());original=p['original'];wanted=desired(p)
 if before['home'] not in (original['home'],TARGET) or any(before['strings'][k] not in (original['strings'][k],wanted['strings'][k]) for k in KEYS):raise Error('Home/startup changed outside this transaction; recovery needs review')
 try:
  tv.set('home',original['home'])
  for k in KEYS:tv.set('string',original['strings'][k],k)
  tv.set('auto',original['auto'])
  after=tv.snapshot()
  for k in ('home','strings','auto'):
   if after[k]!=original[k]:raise Error('Original native state did not read back')
  save(journal,{'status':'restored','physical_home_verified':False})
 except Exception as e:
  save(journal,{'status':'restore-required','error':str(e)})
  raise

def activate(tv,path,token):
 p=load(tv,path,token);journal=Path(str(path)+'.transaction.json')
 if journal.exists():raise Error('Activation already attempted; restore/review before repeating')
 if tv.snapshot()!=p['original']:raise Error('Native state changed after planning')
 save(journal,{'status':'applying'},exclusive=True)
 try:
  tv.set('home',TARGET)
  for k in KEYS:tv.set('string',TARGET,k)
  tv.set('auto',1)
  if tv.snapshot()!=desired(p):raise Error('Native Home/startup settings did not read back')
  save(journal,{'status':'implemented-unverified-on-hardware','physical_home_verified':False})
 except Exception as e:
  try:restore(tv,path,token)
  except Exception as rollback:save(journal,{'status':'restore-required','error':str(e),'rollback_error':str(rollback)})
  raise
