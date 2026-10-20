"""Blender side of the cast registry: turns a resolved look (cast_registry.resolve) into a character on the lion rig.

    import scene_base as sb, cast_builder as cb
    ch=cb.build(S, look, tag)          # S.character with the tint, root scale (width, depth, height), body parts and accessories parented to the rig's bones

The geometry is data first: part_prims(look) and accessory_prims(look) return plain dicts (shape, name, location, scale, rotation, colour, bone) in the lion's idle-pose space (metres, forward is -Y, head centre about (0,-.12,1.45), top of the mane at z 1.71), no Blender needed,
so tests can check them (every prim has a known bone, sizes stay near the lion's body, the head items sit on the head). build() creates the primitives, then parents each to its bone with a parent-inverse computed from the evaluated idle pose, so it
follows the clip exactly and keeps its place. The root scale is set last (the root is an unscaled empty until then, so nothing is corrected twice)."""
import math
from cast_registry import hash_unit
PI=math.pi
HC=(0.,-.12,1.45)                 # head centre, lion idle pose
BONES={'head':'mixamorig:Head','neck':'mixamorig:Neck','spine':'mixamorig:Spine2','spine1':'mixamorig:Spine1','hips':'mixamorig:Hips','hand_r':'mixamorig:RightHand','hand_l':'mixamorig:LeftHand','tail':'Tail'}
PALETTE=[(.75,.15,.12),(.15,.35,.7),(.2,.55,.3),(.85,.65,.15),(.5,.25,.6),(.9,.9,.85),(.3,.2,.12),(.15,.15,.18)]
GOLD=(.95,.75,.2);STEEL=(.7,.72,.78);LEATHER=(.4,.26,.14);CLOTH=(.85,.8,.7);DARK=(.1,.1,.12)
def P(shape,name,loc,scale,color,bone,rot=(0,0,0),emit=0.):return dict(shape=shape,name=name,loc=loc if isinstance(loc,str) else tuple(loc),scale=tuple(scale),rot=tuple(rot),color=tuple(color),bone=bone,emit=emit)
def color_of(acc,rid,i=0):
 return tuple(acc['color']) if acc.get('color') else PALETTE[int(hash_unit(rid,'acc%d'%i)*len(PALETTE))%len(PALETTE)]
def part_prims(look):
 """body parts (ears, horns, ruff, tusks, tail tuft, beak) as primitive dicts"""
 out=[];x0,y0,z0=HC
 for p in look['parts']:
  k=p['kind'];s=p.get('size',1.);c=p.get('color') or (.8,.8,.8);sh=p.get('shape','')
  for sg in (-1,1):
   n=lambda t:'Part_%s_%s%s'%(look['id'],t,'L' if sg>0 else 'R')
   if k=='ears':
    if sh=='round':out.append(P('sphere',n('ear'),(sg*.22,y0+.04,1.66),(.1*s,.055*s,.1*s),c,'head'))
    elif sh=='point':out.append(P('cone',n('ear'),(sg*.2,y0+.04,1.78+.04*s),(.085*s,.045*s,.15*s),c,'head',(0,sg*.2,0)))
    elif sh=='long':out.append(P('cyl',n('ear'),(sg*.12,y0+.06,1.98),(.055*s,.025*s,.28*s),c,'head',(.1,sg*.12,0)))
    elif sh=='side':out.append(P('sphere',n('ear'),(sg*.38,y0+.0,1.5),(.15*s,.05*s,.08*s),c,'head',(0,sg*.3,0)))
    elif sh=='tuft':out.append(P('cone',n('ear'),(sg*.17,y0+.0,1.76),(.05*s,.04*s,.16*s),c,'head',(0,sg*.5,0)))
    elif sh=='disc':out.append(P('cyl',n('ear'),(sg*.3,y0+.02,1.64),(.17*s,.17*s,.015),c,'head',(PI/2,0,0)))
   elif k=='horns':
    out.append(P('cyl',n('horn'),(sg*.26,y0+.0,1.76),(.045*s,.045*s,.13*s),c,'head',(0,sg*.8,0)));out.append(P('cone',n('horntip'),(sg*.4,y0+.0,1.9),(.04*s,.04*s,.12*s),c,'head',(0,sg*.25,0)))
   elif k=='tusks':out.append(P('cone',n('tusk'),(sg*.13,y0-.44,1.26),(.035*s,.035*s,.12*s),c,'head',(.2,sg*-.2,0)))
  if k=='ruff':
   for i in range(10):
    a=2*PI*i/10;out.append(P('sphere','Part_%s_ruff%d'%(look['id'],i),(math.cos(a)*.3*s,y0+.04+math.sin(a)*.26*s,1.3),(.13*s,.13*s,.12*s),c,'neck'))
  elif k=='beak':out.append(P('cone','Part_%s_beak'%look['id'],(0,-.6-.04*s,1.36),(.07*s,.07*s,.14*s),c,'head',(-PI/2,0,0)))
  elif k=='tuft':out.append(P('sphere','Part_%s_tailtuft'%look['id'],'TAIL_TIP',(.11*s,.11*s,.11*s),c,'tail'))
 return out
