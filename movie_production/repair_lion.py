"""Anatomy fit for the prepared original lion; all geometry stays in Blender."""
import math

def repair(rig):
    import bpy
    from mathutils import Vector,Matrix
    if rig.name!='Lion_Realistic' or rig.get('lion_face_version')!=4:raise ValueError('Prepared original lion v4 required')
    surface=next(obj for obj in rig.children_recursive if obj.type=='MESH' and obj.data.shape_keys)
    basis=surface.data.shape_keys.key_blocks[0]
    original=[point.co.copy() for point in basis.data]
    seam_z=1.244
    transform=rig.matrix_world.inverted()@surface.matrix_world
    # Re-cut at the visible lip line; the legacy seam was incorrectly placed near the nose.
    import bmesh
    saved=[(key.name,[point.co.copy() for point in key.data]) for key in surface.data.shape_keys.key_blocks]
    mesh=bmesh.new();mesh.from_mesh(surface.data);mesh.verts.ensure_lookup_table()
    layers={}
    for name,coordinates in saved:
        layer=mesh.verts.layers.shape.get(name) or mesh.verts.layers.shape.new(name);layers[name]=layer
        for vertex,point in zip(mesh.verts,coordinates):vertex[layer]=point
    selected=[face for face in mesh.faces if abs((transform@face.calc_center_median()).x)<.09
              and (transform@face.calc_center_median()).y<-.30 and 1.18<(transform@face.calc_center_median()).z<1.30]
    geometry=list(set(selected)|{edge for face in selected for edge in face.edges}|{vertex for face in selected for vertex in face.verts})
    cut=bmesh.ops.bisect_plane(mesh,geom=geometry,dist=1e-6,plane_co=transform.inverted()@Vector((0,0,seam_z)),
        plane_no=transform.to_3x3().transposed()@Vector((0,0,1)))
    edges=[edge for edge in cut['geom_cut'] if isinstance(edge,bmesh.types.BMEdge)]
    if len(edges)<2:raise ValueError('Actual mouth seam could not be separated')
    bmesh.ops.split_edges(mesh,edges=edges);mesh.verts.index_update()
    lower_seam={vertex.index for vertex in mesh.verts if abs((transform@vertex.co).z-seam_z)<1e-5 and vertex.link_faces
        and max((transform@face.calc_center_median()).z for face in vertex.link_faces)<=seam_z+1e-5}
    transferred={name:[vertex[layer].copy() for vertex in mesh.verts] for name,layer in layers.items()}
    surface.shape_key_clear();mesh.to_mesh(surface.data);mesh.free();surface.data.update()
    surface.shape_key_add(name='Basis')
    for name,coordinates in transferred.items():
        if name=='Basis':continue
        key=surface.shape_key_add(name=name)
        for point,coordinate in zip(key.data,coordinates):point.co=coordinate
    for key in surface.data.shape_keys.key_blocks:key.value=0
    basis=surface.data.shape_keys.key_blocks[0]
    head='mixamorig:Head';new=[]
    for obj in list(rig.children_recursive):
        if obj.name=='Lion_Realistic InnerMouth':bpy.data.objects.remove(obj,do_unlink=True)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    jaw=rig.data.edit_bones.new('Repair-Jaw');jaw.head=(0,-.12,1.25);jaw.tail=(0,-.02,1.25);jaw.parent=rig.data.edit_bones[head]
    tongue=rig.data.edit_bones.new('Repair-Tongue');tongue.head=(0,-.32,1.225);tongue.tail=(0,-.37,1.225);tongue.parent=jaw
    bpy.ops.object.mode_set(mode='OBJECT')
    # Transfer only the already calibrated lower-mouth influence; neutral coordinates do not change.
    cranial=[surface.vertex_groups[name] for name in (head,'mixamorig:HeadTop_End','headfront','mixamorig:Neck') if name in surface.vertex_groups]
    destination=surface.vertex_groups.new(name='Repair-Jaw');affected=0
    def smooth(value):value=max(0,min(1,value));return value*value*(3-2*value)
    for vertex in surface.data.vertices:
        point=transform@vertex.co
        lateral=smooth((.12-abs(point.x))/.045)*smooth((-.28-point.y)/.06)
        chin=smooth((seam_z-point.z)/.025)*smooth((point.z-1.10)/.06)*lateral
        strength=lateral if vertex.index in lower_seam else chin
        if point.z>seam_z+1e-5:strength=0
        if strength<.005:continue
        weights=[]
        for source_group in cranial:
            try:weights.append((source_group,source_group.weight(vertex.index)))
            except RuntimeError:pass
        influence=strength*sum(weight for _,weight in weights)
        if influence<.005:continue
        destination.add([vertex.index],influence,'REPLACE')
        for source_group,weight in weights:source_group.add([vertex.index],weight*(1-strength),'REPLACE')
        affected+=1
    # New speech shapes are restricted to the real mouth; legacy nose-level shapes stay neutral.
    inverse=transform.inverted().to_3x3()
    for name in ('Repair_Round','Repair_Wide','Repair_Close','Repair_Press','Repair_Smile'):
        key=surface.shape_key_add(name=name)
        for vertex,base in zip(key.data,basis.data):
            point=transform@base.co;weight=math.exp(-(point.x/.09)**4-((point.z-seam_z)/.018)**2)*smooth((-.30-point.y)/.065)
            if point.z>seam_z+.025:weight=0
            delta=Vector((0,0,0))
            if name=='Repair_Round':delta=Vector((-.14*point.x,-.004,0))*weight
            if name=='Repair_Wide':delta=Vector((.10*point.x,0,0))*weight
            if name=='Repair_Close':delta=Vector((0,0,.003 if point.z<seam_z else 0))*weight
            if name=='Repair_Press':delta=Vector((0,.002,0))*weight
            if name=='Repair_Smile':delta=Vector((0,0,.004*min(1,abs(point.x)/.06)))*weight
            vertex.co=base.co+inverse@delta
    lip_faces=[]
    def material(name,color,rough=.7):
        mat=bpy.data.materials.new(name);mat.use_nodes=True
        shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(*color,1);shader.inputs['Roughness'].default_value=rough
        return mat
    lining=material('Original lion mouth tissue',(.28,.055,.065));gum=material('Original lion gums',(.32,.055,.065))
    shader=lining.node_tree.nodes.get('Principled BSDF');shader.inputs['Emission Color'].default_value=(.28,.055,.065,1);shader.inputs['Emission Strength'].default_value=.12
    tongue_mat=material('Original lion tongue',(.48,.095,.12),.5);ivory=material('Original lion teeth',(.75,.65,.45),.35)
    sclera=material('Original lion sclera',(.78,.72,.58),.3);iris=material('Original lion amber iris',(.32,.13,.025),.3)
    pupil=material('Original lion pupil',(.005,.003,.001),.2);glint=material('Original lion eye glint',(.95,.95,.9),.15)
    fur=material('Original lion eyelid fur',(.68,.43,.22));rim=material('Original lion eyelid rim',(.18,.085,.035))
    def bind(obj,bone=head):
        obj.parent=rig;group=obj.vertex_groups.new(name=bone);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
        modifier=obj.modifiers.new('Fitted skin','ARMATURE');modifier.object=rig
        for polygon in obj.data.polygons:polygon.use_smooth=True
        new.append(obj);return obj
    def sphere(name,location,scale,mat,bone=head):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=location)
        obj=bpy.context.object;obj.name=name;obj.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        obj.data.materials.append(mat);return bind(obj,bone)
    if lip_faces:
        indices=sorted({index for face in lip_faces for index in face});lookup={index:i for i,index in enumerate(indices)}
        data=bpy.data.meshes.new('Original lower lip fitted topology')
        data.from_pydata([surface.data.vertices[index].co.copy() for index in indices],[],[[lookup[index] for index in face] for face in lip_faces]);data.update()
        lip=bpy.data.objects.new('Fitted original lower lip',data);bpy.context.scene.collection.objects.link(lip)
        lip.matrix_world=surface.matrix_world.copy()
        for material in surface.data.materials:data.materials.append(material)
        for polygon,material_index in zip(data.polygons,lip_materials):polygon.material_index=material_index
        if lip_uvs:
            layer=data.uv_layers.new(name='Preserved lip UV')
            for polygon,coordinates in zip(data.polygons,lip_uvs):
                for index,uv in zip(polygon.loop_indices,coordinates):layer.data[index].uv=uv
        bind(lip,'Repair-Jaw')
    # A concave bowl recessed inside the existing muzzle, not a dark plate across the slit.
    vertices=[];faces=[];rings=12;segments=48
    for ring in range(rings+1):
        radius=max(.001,ring/rings)
        for i in range(segments):
            angle=2*math.pi*i/segments
            vertices.append((.065*radius*math.cos(angle),-.375+.075*(1-radius*radius),1.220+.035*radius*math.sin(angle)))
            if ring<rings:
                a=ring*segments+i;b=ring*segments+(i+1)%segments;faces.append((a,a+segments,b+segments,b))
    data=bpy.data.meshes.new('Recessed oral bowl');data.from_pydata(vertices,[],faces);data.update()
    obj=bpy.data.objects.new('Fitted mouth cavity',data);bpy.context.scene.collection.objects.link(obj);data.materials.append(lining);bind(obj)
    # Lower cavity follows the jaw, blending toward the fixed upper cavity.
    group=obj.vertex_groups.new(name='Repair-Jaw');head_group=obj.vertex_groups[head]
    for vertex in data.vertices:
        weight=max(0,min(1,(seam_z-vertex.co.z)/.04));group.add([vertex.index],weight,'REPLACE');head_group.add([vertex.index],1-weight,'REPLACE')
    sphere('Fitted upper gum',(0,-.375,1.239),(.048,.010,.004),gum)
    sphere('Fitted lower gum',(0,-.350,1.222),(.045,.010,.004),gum,'Repair-Jaw')
    sphere('Fitted tongue',(0,-.350,1.225),(.030,.025,.006),tongue_mat,'Repair-Tongue')
    for upper in (True,False):
        for i,x in enumerate((-.042,-.024,-.008,.008,.024,.042)):
            sphere(('Fitted upper tooth ' if upper else 'Fitted lower tooth ')+str(i),
                (x,(-.382 if upper else -.357)+.12*abs(x),1.233 if upper else 1.225),(.005,.007,.008 if abs(x)>.04 else .005),ivory,head if upper else 'Repair-Jaw')
    # Fit new small eyeballs to the original eye locations, retaining the original face surface.
    settings=[(modifier,modifier.show_viewport) for modifier in surface.modifiers]
    for modifier,_ in settings:modifier.show_viewport=False
    bpy.context.view_layer.update();local=surface.matrix_world.inverted()@rig.matrix_world
    def front(x,z,fallback):
        hit,point,normal,index=surface.ray_cast(local@Vector((x,fallback-1,z)),local.to_3x3()@Vector((0,1,0)))
        return (local.inverted()@point).y if hit else fallback
    eyes=[]
    for side,mark in zip(('L','R'),rig['lion_face_eyes']):
        center=Vector(mark);center.z-=.10*(rig['face_marks']['tip']-rig['face_marks']['chin'])
        center.y=front(center.x,center.z,center.y)+.013
        bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
        bone=rig.data.edit_bones.new('Repair-Eye.'+side);bone.head=center;bone.tail=center+Vector((0,-.03,0));bone.parent=rig.data.edit_bones[head]
        bpy.ops.object.mode_set(mode='OBJECT');eyes.append('Repair-Eye.'+side)
        radius=Vector((.032,.020,.028))
        sphere('Fitted eyeball '+side,center,radius,sclera,eyes[-1])
        sphere('Fitted iris '+side,center+Vector((0,-.0205,0)),(.014,.003,.016),iris,eyes[-1])
        sphere('Fitted pupil '+side,center+Vector((0,-.023,0)),(.0075,.0015,.010),pupil,eyes[-1])
        sphere('Fitted glint '+side,center+Vector((-.003,-.025,.005)),(.002,.001,.0025),glint,eyes[-1])
        for upper in (True,False):
            points=[];closed=[];polygons=[];rows=12;cols=28
            for row in range(rows+1):
                fraction=row/(rows-1)*.99 if row<rows else 1
                pole=math.pi/2 if upper else -math.pi/2;edge=math.radians(50 if upper else -55);end=math.radians(-5)
                for column in range(cols+1):
                    longitude=-math.pi/2+math.pi*column/cols
                    def position(boundary):
                        latitude=pole+(boundary-pole)*fraction
                        return center+Vector((radius.x*1.04*math.cos(latitude)*math.sin(longitude),-radius.y*1.40*math.cos(latitude)*math.cos(longitude),radius.z*1.04*math.sin(latitude)))
                    points.append(position(edge));closed.append(position(end))
                    if row<rows and column<cols:
                        a=row*(cols+1)+column;polygons.append((a,a+1,a+cols+2,a+cols+1))
            data=bpy.data.meshes.new('Fitted spherical eyelid');data.from_pydata(points,[],polygons);data.update()
            obj=bpy.data.objects.new('Fitted '+('upper' if upper else 'lower')+' lid '+side,data);bpy.context.scene.collection.objects.link(obj)
            data.materials.append(fur);data.materials.append(rim)
            for polygon in data.polygons:
                if polygon.index>=(rows-1)*cols:polygon.material_index=1
            bind(obj);obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Repair_Blink_'+side)
            for vertex,point in zip(key.data,closed):vertex.co=point
    for modifier,enabled in settings:modifier.show_viewport=enabled
    error=max((basis.data[i].co-point).length for i,point in enumerate(original))
    return new,{'jaw_bone':'Repair-Jaw','tongue_bone':'Repair-Tongue','eye_bones':eyes,'jaw_weighted_vertices':affected,'new_lip_seam_edges':len(edges),'mouth_line_z':seam_z,
        'neutral_surface_max_change_m':error,'approach':'Original facial surface/UVs preserved; fitted oral anatomy and small eyes/lids added.'}
