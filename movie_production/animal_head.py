"""Parametric stylized lion anatomy, built inside Blender without geometry logs."""
import math

def build_head(rig):
    import bpy
    from mathutils import Vector
    head='mixamorig:Head';objects=[]
    def material(name,color,rough=.65):
        mat=bpy.data.materials.new(name);mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Roughness'].default_value=rough
        return mat
    fur=material('Leo golden fur',(.48,.235,.065));cream=material('Leo muzzle',(.72,.48,.23))
    mane=material('Leo copper mane',(.20,.063,.018));inner=material('Leo mouth lining',(.19,.022,.028),.55)
    scarf=material('Leo teal scarf',(.018,.10,.12))
    pink=material('Leo tongue',(.48,.065,.09),.5);tooth=material('Leo ivory teeth',(.82,.73,.53),.3)
    nose=material('Leo nose',(.045,.018,.009),.4);white=material('Leo sclera',(.83,.76,.59),.25)
    iris=material('Leo amber iris',(.25,.095,.014),.25);pupil=material('Leo pupil',(.004,.002,.001),.2)
    glint=material('Leo eye glint',(.95,.95,.9),.1)
    def bind(obj,bone=head):
        obj.parent=rig;group=obj.vertex_groups.new(name=bone);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
        mod=obj.modifiers.new('Anatomical skin','ARMATURE');mod.object=rig;objects.append(obj)
        for polygon in obj.data.polygons:polygon.use_smooth=True
        return obj
    def sphere(name,location,scale,mat,bone=head,bind_it=True):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=40,ring_count=24,location=location)
        obj=bpy.context.object;obj.name=name;obj.scale=scale
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        obj.data.materials.append(mat)
        return bind(obj,bone) if bind_it else obj
    # True jaw hinge, separate from body/head motion.
    bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    jaw=rig.data.edit_bones.new('Leo-Jaw');jaw.head=(0,-.035,1.285);jaw.tail=(0,.065,1.285);jaw.parent=rig.data.edit_bones[head]
    tongue=rig.data.edit_bones.new('Leo-Tongue');tongue.head=(0,-.20,1.275);tongue.tail=(0,-.27,1.275);tongue.parent=jaw
    bpy.ops.object.mode_set(mode='OBJECT')
    # Solid upper head with an actual mouth opening, rather than a painted black patch.
    skull=sphere('Leo upper head',(0,-.035,1.43),(.235,.19,.25),fur,bind_it=False)
    cutter=sphere('Mouth opening cutter',(0,-.23,1.275),(.158,.20,.078),inner,bind_it=False)
    boolean=skull.modifiers.new('Recessed oral opening','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cutter
    bpy.context.view_layer.objects.active=skull;bpy.ops.object.modifier_apply(modifier=boolean.name)
    bpy.data.objects.remove(cutter,do_unlink=True);bind(skull)
    # Mane and ears frame the rebuilt head and hide the seam to the preserved body.
    for i in range(18):
        angle=2*math.pi*i/18
        obj=sphere('Leo mane tuft %02d'%i,(.255*math.sin(angle),.015,1.41+.29*math.cos(angle)),(.09,.105,.135),mane)
        obj.rotation_euler.y=-angle
    for side in (-1,1):
        sphere('Leo ear '+str(side),(side*.215,.005,1.61),(.085,.05,.095),fur)
        sphere('Leo inner ear '+str(side),(side*.215,-.04,1.61),(.052,.012,.062),mane)
    sphere('Leo scarf collar',(0,-.015,1.035),(.25,.14,.075),scarf,'mixamorig:Neck')
    sphere('Leo scarf knot',(0,-.145,1.01),(.065,.04,.06),scarf,'mixamorig:Spine2')
    sphere('Leo scarf tail',(0,-.13,.925),(.065,.03,.105),scarf,'mixamorig:Spine2')
    # Lining, gums and teeth occupy real depth. Lower teeth and tongue move with the jaw.
    sphere('Leo oral cavity',(0,-.115,1.285),(.145,.105,.072),inner)
    sphere('Leo lower jaw',(0,-.14,1.27),(.155,.15,.055),cream,'Leo-Jaw')
    sphere('Leo lower gum',(0,-.20,1.303),(.13,.075,.012),inner,'Leo-Jaw')
    sphere('Leo upper gum',(0,-.20,1.328),(.13,.06,.012),inner)
    sphere('Leo tongue',(0,-.19,1.305),(.072,.055,.014),pink,'Leo-Tongue')
    for upper in (True,False):
        for i,x in enumerate((-.105,-.065,-.025,.025,.065,.105)):
            scale=(.012,.017,.026 if abs(x)>.09 else .014)
            z=1.31 if upper else 1.312
            sphere(('Leo upper tooth ' if upper else 'Leo lower tooth ')+str(i),(x,-.24+.18*abs(x),z),scale,tooth,head if upper else 'Leo-Jaw')
    muzzle=[]
    for side in (-1,1):muzzle.append(sphere('Leo muzzle '+str(side),(side*.067,-.214,1.367),(.089,.073,.064),cream))
    sphere('Leo nose',(0,-.284,1.398),(.062,.038,.036),nose)
    sphere('Leo nose bridge',(0,-.17,1.455),(.065,.07,.075),fur)
    # Facial shape keys affect soft muzzle geometry; the jaw remains a bone hinge.
    for obj in muzzle:
        obj.shape_key_add(name='Basis');basis=obj.data.shape_keys.key_blocks[0]
        for name,stretch,forward,lift in [('mouthStretch',1.10,0,0),('mouthFunnel',.82,-.012,0),('mouthSmile',1.04,0,.009),('mouthClose',1,0,-.009)]:
            key=obj.shape_key_add(name=name)
            for destination,source in zip(key.data,basis.data):
                p=source.co.copy();world=obj.location+p
                world.x*=stretch;world.y+=forward;world.z+=lift if name=='mouthClose' else lift*min(1,abs(world.x)/.1)
                destination.co=world-obj.location
    # Independent eyes and spherical eyelid caps. Both lids meet during full blink.
    lid_objects=[];eye_bones=[]
    for side,label in [(-1,'L'),(1,'R')]:
        center=Vector((side*.103,-.205,1.505));radius=Vector((.064,.047,.074))
        bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
        eye=rig.data.edit_bones.new('Leo-Eye.'+label);eye.head=center;eye.tail=center+Vector((0,-.04,0));eye.parent=rig.data.edit_bones[head]
        bpy.ops.object.mode_set(mode='OBJECT');eye_bones.append('Leo-Eye.'+label)
        sphere('Leo eyeball '+label,center,radius,white,'Leo-Eye.'+label)
        sphere('Leo iris '+label,center+Vector((0,-.046,0)),(.032,.008,.039),iris,'Leo-Eye.'+label)
        sphere('Leo pupil '+label,center+Vector((0,-.053,0)),(.014,.003,.022),pupil,'Leo-Eye.'+label)
        sphere('Leo glint '+label,center+Vector((-.009,-.057,.015)),(.006,.002,.007),glint,'Leo-Eye.'+label)
        for upper in (True,False):
            vertices=[];closed=[];faces=[];cols=32;rows=12
            for row in range(rows+1):
                fraction=(row/(rows-1)*.99) if row<rows else 1.
                # Upper/lower cap edges move toward one shared seam at -5 degrees.
                pole=math.pi/2 if upper else -math.pi/2
                edge=math.radians(42 if upper else -52);final=math.radians(-5)
                for column in range(cols+1):
                    longitude=-math.pi/2+math.pi*column/cols
                    def position(boundary):
                        latitude=pole+(boundary-pole)*fraction
                        return center+Vector((radius.x*1.025*math.cos(latitude)*math.sin(longitude),
                            -radius.y*1.35*math.cos(latitude)*math.cos(longitude),radius.z*1.025*math.sin(latitude)))
                    vertices.append(position(edge));closed.append(position(final))
                    if row<rows and column<cols:
                        a=row*(cols+1)+column;faces.append((a,a+1,a+cols+2,a+cols+1))
            data=bpy.data.meshes.new('Leo spherical lid');data.from_pydata(vertices,[],faces);data.update()
            obj=bpy.data.objects.new('Leo '+('upper' if upper else 'lower')+' lid '+label,data);bpy.context.scene.collection.objects.link(obj)
            obj.data.materials.append(fur);obj.data.materials.append(mane)
            for polygon in data.polygons:
                if polygon.index>=(rows-1)*cols:polygon.material_index=1
            bind(obj)
            obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='eyeBlink'+('Left' if side==-1 else 'Right'))
            for v,p in zip(key.data,closed):v.co=p
            lid_objects.append(obj)
        brow=sphere('Leo brow '+label,center+Vector((0,-.002,.087)),(.072,.025,.022),mane)
        brow.shape_key_add(name='Basis');key=brow.shape_key_add(name='browInnerUp')
        for vertex in key.data:vertex.co.z+=.018
    return objects,{'jaw_bone':'Leo-Jaw','tongue_bone':'Leo-Tongue','eye_bones':eye_bones,
        'anatomy':['mouth opening','oral lining','separate upper/lower gums and teeth','jaw-attached tongue','separate eyes','spherical upper/lower lids']}
