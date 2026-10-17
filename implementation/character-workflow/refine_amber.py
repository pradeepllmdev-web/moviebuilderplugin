import asyncio,json,sys,shutil
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path[:0]=['C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server',str(H/'server')]
import character_workflow_landmarks as landmarks
import character_workflow_face as fitter
base=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server/character_workflows/8fe21e60764a4190ae23f4f2df71fd65')
out=H/'amber-face-refinement';out.mkdir(exist_ok=True);shutil.copy2(base/'front.png',out/'front.png')
async def run():
 face=await landmarks.detect(base/'body-rig.glb',out,json.loads((base/'face.json').read_text()))
 face.update(separate_eyes=False,separate_mouth=True)
 (out/'face.json').write_text(json.dumps(face,indent=2))
 result=fitter.fit(base/'body-rig.glb',out/'character.glb',face)
 (out/'fit-report.json').write_text(json.dumps(result,indent=2))
 print('Refined face generated; visual review required.')
asyncio.run(run())
