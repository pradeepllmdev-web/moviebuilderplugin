"""Reusable pieces and lessons learned from the creature and ship set pieces (dino_scene.py, ship_scene.py, horse_herd.py, rider_scene.py).

Pure functions (no Blender needed, unit tested): smooth, catmull, push_out, ground_lift, stride_play_speed.
Blender helpers (import bpy lazily): keep_parent_inverse, add_strip, audit.
LESSONS is the single source of truth for what went wrong and the rule that prevents it; SET_PIECES.md is generated from it (python set_pieces.py --write-docs)."""
import math

LESSONS=[
 dict(id='parent_inverse',symptom='Animals look thin and deformed ("sticks") once they run; fine in the source file.',cause='Re-assigning mesh.parent in Python resets matrix_parent_inverse. The Quaternius files keep a x3.5 scale in that inverse, so the skin came out 3.5x smaller than its skeleton.',rule='Save matrix_parent_inverse before setting parent and restore it (scene_kit.keep_parent_inverse); copies must copy it too. audit() flags mesh/skeleton size ratios outside 0.55..2.2.'),
 dict(id='gait_speed',symptom='Running legs blur into a strobing scribble.',cause='Run clips were played at 1.35..1.9x; they are already fast (a 13 frame raptor cycle is 0.54 s).',rule='Play clips at 0.8..1.2x (stride_play_speed) and derive ground speed from stride length instead of speeding the clip up.'),
 dict(id='action_slots',symptom='An action assigned in Python does nothing (static rest pose).',cause='Blender 5 layered actions need a slot: assigning action alone leaves slot None.',rule='Set animation_data.action_slot / strip.action_slot = action.slots[0]. audit() flags strips without a slot.'),
 dict(id='absolute_paths',symptom='libraries.load fails with C:\\assets\\... not found.',cause='Blender -b resolves relative paths against its own folder.',rule='Pass absolute paths to Blender scripts (use pwd -W / Path.resolve()).'),
 dict(id='hidden_templates',symptom='Giant dark shapes fill the frame; wrong object is animated.',cause='Template objects hidden with hide_viewport still render; a copy named like its template collides (Triceratops vs Triceratops.001).',rule='Hide templates in viewport AND render and give them a T_ prefix.'),
 dict(id='asset_scene_clutter',symptom='A flat plane or grid slices through the scene and hides characters.',cause='Lion asset scenes built by the pipeline contain Floor/Grid/Wall planes that travel with the character group.',rule='Drop meshes named Floor*, Grid*, Wall*, Ceiling*, Rug* and camera/light/empty helpers when loading character assets.'),
 dict(id='climb_pose',symptom='Lion climbing looks upside down or lies flat on the mast.',cause='Pitching the body 77 degrees turns the whole body horizontal, not the climbing direction.',rule='Keep the body upright, lean ~0.2 rad into the mast, add rungs; the pipeline has no real climb clip yet (climb_stairs is a walk cycle).'),
 dict(id='floor_contact',symptom='A lying or falling character sinks into the floor.',cause='Baked clips drop the hips below the root; foot-lock only handles standing.',rule='Measure the lowest vertex of the largest skin mesh (face parts are static outliers) per frame and lift the root (scene_kit.ground_lift); audit() reports penetration.'),
 dict(id='moving_platform',symptom='Characters slide on a rocking ship.',cause='World-space paths on a moving floor.',rule='Parent actors and ship cameras to the platform and key everything in its local space; world cameras aim at an empty parented to the platform.'),
 dict(id='no_clipping',symptom='A body that follows its head (serpent) passes through hull, cabin and masts.',cause='Positions come only from a path; nothing pushes them out of scenery.',rule='Run every body point through push_out(p, r, solids) with boxes, cylinders and the hull; this is cheap collision response, use Blender Cloth/Rigid Body only where simulation is the point.'),
 dict(id='cloth',symptom='A sail cut loose looks like a rigid card flying.',cause='Keyed rigid plane.',rule='Real Cloth modifier, pin vertex group on the yard, keyframed pin_stiffness 1 to 0 at the cut, wind field with keyed strength, collision on solids, bake the cache before saving.'),
 dict(id='cameras',symptom='Camera sits inside a sail or sees only sea.',cause='Camera offsets chosen without looking at moving geometry.',rule='audit() checks at least one subject is in frame mid-cut; render a contact sheet of stills (workbench, 480 px) before reporting.'),
 dict(id='contact_audio',symptom='Footsteps and dust do not match the animals.',cause='Constant-rate sound.',rule='Sample foot bone heights per frame, take contacts, and use those times for dust, splashes and sound.'),
 dict(id='no_mp4',symptom='Previews take minutes.',cause='Rendering video.',rule='Never render mp4 for previews; open the .blend with previs.open_viewer (closes earlier viewers) and check stills.'),
 dict(id='downloads',symptom='Assets missing on another machine.',cause='Downloaded CC0 packs are not committed.',rule='Ask before downloading, extract into their own new folder, never run code from them, list the pack and licence in the docs (set_pieces.py reports what is missing).'),
 dict(id='user_preferences',symptom='Wasted time on renders, stale windows, aimless motion.',cause='Standing preferences of the author.',rule='No mp4 renders (open the .blend); close earlier Blender viewers when opening a new one; no hand or leg motion without a purpose or dialogue; larger rooms and themed props; fix issues by automatic checks, not by hand each time; keep sessions fast and cheap with numeric checks and few images.'),
 dict(id='shared_action',symptom='Every horse in a herd runs in lockstep or stands still.',cause='Rig copies share one action.',rule='Call animation_data_clear() on each copy and give each its own NLA strip with a random phase.'),
 dict(id='rider_seat',symptom='Rider POV looks at his own face; stirrups and knees inside the horse.',cause='Camera yaw must be heading minus pi/2; stirrup empties placed at the body surface.',rule='Move stirrups outward, tune knee/rein/lean per rider kind (KINDS in rider_scene.py), use IK seat for animals instead of bench Sit clips.'),
 dict(id='dust_scale',symptom='Dust puffs look like balloons.',cause='Puff size not tied to the animal.',rule='Size puffs by creature (raptor .18, triceratops .55) and by speed; splashes in water use a blue material.'),
 dict(id='visibility_windows',symptom='Characters or props pop in and out or two copies overlap.',cause='Hide keys set on both groups at the same frames.',rule='Use one rig with sequential NLA strips (ship scene) or exact non-overlapping visibility windows (dino scene).'),

 dict(id='grip_ik',symptom='Climbing looks like a walk cycle; hands float near holds.',cause='No contact: limbs were never tied to anything.',rule='Place holds procedurally (right hand, left foot, left hand, right foot, step 0.33 m, hand wrist 1.12..1.45 m and ankle 0.26..0.49 m above the root) and IK the forearm and shin bones (chain 2, poles for elbows and knees) to the hold they are planted on; cliff_scene.limb_eval handles hold-to-hold, hold-to-rope and free transitions. The audit measures wrist and ankle bone against the target (limit 7 cm).'),
 dict(id='grip_transitions',symptom='Hands or feet miss targets right after a mode change (landing, mounting, turning).',cause='The root keeps moving while a planted foot target is fixed, or the body turns away from a planted target.',rule='Start rising only after a mount crossfade finishes (0.5 s); end plants before the body turns; keep planted targets within 0.4 m of the hip.'),
 dict(id='rigid_bodies',symptom='Rocks never fall, or all fall at once.',cause='They rest on a collision shelf; kinematic flag not keyed.',rule='Active rocks start kinematic and get the flag keyed off at their release time; no collider under them; bake with ptcache.bake_all and read the baked positions for impact sounds.'),
 dict(id='pendulum',symptom='Rope swing looks arbitrary.',cause='Hand-keyed arc.',rule='Use the exact pendulum: half period pi*sqrt(L/g), amplitude from the start and end x; choose anchor so both ends are reachable and the landing lines up with the next climb column.'),

 dict(id='carry_small_character',symptom='A small character appears on a big one without a believable pick-up.',cause='Constraint snap from the slab to the back.',rule='Bake the carried character per frame from the carrier bones: lifted in the right hand (pick clip), held at the chest, then settled on the back over about a second; no constraint, so nothing pops (cliff_scene.cub_pose).'),
 dict(id='release_jump',symptom='Letting go of a rope looks like teleporting onto the ledge.',cause='No flight between release and landing.',rule='Release the rope 0.5 s before the end of the swing, play the lion Jump clip fitted around the landing, move the root on a ballistic arc (about 0.45 m high) and plant the feet 0.2 s after the landing.'),
 dict(id='climb_realism',symptom='Climbing looks mechanical.',cause='Rigid upright body.',rule='Lean 0.07 rad into the wall and sway the root +-3.5 cm in step with the limb cycle; keep alternating right hand, left foot, left hand, right foot.'),

 dict(id='contact_solver',symptom='Punches and kicks stop short of the target or go through it.',cause='Spacing between fighters guessed by hand.',rule='Measure the striking limb at full extension in the evaluated clip, shift the attacker root in x/y by the residual to the target bone over 0.3 s before impact, start the reaction at impact, then re-measure and audit (limit 20 cm; z error remains if the target bone is at another height, so pick the matching bone: chest for a jab, foot for a sweep).'),
 dict(id='body_grip',symptom='Grappling hands float beside the opponent.',cause='Fixed IK targets on a moving body.',rule='Make each hand IK target an empty with Copy Location to the opponent shoulder bone and ramp influence 0.5 s in and out; both fighters face each other at 0.62 m and circle about a midpoint.'),
 dict(id='short_loop_strips',symptom='NLA strips refuse to be added or overlap.',cause='A loop strip shorter than its clip kept the full clip length.',rule='scene_kit.add_strip trims action_frame_end when the window is shorter than the clip; strips under 0.25 s do not fit the 5 frame blend overlap, merge them.'),

 dict(id='surface_contact',symptom='A fist or foot goes inside the other lion.',cause='Targets were bone centres, not the skin.',rule='Aim at the skin: BVH ray from the target bone centre towards the attacker (scene_kit.surface_target, in object space) plus 2 cm; the audit reports penetration (limit 6 cm) and miss (limit 20 cm). The arena strikes now end 9, 3 and 4 cm from the skin.'),
 dict(id='dependency_cycle',symptom='Console floods with Dependency cycle warnings; grips jitter.',cause='Two rigs whose IK targets copy the IK-chain bones of each other (arm to arm).',rule='Copy the shoulder bone of the opponent (clavicle) bone TAIL instead; it is not in any IK chain, so there is no cycle. Always grep the log for Dependency cycle.'),
 dict(id='jump_physics',symptom='Jumps look floaty or like a hop.',cause='The pipeline Jump clip keeps the feet on the ground (the arc comes from the route), no crouch or tuck.',rule='Apex from flight time (flight_apex = g T^2 / 8), parabola from ballistic(), and jump_profile() for crouch 0.3 s before take-off, stretch, foot tuck by IK (+0.30 m at the top), reach, and a landing dip; flight time 0.7 s gives a 0.60 m apex.'),
 dict(id='crowds',symptom='Crowds are either cones or too heavy.',cause='Full characters per spectator are expensive.',rule='Tiers: far rows are simple cones grouped in sections that bob together (12 sections, keyed per frame); the front rows are real animated lions made with clone_character (shared mesh data, own armature, random clip phase via negative strip start, tint per clone): 24 clones evaluate a frame in 0.01 s. For thousands use Unreal Mass or Niagara with a vertex-animation texture, with Blender only authoring the clips.'),

 dict(id='palm_lock',symptom='Wrestling or hugging lions merge into one body; hands sink into the shoulders.',cause='Grips aimed at the shoulder bones of a body 0.6 m away.',rule='Palm-to-palm lockup at 1.45 m root spacing: the senior rival wrists go to the midpoint of both root paths (1.2 m high, 0.2 m left and right) and the other lion wrists copy his HAND bones (one-way, no cycle); both lean 0.22 rad. Verify numerically: wrist to target 0 cm, shoulder to wrist 0.37..0.43 m (arm length 0.5).'),
 dict(id='planted_feet',symptom='Feet skate during a grapple.',cause='The body moves, the feet follow the root.',rule='plan_feet in arena_scene: IK feet stay where they are and step (0.3 s, 0.1 m lift) only when the body is 0.3 m away, one foot at a time; influence ramps 0.3 s in and out.'),
 dict(id='landing_room',symptom='A thrown or fallen character gets up inside the other one.',cause='Landing spot too close.',rule='Land 1.6 m behind the thrower and move the winner 2.5 m away before the loser gets up; the audit checks body-bone distance (limit 10 cm).'),

 dict(id='moving_world',symptom='Things on a fast train drift or the scenery moves wrongly.',cause='Mixing train-local and world motion.',rule='Keep the scenery static and key the train (V0 20 m/s after a 4 s ease-in), then compute every character in WORLD space as train x + local x; two groups (front and rear cars) let a coupling release: the rear group decelerates (exponential, k 0.25) so the gap grows by V0*(s-(1-exp(-k s))/k).'),
 dict(id='gap_jumps',symptom='Gap jumps are all the same hop or miss the roof.',cause='Take-off and landing chosen by hand.',rule='kit.run_path puts every flight 0.25 m before the gap and 0.35 m after it at constant speed; flight time = distance / speed; arc from flight_apex; strips for jump windows start 0.3 s earlier for the crouch.'),
 dict(id='obstacle_timing',symptom='A duck happens where there is no obstacle.',cause='Obstacle placed independently of the fighter.',rule='Place the low gantry at the world x where Leo is at the chosen time (X_BR = train x + local x) and duck when the fighter world x is within 0.5 to 1.6 m of it (pitch 0.6, drop 0.3 m).'),
 dict(id='projectile',symptom='A kicked guard slides off sideways like a card.',cause='Keyed position.',rule='kit.ballistic_to(p0,p1,T,t) with T = flight_time_to_ground(z, vz): x,y linear (including the train speed), z a parabola; spin during flight; lie on the ground afterwards with the fall clip and a short exponential slide.'),
 dict(id='kick_apex',symptom='The kick solver never reaches the target.',cause='Maximum forward reach of a leg is a low foot.',rule='Measure a kick at the highest foot, a punch at the farthest hand; then the horizontal snap gives 2 cm.'),
 dict(id='roof_floor',symptom='Landing from a jump sinks the feet into the roof.',cause='Clip crouch plus the landing dip.',rule='Ground lift (lowest skin vertex against the roof) for every non-airborne frame of all three characters.'),

]
def smooth(u):
 u=max(0.,min(1.,u));return u*u*(3-2*u)
