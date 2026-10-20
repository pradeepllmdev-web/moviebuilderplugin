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
def text_strip(name,text,channel,start,n,size,loc,box=None,color=(1,1,1,1),align='CENTER'):
 try:
  t=strips.new_effect(name=name[:40],type='TEXT',channel=channel,frame_start=start,length=max(1,n));t.text=text;t.font_size=size;t.location=loc;t.color=color
  if box:t.use_box=True;t.box_color=box;t.box_margin=.02
  try:t.align_x=align
  except Exception:pass
  return t
 except Exception as ex:report.append('text strip %s: %s'%(name,ex))
def card(item,start):
 """a title card: a dark strip with the scene title large and the story line under it; returns its length in frames"""
 n=int(item.get('card_seconds',0)*24)
 if n<=0:return 0
 try:
  b=strips.new_effect(name='CardBG',type='COLOR',channel=2,frame_start=start,length=n);b.color=(.02,.02,.03)
 except Exception as ex:report.append('card background: %s'%ex)
 text_strip('Title '+item.get('title',''),item.get('title',''),3,start,n,70,(.5,.58))
 if item.get('card'):text_strip('Story '+item.get('title',''),item['card'],4,start,n,34,(.5,.4))
 return n
for item in plan['scenes']:
 path=item.get('file')
 if not path:
  cursor+=card(item,cursor);continue
 if not os.path.exists(path):report.append('missing '+path);continue
 with bpy.data.libraries.load(path,link=True) as (src,dst):dst.scenes=[src.scenes[0]]
 sc=dst.scenes[0]
 cursor+=card(item,cursor)
 length=sc.frame_end-sc.frame_start+1
 st=strips.new_scene(name=(item.get('title') or sc.name)[:40],scene=sc,channel=1,frame_start=cursor);st.frame_final_duration=length
 s2=sc.sequence_editor
 if s2:
  for sd in (s2.strips if hasattr(s2,'strips') else s2.sequences):
   if sd.type=='SOUND':
    try:strips.new_sound(name=sd.name,filepath=bpy.path.abspath(sd.sound.filepath,library=sc.library),channel=4+(nsound%4),frame_start=cursor+int(sd.frame_start)-1);nsound+=1
    except Exception as ex:report.append('sound %s: %s'%(sd.name,ex))
 for sub in item.get('subtitles',[]):
  a=cursor+int(sub['t0']*24);b=cursor+int(sub['t1']*24)
  text_strip('Sub',sub['text'],6+sub.get('lane',0),a,b-a,34,(.5,.07),box=(0,0,0,.55),color=tuple(sub.get('color',(1,1,1,1))))
 for k,h in enumerate(item.get('hud',[])):
  text_strip('Hud%d'%k,h['text'],12+k,cursor,length,h.get('size',30),tuple(h['loc']),box=(0,0,0,.35),align=h.get('align','LEFT'))
 report.append('%s: %d frames at %d'%(item.get('title',sc.name),length,cursor));cursor+=length
master.frame_start=1;master.frame_end=cursor-1
bpy.ops.wm.save_as_mainfile(filepath=out)
print('ASSEMBLED',master.frame_end,'frames',len(plan['scenes']),'scenes',nsound,'sounds');print('\n'.join('REPORT '+r for r in report))
