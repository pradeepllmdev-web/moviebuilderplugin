"""Bounded, smoothly held head attention layered over the existing body animation."""
import math

def smooth(v):
 v=max(0,min(1,v));return v*v*(3-2*v)

def attention(segments,time):
 """Angles in degrees. Smoothly blend to the next beat instead of snapping at cuts."""
 current=next((g for g in segments if g['start']<=time<g['end']),segments[-1]);i=segments.index(current);previous=segments[i-1] if i else {'look_yaw_deg':current.get('look_from_yaw_deg',0),'look_pitch_deg':current.get('look_from_pitch_deg',0)}
 blend=smooth((time-current['start'])/.6)
 yaw=previous.get('look_yaw_deg',0)*(1-blend)+current.get('look_yaw_deg',0)*blend
 pitch=previous.get('look_pitch_deg',0)*(1-blend)+current.get('look_pitch_deg',0)*blend
 # A single restrained listening nod, not a repeating whole-body oscillation.
 if current.get('emotion')=='reassuring':pitch+=1.5*math.sin(math.pi*max(0,min(1,(time-current['start'])/1.5)))**2
 return yaw,pitch
