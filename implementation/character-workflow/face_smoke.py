from pathlib import Path
import json,sys
sys.path[:0]=['C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server',str(Path(__file__).resolve().parent/'server')]
import character_workflow_face as face
import meshy_character
H=Path(__file__).resolve().parent
source=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/samples/lion-open-mouth-meshy/rigged.glb')
(H/'face-smoke-body.glb').write_bytes(meshy_character.rename_bones(source.read_bytes())[0])
# Calibrated only for this local smoke fixture; production obtains these from vision.
fixture={'front':-1,'render':{'center':[0,.86], 'scale':1.9},'boxes':{'image_left_eye':{'x0':435,'x1':475,'y0':210,'y1':250},'image_right_eye':{'x0':525,'x1':565,'y0':210,'y1':250},'mouth_opening':{'x0':440,'x1':560,'y0':300,'y1':340},'head':{'x0':300,'x1':700,'y0':100,'y1':450},'chin':{'x0':450,'x1':550,'y0':340,'y1':380},'nose':{'x0':465,'x1':535,'y0':270,'y1':300},'image_left_brow':{'x0':430,'x1':475,'y0':180,'y1':205},'image_right_brow':{'x0':525,'x1':570,'y0':180,'y1':205}},'separate_mouth':True,'separate_eyes':False}
try:
 result=face.fit(H/'face-smoke-body.glb',H/'face-smoke-output.glb',fixture)
 print(json.dumps({'oral_parts':result['oral_parts'],'hidden_interior_faces':result['hidden_interior_faces'],'morph_count':len(result['morphs'])}))
except Exception:
 raise

