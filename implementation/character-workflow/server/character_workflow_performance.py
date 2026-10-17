"""Engine-independent speech activity and conservative facial calibration math."""
import math

VERSION = 'character-performance/2'

def scene_soundtrack(source, destination):
    """Quiet original synthesized music under offline dialogue; no downloads."""
    import wave
    import numpy as np
    with wave.open(str(source)) as w:
        channels=w.getnchannels();rate=w.getframerate()
        if w.getsampwidth()!=2:raise ValueError('Scene soundtrack requires 16-bit PCM speech')
        voice=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float).reshape(-1,channels)/32768
    t=np.arange(len(voice))/rate;score=np.zeros_like(t)
    for start in np.arange(0,len(t)/rate,5):
        freq=(130.81,164.81,174.61,146.83)[int(start/5)%4];local=np.maximum(t-start,0)
        env=np.exp(-local/3.5)*(1-np.exp(-local*2))*(t>=start)
        score+=.014*env*(np.sin(2*np.pi*freq*t)+.35*np.sin(4*np.pi*freq*t))
    score*=np.minimum(1,np.maximum(0,(len(t)/rate-t)/.4))
    mixed=np.clip(voice+score[:,None],-.98,.98)
    with wave.open(str(destination),'wb') as w:
        w.setnchannels(channels);w.setsampwidth(2);w.setframerate(rate);w.writeframes((mixed*32767).astype('<i2').tobytes())
    return destination

def speech_envelope(jaw, fps, strength=.18):
    """Smooth gestures across syllables, fade to a quiet pose on pauses."""
    if fps <= 0: raise ValueError('fps must be positive')
    strength=max(0.,min(.35,float(strength)))
    activity=[float(v)>.045 for v in jaw]
    radius=max(1,round(fps*.18))
    activity=[any(activity[max(0,i-radius):i+radius+1]) for i in range(len(activity))]
    value=0.;out=[]
    for active in activity:
        tau=.22 if active else .45
        value+=(float(active)-value)*(1-math.exp(-1/(fps*tau)))
        out.append(value*strength)
    return out

def mouth_mode(boxes, requested='auto'):
    if requested not in ('auto','open','closed'):raise ValueError('Unknown source mouth pose')
    if requested!='auto':return requested
    m=boxes['mouth_opening']
    return 'open' if (m['y1']-m['y0'])/max(m['x1']-m['x0'],1e-6)>.22 else 'closed'

def jaw_deformation(vertices, parts, front, mode):
    """Local glTF y-up lower-jaw rotation. Upper face is explicitly protected.

    Source mouth is open: save a nearly closed basis and reverse it with jawOpen.
    Source mouth is closed: preserve the basis and rotate the lower jaw downward.
    """
    import numpy as np
    v=np.asarray(vertices,dtype=float);m=parts['mouth_opening'];nose=parts['nose'];head=parts['head'];f=1 if front>=0 else -1
    w=max(m['w'],1e-5);h=max(m['h'],w*.25);top=min(m['y']+h*.5,nose['y']-nose['h']*.45)
    def smooth(x):
        x=np.clip(x,0,1);return x*x*(3-2*x)
    near=(abs(v[:,0]-m['x'])<w*.7)&(abs(v[:,1]-m['y'])<h)
    if not near.any():raise ValueError('Mouth landmarks miss the surface; review the face')
    rim=float(np.percentile(v[near,2]*f,80))*f
    pivot_y=top; pivot_z=rim-f*w*.8
    weight=smooth((w*.8-abs(v[:,0]-m['x']))/(w*.35))*smooth((top-v[:,1])/(h*.35))*smooth((v[:,1]-(m['y']-h*1.8))/(h*.7))*smooth(((v[:,2]-pivot_z)*f)/(w*.4))
    angle=math.radians(22 if mode=='closed' else -22)*f
    dy=v[:,1]-pivot_y;dz=v[:,2]-pivot_z
    delta=np.zeros_like(v)
    delta[:,1]=pivot_y+np.cos(angle)*dy-np.sin(angle)*dz-v[:,1]
    delta[:,2]=pivot_z+np.sin(angle)*dy+np.cos(angle)*dz-v[:,2]
    delta*=weight[:,None]
    # Cap inferred closure on very elongated or uncertain animal faces.
    length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,head['w']*.16/np.maximum(length,1e-9))[:,None]
    if mode=='open':return delta*.88,-delta*.88,top
    return np.zeros_like(v),delta,top
