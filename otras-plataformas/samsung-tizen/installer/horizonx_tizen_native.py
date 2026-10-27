#!/usr/bin/env python3
"""Experimental Tizen native Home through EXISTING trusted root SSH. No exploit included.

Install/verify the supplied ARMv7 helper manually first. Disable HorizonX's limited Home
watcher in its settings before native activation. Restore before uninstalling HorizonX.
"""
import argparse,json,sys,subprocess
from pathlib import Path
import native_home as n

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('command',choices=['status','home-plan','home-activate','home-restore'])
 p.add_argument('--host',required=True);p.add_argument('--port',type=int,default=22);p.add_argument('--identity',type=Path)
 p.add_argument('--helper',default='/opt/usr/horizonx-native-home');p.add_argument('--helper-sha256',required=True)
 p.add_argument('--profile',choices=list(n.PROFILES));p.add_argument('--backup',type=Path);p.add_argument('--approve')
 a=p.parse_args()
 try:
  tv=n.SSH(a.host,a.helper,a.helper_sha256,a.port,a.identity)
  if a.command in ('status','home-plan') and not a.profile:raise n.Error('--profile required')
  if a.command=='status':print(json.dumps({'identity':tv.identity(a.profile),'native':tv.snapshot()},indent=2));return 0
  if not a.backup:raise n.Error('--backup required')
  if a.command=='home-plan':print('Read-only native Home plan; approval token: '+n.plan(tv,a.backup,a.profile))
  elif a.command=='home-activate':n.activate(tv,a.backup,a.approve);print('Native APIs applied/read back. Physical Home, boot and restore still require testing.')
  else:n.restore(tv,a.backup,a.approve);print('Original native values restored/read back. Check physical Samsung Home.')
  return 0
 except (n.Error,OSError,ValueError,KeyError,subprocess.SubprocessError) as e:print('HorizonX: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
