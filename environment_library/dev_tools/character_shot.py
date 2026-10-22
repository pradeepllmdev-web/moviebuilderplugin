"""Blender script: a close look at one character at one moment (to check faces, hands, hair, stance, clothing edges).

    blender -b scene_04_chime.blend --python dev_tools/character_shot.py -- <seconds> <character id> <face|body> <out.png>

Works for people built on the humanoid rig (their face parts are named <id>_eyeL ...)."""
import bpy,sys
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:];t=float(a[0]);who=a[1];mode=a[2];out=a[3];s=bpy.context.scene
[s.timeline_markers.remove(m) for m in list(s.timeline_markers)];s.frame_set(int(s.frame_start+t*s.render.fps))
rig=bpy.data.objects[who+'_eyeL'].parent;eye=bpy.data.objects[who+'_eyeL'].matrix_world.translation;hp=rig.matrix_world@rig.pose.bones['Head'].head
d=Vector((eye.x-hp.x,eye.y-hp.y,0)).normalized();c=eye if mode=='face' else rig.matrix_world@rig.pose.bones['spine_02'].head
cam=bpy.data.objects.new('CC',bpy.data.cameras.new('CC'));s.collection.objects.link(cam);cam.data.lens=60 if mode=='face' else 50
cam.location=c+d*(1.1 if mode=='face' else 3.2)+Vector((0,0,.03 if mode=='face' else .1));cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=640;s.render.resolution_y=640 if mode=='face' else 800;s.render.filepath=out;bpy.ops.render.render(write_still=True);print('OK',out)
