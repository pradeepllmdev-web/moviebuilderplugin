"""the lens is never inside a tree, rock, house or tower, at any time of any cut (no Blender)"""
import math,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import numpy as np,perf_camera as pc,perf_movie as pm,perf_plan as pp
ENV=os.path.join(os.path.dirname(__file__),'..','environment_library')
def _check(film_name,scene_ids):
    film=pm.load_film(os.path.join(ENV,'films',film_name+'.py'));reg=pm.registry_of(film);pm.plan_check(film,reg);bad=[]
    for sp in film['scenes']:
        if sp['id'] not in scene_ids:continue
        P=pp.compile(sp,reg);O=np.array(P.layout['obstacles'],float).reshape(-1,3)
        for c in pc.direct(P):
            for u in (0,.25,.5,.75,1.):
                t=c['t0']+(c['t1']-c['t0'])*u;pos,aim,lens=pc.frame(P,c,t)
                if P.layout.get('inside'):continue
                for cx,cy,r in O:
                    if r>.5 and math.hypot(pos[0]-cx,pos[1]-cy)<r+.44:bad.append((sp['id'],c['kind'],round(t,1),round(math.hypot(pos[0]-cx,pos[1]-cy),2),round(r,2)))
    return bad
def test_no_camera_inside_a_solid_in_tree_scenes():
    assert _check('farm_egg',{'dawn','chaos','apple'})==[]
    assert _check('pie_thief',{'tracking','hill'})==[]
