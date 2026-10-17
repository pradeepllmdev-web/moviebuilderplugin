"""Run inside Blender only. Consumes data; never executes generated Python."""
import argparse
import json
import os
import math
from pathlib import Path
import sys
import bpy
from mathutils import Euler, Quaternion, Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0,'C:\\Users\\nagal\\OneDrive\\Documents\\GitHub\\blendplugin-next\\scene_pipeline')
from scene_spec import validate, sample, pace_walks, GAITS, join_yaws
from gait import walk_foot, fight_foot
from motion_library import MOTIONS
from rig_adapter import load_asset, animate_asset
from auditorium import build_auditorium
from procession import build_procession
from forest import build_forest
from choreo import choreograph
from realistic_rig import load_realistic, build_nla, smooth_root, feet_drive_root
from look import apply_look
from footlock import lock_feet, ground_feet, AIRBORNE
from props import place_props
from extras import add_extras
from held import attach_items
from lookat import look_at
from qa import check_shot, prop_footprints
from contact import bake_contacts, add_seats, bake_controls, bake_ladder

parser=argparse.ArgumentParser()
parser.add_argument('output',type=Path)
parser.add_argument('--quality',choices=['auto','preview','eevee','cycles','final','draft','sketch'],default='auto')
parser.add_argument('--render',choices=['none','still','animation','preview'],default='still')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
out=args.output
plan=json.loads((out/'scene.json').read_text())
catalog=json.loads((out/'catalog.json').read_text())
plan=choreograph(plan)  # punches get reactions at impact
plan=pace_walks(plan,catalog)  # slow walks: walk at a natural pace, then stand (no skating)
plan=join_yaws(plan)   # rerouted runs end on their own heading: the next segment turns from there
validate(plan,catalog)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
s=bpy.context.scene
s.render.engine='BLENDER_WORKBENCH'; s.render.resolution_x=800; s.render.resolution_y=450
s.render.resolution_percentage=100; s.render.image_settings.file_format='PNG'
s.render.fps=round(plan['fps']*plan.get('slowmo',1)); s.frame_end=round(plan['duration']*s.render.fps)   # slow motion: more frames a story second, played at 24
s.display.shading.light='STUDIO'; s.display.shading.color_type='MATERIAL'
s.display.shading.show_shadows=True; s.display.shading.show_cavity=True
s.display.shading.cavity_type='BOTH'; s.display.shading.background_type='WORLD'
s.world.color=(.065,.075,.095)

def material(name,color):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); return m
dark=material('Eyes and shoes',(.018,.025,.04))
skin=material('Porcelain',(.8,.67,.50))
ground=material('Stage',(.16,.22,.28))
white=material('Markings',(.8,.87,.9))
yellow=material('Obstacles',(.98,.62,.03))

def empty(name,parent=None,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None); s.collection.objects.link(o); o.parent=parent; o.location=loc; return o
def sphere(name,pos,scale,mat,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8 if plan['scene_type']=='auditorium' else 16,ring_count=4 if plan['scene_type']=='auditorium' else 8,location=pos)
    o=bpy.context.object; o.name=name; o.scale=scale; o.parent=parent; o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth=True
    return o
def cube(name,pos,scale,mat,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=bpy.context.object; o.name=name; o.scale=scale; o.parent=parent; o.data.materials.append(mat); return o
def limb(name,radius,mat,parent):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=radius,depth=1)
    o=bpy.context.object; o.name=name; o.parent=parent; o.data.materials.append(mat); return o
def key(o,*paths):
    for path in paths: o.keyframe_insert(data_path=path)
def bone(o,a,b):
    a,b=Vector(a),Vector(b); o.location=(a+b)/2; o.scale.z=(b-a).length
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); key(o,'location','rotation_euler','scale')

cube('Floor',(0,0,-.46 if plan['scene_type']=='auditorium' else -.13),(*plan['floor_size'],.24),ground)
for y in ([] if plan['scene_type']=='auditorium' or plan['environment']['kind']=='forest' else range(-int(plan['floor_size'][1]/2),int(plan['floor_size'][1]/2)+1,2)):
    cube('Grid',(0,y,.002),(plan['floor_size'][0],.02,.008),white)
