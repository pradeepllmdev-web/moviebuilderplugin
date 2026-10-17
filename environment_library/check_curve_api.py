import unreal,json
from pathlib import Path
out={}
for cls in [unreal.AnimationLibrary,unreal.Skeleton,unreal.SkeletalMeshComponent]:
 out[cls.__name__]={name:str(getattr(cls,name).__doc__)[:1200] for name in dir(cls) if ('curve' in name.lower() and ('flag' in name.lower() or 'meta' in name.lower())) or name in ['get_morph_target','get_curve_value']}
Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin/samples/echo-inspector/curve-api.json').write_text(json.dumps(out,indent=2))
