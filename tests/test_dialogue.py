import json,os,sys,tempfile,unittest,wave
import numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','environment_library'))
import dialogue as dg,scene_params,story_plan,set_pieces
SCRIPT='Leo (warm): "We made it."\nMara: "Not yet. The gate is still closed!"\nLeo: "Then we open it together."'
class Parse(unittest.TestCase):
 def test_screenplay(self):
  p=dg.parse(SCRIPT);self.assertEqual([l['speaker'] for l in p['lines']],['Leo','Mara','Leo']);self.assertEqual(p['lines'][0]['mood'],'warm');self.assertEqual(p['lines'][1]['mood'],'angry')
 def test_prose(self):
  p=dg.parse('Mara says, "Not yet," and Leo replies, "Then we keep going."');self.assertEqual([l['speaker'] for l in p['lines']],['Mara','Leo'])
 def test_not_a_conversation(self):self.assertEqual(len(dg.parse('Leo climbs the cliff and waves.')['lines']),0)
 def test_setting_and_cast(self):
  self.assertEqual(dg.parse('In the council hall.\n'+SCRIPT)['setting'],'hall');self.assertEqual(dg.cast(dg.parse(SCRIPT)['lines']),['Leo','Mara'])
 def test_mood_inference(self):
  self.assertEqual(dg.infer_mood('Why?'),'concern');self.assertEqual(dg.infer_mood('We won!'),'joy');self.assertEqual(dg.infer_mood('Stop that!'),'angry');self.assertEqual(dg.infer_mood('I am afraid.'),'sad')
class Timing(unittest.TestCase):
 def test_schedule_never_overlaps_and_uses_real_lengths(self):
  lines=dg.parse(SCRIPT)['lines'];s=dg.schedule(lines)
  for a,b in zip(s,s[1:]):self.assertLess(a['t1'],b['t0'])
  s2=dg.schedule(lines,line_seconds={0:5.0});self.assertAlmostEqual(s2[0]['dur'],5.0)
 def test_synth_fills_its_slot(self):
  s=dg.schedule(dg.parse(SCRIPT)['lines']);x,t=dg.synth_line(s[0]);self.assertEqual(len(x),int(s[0]['dur']*dg.SR));self.assertEqual(len(t),len(s[0]['syl']))
 def test_envelope_follows_the_speech(self):
  sr=dg.SR;x=np.zeros(sr*3);x[sr:sr*2]=np.sin(2*np.pi*150*np.arange(sr)/sr);t=dg.envelope_syllables(x,sr,['a','e','i','o'])
  self.assertEqual(len(t),4);self.assertTrue(all(1.0<=a<=2.0 for a,d,v in t));self.assertEqual([round(a,2) for a,d,v in t],sorted(round(a,2) for a,d,v in t))
 def test_recorded_voice_overrides_synth(self):
  with tempfile.TemporaryDirectory() as d:
   with wave.open(os.path.join(d,'line_0.wav'),'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);sig=(np.sin(2*np.pi*200*np.arange(32000)/16000)*20000).astype('<i2');w.writeframes(sig.tobytes())
   lines=dg.parse(SCRIPT)['lines'];self.assertAlmostEqual(dg.real_lengths(lines,d)[0],2.4,places=1);s=dg.schedule(lines,line_seconds=dg.real_lengths(lines,d));x,t,real=dg.voice_for(s[0],d)
   self.assertIsNotNone(real);self.assertAlmostEqual(real,2.0,places=1)
class Routing(unittest.TestCase):
 def test_script_paragraph_becomes_a_talk_scene(self):
  p=story_plan.plan('In the council hall.\n'+SCRIPT+'\n\nIn the ice cave Leo leaps between drifting ice floes.')
  self.assertEqual([s['piece'] for s in p['scenes']],['talk','ice']);self.assertEqual(p['scenes'][0]['params']['setting'],'hall');self.assertEqual(len(p['scenes'][0]['params']['dialogue']),3)
 def test_scene_params_passthrough_and_validation(self):
  d=scene_params.get(json.dumps(dict(dialogue=[dict(speaker='Leo',text='Hi',mood='warm'),dict(speaker=3,text='x'),dict(speaker='A',text='  ')],setting='hall')))
  self.assertEqual(len(d['dialogue']),1);self.assertEqual(d['setting'],'hall');self.assertIsNone(scene_params.get('{"setting":"moon"}')['setting'])
 def test_match_prefers_talk_for_scripts(self):self.assertEqual(set_pieces.match(SCRIPT),['talk'])
if __name__=='__main__':unittest.main()
