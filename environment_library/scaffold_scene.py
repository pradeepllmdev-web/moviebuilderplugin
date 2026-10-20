"""Create a new scene type from a working template, wired into every registry.

    python scaffold_scene.py <id> "<Title>" "<keyword regex>" [--seconds 30]

Writes <id>_scene.py (a complete, building, auditing scene on scene_base: environment from the bank, Leo walking a short path, three camera cuts, sound, audit), appends a minimal location
'<id>_place' to world2_locations.py, registers the scene in set_pieces / story_plan, and adds a template sentence to story_writer.SENT when you pass --sentence. Then edit the scene file:
replace the walking path with the scene's real mechanic and tighten the audit. Nothing else needs touching: the planner, studio server, build_movie and the Unreal export see the new scene automatically.
A new scene must keep the project rules: everything visible for the whole film (animate, do not hide), measure then schedule (compute times from the planner, never hand-tune), and every claim in the
docstring backed by an audit line."""
import re,sys
from pathlib import Path
H=Path(__file__).resolve().parent
TEMPLATE='''"""Blender script: '{title}' (about {seconds} s).

blender -b --disable-autoexec --python {id}_scene.py -- <ship_assets_dir> <out.blend>

Technique: <describe the mechanic and the planner here; every claim needs an audit line below>. Clips: idle, run."""
import bpy,math,sys,os
import numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scene_base as sb,scene_kit as kit,locations,world2_locations as w2
from mathutils import Vector
S=sb.Scene('{id}');PI=math.pi;smooth=kit.smooth;PLACE=w2.{upper}
S.load_env('{id}_place')
# ---------------------------------------------------------------------------------------------------------- plan (replace with the real mechanic)
T0=2.0;SPEED=2.0;LENGTH=PLACE['length'];T_END=T0+LENGTH/SPEED+3.0;S.clock(T_END)
def x_at(t):return min(LENGTH,max(0.,SPEED*(t-T0)))
# ---------------------------------------------------------------------------------------------------------- Leo
leo=S.character('Leo',S.params['hero_tint']);root=leo['root']
S.play(leo,[(0,T0,'idle',1.),(T0,T0+LENGTH/SPEED,'run',.4),(T0+LENGTH/SPEED,S.seconds,'idle',1.)])
for f in S.keys():
 t=(f-1)/S.fps;root.location=(x_at(t),0,0);root.rotation_euler=(0,0,PI/2);root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_euler',frame=f)
gz=S.gaze(leo,(1,0,0))
for f in S.keys():
 t=(f-1)/S.fps;gz.location=(x_at(t)+8,0,1.4);gz.keyframe_insert('location',frame=f)
# ---------------------------------------------------------------------------------------------------------- cameras
cuts=[('establish',0,T0+1.0,'wide'),('follow',T0+1.0,S.seconds-3.0,'follow'),('end',S.seconds-3.0,S.seconds,'wide')]
def pos(kind,t,u):
 x=x_at(t);lp=Vector((x,0,1.0))
 if kind=='wide':return Vector((x-6,-9,4)),lp,26
 return Vector((x-5,-1.5,2.0)),lp+Vector((2,0,0)),32
S.cameras(cuts,pos)
# ---------------------------------------------------------------------------------------------------------- audit
issues=[]
if x_at(T_END)<LENGTH-1e-6:issues.append('AUDIT route: Leo does not reach the end of the path')
def snd(A):
 A.track('ambience',A.noise(A.N,30)*.3,.3)
 A.track('music',A.chords(((110,138.6,164.8),(98,123.5,146.8),(87.3,110,130.8),(98,123.5,146.8)),.2),.35)
S.audio(snd)
S.finish(issues,[root],world=(.45,.55,.7))
'''
LOCATION='''
{upper}=dict(length=20.)
def _{id}_place(ctx,state):
 import bpy
 link,mat,prim=ctx['link'],ctx['mat'],ctx['prim'];P={upper}
 prim('cube','Floor',(P['length']/2,0,-.5),(.4,.38,.3),scale=(P['length']/2+20,20,.5))
 sn=bpy.data.objects.new('Sun',bpy.data.lights.new('SunLight','SUN'));sn.data.energy=3.;sn.rotation_euler=(math.radians(50),0,math.radians(30));link(sn)
reg('{id}_place',_{id}_place,{upper},'{id}')
'''
def make(id_,title,keywords,seconds=30,sentence=None,root=H):
 if not re.fullmatch(r'[a-z][a-z0-9_]{2,24}',id_):raise ValueError('id must be lowercase letters, digits, underscore')
 scene=root/('%s_scene.py'%id_)
 if scene.exists():raise FileExistsError(scene)
 upper=id_.upper();scene.write_text(TEMPLATE.format(id=id_,title=title,seconds=seconds,upper=upper),encoding='utf-8')
 w2=root/'world2_locations.py';txt=w2.read_text(encoding='utf-8')
 if '_%s_place'%id_ in txt:raise FileExistsError('location exists')
 w2.write_text(txt.rstrip('\n')+'\n'+LOCATION.format(id=id_,upper=upper),encoding='utf-8')
 import register_piece
 register_piece.register(id_,title,'%s_scene.py'%id_,keywords,'TODO: one-sentence description of what happens (shown to the planner)','TODO: honest limits',seconds)
 return scene
if __name__=='__main__':
 a=sys.argv[1:]
 if len(a)<3:print(__doc__);sys.exit(1)
 secs=30
 if '--seconds' in a:i=a.index('--seconds');secs=int(a[i+1]);del a[i:i+2]
 print('created',make(a[0],a[1],a[2],secs))