def catmull(points,t):
 """Smooth path through [(time,(x,y,z))] keys (Catmull-Rom, clamped ends)."""
 ts=[p[0] for p in points]
 if t<=ts[0]:return tuple(points[0][1])
 if t>=ts[-1]:return tuple(points[-1][1])
 i=max(k for k in range(len(ts)) if ts[k]<=t);u=(t-ts[i])/(ts[i+1]-ts[i]);g=lambda j:points[max(0,min(len(points)-1,j))][1]
 p0,p1,p2,p3=g(i-1),g(i),g(i+1),g(i+2)
 return tuple(.5*((2*p1[k])+(-p0[k]+p2[k])*u+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*u*u+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*u**3) for k in range(3))
def push_out(p,r,solids):
 """Collision response for a sphere of radius r at p=(x,y,z). solids: ('box',(x0,x1,y0,y1,z0,z1)) / ('cyl',(cx,cy,z0,z1,R)) / ('hull',(L,half_beam(x),deck_z)). Returns the corrected point."""
 x,y,z=p
 for _ in range(2):
  for kind,d in solids:
   if kind=='hull':
    L,hb,dz=d
    if abs(x)<L+r*.5 and z<dz+r:
     b=hb(max(-L,min(L,x)))+r*.8
     if abs(y)<b:
      if dz+r-z<=b-abs(y):z=dz+r
      else:y=math.copysign(b,y if y else 1.)
   elif kind=='box':
    x0,x1,y0,y1,z0,z1=d
    if x0-r<x<x1+r and y0-r<y<y1+r and z0-r<z<z1+r:
     opts=[(x-(x0-r),'x0'),((x1+r)-x,'x1'),(y-(y0-r),'y0'),((y1+r)-y,'y1'),((z1+r)-z,'z1')]
     _,k=min(opts)
     if k=='x0':x=x0-r
     elif k=='x1':x=x1+r
     elif k=='y0':y=y0-r
     elif k=='y1':y=y1+r
     else:z=z1+r
   elif kind=='cyl':
    cx,cy,z0,z1,R=d;dx,dy=x-cx,y-cy;dd=math.hypot(dx,dy);rr=R+r*.9
    if dd<rr and z0<z<z1:
     if dd<1e-4:dx,dd=rr,rr
     x=cx+dx/dd*rr;y=cy+dy/dd*rr
 return (x,y,z)
