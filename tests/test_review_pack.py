"""the review page (no Blender)"""
import os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import review_pack as rp

ROWS=[dict(t0=0,t1=3,purpose='Establish',detail='where we are'),dict(t0=3,t1=9,purpose='Dialogue',detail='Ann (warm)')]

def test_purpose_is_found_by_time():
    assert rp.purpose_at(ROWS,1.)[0]=='Establish' and rp.purpose_at(ROWS,5.)[0]=='Dialogue' and rp.purpose_at(ROWS,50.)==('','')

def test_page_has_notes_shots_lines_and_audit_and_escapes_text():
    sec=[dict(id='s1',title='1. <Scene>',goal='a goal',shots=[dict(img='review/scene_01/f_00_1.png',time=1.2,cut='establish',purpose='Establish',detail='x & y')],lines=[dict(t0=4.,speaker='ann',to='ben',mood='warm',text='Hello <there>')],audit=['AUDIT pose: arms held out in a T'])]
    page=rp.html_page('Film',['scene 1: a note'],sec)
    assert 'scene 1: a note' in page and 'review/scene_01/f_00_1.png' in page and 'Hello &lt;there&gt;' in page and '1. &lt;Scene&gt;' in page and 'arms held out in a T' in page and 'x &amp; y' in page
    clean=rp.html_page('Film',[],[dict(id='s',title='S',goal='',shots=[],lines=[],audit=[])]);assert 'No story notes' in clean and 'Audit clean' in clean
