"""Build every registered scene type, one after another, and report audits and timings.

    python verify_all_scenes.py [out_folder] [--only id,id] [--fast]

The regression gate for the whole scene library: run it before committing a change to scene_base, scene_kit, the banks or a scene script. Each scene is built with set_pieces.build (its own Blender
process), the audit lines are collected, and a table is written to <out>/VERIFY.md. Exit code 1 when any scene fails to build or has audit issues. --fast skips scenes that took more than 60 s last
time (the slow simulations) so the quick loop stays quick."""
import json,sys,time
from pathlib import Path
import set_pieces
H=Path(__file__).resolve().parent
def main(out,only=None,fast=False):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);hist=out/'VERIFY.json';prev=json.loads(hist.read_text()) if hist.exists() else {};rows=[]
 for k in set_pieces.SET_PIECES:
  if only and k not in only:continue
  if fast and prev.get(k,{}).get('seconds',0)>60:rows.append(dict(id=k,status='skipped (slow)',audit=[],seconds=prev[k]['seconds']));continue
  t=time.time();r=set_pieces.build(k,out=out/('%s.blend'%k))
  if r.get('missing'):rows.append(dict(id=k,status='missing: '+'; '.join(r['missing']),audit=[],seconds=0));continue
  rows.append(dict(id=k,status='ok' if r['ok'] and not r['audit'] else ('build failed' if not r['ok'] else 'audit issues'),audit=r['audit'],seconds=round(time.time()-t,1)))
 hist.write_text(json.dumps({r['id']:r for r in rows}));lines=['# Scene library verification','','| scene | status | seconds | audit |','|---|---|---|---|']
 for r in rows:lines.append('| %s | %s | %s | %s |'%(r['id'],r['status'],r['seconds'],'; '.join(r['audit'])[:140]))
 (out/'VERIFY.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print('\n'.join(lines));return all(r['status'] in ('ok','skipped (slow)') for r in rows)
if __name__=='__main__':
 a=sys.argv[1:];only=None;fast='--fast' in a;a=[x for x in a if x!='--fast']
 if '--only' in a:i=a.index('--only');only=a[i+1].split(',');del a[i:i+2]
 sys.exit(0 if main(a[0] if a else str(H/'scenes'/'verify'),only,fast) else 1)