def accessory_prims(look,hand_r=(-.36,-.1,.66),hand_l=(.36,-.1,.66)):
 """accessories as primitive dicts; hand positions come from the evaluated idle pose"""
 out=[];rid=look['id']
 for i,acc in enumerate(look['accessories']):
  k=acc['kind'];c=color_of(acc,rid,i);n=lambda t:'Acc_%s_%s_%s'%(rid,k,t);x0,y0,z0=HC
  if k=='hat_top':out+=[P('cyl',n('crown'),(0,y0+.02,1.86),(.17,.17,.15),c,'head'),P('cyl',n('brim'),(0,y0+.02,1.72),(.28,.28,.02),c,'head'),P('cyl',n('band'),(0,y0+.02,1.76),(.175,.175,.03),GOLD,'head')]
  elif k=='hat_wizard':out+=[P('cone',n('cone'),(0,y0+.04,1.98),(.2,.2,.26),c,'head',(-.12,0,0)),P('cyl',n('brim'),(0,y0+.02,1.72),(.32,.32,.02),c,'head')]
  elif k=='hat_cap':out+=[P('sphere',n('dome'),(0,y0+.02,1.68),(.29,.29,.2),c,'head'),P('cube',n('peak'),(0,y0-.3,1.68),(.2,.12,.015),c,'head',(.15,0,0))]
  elif k=='hat_straw':out+=[P('cyl',n('brim'),(0,y0+.02,1.72),(.38,.38,.02),(.85,.72,.4),'head'),P('cyl',n('crown'),(0,y0+.02,1.8),(.2,.2,.08),(.85,.72,.4),'head'),P('cyl',n('band'),(0,y0+.02,1.76),(.255,.255,.03),c,'head')]
  elif k=='crown':
   out.append(P('cyl',n('ring'),(0,y0+.02,1.76),(.19,.19,.06),GOLD,'head'))
   for j in range(5):a=2*PI*j/5;out.append(P('cone',n('spike%d'%j),(math.cos(a)*.2,y0+.02+math.sin(a)*.2,1.88),(.04,.04,.09),GOLD,'head'))
  elif k=='helmet':out+=[P('sphere',n('dome'),(0,y0+.02,1.66),(.32,.32,.28),STEEL,'head'),P('cube',n('crest'),(0,y0+.02,1.93),(.025,.28,.07),c,'head')]
  elif k=='glasses':
   for sg in (-1,1):out.append(P('cyl',n('lens%d'%sg),(sg*.11,-.46,1.47),(.06,.06,.01),(.7,.85,.95),'head',(PI/2,0,0)))
   out.append(P('cube',n('bridge'),(0,-.46,1.48),(.04,.01,.01),DARK,'head'))
  elif k=='eyepatch':out+=[P('cyl',n('patch'),(.11,-.465,1.47),(.085,.085,.012),DARK,'head',(PI/2,0,0)),P('cube',n('cord'),(.2,-.43,1.52),(.15,.008,.008),DARK,'head',(0,0,.5))]
  elif k=='flower':
   out.append(P('sphere',n('heart'),(.27,y0-.05,1.62),(.04,.04,.04),(.95,.85,.2),'head'))
   for j in range(5):a=2*PI*j/5;out.append(P('sphere',n('petal%d'%j),(.27+math.cos(a)*.06,y0-.07,1.62+math.sin(a)*.06),(.045,.025,.045),c,'head'))
  elif k=='scarf':out+=[P('cyl',n('wrap'),(0,y0+.08,1.2),(.3,.27,.1),c,'neck'),P('cube',n('end'),(.15,-.21,1.0),(.085,.025,.26),c,'spine'),P('cube',n('end2'),(.27,.0,1.12),(.03,.1,.05),c,'neck')]
  elif k=='bowtie':out+=[P('cone',n('a'),(.07,-.27,1.14),(.06,.06,.08),c,'neck',(0,PI/2,0)),P('cone',n('b'),(-.07,-.27,1.14),(.06,.06,.08),c,'neck',(0,-PI/2,0)),P('sphere',n('knot'),(0,-.27,1.14),(.035,.035,.035),c,'neck')]
  elif k=='cape':out+=[P('cube',n('clothL'),(.15,.24,1.0),(.17,.015,.3),c,'spine',(-.1,0,.3)),P('cube',n('clothR'),(-.15,.24,1.0),(.17,.015,.3),c,'spine',(-.1,0,-.3)),P('cyl',n('clasp'),(0,-.12,1.2),(.07,.07,.02),GOLD,'spine',(PI/2,0,0))]
  elif k=='backpack':out+=[P('cube',n('pack'),(0,.3,.98),(.28,.13,.3),LEATHER,'spine'),P('cyl',n('roll'),(0,.3,1.33),(.12,.12,.34),c,'spine',(0,PI/2,0))]
  elif k=='apron':out+=[P('cube',n('cloth'),(0,-.2,.82),(.22,.015,.36),CLOTH,'spine1'),P('cube',n('strap'),(0,-.19,1.2),(.2,.012,.03),c,'spine1')]
  elif k=='medals':
   for j in range(3):out.append(P('sphere',n('m%d'%j),(.16-j*.1,-.205,1.02),(.035,.015,.035),GOLD if j%2==0 else STEEL,'spine1'))
   out.append(P('cube',n('bar'),(.06,-.2,1.075),(.15,.01,.015),c,'spine1'))
  elif k=='belt':out+=[P('cyl',n('band'),(0,-.02,.8),(.3,.24,.045),LEATHER,'hips'),P('cube',n('buckle'),(0,-.255,.8),(.04,.012,.035),GOLD,'hips')]
  elif k=='satchel':out+=[P('cube',n('bag'),(.37,.0,.72),(.07,.17,.15),LEATHER,'hips'),P('cube',n('strap'),(.0,-.19,1.0),(.025,.015,.3),LEATHER,'spine1',(0,-.75,.0))]
  elif k=='sword':out+=[P('cube',n('blade'),(.34,.12,.5),(.018,.012,.4),STEEL,'hips',(-.3,0,0)),P('cube',n('guard'),(.34,.06,.78),(.07,.014,.014),GOLD,'hips'),P('cyl',n('grip'),(.34,.05,.86),(.015,.015,.07),LEATHER,'hips')]
  elif k=='staff':out+=[P('cyl',n('shaft'),(hand_r[0],hand_r[1],.98),(.028,.028,1.04),LEATHER,'hand_r'),P('sphere',n('orb'),(hand_r[0],hand_r[1],2.0),(.07,.07,.07),c,'hand_r',emit=.8)]
  elif k=='cane':out+=[P('cyl',n('shaft'),(hand_r[0],hand_r[1],.4),(.02,.02,.4),LEATHER,'hand_r'),P('sphere',n('knob'),(hand_r[0],hand_r[1],.82),(.04,.04,.04),GOLD,'hand_r')]
  elif k=='lantern':out+=[P('cube',n('frame'),(hand_l[0],hand_l[1],hand_l[2]-.12),(.08,.08,.1),DARK,'hand_l'),P('sphere',n('flame'),(hand_l[0],hand_l[1],hand_l[2]-.12),(.065,.065,.065),(1.,.8,.35),'hand_l',emit=3.)]
  elif k=='banner':out+=[P('cyl',n('pole'),(hand_r[0],hand_r[1],1.05),(.02,.02,1.05),LEATHER,'hand_r'),P('cube',n('cloth'),(hand_r[0],hand_r[1]-.22,1.85),(.01,.22,.16),c,'hand_r')]
 return out
