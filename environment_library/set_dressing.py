"""Themed set dressing for door huts (pure data, shared by the Blender previs and the layout planner).

A hut is a room behind a door: lateral position `lat` (cm, 0 = door centre) and `depth` (cm from the door plane, positive = inside, negative =
outside). Each item is a primitive with a size, a height centre z and a colour; `solid` items are furniture the actors must not stand in
(story_layout turns them into blocking footprints and the camera solver keeps clear of them). Dressing stays out of the clear acting zone
(|lat| <= 190, depth 120..520), where the anchors put actors.

interior(theme) / exterior(theme) -> list of items: dict(name, shape 'box'|'cyl'|'sphere', lat, depth, z, size (x, y, z) or (radius,) , color, solid)
Themes: cafe, bakery, home. Exterior themes follow the door style (awning and sign come from previs.py)."""
ROOM_HALF_WIDTH_CM=380.;ROOM_DEPTH_CM=640.;WALL_HEIGHT_CM=300.
def box(name,lat,depth,z,sx,sy,sz,color,solid=True):return dict(name=name,shape='box',lat=lat,depth=depth,z=z,size=(sx,sy,sz),color=color,solid=solid)
def cyl(name,lat,depth,z,r,h,color,solid=True):return dict(name=name,shape='cyl',lat=lat,depth=depth,z=z,size=(r,h),color=color,solid=solid)
def ball(name,lat,depth,z,r,color):return dict(name=name,shape='sphere',lat=lat,depth=depth,z=z,size=(r,),color=color,solid=False)
WOOD=[.5,.33,.18];DARK=[.3,.2,.1];CREAM=[.92,.86,.7];RED=[.7,.18,.15];GLOW=[1,.85,.45];GREEN=[.2,.5,.22];BREAD=[.78,.55,.28];STONE=[.5,.5,.48]
def table_set(lat,depth,color=WOOD):
 out=[cyl('DressTable',lat,depth,40,48,5,color),cyl('DressTableLeg',lat,depth,20,6,40,DARK,False)]
 for dx,dy in ((70,0),(-70,0),(0,70)):out.append(box('DressChair',lat+dx,depth+dy,22,40,40,44,color,False))
 return out
def interior(theme):
 d=[]
 W=ROOM_HALF_WIDTH_CM;D=ROOM_DEPTH_CM
 d+=[ball('DressLamp',0,300,270,12,GLOW),box('DressRug',0,320,1,260,200,1,RED if theme!='bakery' else [.8,.7,.55],False)]   # central rug and a hanging lamp
 if theme=='cafe':
  d+=[box('DressCounter',0,D-60,50,380,60,100,WOOD),box('DressShelfA',0,D-30,170,360,24,14,DARK,False),box('DressShelfB',0,D-30,230,360,24,14,DARK,False),box('DressMachine',-110,D-60,115,60,40,30,[.75,.75,.78],False)]
  d+=[cyl('DressCup',-150+i*60,D-30,184,6,10,[.9,.9,.85],False) for i in range(6)]
  d+=table_set(-290,260)+table_set(290,260)+[box('DressMenu',-W+14,300,170,6,120,90,[.15,.2,.15],False)]
 elif theme=='bakery':
  d+=[box('DressDisplay',0,D-80,50,360,70,100,WOOD),box('DressGlass',0,D-80,115,360,60,30,[.75,.9,.95],False),box('DressOven',-W+70,D-90,70,120,100,140,STONE),ball('DressFire',-W+70,D-39,50,18,[1,.55,.2])]
  d+=[box('DressShelfL',-W+16,260+i*40,150,22,34,14,DARK,False) for i in range(5)]+[box('DressBread',-W+20,260+i*40,166,16,28,14,BREAD,False) for i in range(5)]
  d+=[box('DressBread',-120+i*60,D-80,138,34,20,14,BREAD,False) for i in range(5)]+[box('DressSack',W-60,D-70,30,50,40,60,CREAM),box('DressSack',W-120,D-60,26,46,38,52,CREAM)]
  d+=table_set(290,230)
 else:   # home
  d+=[box('DressBed',-W+90,D-120,25,130,210,50,[.65,.45,.3]),box('DressBlanket',-W+90,D-170,52,126,120,8,[.35,.45,.7],False),box('DressPillow',-W+90,D-40,58,70,30,12,[.95,.95,.9],False)]
  d+=[box('DressFireplace',-W+22,300,60,40,130,120,STONE),ball('DressFire',-W+46,300,40,16,[1,.5,.15]),box('DressShelf',W-18,420,110,26,200,220,DARK),box('DressTable',W-110,200,38,90,60,76,WOOD),ball('DressTableLamp',W-110,200,86,10,GLOW)]
  d+=[box('DressChair',W-110,120,22,40,40,44,WOOD,False)]
 return d
def exterior(theme):
 out=[]
 for sx in (-1,1):
  out+=[cyl('DressLampPost',sx*260,-120,110,5,220,DARK,False),ball('DressLampGlow',sx*260,-120,228,14,GLOW),box('DressFlowerBox',sx*170,-20,18,90,28,30,WOOD,False),box('DressFlowers',sx*170,-20,38,84,22,12,[.9,.4,.55],False)]
 out+=[cyl('DressBarrel',-300,-60,40,28,80,WOOD),cyl('DressBarrel',-250,-30,40,26,80,WOOD),box('DressCrate',320,-40,25,50,50,50,WOOD)]
 if theme=='bakery':out+=[box('DressSack',-330,-110,22,50,40,44,CREAM),box('DressCart',330,-160,40,110,70,60,WOOD),cyl('DressWheel',330,-120,28,28,6,DARK,False)]
 if theme=='home':out+=[box('DressWoodpile',330,-70,30,90,50,60,[.45,.3,.15])]
 return out
def solids(theme,cx,py):
 """World footprints (x0,y0,x1,y1,name) of the solid furniture of a hut whose door centre is (cx, py): inside is +Y, as the builder walks."""
 out=[]
 for it in interior(theme)+exterior(theme):
  if not it['solid']:continue
  if it['shape']=='box':hx,hy=it['size'][0]/2,it['size'][1]/2
  else:hx=hy=it['size'][0]
  x=cx+it['lat'];y=py+it['depth'];out.append((x-hx,y-hy,x+hx,y+hy,it['name']))
 return out
