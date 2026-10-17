"""Load a pinned MPFB checkout for this process, without global installation."""
import sys
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[2];LOCAL=ROOT/'.verification/mpfb'

def initialize():
    sys.path.insert(0,str(LOCAL/'source/src'))
    import mpfb
    original_preference=mpfb.get_preference
    mpfb.get_preference=lambda name: str(LOCAL/'runtime') if name=='mpfb_user_data' else original_preference(name)
    original=bpy.utils.extension_path_user
    def isolated(package,*args,**kwargs):
        if package=='mpfb':
            home=LOCAL/'runtime';home.mkdir(exist_ok=True);return str(home)
        return original(package,*args,**kwargs)
    bpy.utils.extension_path_user=isolated
    if 'mpfb' not in bpy.context.preferences.addons:
        bpy.context.preferences.addons.new().module='mpfb'
    mpfb.register()
    from mpfb.services.locationservice import LocationService
    LocationService._user_data=str(LOCAL/'assets')
    from mpfb.services.assetservice import AssetService
    AssetService.rescan_pack_metadata()
    print('MPFB_READY',mpfb.VERSION,flush=True)
    return mpfb

if __name__=='__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True);initialize()
    from mpfb.services.humanservice import HumanService
    from mpfb.services.faceservice import FaceService
    mesh=HumanService.create_human();rig=HumanService.add_builtin_rig(mesh,'mixamo')
    FaceService.load_targets(mesh,load_microsoft_visemes=False,load_arkit_faceunits=True)
    print('CAPABILITIES',len(mesh.data.shape_keys.key_blocks),list(rig.pose.bones.keys()),flush=True)
