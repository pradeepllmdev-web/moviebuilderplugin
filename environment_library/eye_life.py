"""Living eyes: natural blinks and small gaze darts on existing eyelid/gaze shape keys.

Timing is pure and deterministic (seeded by shot title) so tests and reruns agree. Blinks come every
2.5-5.5 s, before each spoken line and when attention shifts; a blink closes over 3 frames, holds 1 and
opens over 5. Gaze darts are small and quick (2 frames) and lead each head-attention change."""
import math,random,zlib
CLOSE,HOLD,OPEN=3,1,5
def blink_starts(frames,fps,timeline,seed):
 rng=random.Random(seed);meaningful=[];idle=[]
 for index,beat in enumerate(timeline):
  if beat.get('dialogue'):meaningful.append(beat['start']-.12)
  if index and abs(beat.get('look_yaw_deg',0)-timeline[index-1].get('look_yaw_deg',0))>=12:meaningful.append(beat['start']-.05)
 t=rng.uniform(.8,2.2)
 while t<frames/fps:idle.append(t);t+=rng.uniform(2.5,5.5)
 starts=[]
 # Blinks before lines and on attention shifts win; idle blinks fill the gaps.
 for cue in sorted(meaningful)+idle:
  frame=round(cue*fps)
  # Keep blinks at least 1.2 s apart and fully inside the shot.
  if 0<=frame<=frames-(CLOSE+HOLD+OPEN) and all(abs(frame-s)>=1.2*fps for s in starts):starts.append(frame)
 return sorted(starts)
def blink_curve(frames,starts):
 values=[0.]*frames
 for s in starts:
  for i in range(CLOSE+HOLD+OPEN):
   if s+i>=frames:break
   v=(i+1)/CLOSE if i<CLOSE else 1 if i<CLOSE+HOLD else 1-(i-CLOSE-HOLD+1)/OPEN
   v=v*v*(3-2*v);values[s+i]=max(values[s+i],v)
 return values
def gaze_curve(frames,fps,timeline,seed,amount=.35):
 """Horizontal gaze (-1 left .. 1 right) and down (0..1) per frame."""
 rng=random.Random(seed+1);targets=[];t=rng.uniform(.6,1.4)
 while t<frames/fps:targets.append((round(t*fps),rng.uniform(-amount,amount),rng.uniform(0,.15)));t+=rng.uniform(.8,2.2)
 for index,beat in enumerate(timeline):
  if index and abs(beat.get('look_yaw_deg',0)-timeline[index-1].get('look_yaw_deg',0))>=12:
   # Eyes lead the head: snap toward the new direction just before the head starts turning.
   direction=1 if beat.get('look_yaw_deg',0)>timeline[index-1].get('look_yaw_deg',0) else -1;targets.append((max(0,round(beat['start']*fps)-3),direction*.6,0))
 targets.sort();x=[0.]*frames;down=[0.]*frames;current=(0.,0.);previous=(0.,0.);moved=-99
 for frame in range(frames):
  for at,tx,td in targets:
   if at==frame:previous=current;current=(tx,td);moved=frame
  u=min(1,(frame-moved+1)/2) if moved>=0 else 1;u=u*u*(3-2*u)
  x[frame]=previous[0]+(current[0]-previous[0])*u;down[frame]=previous[1]+(current[1]-previous[1])*u
 return x,down
def plan(frames,fps,timeline,title,eyes):
 seed=zlib.crc32(title.encode());starts=blink_starts(frames,fps,timeline,seed);blink=blink_curve(frames,starts);x,down=gaze_curve(frames,fps,timeline,seed,eyes.get('gaze_amount',.35))
 return {'blink':blink,'blink_starts':starts,'gaze_x':x,'gaze_down':down}
def animate(scene,frames,fps,timeline,title,eyes):
 """Key the profile's blink and gaze shape keys; returns a compact report."""
 values=plan(frames,fps,timeline,title,eyes);found=set();gaze=eyes.get('gaze',{});flipped=[]
 for name in eyes.get('flip_normals',[]):
  obj=scene.objects.get(name)
  if obj and obj.type=='MESH':obj.data.flip_normals();flipped.append(name)
 for frame in range(1,frames+1):
  i=frame-1;channels={name:values['blink'][i] for name in eyes.get('blink',[])}
  if gaze:channels.update({gaze['right']:max(0,values['gaze_x'][i]),gaze['left']:max(0,-values['gaze_x'][i]),gaze['down']:values['gaze_down'][i]})
  for obj in scene.objects:
   if obj.type!='MESH' or not obj.data.shape_keys:continue
   for name,value in channels.items():
    key=obj.data.shape_keys.key_blocks.get(name)
    if key:key.value=value;key.keyframe_insert('value',frame=frame);found.add(name)
 return {'controls':sorted(found),'flipped_normals':flipped,'blinks':len(values['blink_starts']),'blink_frames':values['blink_starts'],'max_gaze':round(max(map(abs,values['gaze_x']),default=0),2),'scope':'Existing eyelid and gaze shape keys only; review closed lids and gaze in a close-up'}
