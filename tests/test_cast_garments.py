"""cast_garments: pure geometry of skirts, capes and hats, and the new outfits (no Blender)"""
import math,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import cast_garments as cg,cast_registry as cr

def sane(V,F,M):
    assert V and F and len(F)==len(M)
    for f in F:
        assert len(set(f))>=3 and all(0<=i<len(V) for i in f)
    assert all(math.isfinite(c) for v in V for c in v)

def test_every_hat_is_valid_and_sits_on_the_head():
    for k in cg.HATS:
        V,F,M=cg.hat(k);sane(V,F,M)
        zs=[v[2] for v in V];assert 1.4<min(zs)<1.9 and max(zs)<2.4,k
        assert max(abs(v[0]) for v in V)<.5,k

def test_skirts_and_cape_are_valid():
    for k in cg.SKIRTS:
        V,F,M,ts=cg.skirt(k);sane(V,F,M);assert len(ts)==len(V) and 0<=min(ts) and max(ts)<=1.
    sane(*cg.cape()[:3])

def test_dress_flares_below_the_waist():
    V,F,M,ts=cg.skirt('dress');top=max(v[2] for v in V);r=lambda z:max(math.hypot(v[0],v[1]+14) for v in V if abs(v[2]-z)<4)
    assert r(14)>r(top)*1.3

def test_shell_opening_and_panel():
    env=lambda z:(-14.,[19.]*40)
    closed=cg.shell(env,90,56);opened=cg.shell(env,90,56,gap=.3);panel=cg.shell(env,84,60,arc=(-2.2,-.9),seg=10,neck=False)
    for g in (closed,opened,panel):sane(*g)
    assert len(opened[1])<len(closed[1])

def test_new_outfits_resolve_with_known_kinds():
    for o in ('villager','villageress','blacksmith','fisherman','shepherd','innkeeper','miller','monk','mayor','gentleman','tourist','cook','highlander','cowboy','artist'):
        assert o in cr.OUTFITS,o
        for a in cr.expand_outfit(dict(outfit=o,colors=[(.5,.5,.5)]*4)):assert (a if isinstance(a,str) else a['kind']) in cr.ACCESSORIES,(o,a)

def test_camera_keeps_people_in_frame_and_shows_faces():
    from pathlib import Path
    import perf_movie as pm,perf_plan as pp,perf_camera as pc
    for f in sorted((Path(__file__).resolve().parents[1]/'environment_library'/'films').glob('*.py')):
        film=pm.load_film(f);reg=pm.registry_of(film);bad=tot=0
        for sp in film['scenes']:
            P=pp.compile(sp,reg)
            for c in pc.direct(P):
                if c['kind'] in ('wide','group'):continue
                for u in (.15,.5,.85):
                    tot+=1;off,face=pc.shot_quality(P,c,c['t0']+(c['t1']-c['t0'])*u);bad+=off>.8 or face<.25
        assert bad<=.03*tot,(f.name,bad,tot)

def test_creature_species_resolve_and_do_not_speak():
    import perf_dsl as d,perf_plan as pp
    L=cr.resolve(dict(id='pg',name='Percy',species='pig'));assert L['creature']=='Pig' and L['radius']>.3
    reg=cr.Registry([dict(id='pg',name='Percy',species='pig'),dict(id='h',name='H',species='bear')])
    ok=d.scene('t','t',d.loc('meadow',1),[d.at('pg',-3,0),d.at('h',3,0)],[d.go('pg',[2,2],gait='run'),d.act('pg','jump'),d.sfx('oink',0.1,who='pg')]);P=pp.compile(ok,reg);assert P.audit()==[]
    bad=d.scene('t','t',d.loc('meadow',1),[d.at('pg',-3,0),d.at('h',3,0)],[d.say('pg','Hello','joy','h')])
    try:pp.compile(bad,reg);assert False
    except pp.SpecError:pass
