"""Two-lane street tiles: 3.5 m lanes, 1.5 m pavements, centimetre units."""
import math

PORTS={'straight':[(0,-1),(0,1)],'cross':[(0,-1),(0,1),(-1,0),(1,0)],'tee':[(0,-1),(-1,0),(1,0)],'corner':[(0,-1),(1,0)]}

def compile_streets(recipe):
    boxes=[];ports=[];cells=set();ids=set()
    for tile in recipe['tiles']:
        name,kind=tile['id'],tile['kind'];x,y=tile['cell'];yaw=tile.get('yaw',0)
        if kind not in PORTS or name in ids or (x,y) in cells:raise ValueError('Unknown, duplicate or overlapping tile')
        if any(isinstance(v,bool) or not isinstance(v,int) for v in (x,y,yaw)) or yaw%90:raise ValueError('Integer cells and 90 degree rotation required')
        cells.add((x,y));ids.add(name)
        a=math.radians(yaw);c,s=round(math.cos(a)),round(math.sin(a))
        def point(px,py,pz):return [x*1000+px*c-py*s,y*1000+px*s+py*c,pz]
        def box(label,px,py,z,w,d,h,mat):boxes.append(dict(id=name+'_'+label,position_cm=point(px,py,z),size_cm=[w,d,h],yaw=yaw,material=mat))
        box('road',0,0,-10,1000,1000,20,'asphalt')
        local=PORTS[kind]
        # Raised pavement at corners and all closed road edges.
        for sx in (-1,1):
            for sy in (-1,1):box('pavement'+str(sx)+str(sy),sx*425,sy*425,7.5,150,150,15,'pavement')
        for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)]:
            if (dx,dy) not in local:
                box('edge'+str(dx)+str(dy),dx*425,dy*425,7.5,150 if dx else 700,700 if dx else 150,15,'pavement')
            else:
                normal=[dx*c-dy*s,dx*s+dy*c]
                ports.append(dict(part=name,position_cm=point(dx*500,dy*500,0),normal=normal,width_cm=700))
                # Crosswalk on each junction arm; stripes are non-blocking paint.
                if kind!='straight':
                    for i in range(7):
                        across=-270+i*90
                        box('crosswalk'+str(dx)+str(dy)+str(i),dx*270+(across if dy else 0),dy*270+(across if dx else 0),.3,55 if dy else 120,120 if dy else 55,.6,'paint')
        if kind=='straight':
            for py in (-360,-120,120,360):box('lane'+str(py),0,py,.3,8,110,.6,'paint')
    links=[];open_ports=[]
    for i,p in enumerate(ports):
        matches=[q for q in ports if q['part']!=p['part'] and q['position_cm']==p['position_cm'] and q['normal']==[-v for v in p['normal']]]
        if matches:
            if p['part']<matches[0]['part']:links.append([p['part'],matches[0]['part']])
        else:open_ports.append(p)
    # Neighbouring tiles must expose compatible ports at their shared boundary.
    for p in open_ports:
        x,y,_=p['position_cm'];dx,dy=p['normal']
        other=(round((x+dx*500)/1000),round((y+dy*500)/1000))
        if other in cells:raise ValueError('Road enters a neighbouring closed pavement edge: '+p['part'])
    return dict(boxes=boxes,connectors=ports,links=links,open_ports=open_ports,units='cm')

def demo_recipe():
    tiles=[dict(id='junction',kind='cross',cell=[0,0])]
    for axis in (0,1):
        for sign in (-1,1):
            for distance in (1,2):
                cell=[0,0];cell[axis]=sign*distance
                tiles.append(dict(id=f'arm_{axis}_{sign}_{distance}',kind='straight',cell=cell,yaw=90 if axis==0 else 0))
    return dict(version=1,tiles=tiles)
