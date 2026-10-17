from pathlib import Path
p=Path('implementation/character-workflow/server/character_workflow_face.py');t=p.read_text();t=t.replace('def fit(src,dst,face):','def fit_replacement(src,dst,face):',1)
t+='''

def fit(src,dst,face):
    """Default to preserving source anatomy until replacement fitting is reviewed."""
    face={**face,'separate_mouth':False,'separate_eyes':False}
    info=fg.add_face(src,dst,face,.25)
    g=gl.GLTF2().load(str(dst));blob=bytearray(g.binary_blob())
    for mesh in g.meshes:
        names=(mesh.extras or {}).get('targetNames',[])
        for primitive in mesh.primitives:
            for name,target in zip(names,primitive.targets or []):
                if name not in ('jawOpen','mouthPucker','mouthWide','mouthClose','lowerLipBite'):continue
                idx=target['POSITION'] if isinstance(target,dict) else target.POSITION
                accessor=g.accessors[idx];view=g.bufferViews[accessor.bufferView]
                start=(view.byteOffset or 0)+(accessor.byteOffset or 0)
                delta=read_accessor(g,idx).copy();delta*=.35 if name=='jawOpen' else .4
                blob[start:start+delta.nbytes]=delta.tobytes()
                accessor.min=delta.min(axis=0).tolist();accessor.max=delta.max(axis=0).tolist()
    g.set_binary_blob(bytes(blob));g.save(str(dst))
    info.update(oral_parts=0,anatomy_mode='preserve source mouth',visual_review_required=True,
                limitations=['Source teeth and tongue are retained, not inferred or rebuilt','Lip closure and facial likeness require visual review'])
    return info
''';p.write_text(t)
p=Path('implementation/character-workflow/server/character_workflow.py');t=p.read_text();old="face = await character3d_api.detect_face(path / 'body-rig.glb', path, 'front', face_on_glb.facing(path / 'body-rig.glb'))";new="import character_workflow_landmarks\n                    face = await character_workflow_landmarks.detect(path / 'body-rig.glb', path)";assert old in t;t=t.replace(old,new);p.write_text(t)