def ground_lift(lowest,floor,margin=.01,limit=1.,window=1):
 """{frame: lowest skin z} -> {frame: lift}: raise the root so the lowest point rests on the floor, clamped, smoothed over +-window samples."""
 fr=sorted(lowest);raw={f:max(0.,min(limit,floor+margin-lowest[f])) for f in fr}
 return {f:sum(raw[g] for g in fr[max(0,i-window):i+window+1])/len(fr[max(0,i-window):i+window+1]) for i,f in enumerate(fr)}
def stride_play_speed(ground_speed,stride_m,cycle_frames,fps=24.,lo=.8,hi=1.2):
 """Clip play speed that matches a ground speed (stride_m per cycle), clamped to natural speeds; returns (play, residual_slide_ratio)."""
 natural=stride_m/(cycle_frames/fps);want=ground_speed/natural;play=max(lo,min(hi,want));return play,(ground_speed/(natural*play))
def flight_apex(T,g=9.81):
 """Apex height of a ballistic jump that stays in the air T seconds (g*T^2/8)."""
 return g*T*T/8.
def ballistic(u,apex):
 """Height above the take-off/landing line at flight fraction u in 0..1 (parabola)."""
 return 4.*apex*u*(1.-u)
def jump_profile(t,launch,land):
 """Pose layers of a believable jump: crouch before take-off, stretch at take-off, tuck at the top, reach for the ground, absorb the landing.
 Returns dict(dz root height offset, tuck 0..1 foot lift, pitch). The arc itself comes from ballistic(); flight time is land-launch."""
 dz=0.;tuck=0.;pitch=0.
 if launch-.30<=t<launch:
  u=(t-(launch-.30))/.30;dz=-.14*math.sin(math.pi*u*.5);pitch=.10*u
 elif launch<=t<=land:
  u=(t-launch)/(land-launch);tuck=smooth(u/.25)*(1-smooth((u-.75)/.2));pitch=.10*(1-u)-.05*u
 elif land<t<=land+.30:
  u=(t-land)/.30;dz=-.12*math.sin(math.pi*u);pitch=.12*(1-u)
 return dict(dz=dz,tuck=tuck,pitch=pitch)
