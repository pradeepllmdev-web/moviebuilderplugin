"""Opt-in upper-body retargeter for existing human clip library.

Source actions only are loaded; no source meshes. Stationary bipeds only.
Facial bones, root translation and foot controls are never keyed here.
"""
import json,math
from pathlib import Path

def smooth_activity(t,intervals,fade=.35):
    def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
    return max((smooth((t-start)/fade)*smooth((end-t)/fade) for start,end in intervals),default=0)

def load_body_profile(path):
    data=json.loads(Path(path).read_text())
    if data.get('schema')!='body-retarget/1' or data.get('anatomy')!='biped':raise ValueError('A calibrated biped profile is required')
    if not data.get('mapping') or len(set(data['mapping'].values()))!=len(data['mapping']):raise ValueError('Invalid body mapping')
    allowed={'Spine','Spine1','Spine2','LeftArm','LeftForeArm','LeftHand','RightArm','RightForeArm','RightHand'}
    if set(data['mapping'])-allowed:raise ValueError('This adapter supports stationary torso and arms only')
    strength=data.get('gesture_strength',.55)
    if not isinstance(strength,(int,float)) or not math.isfinite(strength) or not 0<=strength<=1:raise ValueError('Gesture strength must be between zero and one')
    return data

class ClipSampler:
    PARENTS={'Hips':None,'Spine':'Hips','Spine1':'Spine','Spine2':'Spine1','Neck':'Spine2','Head':'Neck',
             'LeftShoulder':'Spine2','LeftArm':'LeftShoulder','LeftForeArm':'LeftArm','LeftHand':'LeftForeArm',
             'RightShoulder':'Spine2','RightArm':'RightShoulder','RightForeArm':'RightArm','RightHand':'RightForeArm'}
    def __init__(self,action):
        from mathutils import Quaternion
        self.action=action;self.rest={k.split(':')[-1]:Quaternion(v) for k,v in json.loads(action['rest']).items()}
        self.curves={}
        from realistic_rig import bone_curves
        for name,properties in bone_curves(action).items():
            if 'rotation_quaternion' in properties:self.curves[name.split(':')[-1]]=properties['rotation_quaternion']
        self.start,self.end=action.frame_range
        missing=set(self.PARENTS)-set(self.rest)
        if missing:raise ValueError('Source clip skeleton is incomplete: '+str(sorted(missing)))

    def pose(self,t,fps=24):
        from mathutils import Quaternion
        frame=self.start+(t*fps)%max(1,self.end-self.start);result={}
        for name,parent in self.PARENTS.items():
            local=Quaternion([curve.evaluate(frame) for curve in self.curves[name]]).normalized() if name in self.curves else Quaternion()
            base=result[parent]@self.rest[parent].inverted()@self.rest[name] if parent else self.rest[name]
            result[name]=base@local
        # Existing human adapter removes clip root heading. Keep that policy:
        # a standing gesture must not turn the whole actor away from its mark.
        root_delta=result['Hips']@self.rest['Hips'].inverted()
        result={name:root_delta.inverted()@rotation for name,rotation in result.items()}
        return result

class BodyRetargeter:
    def __init__(self,rig,profile,talk,idle):
        import bpy
        self.rig,self.profile,self.talk,self.idle=rig,profile,talk,idle
        missing=set(profile['mapping'].values())|{profile['alignment_bone']}
        missing-=set(rig.pose.bones.keys())
        if missing:raise ValueError('Missing body controls: '+', '.join(sorted(missing)))
        for setting in profile.get('properties',[]):
            bone=rig.pose.bones.get(setting['bone'])
            if bone is None or setting['name'] not in bone:raise ValueError('Missing body rig switch: '+setting['name'])
        for setting in profile.get('properties',[]):rig.pose.bones[setting['bone']][setting['name']]=setting['value']
        rig.update_tag();bpy.context.view_layer.update()
        self.align=rig.data.bones[profile['alignment_bone']].matrix_local.to_quaternion()@talk.rest[profile.get('source_alignment','Spine')].inverted()
        self.align_idle=rig.data.bones[profile['alignment_bone']].matrix_local.to_quaternion()@idle.rest[profile.get('source_alignment','Spine')].inverted()
        self.rest={source:rig.data.bones[target].matrix_local.to_quaternion() for source,target in profile['mapping'].items()}
        self.order=sorted(profile['mapping'],key=lambda source:len(rig.pose.bones[profile['mapping'][source]].parent_recursive))
        self.previous_quaternions={}
        self.previous_frames={}
        # Mean poses retain a relaxed stance while dampening recorded gestures.
        from mathutils import Quaternion
        self.means={}
        for label,sampler in [('talk',talk),('idle',idle)]:
            poses=[sampler.pose(i/24) for i in range(0,int(sampler.end-sampler.start),4)]
            self.means[label]={}
            for source in self.order:
                reference=poses[0][source];values=[q[source] if reference.dot(q[source])>=0 else -q[source] for q in poses]
                self.means[label][source]=Quaternion([sum(q[k] for q in values)/len(values) for k in range(4)]).normalized()

    def key(self,frame,t,speaking):
        import bpy
        from mathutils import Vector,Matrix,Quaternion
        talk=self.talk.pose(t);idle=self.idle.pose(t);strength=self.profile.get('gesture_strength',.55)
        if hasattr(self.talk,'confidence'):speaking*=max(0,min(1,self.talk.confidence(t)))
        for source in self.order:
            target=self.profile['mapping'][source];bone=self.rig.pose.bones[target]
            a=self.means['idle'][source].slerp(idle[source],strength)
            b=self.means['talk'][source].slerp(talk[source],strength)
            pose=(self.align_idle@a).slerp(self.align@b,speaking)
            if source in ('Spine','Spine1','Spine2'):
                neutral=(self.align_idle@self.means['idle'][source]).slerp(self.align@self.means['talk'][source],speaking)
                delta=pose@neutral.inverted()
                if delta.w<0:delta=-delta
                limit=math.radians(self.profile.get('torso_limit_degrees',7))
                if delta.angle>limit:delta=Quaternion().slerp(delta,limit/delta.angle)
                desired=delta@self.rest[source]
            else:
                difference=(self.align@self.talk.rest[source]).inverted()@self.rest[source]
                twist=Quaternion((difference.w,0,difference.y,0))
                desired=pose@(twist.normalized() if twist.magnitude>1e-6 else Quaternion())
            bpy.context.view_layer.update()
            location=bone.matrix.translation.copy();bone.rotation_mode='QUATERNION'
            bone.matrix=Matrix.LocRotScale(location,desired,Vector((1,1,1)))
            previous=self.previous_quaternions.get(target)
            if previous is not None and previous.dot(bone.rotation_quaternion)<0:bone.rotation_quaternion.negate()
            speed=self.profile.get('max_angular_speed_degrees')
            if previous is not None and speed:
                angle=previous.rotation_difference(bone.rotation_quaternion).angle
                limit=math.radians(speed)*(frame-self.previous_frames[target])/24
                if angle>limit:bone.rotation_quaternion=previous.slerp(bone.rotation_quaternion,limit/angle)
            self.previous_quaternions[target]=bone.rotation_quaternion.copy()
            self.previous_frames[target]=frame
            bone.keyframe_insert('rotation_quaternion',frame=frame)
        bpy.context.view_layer.update()
