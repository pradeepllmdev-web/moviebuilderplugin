"""production rules, prompts, the lint and the generate-and-repair loop (no Blender, no network: a fake model)"""
import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import production_rules as pr,film_lint as fl,film_from_story as ffs,llm
ENV=os.path.join(os.path.dirname(__file__),'..','environment_library')
def _source():
    return '\n'.join(open(os.path.join(ENV,f),encoding='utf-8',errors='ignore').read() for f in sorted(os.listdir(ENV)) if f.endswith(('.py','.json')) and f!='production_rules.json')

def test_rules_are_well_formed_and_every_guard_exists_in_the_code():
    rules=pr.load();ids=[r['id'] for r in rules];assert len(ids)==len(set(ids)) and len(rules)>=25;src=_source()
    for r in rules:
        assert r['severity'] in('must','should') and r['text'] and set(r['stages'])<=set(pr.STAGES),r['id']
        assert r['guard']=='manual' or r['guard'] in src,(r['id'],r['guard'])

def test_prompts_carry_the_rules_and_the_real_capabilities():
    p=pr.prompt_for('film_spec');cap=pr.capabilities()
    for r in pr.rules_for('film_spec'):assert r['text'] in p
    assert 'FILM JSON' in p and 'person' in cap['species'] and 'brisk' in cap['gaits'] and 'meadow' in cap['location_presets'] and 'key' in cap['prop_kinds'] and 'pedestal' in cap['location_object_kinds']
    assert 'T-pose' in pr.prompt_for('animation') and 'T-pose' not in pr.prompt_for('story')
    assert [r['id'] for r in pr.rules_for('unreal')]==['U01','U02']

def test_messages_map_back_to_rules():
    assert 'T01' in pr.rule_ids_in('s: nell walks for 12 s (4-16 s) without speaking') and 'S02' in pr.rule_ids_in("the prop 'x' is set up but never used (a setup")

PEOPLE=[dict(id='ann',name='Ann',species='person',height=1.6,colors=[[.8,.3,.3],[.25,.28,.4],[.2,.12,.08]],description='a woman in red'),dict(id='ben',name='Ben',species='person',height=1.9,width=1.15,colors=[[.3,.5,.8],[.35,.3,.2],[.2,.12,.08]],description='a tall man in blue')]
def scene_json(sid,lines):
    return {'id':sid,'title':sid.title(),'objective':'talk about '+sid,'intent':'x','location':{'preset':'meadow','seed':3},'time':'day','ambience':'wind','music':'calm',
        'cast':[{'id':'ann','at':[-1.5,0],'face':'ben'},{'id':'ben','at':[1.5,0],'face':'ann'}],
        'steps':[{'do':'convo','lines':[['ann',lines[0],'warm','ben'],['ben',lines[1],'joy','ann'],['ann',lines[2],'warm','ben']]},{'do':'icon','who':'ben','kind':'joy','dur':1.5}]}

def test_lint_accepts_a_good_scene_expands_convo_and_flags_a_silent_walk():
    film=dict(id='f',title='F',cast=PEOPLE,scenes=[scene_json('a',['Morning, Ben, the bread smells wonderful.','It does, Ann. Warm from the oven.','Then let us eat it before it cools.'])])
    n=fl.normalise(film);assert sum(1 for b in n['scenes'][0]['steps'] if b['do']=='say')==3 and fl.lint(film)['ok']
    bad=json.loads(json.dumps(film));bad['scenes'][0]['cast'][0]['at']=[-12,0];bad['scenes'][0]['steps'].insert(0,{'do':'go','who':'ann','to':[-2,0],'gait':'walk'})
    rep=fl.lint(bad);assert 'T01' in rep['rules'] or 'T05' in rep['rules']

def test_generate_repairs_a_bad_scene_with_the_error_text():
    calls=dict(outline=0,scene=0,bad_seen=0);texts={'one':['The tower bell rang early today.','I heard it from the bakery, Ann.','Then somebody is awake before us.'],'two':['Look at the tower, the door is open.','Somebody has left a lantern burning.','Let us see who it belongs to.'],'three':['The lantern was the keeper’s all along.','He will be glad we found it.','Then we return it with our thanks.']}
    outline={'id':'tower','title':'The Tower','logline':'x','target_minutes':3,'cast':PEOPLE,'scenes':[{'id':k,'title':k.title(),'objective':'goal '+k,'location':'meadow','time':'day','who':['ann','ben'],'summary':'s'} for k in texts]}
    state={}
    def fake(system,prompt):
        if 'STORY:' in prompt:calls['outline']+=1;return outline
        tail=prompt.split('WRITE THIS SCENE',1)[1];sid=[k for k in texts if '"id": "%s"'%k in tail][0];calls['scene']+=1
        if sid=='two' and not state.get('tried'):
            state['tried']=True;s=scene_json('two',texts['two']);s['steps'][0]['do']='teleport';return s       # a mistake
        if 'rejected' in prompt:calls['bad_seen']+=1
        return scene_json(sid,texts[sid])
    llm.register_provider('fake',fake)
    got=ffs.generate('A short story about a lantern.',provider='fake',use_cache=False)
    assert got is not None;film,rep=got
    assert [s['id'] for s in film['scenes']]==['one','two','three'] and rep['ok'] and calls['bad_seen']==1 and calls['scene']==4
    import tempfile;assert ffs.write_film(film,tempfile.mkdtemp()).exists()

def test_generate_returns_none_without_a_model():
    assert ffs.generate('x',provider='none',use_cache=False) is None


def _one_scene(steps,cast_at=((-3,0),(1.5,0)),target=None):
    s=scene_json('x',['a b c d','e f g h','i j k l']);s['steps']=steps;s['cast']=[{'id':'ann','at':list(cast_at[0]),'face':'ben'},{'id':'ben','at':list(cast_at[1]),'face':'ann'}]
    if target:s['target_seconds']=target
    return dict(id='f',title='F',cast=PEOPLE,scenes=[s])

def test_lint_enforces_the_scene_length_the_brief_asks_for():
    steps=[{'do':'say','who':'ann','text':'Morning, Ben, the bread smells wonderful.','mood':'warm','to':'ben'},{'do':'say','who':'ben','text':'It does, Ann. Warm from the oven.','mood':'joy','to':'ann'}]
    rep=fl.lint(_one_scene(steps,target=2));assert any('but the brief asks for' in e for e in rep['errors']) and 'S09' in rep['rules']
    assert not any('but the brief asks for' in e for e in fl.lint(_one_scene(steps,target=10))['errors'])

def test_lint_flags_a_run_without_a_chase_or_an_emergency():
    steps=[{'do':'go','who':'ann','to':[0,0],'gait':'run','talk':['Ben, wait for me please.','warm','ben']}]
    rep=fl.lint(_one_scene(steps));assert 'T04' in rep['rules']
    alarmed=[{'do':'icon','who':'ann','kind':'alarm','dur':1.5},{'do':'go','who':'ann','to':[0,0],'gait':'run','talk':['Ben, the bridge is falling!','concern','ben']}]
    assert 'T04' not in fl.lint(_one_scene(alarmed))['rules']

def test_two_beats_for_one_character_at_once_is_a_spec_error_the_model_sees():
    steps=[[{'do':'act','who':'ann','clip':'nod'},{'do':'act','who':'ann','clip':'wave'}]]
    rep=fl.lint(_one_scene(steps));assert any('two beats at the same time' in e for e in rep['errors'])
