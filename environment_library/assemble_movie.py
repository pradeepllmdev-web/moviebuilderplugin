"""Blender script: join finished scene files into one master film (a sequencer timeline of scene strips, sound re-added with offsets, title cards).

blender -b --python assemble_movie.py -- <plan.json> <out.blend>

plan.json: {"scenes":[{"file":"abs/path/scene.blend","title":"..","card_seconds":2.0}, ...]}  Each scene is LINKED (not copied), so the scene files stay the single source of truth:
rebuild one scene and the master updates. Cameras switch by the markers inside each scene, sound strips are copied with their frame offset. Open the master and use the Video Editing workspace
(or View > Sequencer Preview); the 3D viewport only shows one scene at a time."""
import bpy,sys,json,os
args=sys.argv[sys.argv.index('--')+1:];plan=json.load(open(args[0],encoding='utf-8'));out=args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
master=bpy.context.scene;master.render.fps=24;master.render.resolution_x=1280;master.render.resolution_y=720
se=master.sequence_editor_create();strips=se.strips if hasattr(se,'strips') else se.sequences
cursor=1;report=[];nsound=0
for item in plan['scenes']:
 path=item['file']
 if not os.path.exists(path):report.append('missing '+path);continue
 with bpy.data.libraries.load(path,link=True) as (src,dst):dst.scenes=[src.scenes[0]]
 sc=dst.scenes[0]
 if item.get('card_seconds',0)>0:
  n=int(item['card_seconds']*24)
  try:
   t=strips.new_effect(name='Title '+item.get('title','')[:20],type='TEXT',channel=3,frame_start=cursor,length=n);t.text=item.get('title','');t.font_size=64;t.location=(.5,.5)
  except Exception as ex:report.append('title card: %s'%ex)
  cursor+=n
 length=sc.frame_end-sc.frame_start+1
 st=strips.new_scene(name=(item.get('title') or sc.name)[:40],scene=sc,channel=1,frame_start=cursor);st.frame_final_duration=length
 s2=sc.sequence_editor
 if s2:
  for sd in (s2.strips if hasattr(s2,'strips') else s2.sequences):
   if sd.type=='SOUND':
    try:strips.new_sound(name=sd.name,filepath=bpy.path.abspath(sd.sound.filepath,library=sc.library),channel=4+(nsound%4),frame_start=cursor+int(sd.frame_start)-1);nsound+=1
    except Exception as ex:report.append('sound %s: %s'%(sd.name,ex))
 report.append('%s: %d frames at %d'%(item.get('title',sc.name),length,cursor));cursor+=length
master.frame_start=1;master.frame_end=cursor-1
bpy.ops.wm.save_as_mainfile(filepath=out)
print('ASSEMBLED',master.frame_end,'frames',len(plan['scenes']),'scenes',nsound,'sounds');print('\n'.join('REPORT '+r for r in report))
