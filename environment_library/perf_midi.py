"""Minimal MIDI writer and FluidSynth renderer (pure Python; FluidSynth and a SoundFont are downloaded into music_tools/ by `python perf_midi.py download`).

    notes=[dict(t=0.0, dur=1.0, pitch=60, vel=80, ch=0)]   seconds, MIDI pitch, velocity 1-127, channel 0-15 (channel 9 is drums)
    perf_midi.write(path, notes, programs={0:48, 1:73}, bpm=90)       programs: channel -> General MIDI program (0-based)
    x = perf_midi.render(notes, programs, seconds, sr=22050)         numpy samples through FluidSynth + the SoundFont (None when the tools are missing)

Times are in seconds; the file uses 480 ticks per quarter note at the given bpm so seconds map to ticks exactly."""
import os,struct,subprocess,sys,tempfile,wave,zipfile
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;TOOLS=H/'music_tools'
SOUNDFONT=TOOLS/'GeneralUser-GS.sf2'
def fluidsynth_exe():
 for p in TOOLS.glob('fluidsynth_dl/*/bin/fluidsynth.exe'):return p
 return None
def available():return fluidsynth_exe() is not None and SOUNDFONT.exists()
def _vlq(n):
 out=[n&0x7f];n>>=7
 while n:out.append((n&0x7f)|0x80);n>>=7
 return bytes(reversed(out))
def write(path,notes,programs=None,bpm=90.,tpq=480):
 """a type-0 MIDI file of the notes"""
 programs=programs or {};spt=60./bpm/tpq;ev=[]
 for ch,pr in programs.items():ev.append((0,0,bytes([0xC0|ch,pr&127])))
 for n in notes:
  a=int(round(n['t']/spt));b=int(round((n['t']+max(.03,n['dur']))/spt));ch=n.get('ch',0)&15;p=int(n['pitch'])&127;v=max(1,min(127,int(n.get('vel',80))))
  ev.append((a,2,bytes([0x90|ch,p,v])));ev.append((b,1,bytes([0x80|ch,p,0])))
 ev.sort(key=lambda e:(e[0],e[1]));data=_vlq(0)+bytes([0xFF,0x51,3])+int(60000000/bpm).to_bytes(3,'big');last=0
 for t,_,m in ev:data+=_vlq(t-last)+m;last=t
 data+=_vlq(0)+bytes([0xFF,0x2F,0])
 open(path,'wb').write(b'MThd'+struct.pack('>IHHH',6,0,1,tpq)+b'MTrk'+struct.pack('>I',len(data))+data)
def render(notes,programs,seconds,sr=22050,bpm=90.,gain=.7):
 """FluidSynth render of the notes to a mono numpy array of `seconds`, or None without the tools"""
 if not available():return None
 d=tempfile.mkdtemp(prefix='mid_');mid=os.path.join(d,'a.mid');wav=os.path.join(d,'a.wav');write(mid,notes,programs,bpm)
 r=subprocess.run([str(fluidsynth_exe()),'-ni','-g',str(gain),'-r',str(sr),'-F',wav,str(SOUNDFONT),mid],capture_output=True,text=True,errors='ignore')
 if not os.path.exists(wav):return None
 with wave.open(wav,'rb') as w:
  ch,nf=w.getnchannels(),w.getnframes();x=np.frombuffer(w.readframes(nf),dtype='<i2').astype(float)/32768.
 if ch>1:x=x.reshape(-1,ch).mean(axis=1)
 n=int(seconds*sr);return np.pad(x,(0,max(0,n-len(x))))[:n]
def download():
 import urllib.request
 TOOLS.mkdir(exist_ok=True)
 if not SOUNDFONT.exists():urllib.request.urlretrieve('https://github.com/mrbumpy409/GeneralUser-GS/raw/main/GeneralUser-GS.sf2',str(SOUNDFONT))
 if fluidsynth_exe() is None:
  z=TOOLS/'fs.zip';urllib.request.urlretrieve('https://github.com/FluidSynth/fluidsynth/releases/download/v2.6.1/fluidsynth-v2.6.1-win10-x64-cpp11.zip',str(z))
  with zipfile.ZipFile(z) as f:f.extractall(TOOLS/'fluidsynth_dl')
if __name__=='__main__':
 if sys.argv[1:2]==['download']:download();print('ok',available())
 else:print(__doc__)
