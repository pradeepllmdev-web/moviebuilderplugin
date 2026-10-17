import unreal,json
from pathlib import Path
H=Path(__file__).resolve().parent/'physics_lab'
world=unreal.EditorLevelLibrary.get_game_world()
actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
ignore=[a for a in actors if a.get_actor_label().startswith('Physics_')]
rows=[]
for x in [-1100,-1040,-1000,-800,-600,-300,-150,0,500]:
 hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,0,3000),unreal.Vector(x,0,-1000),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,unreal.DrawDebugTrace.NONE,True)
 t=hit.to_tuple()
 rows.append({'x':x,'z':t[5].z,'normal':list(t[7].to_tuple())} if t[0] else {'x':x,'miss':True})
ramp=next(a for a in actors if a.get_actor_label()=='LabRamp')
(H/'surface-probe.json').write_text(json.dumps({'ramp_rotation':list(ramp.get_actor_rotation().to_tuple()),'samples':rows},indent=2))
