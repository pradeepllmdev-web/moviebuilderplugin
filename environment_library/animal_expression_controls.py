"""Restrained existing mouth/brow channels. Unsafe blink morphs stay disabled."""
import math
def values(shapes,index,emotion,time):
 sample=lambda name:shapes.get(name,[0]*(index+1))[index]
 return {'MouthRound':min(.4,sample('O')*.4),'Round':min(.4,sample('O')*.4),'MouthWide':min(.3,sample('E')*.3),'Wide':min(.3,sample('E')*.3),'WarmSmile':.18 if emotion=='reassuring' else .04,'Smile':.18 if emotion=='reassuring' else .04,'ActingBrow':.18 if emotion in ['alert','curious'] else .06}
def animate(scene,frames,fps,timeline,shapes):
 found=set()
 for frame in range(1,frames+1):
  time=(frame-1)/fps;beat=next((b for b in timeline if b['start']<=time<b['end']),timeline[-1])
  for obj in scene.objects:
   if obj.type!='MESH' or not obj.data.shape_keys:continue
   for name,value in values(shapes,frame-1,beat.get('emotion','neutral'),time).items():
    key=obj.data.shape_keys.key_blocks.get(name)
    if key:key.value=value;key.keyframe_insert('value',frame=frame);found.add(name)
 return {'animated_controls':sorted(found),'blink_enabled':False,'scope':'Existing bounded mouth/brow targets only; no geometry modification or unverified eyelids'}
