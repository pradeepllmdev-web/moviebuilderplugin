"""Conversation attention: held looks with eased turns, not perpetual head sway."""
import math

def ease(value):
    value=max(0,min(1,value));return value*value*(3-2*value)

def attention_commands(actor,t,shots,partner_side):
    if partner_side not in (-1,1):raise ValueError('Partner side must be -1 or 1')
    # Cinematic three-quarter looks: speakers briefly address the forward mark,
    # listeners turn farther toward their partner. Eyes lead head motion.
    def focus(at):
        shot=next((s for s in shots if s['start']<=at<s['start']+s['duration']),shots[-1])
        return .50 if shot['speaker']==actor else .85
    def value(at,lead=0):
        result=focus(0)
        for shot in shots[1:]:
            boundary=shot['start'];before=focus(boundary-.01);after=focus(boundary+.01)
            result+=(after-before)*ease((at+lead-boundary+.18)/.85)
        return partner_side*result*ease((at+lead)/.85)
    head=value(t);eyes=value(t,.18)
    # Brief return toward the path, then back to the conversation.
    glance=ease((t-7.0)/.45)*(1-ease((t-8.1)/.55))
    head*=1-.7*glance
    # One small emphasis or acknowledgement per shot, with a held neutral rest.
    shot=next((s for s in shots if s['start']<=t<s['start']+s['duration']),shots[-1])
    local=t-shot['start'];centre=1.25 if shot['speaker']==actor else 2.55
    pulse=max(0,1-abs(local-centre)/.45)
    nod=math.sin(math.pi*.5*pulse)**2*(.65 if shot['speaker']==actor else .4)
    return {'head_yaw':head,'head_nod':nod,'gaze':max(-1,min(1,(eyes-head)*2.5+partner_side*.12))}
