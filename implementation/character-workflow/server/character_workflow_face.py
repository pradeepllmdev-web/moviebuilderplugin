"""Reuse the server face kit's oral anatomy on an existing skinned mesh."""
import numpy as np
import pygltflib as gl
from scipy.spatial import cKDTree
import animation_builder as ab
import face_on_glb as fg
import face_rig
from blend_shapes import read_accessor

def fit_replacement(src,dst,face):
    original=gl.GLTF2().load(str(src));om,op=fg._mesh_primitive(original)
    vertices=read_accessor(original,op.attributes.POSITION).astype(np.float64)
    faces=read_accessor(original,op.indices).astype(np.int64).reshape(-1,3)
    colors=fg._vertex_colours(original,op,len(vertices))
    kit=face_rig.build_face(vertices,faces,colors,face['boxes'],face['render'],face['front'],separate_eyes=False,separate_mouth=True)
    info=fg.add_face(src,dst,face,1.0)
    g=gl.GLTF2().load(str(dst));mesh,prim=fg._mesh_primitive(g);blob=bytearray(g.binary_blob())
    names=mesh.extras['targetNames'];tree=cKDTree(vertices)
    joints=read_accessor(original,op.attributes.JOINTS_0).astype(np.uint16)
    weights=read_accessor(original,op.attributes.WEIGHTS_0).astype(np.float32)
    def accessor(a,kind,component=gl.FLOAT):
        return ab.add_accessor(blob,g,a.tobytes(),component,len(a),kind)
    kept=faces[~kit['hidden_faces']].astype(np.uint32).reshape(-1)
    if len(kept):prim.indices=accessor(kept,'SCALAR',gl.UNSIGNED_INT)
    for part in kit['parts']:
        points=np.asarray(part['positions'],dtype=np.float32)
        neutral=points+np.asarray(part.get('base_shift',np.zeros_like(points)),dtype=np.float32)
        nearest=tree.query(points)[1]
        # Copy normalized skin influences so anatomy follows the same head skeleton.
        ww=weights[nearest].copy();ww/=np.maximum(ww.sum(axis=1,keepdims=True),1e-8)
        attrs=gl.Attributes(POSITION=accessor(neutral,'VEC3'),JOINTS_0=accessor(joints[nearest],'VEC4',gl.UNSIGNED_SHORT),WEIGHTS_0=accessor(ww,'VEC4'))
        material=len(g.materials);g.materials.append(gl.Material(name=part['name'],doubleSided=True,pbrMetallicRoughness=gl.PbrMetallicRoughness(baseColorFactor=list(part['color']),roughnessFactor=part.get('roughness',.7),metallicFactor=0)))
        targets=[]
        for name in names:
            delta=np.asarray(part.get('morphs',{}).get(name,np.zeros_like(points)),dtype=np.float32)
            targets.append({'POSITION':accessor(delta,'VEC3')})
        indices=np.asarray(part['faces'],dtype=np.uint32).reshape(-1)
        mesh.primitives.append(gl.Primitive(attributes=attrs,indices=accessor(indices,'SCALAR',gl.UNSIGNED_INT),material=material,targets=targets))
    g.set_binary_blob(bytes(blob));g.buffers[0].byteLength=len(blob);g.save(str(dst))
    info['oral_parts']=len(kit['parts']);info['hidden_interior_faces']=int(kit['hidden_faces'].sum());info['visual_review_required']=True
    return info


def fit(src,dst,face):
    """Default to preserving source anatomy until replacement fitting is reviewed."""
    face={**face,'separate_mouth':False,'separate_eyes':False}
    from character_workflow_performance import mouth_mode,jaw_deformation,VERSION
    mode=mouth_mode(face['boxes'],face.get('source_mouth','auto'))
    original=gl.GLTF2().load(str(src));om,op=fg._mesh_primitive(original)
    original_vertices=read_accessor(original,op.attributes.POSITION).astype(np.float64)
    calibration=face_rig.Face(original_vertices,None,face['boxes'],face['render'],face['front'])
    shift,jaw,protected_top=jaw_deformation(original_vertices,calibration.part,face['front'],mode)
    info=fg.add_face(src,dst,face,0)
    g=gl.GLTF2().load(str(dst));blob=bytearray(g.binary_blob())
    fitted_mesh,fitted_prim=fg._mesh_primitive(g)
    fitted_prim.attributes.POSITION=ab.add_accessor(blob,g,(original_vertices+shift).astype(np.float32).tobytes(),gl.FLOAT,len(shift),'VEC3',min_val=(original_vertices+shift).min(axis=0).tolist(),max_val=(original_vertices+shift).max(axis=0).tolist())
    for mesh in g.meshes:
        names=(mesh.extras or {}).get('targetNames',[])
        for primitive in mesh.primitives:
            if primitive.material is not None and g.materials[primitive.material].name=='eyelids':
                if face.get('front',1)>0:
                    acc=g.accessors[primitive.indices];view=g.bufferViews[acc.bufferView]
                    start=(view.byteOffset or 0)+(acc.byteOffset or 0)
                    indices=read_accessor(g,primitive.indices).reshape(-1,3).copy()[:,[0,2,1]].copy()
                    blob[start:start+indices.nbytes]=indices.tobytes()
                if primitive.attributes.COLOR_0 is not None:
                    acc=g.accessors[primitive.attributes.COLOR_0];view=g.bufferViews[acc.bufferView]
                    start=(view.byteOffset or 0)+(acc.byteOffset or 0)
                    color=read_accessor(g,primitive.attributes.COLOR_0).copy()
                    # Keep only a thin lash edge, rather than a broad dark band.
                    for offset in range(0,len(color),221):
                        skin=color[offset,:3].copy();color[offset:offset+221,:3]=skin
                        color[offset+204:offset+221,:3]=skin*.6
                    blob[start:start+color.nbytes]=color.tobytes()
            for name,target in zip(names,primitive.targets or []):
                if name not in ('jawOpen','mouthPucker','mouthWide','mouthClose','lowerLipBite'):continue
                idx=target['POSITION'] if isinstance(target,dict) else target.POSITION
                accessor=g.accessors[idx];view=g.bufferViews[accessor.bufferView]
                start=(view.byteOffset or 0)+(accessor.byteOffset or 0)
                delta=read_accessor(g,idx).copy()
                if primitive is fitted_prim and name=='jawOpen':delta=jaw.astype(np.float32)
                else:
                    delta*=.4
                    if primitive is fitted_prim:delta[original_vertices[:,1]>=protected_top]=0
                blob[start:start+delta.nbytes]=delta.tobytes()
                accessor.min=delta.min(axis=0).tolist();accessor.max=delta.max(axis=0).tolist()
    g.set_binary_blob(bytes(blob));g.buffers[0].byteLength=len(blob);g.save(str(dst))
    info.update(oral_parts=0,anatomy_mode='preserve source mouth',source_mouth=mode,performance_version=VERSION,upper_face_jaw_error=float(np.max(np.abs(jaw[original_vertices[:,1]>=protected_top]))) if np.any(original_vertices[:,1]>=protected_top) else 0,visual_review_required=True,
                limitations=['Source teeth and tongue are retained, not inferred or rebuilt','Separate unbound mouth parts may require fitting','Lip closure and facial likeness require visual review'])
    return info
