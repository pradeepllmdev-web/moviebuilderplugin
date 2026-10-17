"""Engine-independent architectural kit. Dimensions and bottom pivots use centimetres."""
import math

GRID = 200
HEIGHT = 300
THICKNESS = 20
PARTS = {
    'wall': [(0, 0, 150, 200, 20, 300)],
    'door': [(-75, 0, 150, 50, 20, 300), (75, 0, 150, 50, 20, 300), (0, 0, 260, 100, 20, 80)],
    'window': [(0, 0, 40, 200, 20, 80), (0, 0, 280, 200, 20, 40), (-90, 0, 170, 20, 20, 180), (90, 0, 170, 20, 20, 180)],
    'floor': [(0, 0, -10, 200, 200, 20)],
    'roof': [(0, 0, 310, 200, 200, 20)],
    'corner': [(0, 0, 150, 20, 20, 300)],
    'stairs': [(0, -90+i*30, (i+1)*10, 200, 30, (i+1)*20) for i in range(6)],
}

def compile_recipe(recipe):
    """Validate before spawning; emit boxes, connectors and usable door anchors."""
    result = {'boxes': [], 'connectors': [], 'anchors': [], 'parts': []}
    occupied = set()
    for part in recipe['parts']:
        kind, name = part['kind'], part['id']
        if kind not in PARTS or name in result['parts']:
            raise ValueError('Unknown part or duplicate ID: '+name)
        x, y, z = part['position_cm']
        yaw = part.get('yaw', 0)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (x,y,z,yaw)):
            raise ValueError('Coordinates must be finite numbers')
        if yaw % 90 or x % 100 or y % 100 or z % 20:
            raise ValueError('Use 100 cm XY / 20 cm Z grid and 90 degree rotations')
        key = (kind,x,y,z,yaw % 180)
        if key in occupied:
            raise ValueError('Duplicate overlapping placement: '+name)
        occupied.add(key); result['parts'].append(name)
        a = math.radians(yaw); c,s = round(math.cos(a)),round(math.sin(a))
        def world(px,py,pz): return [x+px*c-py*s,y+px*s+py*c,z+pz]
        for i,(px,py,pz,w,d,h) in enumerate(PARTS[kind]):
            result['boxes'].append({'id':name+'_'+str(i),'position_cm':world(px,py,pz),'size_cm':[w,d,h],'yaw':yaw,'material':part.get('material','plaster' if kind in ('wall','door','window','corner') else 'wood')})
        if kind in ('wall','door','window'):
            for end in (-100,100): result['connectors'].append({'part':name,'position_cm':world(end,0,0),'type':'wall_end'})
        if kind == 'door': result['anchors'].append({'part':name,'type':'passage','position_cm':world(0,0,0),'clearance_cm':[100,220]})
    return result

def room_recipe(width=4, depth=3):
    """Same kit assembles different room sizes without editing the Unreal builder."""
    if any(isinstance(v,bool) or not isinstance(v,int) or not 2<=v<=20 for v in (width,depth)):
        raise ValueError('Room dimensions must be 2..20 whole tiles')
    parts=[]
    def add(kind,x,y,yaw=0): parts.append({'id':str(len(parts))+'_'+kind,'kind':kind,'position_cm':[x,y,0],'yaw':yaw})
    for x in range(width):
        for y in range(depth): add('floor',x*200+100,y*200+100)
        add('door' if x==1 else 'window',x*200+100,0)
        add('wall',x*200+100,depth*200)
    for y in range(depth):
        add('window',0,y*200+100,90);add('wall',width*200,y*200+100,90)
    for x in (0,width*200):
        for y in (0,depth*200): add('corner',x,y)
    return {'version':1,'units':'cm','parts':parts}
