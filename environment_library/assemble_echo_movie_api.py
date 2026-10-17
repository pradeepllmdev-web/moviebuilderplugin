import urllib.request,json
from pathlib import Path
D=Path('samples/echo-inspector');m=json.loads((D/'movie.json').read_text());plan=json.loads((D/'production-plan.json').read_text());job=json.loads((D/'final-status.json').read_text())
tracks=[]
for index,shot in enumerate(plan['contract']['shots']):
 for line in shot['lines']:tracks.append({'kind':'dialogue','ref_id':line['id'],'start':index*8+line['start'],'volume':1})
body={'clips':[{'video_id':s['video_id'],'length':8} for s in job['result']['shots']],'tracks':tracks,'width':640,'height':360,'transition':'cut','state':{'title':m['title'],'demo':True}}
(D/'builder-request.json').write_text(json.dumps(body,indent=2));req=urllib.request.Request('http://127.0.0.1:8000/api/movies/'+str(m['movie_id'])+'/builder/render',json.dumps(body).encode(),{'Content-Type':'application/json'})
try:
 with urllib.request.urlopen(req,timeout=180) as r:data=json.load(r)
 (D/'builder-result.json').write_text(json.dumps(data,indent=2));print(json.dumps(data)[:1000])
except urllib.error.HTTPError as e:print(e.read().decode()[:1000]);raise
