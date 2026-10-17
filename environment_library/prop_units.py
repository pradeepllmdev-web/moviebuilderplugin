import math
def world_length_to_local(metres,metres_per_unit):
 if not math.isfinite(metres_per_unit) or metres_per_unit<1e-6:raise ValueError('Invalid rig scale')
 if not math.isfinite(metres) or metres<0:raise ValueError('Invalid prop dimension')
 return metres/metres_per_unit