for ob in ([] if plan.get('set','field')!='field' else plan['obstacles']):   # built sets (street, gym, rooftop) have real buildings
    cube(ob['kind'],ob['position'],ob['size'],yellow)
    if ob['kind']!='box':
        x,y,z=ob['position']; width=ob['size'][1]
        for dy in (-width/2,width/2): cube('Support',(x,y+dy,z/2),(.12,.12,z),dark)

if plan['scene_type']=='auditorium': build_auditorium(s,out)
if plan['scene_type']=='procession': build_procession(s,plan)
if plan['environment']['kind']=='forest' and plan.get('set','field')=='field': build_forest(s,plan,out)   # built sets bring their own world
if plan.get('props'): place_props(s,plan)
extras_added=add_extras(s,plan,catalog)  # background people (no QA/framing)
rigs=[]
lens_log=[]
zoom_k={}   # frame: the dolly zoom's lens factor (kept apart from the framing lens, which is smoothed)
focus_pts=[]   # where the lens focuses each frame (racks to whoever speaks in a two-shot)
thirds_side={}
assets={}
realistic={}
centers=[]
for i,actor in enumerate(plan['actors']):
    info=catalog[actor['name']]; color=material(actor['name'],info['color'])
    root=empty(actor['name']); root.scale=(info['height_m']/1.8,)*3
    body=empty('Body',root,(0,0,.88)); head=empty('Head control',body,(0,0,.53))
    sphere('Torso',(0,0,.20),(.23,.15,.34),color,body)
    sphere('Head',(0,0,.18),(.155,.145,.20),skin,head)
    eyes=[sphere('Eye',(side*.06,-.136,.22),(.023,.025,.026),dark,head) for side in (-1,1)]
    mouth=sphere('Mouth',(0,-.14,.10),(.04,.014,.006),dark,head)
    parts=[]
    for side in (-1,1):
        parts.append((side,limb('Thigh',.075,color,root),limb('Shin',.06,color,root),
                      limb('Upper arm',.052,color,root),limb('Forearm',.045,color,root),
                      sphere('Shoe',(0,0,0),(.095,.17,.075),dark,root),
                      sphere('Hand',(0,0,0),(.06,.06,.065),skin,root)))
    rigs.append((actor,root,body,head,eyes,mouth,parts))
    if info.get('asset_type')=='rigged_lowpoly':
        assets[actor['name']]=load_asset(info)
    if info.get('asset_type')=='rigged_realistic':
        role=next((c['role'] for c in plan.get('costumes',()) if c['name']==actor['name']),None)   # dressed for the job here
        realistic[actor['name']]=load_realistic(dict(info,costume=role) if role else info)
        if info.get('armature')=='Lion_Realistic' and os.environ.get('LION_FACE','1')!='0':
            import lion_face
            lion_face.add_controls(realistic[actor['name']])
        import facerig
        if facerig.profile(realistic[actor['name']]): pass   # a real facial rig: facerig.perform drives it (below)
        elif info.get('species','human')=='human' and any(l['speaker']==actor['name'] for l in plan.get('lines',())):
            import face; face.add_mouth(realistic[actor['name']])   # speakers' mouths open on their words
        if info.get('species','human')=='human' and os.environ.get('BLINKS','1')!='0' and not facerig.profile(realistic[actor['name']]):
            import face; face.add_blinks(realistic[actor['name']])   # eyelids that blink
            import expressions
            try: expressions.add_expressions(realistic[actor['name']])   # smiles, frowns, brows
            except Exception as exc: print('Expressions skipped:',actor['name'],exc)   # a face the landmarks can't read stays neutral
    if actor['name'] in assets or actor['name'] in realistic:
        for obj in root.children_recursive:
            if obj.type=='MESH': obj.hide_render=True;obj.hide_set(True)

import vehicles
cars=[vehicles.build(bpy,v,i) for i,v in enumerate(plan.get('vehicles',()))]   # cars driving along the street
vehicles.tyre_smoke(bpy,plan,s.render.fps)   # a chase car skidding round a corner
if plan.get('set') in ('sky','sea','rail','launch','orbit','station'):   # outside the plane in flight / the ship at sea: the cast is aboard, unseen
    for rig in realistic.values():
        for o in [rig,*rig.children_recursive]: o.hide_render=True; o.hide_set(True)