def ballistic_to(p0,p1,T,t,g=9.81):
 """Position at time t (0..T) of a projectile that leaves p0 and reaches p1 after T seconds under gravity: x,y linear, z a parabola (vz derived from the end height)."""
 u=max(0.,min(1.,t/T));vz=(p1[2]-p0[2]+.5*g*T*T)/T
 return (p0[0]+(p1[0]-p0[0])*u,p0[1]+(p1[1]-p0[1])*u,p0[2]+vz*t-.5*g*t*t)
def flight_time_to_ground(z0,vz,g=9.81):
 """Time to fall from height z0 (above the ground, m) when leaving upward at vz m/s."""
 return (vz+math.sqrt(vz*vz+2*g*z0))/g
def run_path(t0,x0,x1,gaps,speed,take=.25,land=.35):
 """Constant-speed run along +x that jumps every gap (gap_start,gap_end): returns [(kind,t_start,t_end,x_start,x_end)] with kind run/jump; flights take off take m before the gap and land land m after it."""
 segs=[];t=t0;x=x0
 for gs,ge in gaps:
  if not x0<gs<x1:continue
  xt=gs-take
  if xt>x:segs.append(('run',t,t+(xt-x)/speed,x,xt));t+=(xt-x)/speed;x=xt
  xl=ge+land;T=(xl-x)/speed;segs.append(('jump',t,t+T,x,xl));t+=T;x=xl
 if x1>x:segs.append(('run',t,t+(x1-x)/speed,x,x1));t+=(x1-x)/speed
 return segs
