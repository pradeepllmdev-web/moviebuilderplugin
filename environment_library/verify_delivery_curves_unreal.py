import unreal,json,traceback,bisect
from pathlib import Path
D=Path(__file__).resolve().parent/'delivery_scene';result={'ok':False}
try:
 info=json.loads((D/'sequence.json').read_text());plan=json.loads((D/'plan.json').read_text());folder=info['sequence'].rsplit('/',1)[0]
 maximum=0;checked=0
 for name in ['cat','lion']:
  anim=unreal.load_asset(folder+'/'+name+'_Performance')
  curve='JawClose' if name=='cat' else 'JawOpen'
  times,values=unreal.AnimationLibrary.get_float_keys(anim,curve)
  if len(values)!=info['frames']:
   result.setdefault('key_counts',{})[name]={'keys':len(values),'first_time':times[0] if times else None,'last_time':times[-1] if times else None}
  assert times and len(times)==len(values)
  for i in range(info['frames']):
   time=i/24;j=bisect.bisect_right(times,time)
   if j==0:value=values[0]
   elif j>=len(times):value=values[-1]
   else:
    fraction=(time-times[j-1])/max(.000001,times[j]-times[j-1]);value=values[j-1]+fraction*(values[j]-values[j-1])
   t=i/24;line=next((l for l in plan['lines'] if l['actor']==name and l['start']<=t<l['start']+l['duration']),None)
   expected=0
   if line:
    tr=line['track'];index=min(tr['frames']-1,max(0,round((t-line['start']+tr['lead'])*24)));expected=tr['weights']['jawOpen'][index]
   if curve=='JawClose':expected=1-expected
   maximum=max(maximum,abs(value-expected),abs(time-t))
  assert max(values)-min(values)>.1;checked+=1
 assert maximum<.0001
 result.update(ok=True,characters_checked=checked,samples_per_character=info['frames'],max_error=maximum)
except Exception:result['error']=traceback.format_exc()
(D/'curve-check.json').write_text(json.dumps(result,indent=2))
