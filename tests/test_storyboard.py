"""storyboard purposes and the table-read review (no Blender)"""
import os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import perf_dsl as d,perf_plan as pp,cast_registry as cr,perf_storyboard as sb

def plan():
    reg=cr.Registry([dict(id='a',name='A',species='fox'),dict(id='b',name='B',species='bear')])
    spec=d.scene('t','t',d.loc('village_square',1),[d.at('a',-6,0),d.at('b',4,0)],[d.convo([('a','Look over there!','joy','b')]),d.point('a',[10,6],1.6),d.go('b',[-2,4],gait='run'),d.act('a','joy'),d.icon('b','alarm',1.5)],props=[])
    return pp.compile(spec,reg)

def test_every_shot_has_a_purpose():
    rows=sb.scene_rows(plan());assert rows and rows[0]['purpose']=='Establish' and {r['purpose'] for r in rows}&{'Dialogue','Reveal','Chase','Travel','Action','Reaction','Wide hold','Wide','Hold'}

def test_review_flags_dead_time_and_talk():
    film=dict(title='t',id='t',cast=[dict(id='a'),dict(id='b')],scenes=[dict(id='s',title='s',objective='o',intent='i')]);md=sb.review_md(film,[plan()]);assert '| s |' in md and '## Notes' in md


def _film(scenes,cast=None):
    cast=cast or [dict(id='a',name='A',species='fox'),dict(id='b',name='B',species='bear')]
    return dict(id='f',title='F',cast=cast,scenes=scenes)

def _plans(film):
    reg=cr.Registry(film['cast'])
    return [pp.compile(s,reg) for s in film['scenes']]

def test_story_check_flags_a_walk_that_arrives_at_nothing():
    s=d.scene('s','S',d.loc('meadow',1),[d.at('a',-9,0),d.at('b',9,6)],[d.go('a',[-9,-5],gait='walk'),d.wait(5.),d.convo([('b','Hello there friend.','warm','a')]),d.wait(2.)],intent='x')
    f=_film([s]);notes=sb.story_check(f,_plans(f))
    assert any('walks for' in n and 'a walks' in n for n in notes)

def test_story_check_accepts_a_walk_up_to_someone_and_a_chase():
    s=d.scene('s','S',d.loc('meadow',1),[d.at('a',-9,0),d.at('b',2,0)],[d.go('a',[0.5,0],gait='walk'),d.convo([('a','Here I am again.','warm','b')]),d.run('b',[12,6])],intent='x')
    f=_film([s]);assert not [n for n in sb.story_check(f,_plans(f)) if 'walks for' in n]

def test_story_check_flags_a_prop_that_vanishes_between_scenes_and_repeated_lines():
    s1=d.scene('s1','S1',d.loc('meadow',1,objects=[dict(kind='pedestal',at=[2,0],id='stand0',height=.8,size=.3)]),[d.at('a',0,0)],[d.take('a','key'),d.convo([('a','This is the key to the tower.','warm','a')])],props=[d.prop('key','key',2,0,on='stand0')],intent='x')
    s2=d.scene('s2','S2',d.loc('meadow',1),[d.at('a',0,0)],[d.convo([('a','This is the key to the tower.','warm','a')])],intent='x')
    f=_film([s1,s2]);notes=sb.story_check(f,_plans(f))
    assert any('does not carry it on' in n for n in notes) and any('spoken 2 times' in n for n in notes)
    s2['cast'][0]['holds']='key';s2['props']=[d.prop('key','key',0,0,z=.8)]
    assert not any('does not carry it on' in n for n in sb.story_check(f,_plans(f)))
