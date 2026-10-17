import sys,json
from pathlib import Path
sys.path.insert(0,'C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server')
import auto_rig
H=Path(__file__).resolve().parent
blob,info=auto_rig.auto_rig_glb(H/'model.glb',tpose=True,face=None)
(H/'rigged.glb').write_bytes(blob)
(H/'local-rig.json').write_text(json.dumps({'method':'free local auto_rig','joints':info['joints'],'textured':info['textured'],'outside_joints':info['joints_outside_mesh'],'review_required':True,'meshy_rig_error':'HTTP 402; no successful paid rig task'},indent=2));print(json.dumps({'joints':info['joints'],'textured':info['textured'],'outside_joints':info['joints_outside_mesh']}))