for name in plan.get('hidden',()):   # in the story but not in this place (passengers while the driver drives)
    rig=realistic.get(name)
    if rig:
        for o in [rig,*rig.children_recursive]: o.hide_render=True; o.hide_set(True)
bpy.ops.object.camera_add(); cam=bpy.context.object; s.camera=cam
cam.data.lens=plan['camera']['lens_mm']; cam.data.clip_end=500
if plan.get('set') in ('sky','sea','deck','rail','carriage','train_cab','train_roof','western','warzone','jungle','snow','platform'): cam.data.clip_end=30000
if plan.get('set')=='chase': cam.data.clip_end=2000   # down the whole avenue
if plan.get('set') in ('launch','orbit','station','module'): cam.data.clip_end=400000   # the Earth below, the rocket kilometres up
if plan.get('set') in ('launch','orbit','station'): cam.data.clip_start=1.0   # depth precision over 400 km: no speckled surfaces   # the sea of cloud / the horizon lies kilometres away
framing=[]
# Characters far from everyone else for the whole shot have left the scene (e.g. hunters who ran off): the camera
# frames the others, otherwise it centres an empty field and puts the far one on a third.
AWAY=6.0
def _apart(i,t):
    here=sample(rigs[i][0],t)[2]
    return min((math.dist(here[:2],sample(r[0],t)[2][:2]) for j,r in enumerate(rigs) if j!=i),default=0)>AWAY
present=[i for i in range(len(rigs)) if not all(_apart(i,k*.5) for k in range(int(plan['duration']*2)+1))] or list(range(len(rigs)))
if plan.get('set')=='cabin':   # the camera stays in the cabin: between the walls, above the headrests, under the bins
    import cabin as _cabin
    INDOOR_BOX=((_cabin.ROWS[0]-1.0,_cabin.ROWS[-1]+1.3),(-1.0,1.0),(1.25,1.95))
elif plan.get('set')=='carriage':   # inside the train car: in the aisle zone, above the seat backs, below the racks
    import train as _train
    INDOOR_BOX=tuple(tuple(r) for r in _train.CAR['camera_box'])
elif plan.get('set')=='module':   # inside the station module, clear of the racks
    INDOOR_BOX=((-3.2,3.2),(-.65,.65),(.6,1.95))
elif plan.get('set')=='train_cab':
    import train as _train
    INDOOR_BOX=_train.CAB_BOX
elif plan.get('set') in ('apartment','office','diner','bedroom','hospital','interrogation'):   # inside the room: off the walls and under the ceiling (the front is open)
    import interior_sets as _int
    INDOOR_BOX=_int.CAMERA_BOX
elif plan.get('set')=='cockpit':   # inside the flight deck, in front of the back wall, behind the panel
    import cabin as _cabin
    INDOOR_BOX=_cabin.COCKPIT_BOX
else: INDOOR_BOX=None
def inside(loc):
    if not INDOOR_BOX: return loc
    return Vector(tuple(min(hi,max(lo,v)) for v,(lo,hi) in zip(loc,INDOOR_BOX)))
pan_from={}
ROOMS=('apartment','office','diner','bedroom','hospital','interrogation')
def tall(a,t):
    """How tall someone is right now: seated about 72 % of standing, sitting down or rising in between."""
    h=catalog[a['name']]['height_m']; seg=sample(a,t)[0]
    if seg['action'] in ('sit_down','stand_up') or seg.get('clip') in ('Stand_To_Sit','Sit_To_Stand','Sit_To_Stand_F','Sit_To_Stand_M'): return h*.86
    if seg['action'] in ('sleep','sick'): return .45   # lying in bed: the camera frames the body on the pillow
    return h*.72 if seg['action']=='sit' else h
