"""Semantic facial commands mapped to calibrated native rig controls.

Profile math is independent of Blender. Blender imports occur only when binding.
No geometry is read, reconstructed, or printed by this adapter.
"""
import json
import math
from pathlib import Path

CHANNELS = {'jaw', 'blink', 'gaze', 'spread', 'smile', 'brow', 'head_yaw', 'head_nod','head_roll'}

def load_profile(path):
    profile = json.loads(Path(path).read_text(encoding='utf-8'))
    if profile.get('schema') != 'character-controls/1':
        raise ValueError('Unsupported character profile schema')
    if not profile.get('targets'):
        raise ValueError('Profile has no targets')
    for target in profile['targets']:
        if target.get('channel') not in CHANNELS:
            raise ValueError('Unknown semantic channel: '+str(target.get('channel')))
        if target.get('transform') not in ('location', 'rotation') or target.get('axis') not in (0,1,2):
            raise ValueError('Invalid target transform')
        if not target.get('bone') or not math.isfinite(target.get('scale', float('nan'))):
            raise ValueError('Invalid target bone or scale')
        if target.get('space','LOCAL') not in ('LOCAL','WORLD_DELTA'):
            raise ValueError('Invalid transform space')
        if target.get('space')=='WORLD_DELTA' and target['transform']!='location':
            raise ValueError('World deltas are only supported for translations')
    return profile

def speech_commands(visemes, amplitude, frame_index):
    """Existing heuristic visemes, with explicit lip-closure suppression."""
    clamp=lambda v: min(1,max(0,float(v)))
    closure=clamp(visemes['MBP'][frame_index])
    return {'jaw':clamp(amplitude[frame_index])*(1-closure)*(1-.35*clamp(visemes['FV'][frame_index])),
            'spread':max(-1,min(1,.4*visemes['E'][frame_index]-.6*visemes['O'][frame_index]))}

def evaluate_targets(profile, commands):
    unknown=set(commands)-CHANNELS
    if unknown:raise ValueError('Unknown commands: '+', '.join(sorted(unknown)))
    result={}
    for target in profile['targets']:
        value=float(commands.get(target['channel'],0))
        if not math.isfinite(value):raise ValueError('Nonfinite semantic value')
        value=max(-1 if target['channel'] in ('gaze','spread','head_yaw','head_nod','head_roll') else 0,min(1,value))
        key=(target['bone'],target['transform'],target.get('space','LOCAL'))
        result.setdefault(key,[0.,0.,0.])[target['axis']]+=value*target['scale']
    return result

class RigController:
    def __init__(self, rig, profile, height):
        self.rig,self.profile,self.height=rig,profile,height
        missing=sorted({t['bone'] for t in profile['targets']} - set(rig.pose.bones.keys()))
        if missing:raise ValueError('Rig does not match profile; missing controls: '+', '.join(missing))
        for setting in profile.get('properties',[]):
            bone=rig.pose.bones.get(setting['bone'])
            if bone is None or setting['name'] not in bone:
                raise ValueError('Missing rig setup property: '+setting['name'])
        for setting in profile.get('properties',[]):
            rig.pose.bones[setting['bone']][setting['name']]=setting['value']
        if profile.get('properties'):rig.update_tag()
        self.capabilities=sorted({t['channel'] for t in profile['targets']})

    def key(self, frame, commands):
        from mathutils import Vector,Euler
        targets=evaluate_targets(self.profile,commands)
        locations={};rotations={}
        for (name,transform,space),values in targets.items():
            bone=self.rig.pose.bones[name]
            if transform=='rotation':
                rotations.setdefault(name,Vector((0,0,0)))[:]=values
            else:
                vector=Vector(values)
                if space=='WORLD_DELTA':
                    vector=bone.bone.matrix_local.to_3x3().inverted() @ self.rig.matrix_world.to_3x3().inverted() @ (vector*self.height)
                locations[name]=locations.get(name,Vector((0,0,0)))+vector
        for name,vector in locations.items():
            bone=self.rig.pose.bones[name]
            for axis,locked in enumerate(bone.lock_location):
                if locked:vector[axis]=0
            bone.location=vector;bone.keyframe_insert('location',frame=frame)
        for name,vector in rotations.items():
            bone=self.rig.pose.bones[name]
            if bone.rotation_mode=='QUATERNION':
                bone.rotation_quaternion=Euler(vector,'XYZ').to_quaternion();path='rotation_quaternion'
            elif bone.rotation_mode=='AXIS_ANGLE':
                raise ValueError('Axis-angle controls need an explicit adapter')
            else:
                bone.rotation_euler=Euler(vector,bone.rotation_mode);path='rotation_euler'
            bone.keyframe_insert(path,frame=frame)
