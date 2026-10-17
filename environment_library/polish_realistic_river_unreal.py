"""Add ecological layers and neutral lighting to the currently built river set."""
import unreal, json, traceback
from pathlib import Path
H=Path(__file__).resolve().parent
try:
    from unreal_bridge.realworld import scan_library, _pick, CONIFER, BIRCH
    from unreal_bridge.forest import handle_add_forest
    from unreal_bridge.moods import handle_apply_mood
    latest=json.loads((H/'demos/latest-realistic-river.json').read_text())
    D=Path(latest['directory'])
    report=json.loads((D/'build-result.json').read_text())
    lib=scan_library()
    def meshes(kind,prefer=None):
        return [m for e in _pick(lib,kind,prefer,None) for m in e['meshes'][:6]]
    layers=[{'meshes':meshes('tree',CONIFER),'density':2.3,'scale':[.65,1.15]},
            {'meshes':meshes('tree',BIRCH),'density':.45,'scale':[.65,1.05]}]
    backdrop=handle_add_forest({'layers':layers,'center':[0,8500],'size':14000,'density':1,'seed':89,
                               'clumping':.65,'clearings':.03,'label':'River_BackgroundWoods'})
    shore=[]
    for i,(x,y,radius) in enumerate([(-2400,450,1500),(2400,650,1500),(-2300,2800,1300),(2300,2800,1300)]):
        layers=[{'meshes':meshes('rock'),'density':1.4,'scale':[.3,.9],'sink':15,'align':True,'species':'rock'},
                {'meshes':meshes('grass'),'density':190,'scale':[.8,1.35],'in_clear':True},
                {'meshes':meshes('fern'),'density':15,'scale':[.65,1.2]}]
        for layer in layers:layer['within']=[x,y,radius]
        shore.append(handle_add_forest({'layers':layers,'center':[x,y],'size':radius*2,'density':1,
                  'seed':100+i,'clumping':.75,'clearings':.08,'label':'River_Shore_'+str(i)}))
    handle_apply_mood({'mood':'blockbuster','weather':False,'sun_azimuth':120})
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        if isinstance(actor,unreal.ExponentialHeightFog):
            actor.component.set_editor_property('fog_density',.012)
    path=report['level']+'_Polished'
    n=1
    while unreal.EditorAssetLibrary.does_asset_exist(path):
        n+=1;path=report['level']+'_Polished_v'+str(n)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert unreal.EditorLoadingAndSavingUtils.save_map(world,path)
    report.update(level=path,polish={'background':backdrop,'shore':shore,'lighting':'neutral daylight, light haze'})
    (D/'build-result.json').write_text(json.dumps(report,indent=2))
except Exception:
    (H/'demos/river-polish-error.txt').write_text(traceback.format_exc())
    raise
