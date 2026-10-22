"""interrupted builds and silent voices recover on their own (no Blender)"""
import os,sys,tempfile,wave
from pathlib import Path
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import numpy as np,perf_movie as pm,perf_voices as pv

def test_atomic_write_leaves_no_partial_file():
    d=Path(tempfile.mkdtemp());f=d/'meta.json';pm.write_atomic(f,'{"a": 1}');assert pm.read_json(f)=={'a':1};assert not (d/'meta.json.tmp').exists()

def test_damaged_or_missing_json_is_none_not_a_crash():
    d=Path(tempfile.mkdtemp());f=d/'x.json';assert pm.read_json(f) is None
    f.write_text('{"a": ',encoding='utf-8');assert pm.read_json(f) is None
    f.write_text('',encoding='utf-8');assert pm.read_json(f) is None

def _wav(p,x):
    with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(pv.SR);w.writeframes((np.asarray(x)*32767).astype('<i2').tobytes())

def test_silent_or_truncated_voice_is_deleted_and_not_usable():
    d=Path(tempfile.mkdtemp());good=d/'g.wav';_wav(good,.5*np.sin(np.linspace(0,400,pv.SR)))
    silent=d/'s.wav';_wav(silent,np.zeros(pv.SR));short=d/'t.wav';_wav(short,.5*np.ones(100))
    assert pv.usable(good) and good.exists()
    assert not pv.usable(silent) and not silent.exists()
    assert not pv.usable(short) and not short.exists()
    assert not pv.usable(d/'missing.wav')
