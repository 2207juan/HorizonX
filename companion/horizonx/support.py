"""Offline compatibility assessment. Device recognition never authorizes system changes."""
import argparse,json,re
from pathlib import Path
CATALOG=Path(__file__).resolve().parents[1]/'profiles/device-support.json'
def catalog():return json.loads(CATALOG.read_text(encoding='utf-8'))
def assess(platform,sdk=None,version=None,model=None):
 db=catalog();p=db['platforms'].get(platform)
 if p is None:raise ValueError('Unknown platform: '+platform)
 result={'platform':platform,'package':p['package'],'home':p['home'],'status':'unknown','hardware_tested':False,'reasons':[]}
 if 'minimum_sdk' in p:
  if sdk is not None:result['status']='candidate' if int(sdk)>=p['minimum_sdk'] else 'unsupported';result['minimum_sdk']=p['minimum_sdk']
  else:result['reasons'].append('Read the installed Android SDK level; model/year alone is insufficient')
 elif 'minimum_version' in p and version:
  def parts(s):
   values=[int(x) for x in re.findall(r'\d+',str(s))[:2]]
   return tuple((values+[0,0])[:2])
  result['status']='candidate' if parts(version)>=parts(p['minimum_version']) else 'unsupported'
 elif platform=='hisense-vidaa':result['reasons'].append('Verify web engine, URL installation and firmware-specific APIs')
 if model:
  result['catalog_matches']=[m for m in db['models'] if m['platform']==platform and m.get('identifier','').lower()==model.lower()]
 result['reasons'].append('Candidate means requirements reviewed, not physical TV certification')
 if result['home'] in ('not-replaceable','limited-watcher-or-verified-existing-root'):result['reasons'].append('Installing this package does not guarantee Home replacement')
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('platform',choices=list(catalog()['platforms']));p.add_argument('--sdk',type=int);p.add_argument('--version');p.add_argument('--model');a=p.parse_args()
 print(json.dumps(assess(a.platform,a.sdk,a.version,a.model),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