def path_x(segs,t):
 if not segs:return 0.
 if t<=segs[0][1]:return segs[0][3]
 for k,a,b,x0,x1 in segs:
  if a<=t<b:return x0+(x1-x0)*(t-a)/(b-a)
 return segs[-1][4]
def surface_target(target_obj,from_pt,to_pt,depsgraph):
 """Where the hand should stop: the point where the ray from the target's centre (to_pt) towards the attacker (from_pt) leaves the target's skin (world space), plus how deep from_pt is inside (m, positive = inside).
 The BVH is built in the object's own space, so points are transformed in and the hit is transformed out."""
 from mathutils.bvhtree import BVHTree
 from mathutils import Vector
 bvh=BVHTree.FromObject(target_obj,depsgraph);mw=target_obj.matrix_world;inv=mw.inverted()
 c=Vector(to_pt);h=Vector(from_pt);dist=(h-c).length
 if dist<1e-6:return h,0.
 hit=bvh.ray_cast(inv@c,(inv.to_3x3()@(h-c)).normalized())
 if hit[0] is None:return h,0.
 w=mw@hit[0];n=(mw.to_3x3()@hit[1]).normalized();return w+n*.02,(w-c).length-dist
def clone_character(rig,body,name,location,heading=0.,scale=1.,tint=None):
 """Cheap crowd member: a new armature copy plus a body object that SHARES the original mesh data (one copy of the vertices in memory); materials can be tinted per clone."""
 import bpy
 r=rig.copy();r.data=rig.data.copy();r.name=name;r.animation_data_clear();r.animation_data_create()
 b=body.copy();b.name=name+'_body';b.parent=r;b.matrix_parent_inverse=body.matrix_parent_inverse.copy()
 for m in b.modifiers:
  if m.type=='ARMATURE':m.object=r
 root=bpy.data.objects.new(name+'Root',None);root.location=location;root.rotation_euler=(0,0,heading+math.pi/2);root.scale=(scale,)*3;r.parent=root
 for o in (r,b,root):
  if o.name not in bpy.context.scene.collection.objects:bpy.context.scene.collection.objects.link(o)
 if tint:
  for slot in b.material_slots:
   if slot.material:
    m=slot.material.copy();c=slot.material.diffuse_color;m.diffuse_color=(c[0]*tint[0],c[1]*tint[1],c[2]*tint[2],1);slot.link='OBJECT';slot.material=m
 return root,r,b
