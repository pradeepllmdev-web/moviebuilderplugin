"""atmosphere choice and the ffmpeg command lines of the final render (no Blender, no ffmpeg run)"""
import os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import perf_fx as fx,render_film as rf

def test_effects_follow_time_ambience_and_place():
    assert fx.choose('day','wind','meadow')==['dust','leaves'] and fx.choose('night','wind','harbor')==['fireflies'] and fx.choose('day','rain','harbor')==['rain']
    assert fx.choose('day','hall','room')==['dust'] and fx.choose('day','wind','meadow',0,['snow','bad'])==['snow']

def test_scene_command_mixes_tracks_and_draws_a_card():
    c=rf.scene_cmd('f','a1.wav a2.wav'.split(),'o.mp4',24,'A: title','goal',True,seconds=9.5)
    s=' '.join(c);assert 'amix=inputs=2:normalize=0' in s and 'drawtext' in s and '-t 9.500' in s and c[-1]=='o.mp4'
    assert 'drawtext' not in ' '.join(rf.scene_cmd('f',[],'o.mp4',24,'t','g',False))

def test_final_command_normalises_loudness():
    assert 'loudnorm=I=-16' in ' '.join(rf.final_cmd('l.txt','f.mp4'))
