"""Fitted eyelid overlays for the explicitly calibrated, prepared biped lion."""
import math

def add_lids(rig):
    import bpy
    from mathutils import Vector
    if rig.name!='Lion_Realistic' or rig.get('lion_face_version')!=4:
        raise ValueError('This eyelid fit is calibrated only for the prepared Lion_Realistic v4')
    surface=next(obj for obj in rig.children_recursive if obj.type=='MESH' and obj.data.shape_keys)
    marks=[Vector(point) for point in rig['lion_face_eyes']]
    scale=float(rig['face_marks']['tip']-rig['face_marks']['chin'])
    # Raycast in rest space; source skin modifiers are disabled temporarily for fitting.
    modifiers=[(mod,mod.show_viewport) for mod in surface.modifiers]
    for mod,_ in modifiers:mod.show_viewport=False
    bpy.context.view_layer.update()
    relative=surface.matrix_world.inverted()@rig.matrix_world
    inverse=relative.inverted()
    def fitted(x,z,fallback):
        origin=relative@Vector((x,fallback-1,z));direction=relative.to_3x3()@Vector((0,1,0))
        hit,point,normal,index=surface.ray_cast(origin,direction)
        if not hit:return Vector((x,fallback,z))
        return inverse@point
    created=[]
    for side,eye in zip(('L','R'),marks):
        eye.z-=.10*scale
        vertices=[];closed=[];faces=[];columns=20;rows=8
        rx=.24*scale;rz=.20*scale
        for row in range(rows+1):
            v=row/rows
            for column in range(columns+1):
                u=-1+2*column/columns;arc=math.sqrt(max(0,1-u*u));x=eye.x+rx*u
                z=eye.z+rz*arc*(1-2*v)
                point=fitted(x,z,eye.y);point.y-=.0015
                rest=fitted(x,eye.z+rz*arc+.001,eye.y);rest.y+=.003+v*.001
                vertices.append(rest);closed.append(point)
                if row<rows and column<columns:
                    a=row*(columns+1)+column;faces.append((a,a+1,a+columns+2,a+columns+1))
        data=bpy.data.meshes.new('Lion eyelid '+side);data.from_pydata(vertices,[],faces);data.update()
        obj=bpy.data.objects.new('Lion upper lid '+side,data);bpy.context.scene.collection.objects.link(obj);obj.parent=rig
        obj.shape_key_add(name='Basis');key=obj.shape_key_add(name='Lion_LidClosure_'+side)
        for vertex,point in zip(key.data,closed):vertex.co=point
        group=obj.vertex_groups.new(name='mixamorig:Head');group.add(list(range(len(vertices))),1,'REPLACE')
        armature=obj.modifiers.new('Head skin','ARMATURE');armature.object=rig
        material=bpy.data.materials.new('Lion lid fur '+side);material.use_nodes=True
        shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.68,.43,.22,1);shader.inputs['Roughness'].default_value=.9
        obj.data.materials.append(material)
        for polygon in data.polygons:polygon.use_smooth=True
        created.append(obj)
        # A narrow lid crease makes a closed eye readable, rather than a blank skin patch.
        crease_vertices=[];crease_closed=[];crease_faces=[]
        for row in range(2):
            for column in range(columns+1):
                u=-1+2*column/columns;x=eye.x+rx*.87*u
                z=eye.z+.002*u*u+(row-.5)*.0007
                point=fitted(x,z,eye.y);point.y-=.0022
                rest=fitted(x,eye.z+rz*math.sqrt(max(0,1-u*u))+.001,eye.y);rest.y+=.005
                crease_vertices.append(rest);crease_closed.append(point)
                if row==0 and column<columns:crease_faces.append((column,column+1,column+columns+2,column+columns+1))
        data=bpy.data.meshes.new('Lion lid crease '+side);data.from_pydata(crease_vertices,[],crease_faces);data.update()
        crease=bpy.data.objects.new('Lion lid crease '+side,data);bpy.context.scene.collection.objects.link(crease);crease.parent=rig
        crease.shape_key_add(name='Basis');key=crease.shape_key_add(name='Lion_LidClosure_'+side)
        for vertex,point in zip(key.data,crease_closed):vertex.co=point
        group=crease.vertex_groups.new(name='mixamorig:Head');group.add(list(range(len(crease_vertices))),1,'REPLACE')
        modifier=crease.modifiers.new('Head skin','ARMATURE');modifier.object=rig
        material=bpy.data.materials.new('Lion crease '+side);material.use_nodes=True
        shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.09,.035,.009,1)
        shader.inputs['Roughness'].default_value=.9;data.materials.append(material);created.append(crease)
    for mod,enabled in modifiers:mod.show_viewport=enabled
    bpy.context.view_layer.update()
    return created
