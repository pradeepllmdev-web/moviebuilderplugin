"""Typed, captured movement tracks. Never copies reference speech into target lips."""
import json
from pathlib import Path
import numpy as np

class RecordedBodySampler:
    def __init__(self,path,speed=.65,offset=0):
        from mathutils import Quaternion
        data=np.load(path,allow_pickle=False);self.times=data['time'];self.quaternions=data['quaternions'];self.names=list(data['names']);self.rest={str(n):Quaternion(v) for n,v in zip(self.names,data['rest'])}
        self.valid=np.convolve(data['valid'].astype(float),np.ones(7)/7,mode='same')
        self.start=0;self.end=float(self.times[-1])*24;self.speed=speed;self.offset=offset
    def confidence(self,t):
        return float(np.interp(t*self.speed+self.offset,self.times,self.valid))
    def pose(self,t,fps=24):
        from mathutils import Quaternion
        at=min(float(self.times[-1]),max(0,t*self.speed+self.offset));right=min(len(self.times)-1,max(1,int(np.searchsorted(self.times,at))));left=right-1
        alpha=(at-self.times[left])/max(.0001,self.times[right]-self.times[left])
        result={str(n):Quaternion(self.quaternions[left,i]).slerp(Quaternion(self.quaternions[right,i]),float(alpha)) for i,n in enumerate(self.names)}
        delta=result['Hips']@self.rest['Hips'].inverted()
        return {name:delta.inverted()@value for name,value in result.items()}

class TypedPerformanceBank:
    def __init__(self,bank_path):
        self.path=Path(bank_path);self.bank=json.loads(self.path.read_text());self.tracks={}
        if self.bank.get('schema')!='performance-reference-bank/1':raise ValueError('Invalid performance bank')
        for name,item in self.bank['references'].items():
            report=json.loads((self.path.parent/(name+'-capture.json')).read_text())
            if report['tracking_coverage']<.8:raise ValueError('Reference failed tracking gate: '+name)
            self.tracks[name]=dict(np.load(self.path.parent/(name+'.npz'),allow_pickle=False))
    def sample(self,name,t,kind):
        if kind not in self.bank['references'][name]['types']:raise ValueError('Reference does not support motion type: '+kind)
        data=self.tracks[name];times=data['time'];at=max(0,min(float(times[-1]),t));result={}
        for key in ('head_angles','expression'):
            if key in data:result[key]=np.array([np.interp(at,times,data[key][:,column]) for column in range(data[key].shape[1])])
        return result
    def facial_commands(self,t,offset=0):
        head=self.sample('head_attention',t*.50+offset*.35,'head_attention')['head_angles']
        expression=self.sample('face_expression',t+offset,'blink_brow_expression')['expression']
        scores=self.tracks['face_expression']['expression'][:,0]
        blink_neutral=float(np.percentile(scores,70));blink_peak=max(blink_neutral+.15,float(np.percentile(scores,99)))
        return {'head_yaw_variation':float(np.clip(head[1]/.5,-.25,.25)),
                'head_nod':float(np.clip(head[0]/.18,-.8,.8)),
                'head_roll':float(np.clip(head[2]/.15,-.7,.7)),
                'blink':float(np.clip((expression[0]-blink_neutral)/(blink_peak-blink_neutral),0,1)),
                'brow':float(np.clip(expression[1]*1.3,0,1)),
                'smile':float(np.clip(expression[2]*.5,0,.6)),
                'gaze_variation':float(np.clip(expression[3]*.3,-.15,.15))}
