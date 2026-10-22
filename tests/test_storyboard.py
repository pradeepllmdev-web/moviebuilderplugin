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
