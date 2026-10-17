"""Position-based partner attention for stationary conversation shots."""
import math

def partner_angles(position,target,body_yaw,eye_height,target_eye_height):
 dx=target[0]-position[0];dy=target[1]-position[1];distance=math.hypot(dx,dy)
 if distance<90:raise ValueError('Partners need at least 90 cm separation')
 desired=math.degrees(math.atan2(-dx,dy));relative=(desired-body_yaw+180)%360-180
 yaw=max(-35,min(35,relative));pitch=max(-8,min(8,math.degrees(math.atan2(target_eye_height-eye_height,distance))))
 return {'body_yaw_deg':body_yaw,'head_yaw_deg':yaw,'head_pitch_deg':pitch,'remaining_yaw_error_deg':abs(relative-yaw)}

def conversation_context(plan,actor):
 others=[a for a in plan.get('actors',[]) if a['character']!=actor['character']]
 if not any(g.get('look_at')=='partner' for g in actor['segments']):return None
 if len(others)!=1:raise ValueError('Partner gaze requires exactly two actors')
 other=others[0]
 if any(g['action'] not in ['idle','talk'] for a in [actor,other] for g in a['segments']):raise ValueError('Partner gaze currently supports stationary conversation; use manual glances while moving')
 pos=actor.get('position_cm',[0,0]);target=other.get('position_cm',[0,0]);desired=math.degrees(math.atan2(-(target[0]-pos[0]),target[1]-pos[1]))
 body=actor.get('facing_yaw_deg',desired-max(-35,min(35,desired)))
 heights={'lion':163,'cat':132,'rowan':168}
 result=partner_angles(pos,target,body,heights[actor['character']],heights[other['character']])
 if result['remaining_yaw_error_deg']>10:raise ValueError('Body facing requires an excessive head turn; change facing_yaw_deg or allow automatic orientation')
 return result
