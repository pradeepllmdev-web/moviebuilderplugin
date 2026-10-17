import bpy,json
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew/server/character_workflows/8fe21e60764a4190ae23f4f2df71fd65/character.glb')
print('ACTIONS '+json.dumps([{'name':a.name,'slots':[(slot.identifier,slot.target_id_type) for slot in a.slots]} for a in bpy.data.actions if any(w in a.name.lower() for w in ['walk','run','talk'])]))
