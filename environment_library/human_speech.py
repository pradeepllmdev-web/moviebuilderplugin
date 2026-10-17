"""Bounded ARKit mouth cues from the existing heuristic viseme solver."""
def speech_values(shapes,index,amplitude):
 get=lambda name:max(0,min(1,shapes.get(name,[0]*(index+1))[index]))
 closure=get('MBP');opening=max(0,min(.8,amplitude*.8))*(1-.85*closure)
 return {'jawOpen':opening,'mouthClose':closure*.65,'mouthPressLeft':closure*.25,'mouthPressRight':closure*.25,'mouthFunnel':get('O')*.35,'mouthPucker':get('O')*.2,'mouthStretchLeft':get('E')*.18,'mouthStretchRight':get('E')*.18,'mouthRollLower':get('FV')*.3}
