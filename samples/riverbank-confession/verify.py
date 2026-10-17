import bpy,json
from pathlib import Path
H=Path(__file__).resolve().parent;plan=json.loads((H/'plan.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(H/'no-shortcuts.blend'),use_scripts=False,load_ui=False);s=bpy.context.scene;report={}
for name in ('lion','cat'):
 root=bpy.data.objects[name+' race path'];rig=next(o for o in root.children_recursive if o.type=='ARMATURE');body=max((o for o in rig.children_recursive if o.type=='MESH' and o.data.shape_keys),key=lambda o:len(o.data.vertices));keys=body.data.shape_keys.key_blocks
 silence_error=0;root_positions=[];tracks={k:[] for k in ('ConcernStrong','Frown','WarmSmile','LipPress','Round','Wide','GazeLeft','GazeRight','GazeDown')}
 jaw=keys.get('JawOpen') or keys.get('JawClose')
 for f in range(1,s.frame_end+1):
  s.frame_set(f);t=(f-1)/24;root_positions.append(tuple(root.location));active=any(l['actor']==name and l['start']<=t<l['start']+l['duration'] for l in plan['lines']);opening=jaw.value if jaw.name=='JawOpen' else 1-jaw.value
  if not active:silence_error=max(silence_error,abs(opening))
  for k in tracks:tracks[k].append(keys[k].value)
 assert silence_error<1e-5;assert len(set(root_positions))==1
 assert max(tracks['LipPress'])>.5;assert max(tracks['WarmSmile'])>.5;assert max(tracks['ConcernStrong'])-min(tracks['ConcernStrong'])>.3
 report[name]={'silent_jaw_max_error':silence_error,'root_stationary':True,'ranges':{k:[min(v),max(v)] for k,v in tracks.items()}}
(H/'verification.json').write_text(json.dumps({'characters':report,'visual_emotion_readability':'requires human review','independent_eyeballs':False},indent=2));print('ACTING_CHANNEL_CHECKS_PASSED')