for frame in range(1,s.frame_end+1):
    s.frame_set(frame); t=(frame-1)/s.render.fps
    vehicles.animate(cars,plan,t)
    targets=[]
    for i,(actor,root,body,head,eyes,mouth,parts) in enumerate(rigs):
        seg,u,pos,yaw=sample(actor,t); action=seg['action']; intensity=seg['intensity']
        on=next((b for b in plan.get('aboard',()) if b['name']==actor['name'] and t>b['at']),None)
        if on:   # leapt aboard: rides with the vehicle from then on
            v=plan['vehicles'][on['vehicle']]; pos=(pos[0]+vehicles.vehicle_pose(v,t)[0]-vehicles.vehicle_pose(v,on['at'])[0],*pos[1:])
        riding=action=='ride' and actor['name']==plan['staging']['rider']
        if riding:
            mount=next(a for a in plan['actors'] if a['name']==plan['staging']['mount'])
            _,_,pos,yaw=sample(mount,t)
        preset=MOTIONS.get(action,{})
        action=preset.get('controller',action)
        if action=='wave' and math.dist(seg['from'],seg['to'])>.2: action='walk'  # wave while walking: legs walk, arm waves
        dancing=action in ('dance_a','dance_b')
        phase=t*math.tau*preset.get('tempo_hz',2.05 if action!='walk' else 1.3)+(0 if dancing else i*.65)
        moving=action in ('run','walk','duck')
        running=1 if moving else 0
        duck=(math.sin(math.pi*u)**.5)*intensity if action=='duck' else 0
        jump=math.sin(math.pi*u) if action=='jump' else 0
        elevation=jump*(.5+.7*intensity)
        scale=catalog[actor['name']]['height_m']/1.8
        bounce=(.025+.04*(1-math.cos(2*phase)))*running*(1-duck)
        if action=='walk': bounce=0
        root.location=Vector(pos)+Vector((0,0,(.04+bounce)*scale+elevation))
        if riding:
            mount_info=catalog[plan['staging']['mount']]
            root.location.z=mount_info['ride_height_m']+.12-.84*scale+.04*mount_info['height_m']/1.8
        if action=='pounce': root.location.z+=.5*math.sin(math.pi*u)
        if action=='animal_dodge': root.location.z+=.12*math.sin(math.pi*u)
        if action=='crouch': root.location.z-=.1*math.sin(math.pi*u)
        root.rotation_euler=(0,0,math.radians(yaw)); key(root,'location','rotation_euler')
        pelvis=.82 if action=='walk' else .88-.32*duck
        body.location=(0,0,pelvis)
        body.rotation_euler=(.13*running+.78*duck,.016*math.sin(t*2),.018*math.sin(phase)*running)
        combat=action in ('punch','dodge')
        combat_time=t-seg['start']
        hit=max(0,math.sin(combat_time*math.tau*1.1))**2
        if combat:
            pelvis=.77+.018*math.sin(t*math.tau*1.4)
            body.location.z=pelvis
            body.location.y=-.04*hit
            if action=='punch': body.rotation_euler=(.06+.10*hit,0,.10*math.sin(combat_time*math.tau*1.1))
            else:
                body.location.x=.09*math.sin(combat_time*math.tau*1.1)
                body.rotation_euler=(-.20*hit,.16*math.sin(combat_time*math.tau*1.1),0)
        if dancing:
            pelvis=.77+.025*math.cos(phase*2)
            body.location=(.06*math.sin(phase),0,pelvis)
            body.rotation_euler=(.025*math.sin(phase*2),.07*math.sin(phase),.10*math.sin(phase))
        key(body,'location','rotation_euler')
        head.rotation_euler=(.055*math.sin(t*4+i) if action=='talk' else 0,0,.025*math.sin(t*2))
        key(head,'rotation_euler')
        mouth.scale.z=.006+(.028*abs(math.sin(t*12))*intensity if action=='talk' else 0)
        key(mouth,'scale')
        for eye in eyes:
            eye.scale.z=.004 if (frame+i*31)%87<4 else .026; key(eye,'scale')
        bpy.context.view_layer.update()
        for side,thigh,shin,arm,fore,shoe,hand in parts:
            q=phase+(math.pi if side<0 else 0)
            hip=Vector((side*.12,0,pelvis))
            swing=.8*math.sin(q)*running*(.65 if action=='walk' else 1)
            a=swing+.8*jump+.5*duck
            knee=hip+Vector((0,-.4*math.sin(a),-.4*math.cos(a)))
            bend=(.25+1.2*max(0,math.cos(q)))*running+1.45*jump+.8*duck
            ankle=knee+Vector((0,-.4*math.sin(a-bend),-.4*math.cos(a-bend)))
            if action=='walk':
                speed=math.dist(seg['from'],seg['to'])/(seg['end']-seg['start'])
                foot_y,lift=walk_foot(t-seg['start'],speed,scale,side)
                ankle=Vector((side*.12,foot_y,.11-root.location.z/scale+lift))
                d=ankle-hip
                length=min(.839,max(.001,d.length)); d.normalize()
                ankle=hip+d*length
                # Bend the knee toward the character's forward direction, local -Y.
                perpendicular=Vector((0,d.z,-d.y)).normalized()
                knee=(hip+ankle)/2+perpendicular*math.sqrt(max(0,.42**2-(length/2)**2))
            if combat:
                hip.x=side*.16
                foot_y,lift=fight_foot(t,side)
                ankle=Vector((side*.19,foot_y,.11-root.location.z/scale+lift))
                d=ankle-hip; length=min(.839,max(.001,d.length)); d.normalize()
                ankle=hip+d*length
                perpendicular=Vector((0,d.z,-d.y)).normalized()
                knee=(hip+ankle)/2+perpendicular*math.sqrt(max(0,.42**2-(length/2)**2))
            if dancing:
                lift=max(0,math.sin(q))
                foot_x=side*(.17+(.15*lift if action=='dance_a' else 0))
                foot_y=-.17*lift if action=='dance_b' else 0
                ankle=Vector((foot_x,foot_y,.11-root.location.z/scale+lift*(.27 if action=='dance_b' else .08)))
                d=ankle-hip; length=min(.839,max(.001,d.length)); d.normalize()
                ankle=hip+d*length
                perpendicular=Vector((0,d.z,-d.y)).normalized()
                knee=(hip+ankle)/2+perpendicular*math.sqrt(max(0,.42**2-(length/2)**2))
            if riding:
                hip=Vector((side*.14,0,.84))
                knee=Vector((side*.40,-.16,.69))
                ankle=Vector((side*.46,-.12,.32))
            # Ground clamp + two-segment knee solve limits penetration during crouching.
            minimum=.105-root.location.z/scale
            if ankle.z<minimum and not riding:
                ankle.z=minimum
                d=ankle-hip; length=min(.799,max(.001,d.length))
                d.normalize(); ankle=hip+d*length
                perpendicular=Vector((0,d.z,-d.y)).normalized()
                knee=(hip+ankle)/2+perpendicular*math.sqrt(max(0,.4**2-(length/2)**2))
            bone(thigh,hip,knee); bone(shin,knee,ankle)
            shoe.location=ankle+Vector((0,-.06,-.035)); key(shoe,'location')
            shoe.rotation_euler.z=side*.12 if combat else 0
            key(shoe,'rotation_euler')
            shoulder=body.matrix_local@Vector((side*.24,0,.41))
            angle=-.7*math.sin(q)*running-.7*jump
            if action=='walk': angle=foot_y*1.5
            elbow=shoulder+Vector((side*.025,-.27*math.sin(angle),-.27*math.cos(angle)))
            wrist=elbow+Vector((0,-.26*math.cos(angle),.26*math.sin(angle)))
            if seg['action']=='wave' and side>0:
                elbow=shoulder+Vector((side*.2,-.05,.08))
                wrist=elbow+Vector((side*.09*math.sin(t*11),-.03,.25))
            if action=='talk': wrist+=Vector((side*.06*math.sin(t*3),-.08,.10+.12*math.sin(t*4+side)*intensity))
            if combat:
                extension=max(0,math.sin(combat_time*math.tau*1.1+(math.pi if side<0 else 0)))**2 if action=='punch' else 0
                extension*=intensity
                elbow=shoulder+Vector((side*.07,-.10-.22*extension,-.18+.17*extension))
                wrist=body.matrix_local@Vector((side*(.17-.07*extension),-.25-.43*extension,.49+.025*math.sin(combat_time*4)))
            if dancing:
                elbow=shoulder+Vector((side*(.13+.04*math.sin(q)),-.1,-.12))
                wrist=body.matrix_local@Vector((side*(.42+.10*math.cos(phase)),-.20,.40+.19*math.sin(q)))
            bone(arm,shoulder,elbow); bone(fore,elbow,wrist)
            hand.location=wrist; key(hand,'location')
        if actor['name'] in assets:
            animate_asset(assets[actor['name']],catalog[actor['name']],root,body,head,parts,action,t,u)
        if actor['name'] in realistic:
            rig=realistic[actor['name']]
            rig.location=Vector(pos)+Vector((0,0,root.location.z-(.04+bounce)*scale if riding else 0))
            if action in ('sleep','sick'): rig.location.z+={'bedroom':.48,'hospital':.5}.get(plan.get('set'),0)   # in bed: on the mattress (contacts.BEDS)
            rig.rotation_euler.z=rig['base_yaw']+math.radians(yaw)
            ride=next((v for v in plan.get('vehicles',()) if actor['name'] in (v.get('driver'),v.get('passenger'))),None)
            if ride:   # a driver sits in the driver's seat (a passenger beside them) and moves with the car
                x,y,z,vyaw,pitch,_=vehicles.vehicle_pose(ride,t); seat=Vector(vehicles.seat(ride))
                if ride.get('passenger')==actor['name']: seat.y=-seat.y
                seat.rotate(Euler((0,0,math.radians(vyaw)))); rig.location=Vector((x,y,z))+seat; root.location=rig.location.copy()
                rig.rotation_euler.z=rig['base_yaw']+math.radians(vyaw+90)   # characters face -y at yaw 0, cars +x
            cl=plan.get('climb')
            if cl and cl['name']==actor['name'] and t>=cl['grab']:   # up the helicopter's rope ladder, hand over hand
                hv=plan['vehicles'][0]; (lx,ly,lz),hy=vehicles.ladder_top(hv,t); (fx,fy),_=vehicles.ladder_foot(hv,t)
                rig.location=Vector((fx,fy,min(vehicles.CLIMB_RATE*(t-cl['grab']),max(lz-.1,0)))); root.location=rig.location.copy()
                rig.rotation_euler.z=rig['base_yaw']+math.radians(hy)
                if 'climb_scale' not in rig: rig['climb_scale']=rig.scale.x
                rig.scale=(rig['climb_scale'] if t<cl['top'] else .001,)*3; key(rig,'scale')   # in through the door: gone
            key(rig,'location','rotation_euler')
        targets.append(root.location+Vector((0,0,tall(actor,t)/2)))
    center=sum((targets[i] for i in present),Vector())/len(present)
    if plan['scene_type']=='auditorium': center=Vector((0,-1.6,1.1))
    shot=plan['camera']; framed=[rigs[i] for i in present]; begin=0; finish=plan['duration']  # in-shot cuts: latest cut at or before t
    for cut in plan.get('camera_cuts',()):
        if cut['time']<=t+1e-6: shot=cut; begin=cut['time']
        elif cut['time']<finish and cut['time']>begin and shot is not cut: finish=min(finish,cut['time'])
    car=shot.get('focus','').startswith('vehicle:') and int(shot['focus'][8:]) < len(cars)
    if car:   # the camera rides with a car: centred on it, no character framing
        v=plan['vehicles'][int(shot['focus'][8:])]; x,y,z,vyaw,*_=vehicles.vehicle_pose(v,t)
        center=Vector((x,y,z+{'car':.8,'plane':4,'train':2.2,'rocket':33,'satellite':0,'capsule':0,'helicopter':1.8}.get(v['kind'],22))); framed=[]
        if shot.get('target'):   # a point on the vehicle (its frame: x ahead), e.g. the cockpit windows
            tg=Vector(shot['target']); tg.rotate(Euler((0,0,math.radians(vyaw)))); center=Vector((x,y,z))+tg
    elif shot.get('focus'):
        framed=[r for r in rigs if r[0]['name']==shot['focus']] or rigs
        center=targets[[r[0]['name'] for r in rigs].index(framed[0][0]['name'])] if len(framed)==1 else center
    if 'aim' in shot and plan['scene_type']!='auditorium' and framed:  # headroom: aim higher on close shots
        heights=[root.location.z+tall(a,t)*shot['aim'] for a,root,*_ in framed]   # seated people: their seated height
        center.z=sum(heights)/len(heights)
    if plan.get('set')=='module':   # weightless: follow the bob of whoever is framed (the float below), after the aim height
        k=[*realistic].index(shot['focus']) if shot.get('focus') in realistic else None
        center=center+Vector((0,0,.3+(.07*math.sin(t*.55+k*1.7) if k is not None else 0)))
    centers.append(center.copy())
    sharp=center.copy()   # rack focus: in a shot holding two people, the focus pulls to whoever is speaking
    talk=next((l for l in plan.get('lines',()) if l['start']-.3<=t<l['end']+.2),None)
    if talk and len(framed)>=2:
        sp=next((r for r in framed if r[0]['name']==talk['speaker']),None)
        if sp: sharp=sp[1].location+Vector((0,0,tall(sp[0],t)*.9))
    focus_pts.append(sharp if not focus_pts or frame==1 else focus_pts[-1].lerp(sharp,1-math.exp(-1/(s.render.fps*.12))))
    if plan.get('set') in ('cockpit','train_cab','carriage','module'): framed=[]   # close angles placed by hand: a seated pilot at arm's length never fits whole
    off=Vector(shot['offset']); move=shot.get('move','static')
    u=min(1,max(0,(t-begin)/max(.1,finish-begin))); e=u*u*(3-2*u)  # eased progress through this angle
    span=min(1,(finish-begin)/8)  # short angles move less: 8 s gets the full move
    if move=='push_in': off*=1-.12*span*e
    elif move=='pull_out': off*=1-.12*span*(1-e)
    elif move=='orbit': off.rotate(Euler((0,0,math.radians((-6+12*e)*span))))
    elif move=='fly_in': off*=1-.7*e   # flies right up to the target (the cockpit windows)
    elif move=='crane': off.z+=2.5*span*(1-e); off.xy*=1+.12*span*(1-e)  # descends onto the cast
    elif move=='rise': off.z+=3*span*e; off.xy*=1+.2*span*e   # cranes up and back: the closing reveal
    elif move=='arc': off.rotate(Euler((0,0,math.radians((-20+40*e)*span))))   # a wide sweep round the hero moment
    elif move=='track':   # dollies sideways along the action (the camera on rails beside it)
        side=Vector((-off.y,off.x,0)).normalized() if off.xy.length>1e-6 else Vector((1,0,0)); off+=side*(-1.6+3.2*e)*span
    elif move=='dolly_zoom': off*=1-.45*span*e   # the vertigo shot: the camera pushes in as the lens widens (below)
    zoom_k[frame]=(1-.45*span*e) if move=='dolly_zoom' else 1   # the subject keeps its size, the world behind it stretches away
    if move=='pan': cam.location=pan_from.setdefault(begin,center.copy())+off   # stands still, turns to follow
    else: cam.location=center+off
    cam.location=inside(cam.location)
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    if shot.get('thirds') and len(framed)>=2:  # put the facing (far) character on a third, the near one opposite
        bpy.context.view_layer.update()
        dist=lambda r:(r[1].location-cam.location).length
        far=max(framed,key=dist); near=min(framed,key=dist)
        head=lambda r:r[1].location+Vector((0,0,tall(r[0],t)*.85))
        if begin not in thirds_side:
            thirds_side[begin]=.62 if world_to_camera_view(s,cam,head(near)).x<.5 else .38
        hfov=2*math.atan(18/shot['lens_mm'])
        for _ in range(2):
            bpy.context.view_layer.update()
            cam.rotation_euler.z+=(thirds_side[begin]-world_to_camera_view(s,cam,head(far)).x)*hfov
        framed=[far]  # the near character is a foreground shoulder: only the facing one must be fully in frame
    if move=='handheld':  # layered slow sines: operator sway, no jitter
        cam.rotation_euler.x+=.006*math.sin(t*1.7)+.003*math.sin(t*4.1+1)
        cam.rotation_euler.z+=.007*math.sin(t*1.3+2)+.003*math.sin(t*3.7)
        cam.location.z+=.015*math.sin(t*2.3)
    for shake in plan.get('shakes',()):  # short decaying jolt on heavy impacts
        dt=t-shake['time']
        if 0<=dt<.45:
            amp=shake['strength']*(1-dt/.45)**2
            cam.rotation_euler.x+=.012*amp*math.sin(dt*70); cam.rotation_euler.z+=.009*amp*math.sin(dt*53+1)
            cam.location.z+=.03*amp*math.sin(dt*61)
    if plan.get('set')=='deck':   # the ship rolls gently on the swell
        cam.rotation_euler=(cam.rotation_euler.to_quaternion()@Quaternion((0,0,1),.012*math.sin(t*.55))).to_euler()
    key(cam,'location','rotation_euler')
    # Evaluate conservative character envelopes; widen the lens to retain the cast.
    cam.data.lens=shot['lens_mm']
    bpy.context.view_layer.update()
    for attempt in range(14):
        visible=True
        for actor,root,*_ in framed:
            h=tall(actor,t)
            for dx in ((-.22,.22) if shot['lens_mm']>=70 else (-.5,.5)):
                for dy in ((-.22,.22) if shot['lens_mm']>=70 else (-.5,.5)):
                    for dz in ((h*.8,h+.06) if shot['lens_mm']>=70 else (0,h+.15)):   # a long lens is a close-up: head and shoulders
                        p=world_to_camera_view(s,cam,root.location+Vector((dx,dy,dz)))
                        if p.z<=0 or not .06<p.x<.94 or not .06<p.y<.94: visible=False
        if visible: break
        cam.data.lens*=.90
    cam.data.keyframe_insert(data_path='lens'); lens_log.append((frame,cam.data.lens,begin,cam.location.copy(),off.copy()))
    if zoom_k[frame]!=1: cam.data.lens*=zoom_k[frame]; cam.data.keyframe_insert(data_path='lens')
    if not visible: framing.append(frame)

