"""Exercise installed fitting, library assembly and Blender demos; no Meshy calls."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;D=H/'performance-verification';D.mkdir(exist_ok=True)
S=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server');sys.path.insert(0,str(S))
import character_workflow_face as face,character3d_api,character_workflow as workflow,blender_runner
source=S/'character_workflows/8fe21e60764a4190ae23f4f2df71fd65/body-rig.glb'
landmarks=json.loads((H/'amber-face-refinement/face.json').read_text());landmarks['source_mouth']='open'
report=face.fit(source,D/'fitted.glb',landmarks);assert report['upper_face_jaw_error']<1e-8
character3d_api.SAVED_MODELS_DIR=D
cached=list(D.glob('performance-test-*-expressions.glb'))
if cached:g=cached[-1]
else:
 model=character3d_api._finish_model('performance-test',(D/'fitted.glb').read_bytes(),{'joints_outside_mesh':[],'engine':'meshy'})
 g=D/model['animated']
checks=workflow.inspect_model(g)
track={'fps':24,'frames':72,'lead':0,'weights':{'jawOpen':[0]*12+[.1,.35,.55,.2]*9+[0]*24,'eyeBlinkLeft':[max(0,1-abs(i-35)/3) for i in range(72)],'eyeBlinkRight':[max(0,1-abs(i-35)/3) for i in range(72)]}}
(D/'track.json').write_text(json.dumps(track))
results={}
for mode in ('standing','scene','walking','running','circle'):
 test_track=track if mode in ('standing','scene') else {**track,'frames':24,'weights':{k:v[:24] for k,v in track['weights'].items()}}
 (D/'track.json').write_text(json.dumps(test_track))
 results[mode]=blender_runner.run('character_workflow_demo.py',{'glb':str(g),'track':str(D/'track.json'),'frames_dir':str(D/mode/'frames'),'mode':mode,'size':384,'front':landmarks['front'],'gesture_strength':.18},timeout=600)
 if mode in ('standing','scene'):workflow.inspect_model(D/mode/'performance.glb')
 workflow.encode(D/mode/'frames',S/'character_workflows/8fe21e60764a4190ae23f4f2df71fd65/demo/standing/voice.wav',D/mode/'demo.mp4',24,test_track['frames']/24,0)
(D/'report.json').write_text(json.dumps({'face':report,'structure':checks,'demos':results,'meshy_calls':0},indent=2))
print(json.dumps({'face_protection':True,'structural_checks':True,'demos':results,'meshy_calls':0}))
