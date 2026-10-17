"""Engine-independent dimension validation; no model geometry is loaded."""
import json,math
from pathlib import Path
POLICY=json.loads(Path(__file__).with_suffix('.json').read_text())
def positive(value,label):
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:raise ValueError(label+' must be a positive finite number')
 return float(value)
def metres(value):return positive(value,'metres')*POLICY['unreal_units_per_metre']
def building_height(floors,kind='residential',roof_cm=90):
 if isinstance(floors,bool) or not isinstance(floors,int) or not 1<=floors<=200:raise ValueError('floors must be an integer from 1 to 200')
 if kind not in ('residential','office'):raise ValueError('Unknown building kind')
 if isinstance(roof_cm,bool) or not isinstance(roof_cm,(int,float)) or not math.isfinite(roof_cm) or roof_cm<0:raise ValueError('Invalid roof height')
 return floors*POLICY['architecture_cm'][kind+'_floor']+roof_cm
def fit_dimensions(dimensions,profile=None,axis=None,target_cm=None):
 if len(dimensions)!=3:raise ValueError('Expected XYZ dimensions')
 native=[positive(v,'native dimension') for v in dimensions]
 if profile:
  spec=POLICY['profiles'][profile];axis=spec['axis'];target_cm=spec['target_cm']
 if axis not in ('x','y','z'):raise ValueError('Unknown fitting axis')
 target=positive(target_cm,'target size');factor=target/native['xyz'.index(axis)]
 return {'native_dimensions_cm':native,'uniform_scale':factor,'dimensions_cm':[v*factor for v in native],
         'fit_axis':axis,'target_cm':target,'profile':profile}
def grounded_location(origin,extent,scale=1):
 scale=positive(scale,'scale')
 return [-origin[0]*scale,-origin[1]*scale,(extent[2]-origin[2])*scale]
def pack_conversion(pack):
 spec=POLICY['pack_references'][pack['name']]
 reference=next(m for m in pack['meshes'] if m['path'].split('.')[-1]==spec['asset'])
 dimensions=[2*v for v in reference['extent_cm']]
 target=spec.get('target_cm') or building_height(spec['floors'],spec['kind'],spec['roof_cm'])
 result=fit_dimensions(dimensions,axis=spec['axis'],target_cm=target)
 result.update(reference_asset=reference['path'],assumption='Reference dimensions are configurable art-direction defaults, not inferred architectural measurements.')
 return result