# ---------------------------------------------------------------------------------------------------------- Blender helpers
def keep_parent_inverse(child,parent):
 inv=child.matrix_parent_inverse.copy();child.parent=parent;child.matrix_parent_inverse=inv
def add_strip(track,action,start,end,mode='loop',slot=True,name=None):
 """NLA strip filling [start,end] frames: mode 'loop' repeats the clip, 'fit' stretches it once. Binds the action's first slot."""
 length=action.frame_range[1]-action.frame_range[0]+1;st=track.strips.new(name or action.name,int(start),action)
 if slot and len(action.slots):st.action_slot=action.slots[0]
 if mode=='fit':st.scale=(end-start)/length;st.repeat=1
 elif end-start<length:st.action_frame_end=st.action_frame_start+max(2,end-start)-1   # window shorter than the clip: play its first part
 else:st.repeat=max(1.,(end-start)/length)
 return st
def audit(scene,bodies=(),floor_z=0.,space=None,skip=(),subjects=(),step=12,fps=24):
 """Automatic checks on a built scene; returns a list of 'AUDIT ...' strings (empty = clean). bodies: [(armature, skin mesh)], skip: [(t0,t1)] airborne windows,
 subjects: objects at least one of which must be in frame mid-cut, space: object whose local z is the floor height frame (e.g. a ship)."""
 import bpy
 from mathutils import Vector
 from bpy_extras.object_utils import world_to_camera_view
 out=[]
 for ob in scene.objects:
  ad=ob.animation_data
  if ad:
   for tr in ad.nla_tracks:
    for st in tr.strips:
     if st.action and len(st.action.slots) and st.action_slot is None:out.append('AUDIT action_slots: %s strip %s has no slot'%(ob.name,st.name))
 def verts(mesh,dg):
  e=mesh.evaluated_get(dg);return [e.matrix_world@v.co for v in e.data.vertices]
 for rig,mesh in bodies:
  scene.frame_set(scene.frame_start+2);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
  pts=verts(mesh,dg);bones=[rig.matrix_world@pb.head for pb in rig.pose.bones]
  ext=lambda P:Vector((max(p[i] for p in P)-min(p[i] for p in P) for i in range(3))).length
  ratio=ext(pts)/max(1e-6,ext(bones))
  if not .55<=ratio<=2.2:out.append('AUDIT parent_inverse: %s skin/skeleton size ratio %.2f (expected .55..2.2)'%(rig.name,ratio))
  worst=(0.,None)
  for f in range(scene.frame_start,scene.frame_end+1,step):
   t=(f-1)/fps
   if any(a<=t<=b for a,b in skip):continue
   scene.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();inv=space.matrix_world.inverted() if space else None
   low=min(((inv@p).z if inv else p.z) for p in verts(mesh,dg)[::4]);pen=floor_z-low
   if pen>worst[0]:worst=(pen,f)
  if worst[0]>.05:out.append('AUDIT floor_contact: %s sinks %.2f m below the floor at frame %d'%(rig.name,worst[0],worst[1]))
 marks=sorted(scene.timeline_markers,key=lambda m:m.frame)
 for i,m in enumerate(marks):
  if not m.camera or not subjects:continue
  f=(m.frame+(marks[i+1].frame if i+1<len(marks) else scene.frame_end))//2;scene.frame_set(f);bpy.context.view_layer.update();scene.camera=m.camera
  seen=any((lambda c:0<=c.x<=1 and 0<=c.y<=1 and c.z>0)(world_to_camera_view(scene,m.camera,s.matrix_world.translation)) for s in subjects)
  if not seen:out.append('AUDIT cameras: cut "%s" shows none of the subjects at frame %d'%(m.name,f))
 scene.frame_set(scene.frame_start)
 return out
