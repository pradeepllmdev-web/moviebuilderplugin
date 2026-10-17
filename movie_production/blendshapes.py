"""Shared facial commands for calibrated morph-target characters."""
import math

def expression_weights(commands):
    def value(name,default=0):
        number=float(commands.get(name,default))
        if not math.isfinite(number):raise ValueError('Nonfinite facial command: '+name)
        return max(-1 if name in ('gaze','spread') else 0,min(1,number))
    jaw=value('jaw');blink=value('blink');gaze=value('gaze');spread=value('spread')
    weights={'jawOpen':jaw,'mouthClose':value('mouth_close'),'mouthPressLeft':value('lip_press'),'mouthPressRight':value('lip_press'),
        'eyeBlinkLeft':blink,'eyeBlinkRight':blink,
        'browInnerUp':value('brow')*.65,'mouthSmileLeft':value('smile')*.55,'mouthSmileRight':value('smile')*.55,
        'mouthStretchLeft':max(0,spread)*.6,'mouthStretchRight':max(0,spread)*.6,
        'mouthFunnel':max(0,-spread)*.65,'mouthPucker':max(0,-spread)*.35,
        'eyeLookOutLeft':max(0,gaze)*.45,'eyeLookInRight':max(0,gaze)*.45,
        'eyeLookInLeft':max(0,-gaze)*.45,'eyeLookOutRight':max(0,-gaze)*.45}
    return weights

class BlendshapeController:
    def __init__(self,objects,profile):
        if profile.get('schema')!='blendshape-controls/1':raise ValueError('Invalid morph profile')
        self.bindings={};self.objects=objects
        for semantic,key_name in profile['mapping'].items():
            bindings=[obj.data.shape_keys.key_blocks[key_name] for obj in objects
                      if obj.data.shape_keys and key_name in obj.data.shape_keys.key_blocks]
            if not bindings:raise ValueError('Missing facial morph: '+key_name)
            self.bindings[semantic]=bindings
        required={'eyeBlinkLeft','eyeBlinkRight'}
        if profile.get('require_jaw_morph',True):required.add('jawOpen')
        if not required<=self.bindings.keys():
            raise ValueError('Jaw and independent eyelids are required')

    def key(self,frame,commands):
        for semantic,weight in expression_weights(commands).items():
            for key in self.bindings.get(semantic,[]):
                key.value=weight;key.keyframe_insert('value',frame=frame)
