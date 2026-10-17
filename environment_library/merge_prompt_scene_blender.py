"""Combine separately baked actors; emit only routes and compact collision QA."""
import bpy,json,sys,math
from pathlib import Path
D=Path(sys.argv[sys.argv.index('--')+1]);p=json.loads((D/'plan.json').read_text());actors=p.get('actors') or [dict(character=p['character'],segments=p['segments'],position_cm=[0,0])]
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));from character_profiles import profile
bpy.ops.wm.open_mainfile(filepath=str(D/'actor_0/scene.blend'))
s=bpy.context.scene;catalog={};plan=json.loads((D/'actor_0/scene.json').read_text());plan['actors']=[];plan['lines']=[];plan['events']=p.get('events',[]);routes={};profiles={};rocks=[]
for i,a in enumerate(actors):
 folder=D/('actor_'+str(i));part=json.loads((folder/'scene.json').read_text());info=json.loads((folder/'catalog.json').read_text());name=profile(a['character'])['name']
 if i:
  with bpy.data.libraries.load(str(folder/'scene.blend'),link=False) as (src,dst):dst.objects=src.objects
  objects=[o for o in dst.objects if o];rig=next(o for o in objects if o.type=='ARMATURE');keep=[rig]+[o for o in objects if o.type=='MESH' and (o in rig.children_recursive or any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers))]
  for o in keep:s.collection.objects.link(o)
 else:rig=next(o for o in s.objects if o.type=='ARMATURE')
 rig.name=name+'_PerformanceRig';info[name]['armature']=rig.name;catalog.update(info);plan['actors']+=part['actors'];plan['lines']+=part['lines'];profiles[name]=a['character'];x,y=a.get('position_cm',[0,0]);rows=json.loads((folder/'route.json').read_text())
 for row in rows:row['location_cm'][0]+=x;row['location_cm'][1]+=y
 routes[name]=rows
 box_path=folder/'box-trajectory.json'
 if box_path.exists():
  box=json.loads(box_path.read_text());bumps=[row for row in box['rows'] if row['action']=='box_bump']
  if bumps:plan['events'].append({'type':'box_contact','time':bumps[len(bumps)//2]['frame']/24})
 for rock in json.loads((folder/'rocks.json').read_text()):rock['y']+=y;rock['x']=x;rocks.append(rock)
from scene_contacts import validate_routes
contact_report=validate_routes(routes)
(D/'catalog.json').write_text(json.dumps(catalog));(D/'scene.json').write_text(json.dumps(plan));(D/'routes.json').write_text(json.dumps(routes));(D/'profiles.json').write_text(json.dumps(profiles));(D/'rocks.json').write_text(json.dumps(rocks));(D/'contact-check.json').write_text(json.dumps(contact_report))
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(D/'scene.blend'))
