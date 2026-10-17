"""Join facial meshes while preserving shape deltas in the active object's space."""
import bpy

def join_preserving_shapes(objects, active):
    meshes=[o for o in objects if o.type=='MESH']
    # Blender appends the active object's vertices first.
    meshes=[active]+[o for o in bpy.context.scene.objects if o in meshes and o!=active]
    inverse=active.matrix_world.inverted()
    blocks=[];names=set()
    marker='_production_join_index';count=0
    for obj in meshes:
        if obj.data.attributes.get(marker):raise RuntimeError('Reserved join attribute already exists')
        attribute=obj.data.attributes.new(marker,'INT','POINT')
        for i,value in enumerate(attribute.data):value.value=count+i
        count+=len(obj.data.vertices)
        transform=inverse@obj.matrix_world
        keys=obj.data.shape_keys
        basis=keys.key_blocks[0] if keys else None
        base=[transform@v.co for v in (basis.data if basis else obj.data.vertices)]
        shapes={}
        if keys:
            for key in list(keys.key_blocks)[1:]:
                # Relative shapes must retain deltas, not another key's absolute pose.
                shapes[key.name]=[base[i]+transform.to_3x3()@(v.co-key.relative_key.data[i].co) for i,v in enumerate(key.data)]
                names.add(key.name)
        blocks.append((base,shapes))
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes:obj.select_set(True)
    bpy.context.view_layer.objects.active=active
    bpy.ops.object.join()
    attribute=active.data.attributes.get(marker)
    if not attribute:raise RuntimeError('Join lost vertex identity metadata')
    indices=[v.value for v in attribute.data]
    active.data.attributes.remove(attribute)
    if sorted(indices)!=list(range(count)):raise RuntimeError('Join changed vertex identities')
    if not names:return active
    if not active.data.shape_keys:active.shape_key_add(name='Basis')
    basis=active.data.shape_keys.key_blocks[0]
    expected=sum(len(base) for base,_ in blocks)
    if len(basis.data)!=expected:raise RuntimeError('Joined facial topology count changed')
    bases=[co for base,_ in blocks for co in base]
    for i,original in enumerate(indices):
        basis.data[i].co=bases[original]
        active.data.vertices[i].co=bases[original]
    for name in names:
        key=active.data.shape_keys.key_blocks.get(name) or active.shape_key_add(name=name)
        key.relative_key=basis
        values=[co for base,shapes in blocks for co in shapes.get(name,base)]
        for i,original in enumerate(indices):key.data[i].co=values[original]
    return active

def join_animated_shapes(scene,rig,frames):
    meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
    active=max(meshes,key=lambda o:len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0)
    samples={}
    for frame in range(1,frames+1):
        scene.frame_set(frame);values={}
        for mesh in meshes:
            if not mesh.data.shape_keys:continue
            for key in list(mesh.data.shape_keys.key_blocks)[1:]:values[key.name]=max(values.get(key.name,0),key.value)
        for name,value in values.items():samples.setdefault(name,[]).append(value)
    active=join_preserving_shapes(meshes,active);active.data.shape_keys.animation_data_clear()
    for name,values in samples.items():
        key=active.data.shape_keys.key_blocks[name]
        for frame,value in enumerate(values,1):key.value=value;key.keyframe_insert('value',frame=frame)
    return active