def build(S,look,tag=None):
 """the character: lion rig, tint, scaled root, parts and accessories. Returns the S.character dict plus ch['look'], ch['dress'] (the dressing objects)."""
 import bpy
 from mathutils import Matrix,Vector
 tag=tag or look['id'];ch=S.character(tag,look['tint']);rig=ch['rig'];root=ch['root'];ch['look']=look
 act=S.clip('idle');rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];S.scene.frame_set(1);bpy.context.view_layer.update()
 W=lambda b:rig.matrix_world@rig.pose.bones[b].head;hr,hl=W('mixamorig:RightHand'),W('mixamorig:LeftHand');tail=rig.matrix_world@rig.pose.bones['Tail'].tail
 prims=part_prims(look)+accessory_prims(look,tuple(hr),tuple(hl));dress=[]
 for p in prims:
  loc=p['loc'];loc=tuple(tail) if loc=='TAIL_TIP' else loc
  o=S.prim(p['shape'],p['name'],loc,p['color'],scale=p['scale'],rot=p['rot'],emit=p['emit']);bpy.context.view_layer.update();Wm=o.matrix_world.copy()
  pb=rig.pose.bones[BONES[p['bone']]];o.parent=rig;o.parent_type='BONE';o.parent_bone=pb.name;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Wm;bpy.context.view_layer.update()
  Pm=o.matrix_world@Wm.inverted();o.matrix_parent_inverse=Pm.inverted();o.matrix_basis=Wm;dress.append(o)
 rig.animation_data.action=None;rig.animation_data_clear();rig.animation_data_create();ch['tracks']=[rig.animation_data.nla_tracks.new(),rig.animation_data.nla_tracks.new()];ch['n']=0
 for o in dress:ch['objs'].append(o)
 ch['dress']=dress;root.scale=tuple(look['scale']);return ch
