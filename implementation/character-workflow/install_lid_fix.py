from pathlib import Path
p=Path('implementation/character-workflow/server/character_workflow_face.py');t=p.read_text();needle="            for name,target in zip(names,primitive.targets or []):";replacement="""            if primitive.material is not None and g.materials[primitive.material].name=='eyelids':
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
            for name,target in zip(names,primitive.targets or []):"""
assert needle in t;t=t.replace(needle,replacement);p.write_text(t)
