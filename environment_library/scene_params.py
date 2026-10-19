"""Run-time parameters for the set pieces (pure Python, no Blender needed to read them).

A story planner or the studio passes a JSON object in the environment variable SCENE_PARAMS, for example {"time_of_day":"night","hero_tint":[.9,.7,.5],"title":"Chapter 3"}.
Scenes read it with scene_params.get() and apply it with scene_kit.apply_params(); unknown keys are ignored, missing keys keep the scene's own look."""
import json,os,math
TIME_OF_DAY={
 'dawn':dict(sun_color=(1,.78,.55),sun_energy=3.4,sun_rot=(48,0,-30),world=(.82,.62,.5)),
 'day':dict(sun_color=(1,.97,.9),sun_energy=4.2,sun_rot=(60,0,-20),world=(.55,.72,.95)),
 'dusk':dict(sun_color=(1,.66,.42),sun_energy=3.0,sun_rot=(80,0,40),world=(.72,.45,.35)),
 'night':dict(sun_color=(.45,.55,.9),sun_energy=.8,sun_rot=(40,0,60),world=(.04,.05,.1)),
 'overcast':dict(sun_color=(.85,.88,.95),sun_energy=1.6,sun_rot=(55,0,0),world=(.5,.54,.6)),
}
KEYS=('time_of_day','hero_tint','title')
def defaults():return dict(time_of_day=None,hero_tint=None,title=None)
def get(env=None):
 """Parameters from SCENE_PARAMS (or the given string/dict), validated; bad values fall back to the scene defaults."""
 raw=env if env is not None else os.environ.get('SCENE_PARAMS','')
 d=defaults()
 if isinstance(raw,str):
  try:raw=json.loads(raw) if raw.strip() else {}
  except ValueError:raw={}
 if not isinstance(raw,dict):return d
 t=raw.get('time_of_day')
 if t in TIME_OF_DAY:d['time_of_day']=t
 h=raw.get('hero_tint')
 if isinstance(h,(list,tuple)) and len(h)==3 and all(isinstance(x,(int,float)) and 0<=x<=2 for x in h):d['hero_tint']=tuple(float(x) for x in h)
 if isinstance(raw.get('title'),str):d['title']=raw['title'][:80]
 return d
def preset(name):
 p=TIME_OF_DAY[name];return dict(p,sun_rot=tuple(math.radians(v) for v in p['sun_rot']))
