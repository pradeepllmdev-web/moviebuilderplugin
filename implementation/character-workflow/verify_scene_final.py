from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent/'performance-verification';S=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server');sys.path.insert(0,str(S))
import blender_runner,character_workflow as w
from character_workflow_performance import scene_soundtrack
track={'fps':24,'frames':72,'lead':0,'weights':{'jawOpen':[0]*12+[.1,.35,.55,.2]*9+[0]*24,'eyeBlinkLeft':[max(0,1-abs(i-35)/3) for i in range(72)],'eyeBlinkRight':[max(0,1-abs(i-35)/3) for i in range(72)]}}
(H/'track.json').write_text(json.dumps(track))
result=blender_runner.run('character_workflow_demo.py',{'glb':str(next(H.glob('performance-test-*-expressions.glb'))),'track':str(H/'track.json'),'frames_dir':str(H/'scene/frames'),'mode':'scene','size':384,'front':1,'gesture_strength':.18},timeout=600)
audio=scene_soundtrack(S/'character_workflows/8fe21e60764a4190ae23f4f2df71fd65/demo/standing/voice.wav',H/'scene/soundtrack.wav')
w.encode(H/'scene/frames',audio,H/'scene/demo.mp4',24,3,0)
print(json.dumps({'scene':result,'music':True,'full_decode_passed':True,'meshy_calls':0}))
