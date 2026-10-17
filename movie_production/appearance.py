"""Conservative image-measurement to MPFB preset mapping; approximate likeness."""
import math

def targets_from_ratios(ratios):
    required={'eye_width','nose_width','mouth_width','chin_width','face_aspect'}
    if not required<=ratios.keys():raise ValueError('Missing facial measurements')
    if any(not isinstance(ratios[k],(int,float)) or not math.isfinite(ratios[k]) or ratios[k]<=0 for k in required):
        raise ValueError('Invalid facial measurements')
    # Heuristic starting values, not a learned inverse model or identity reconstruction.
    proposals={'eyes/l-eye-scale':(ratios['eye_width']-.20)*6,
        'eyes/r-eye-scale':(ratios['eye_width']-.20)*6,
        'nose/nose-scale-horiz':(ratios['nose_width']-.24)*4,
        'mouth/mouth-scale-horiz':(ratios['mouth_width']-.36)*3,
        'chin/chin-width':(ratios['chin_width']-.85)*2,
        'head/head-scale-vert':(ratios['face_aspect']-1.25)*.6}
    return {name+('-incr' if value>=0 else '-decr'):round(min(.65,abs(value)),4) for name,value in proposals.items()}

def validate_preset(preset):
    if preset.get('schema')!='image-mpfb-preset/1':raise ValueError('Unsupported appearance preset')
    name=preset.get('character_id','')
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in name):raise ValueError('Invalid character ID')
    for path,weight in preset.get('targets',{}).items():
        if '..' in path or path.startswith(('/','\\')) or '\\' in path or ':' in path:raise ValueError('Unsafe target path')
        if not isinstance(weight,(int,float)) or not math.isfinite(weight) or not 0<=weight<=.65:raise ValueError('Unsafe target weight')
    return preset