# Smooth the zoom within each camera angle: the widest lens needed over the next/previous 1.5 s, eased over
# 1 s, so the lens never pumps as the cast moves. Cuts keep their own lens (hard change at the cut).
MIN_LENS=18 if INDOOR_BOX else 24  # wider than this distorts faces: the camera backs away along its offset instead (a cabin has no room)
def _smooth_lens(log,fps):
    W=int(1.5*fps); A=max(1,fps//2)
    angles={}
    for f,l,b,loc,off in log: angles.setdefault(b,[]).append((f,l,loc,off))
    for keys in angles.values():
        need=[k[1] for k in keys]
        wide=[min(need[max(0,i-W):i+W+1]) for i in range(len(need))]
        soft=[sum(wide[max(0,i-A):i+A+1])/len(wide[max(0,i-A):i+A+1]) for i in range(len(wide))]
        soft=[min(l,w*1.04) for l,w in zip(soft,wide)]
        R=1+.2/fps   # a zoom an operator would make: at most ~20 % a second (it starts earlier instead of snapping)
        for i in range(len(soft)-2,-1,-1): soft[i]=min(soft[i],soft[i+1]*R)   # widen ahead of need
        for i in range(1,len(soft)): soft[i]=min(soft[i],soft[i-1]*R)        # tighten back slowly
        for (f,_,loc,off),l in zip(keys,soft):
            lens=l*zoom_k.get(f,1)
            if lens<MIN_LENS:  # same framing from further back: field of view ~ distance / focal length
                cam.location=inside(loc+off*(MIN_LENS/lens-1)); cam.keyframe_insert(data_path='location',frame=f); lens=MIN_LENS
            cam.data.lens=lens; cam.data.keyframe_insert(data_path='lens',frame=f)
_smooth_lens(lens_log,s.render.fps)
if plan.get('director_camera'):   # the director framed this shot in Blender: film through those keys instead
    import director_cam; print('DIRECTOR CAMERA', director_cam.apply(cam,plan['director_camera'],s),'keys')

# These are baked per-frame poses: linear interpolation prevents Bezier overshoot.
for datablock in list(bpy.data.objects)+list(bpy.data.cameras):
    animation=datablock.animation_data
    if not animation or not animation.action: continue
    action=animation.action
    if hasattr(action,'layers'):
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for point in curve.keyframe_points: point.interpolation='LINEAR'
    else:
        for curve in action.fcurves:
            for point in curve.keyframe_points: point.interpolation='LINEAR'

warnings=[]
for actor in plan['actors']:
    build_nla(realistic[actor['name']],catalog[actor['name']],actor,s.render.fps,warnings,cam)
for rig in realistic.values():
    for bone in rig.pose.bones:
        for constraint in list(bone.constraints):bone.constraints.remove(constraint)
for obj in list(s.objects):
    if obj.type=='MESH' and obj.data.shape_keys:
        obj.data.shape_keys.animation_data_clear()
        for key in obj.data.shape_keys.key_blocks:key.value=0
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'scene.blend'))
print('SINGLE_RUN_ONLY',warnings)
