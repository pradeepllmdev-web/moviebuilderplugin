"""Procedural body language on top of the clips (pure Python + numpy): the small motions that make a standing character look alive and make a line of dialogue look meant.

    sig=perf_body.signals(plan, who)        {bone: array (n,3) of local Euler angles (pitch down, yaw left, roll) in radians} for the keys at frames 1,3,5,... ; bones Hips, Spine, Spine1, Spine2, Neck, Head
perf_scene keys these as a COMBINE layer over the NLA clips (the rig's chain bones have local X = sideways, Y = up, Z = forward, measured), so they add to whatever clip is playing.

What it contains:
 * breathing and a slow weight sway, out of phase between characters;
 * speaking: head nods on the stressed syllables of the line (stronger when angry or happy, small when sad), the delivery posture of the mood (sad: head and chest down; angry: chest forward; joy: chin up; concern: a little tilt), a questioning tilt on the last second of a question;
 * listening: slow nods at the start of what is said to the character, two small ones before its end when the mood invites agreement;
 * turning: the upper body, neck and head lead the body's turn (look-ahead of the plan's heading) and the root catches up, instead of the whole character rotating as one block.
Everything is a function of the plan, so it is deterministic and testable."""
import math
import numpy as np
BONES=('Hips','Spine','Spine1','Spine2','Neck','Head')
NOD_MOODS=('serious','warm','concern','joy')
LEAD_W={'Spine':.18,'Spine1':.3,'Spine2':.27,'Neck':.2,'Head':.12}      # share of the look-ahead turn each bone takes
def _wrap(a):return (a+math.pi)%(2*math.pi)-math.pi
def _bump(t,t0,amp,rise=.05,fall=.14):
 """a nod: quick rise, slower fall (arrays or scalars)"""
 d=t-t0;return np.where(d<0,0.,np.where(d<rise,amp*d/rise,amp*np.exp(-(d-rise)/fall)))
def signals(plan,who,step=2):
 a=plan.actors[who];n=plan.frames;frames=np.arange(1,n+1,step);t=(frames-1)/24.;m=len(t);sig={b:np.zeros((m,3)) for b in BONES}
 ph=(sum(map(ord,who))%100)/100.*2*math.pi
 sig['Spine1'][:,0]+=.010*np.sin(2*math.pi*.28*t+ph);sig['Spine2'][:,0]+=.014*np.sin(2*math.pi*.28*t+ph+.4);sig['Neck'][:,0]-=.006*np.sin(2*math.pi*.28*t+ph)
 sig['Hips'][:,2]+=.02*np.sin(2*math.pi*.11*t+ph*1.7);sig['Spine'][:,2]-=.012*np.sin(2*math.pi*.11*t+ph*1.7);sig['Spine1'][:,1]+=.015*np.sin(2*math.pi*.07*t+ph)
 H=np.array(a.H);idx=np.minimum(frames-1,len(H)-1);ahead=np.minimum(idx+6,len(H)-1);lead=np.clip([_wrap(H[j]-H[i]) for i,j in zip(idx,ahead)],-.8,.8)
 for b,w in LEAD_W.items():sig[b][:,1]+=w*lead
 for L in plan.lines:
  t0,t1=L['t0'],L['t1'];mood=L['mood']
  if L['speaker']==who:
   ramp=np.clip(np.minimum((t-t0+.3)/.4,(t1+.4-t)/.4),0,1)
   gain={'angry':1.5,'joy':1.2,'sad':.5,'warm':1.0,'serious':.9,'concern':.8}.get(mood,1.)
   if mood=='sad':sig['Head'][:,0]+=.12*ramp;sig['Spine1'][:,0]+=.08*ramp;sig['Neck'][:,0]+=.05*ramp
   elif mood=='angry':sig['Spine1'][:,0]+=.06*ramp;sig['Head'][:,0]-=.04*ramp;sig['Spine2'][:,0]+=.03*ramp
   elif mood=='joy':sig['Head'][:,0]-=.05*ramp;sig['Spine2'][:,0]-=.02*ramp
   elif mood=='concern':sig['Head'][:,2]+=.06*ramp
   syl=L['syl'];k=len(syl);ts=np.linspace(t0+.25,t1-.2,max(1,k))
   for j,v in enumerate(syl):
    if v in 'ao' or j%3==0:
     tj=ts[j];amp=.05*gain*(1.0 if v in 'ao' else .6);sig['Head'][:,0]+=_bump(t,tj,amp);sig['Neck'][:,0]+=_bump(t,tj,amp*.5);sig['Spine2'][:,0]+=_bump(t,tj,amp*.25)
   if L['text'].rstrip().endswith('?'):
    q=np.clip((t-(t1-.9))/.4,0,1)*np.clip((t1+.5-t)/.4,0,1);sig['Head'][:,2]+=.12*q;sig['Head'][:,0]-=.04*q
  elif L['to']==who and a.state=='stand':
   sig['Head'][:,0]+=_bump(t,t0+.8,.04,.12,.3)
   if mood in NOD_MOODS:
    for tt in (t1-1.0,t1-.45):sig['Head'][:,0]+=_bump(t,tt,.07,.1,.2);sig['Neck'][:,0]+=_bump(t,tt,.03,.1,.2)
 for b in sig:sig[b]=np.clip(sig[b],-.35,.35)
 return sig
def key_frames(plan,step=2):return list(range(1,plan.frames+1,step))
