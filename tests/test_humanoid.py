import os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import cast_registry as cr,perf_plan as pp
from perf_dsl import *
def person(i,h=1.75,**k):return dict(dict(id=i,name=i.title(),species='person',height=h,colors=[(.8,.3,.3),(.25,.28,.4),(.2,.12,.08)]),**k)
def spec(cast,props=None,objects=None,steps=None):
 return scene('t','t',loc('meadow',3,objects=objects or []),cast,steps or [],props=props)
def plan(cast,**k):
 reg=cr.Registry();[reg.add(c) for c in cast]
 return pp.compile(spec([at(c['id'],-3+2*i,-2) for i,c in enumerate(cast)],**k),reg)
class Registry(unittest.TestCase):
 def test_person_is_a_humanoid_with_a_dress(self):
  L=cr.resolve(person('ann'));self.assertEqual(L['humanoid'],'UAL');self.assertEqual(set(L['dress']),{'skin','shirt','pants','shoes','hair'})
  self.assertAlmostEqual(L['scale'][2],1.75/cr.LION_HEIGHT,3);self.assertIsNone(cr.resolve(dict(id='mara',name='Mara',species='fox')).get('humanoid'))
 def test_dress_follows_the_record_colours_and_is_stable(self):
  a=cr.resolve(person('ann'))['dress'];self.assertEqual(a,cr.resolve(person('ann'))['dress']);self.assertEqual(a['shirt'],(.8,.3,.3));self.assertEqual(a['pants'],(.25,.28,.4))
 def test_people_of_different_ids_differ(self):
  self.assertNotEqual(cr.resolve(person('ann',colors=[]))['dress'],cr.resolve(person('bob',colors=[]))['dress'])
 def test_speeds_scale_with_height_and_pick_the_clip(self):
  v,c=cr.humanoid_speed('walk',1.83);self.assertAlmostEqual(v,cr.HUMAN_PLAN['walk']);self.assertEqual(c,'walk')
  self.assertLess(cr.humanoid_speed('walk',1.2)[0],v);self.assertEqual(cr.humanoid_speed('run',1.8)[1],'sprint');self.assertEqual(cr.humanoid_speed('brisk',1.8)[1],'jog');self.assertEqual(cr.humanoid_speed('sneak',1.8)[1],'slow')
 def test_plan_speed_is_always_within_the_scale_range_of_a_clip(self):       # the clip is played at nat/planned: stay inside the 0.45 .. 2.6 clamp
  for g,key in (('walk','walk'),('brisk','jog'),('run','sprint'),('slow','slow')):
   ratio=cr.HUMAN_NAT[key]/cr.HUMAN_PLAN[g];self.assertTrue(.45<=ratio<=2.6,(g,ratio))
class Planner(unittest.TestCase):
 def test_a_person_walks_at_a_human_pace(self):
  P2=pp.compile(spec([at('ann',-2,0)],steps=[go('ann',[2,0],gait='walk')]),_reg([person('ann')]))
  t=P2.actors['ann'].walks[0];speed=t[4];self.assertAlmostEqual(speed,cr.humanoid_speed('walk',1.75)[0]*P2.actors['ann'].look['pace'],2)
 def test_a_long_walk_becomes_a_jog_at_the_jog_pace(self):
  P=pp.compile(spec([at('ann',-9,0)],steps=[go('ann',[9,0],gait='walk')]),_reg([person('ann')]));w=P.actors['ann'].walks[0];self.assertEqual(w[2],'brisk');self.assertAlmostEqual(w[4],cr.humanoid_speed('brisk',1.75)[0]*P.actors['ann'].look['pace'],2)
 def test_a_person_can_take_from_a_table_and_give_to_a_seated_person(self):
  c=[person('ann'),person('ben',1.85)];reg=_reg(c)
  s=spec([at('ann',-3,-2,face=[0,0]),at('ben',3,-2,face=[0,0])],props=[prop('apple','apple',4,3,on='stand0',size=1.4)],objects=[dict(kind='log',at=[0,0],id='seat1',w=2.4),dict(kind='pedestal',at=[4,3],id='stand0',height=1.05,size=.3)],steps=[sit('ann','seat1.0',face='ben'),take('ben','apple'),give('ben','ann')])
  P=pp.compile(s,reg);self.assertEqual([e['kind'] for e in P.events if e['kind'] in('take','give')],['take','give'])
 def test_a_low_prop_is_refused_for_a_person_who_cannot_bend(self):
  reg=_reg([person('ben',1.85)]);s=spec([at('ben',3,-2)],props=[prop('apple','apple',4,3,on='stand0',size=1.4)],objects=[dict(kind='pedestal',at=[4,3],id='stand0',height=.4,size=.3)],steps=[take('ben','apple')])
  with self.assertRaises(pp.SpecError):pp.compile(s,reg)
 def test_a_person_points_inside_arms_reach(self):
  reg=_reg([person('ann')]);P=pp.compile(spec([at('ann',0,0)],steps=[point('ann',[8,-4,1.],1.4)]),reg);a=P.actors['ann'];_,pos=P.hand_target(a,'R',a.hands['R'][1][0]+.5)
  self.assertLess(((pos[0]-a.X[0])**2+(pos[1]-a.Y[0])**2)**.5,.62*a.size)
def _reg(cast):
 reg=cr.Registry();[reg.add(c) for c in cast];return reg
if __name__=='__main__':unittest.main()
