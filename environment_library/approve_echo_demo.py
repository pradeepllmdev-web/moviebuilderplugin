import json,sys
from pathlib import Path
H=Path('C:/Users/nagal/OneDrive/Documents/GitHub/moviebuilderplugin');D=H/'samples/echo-inspector';sys.path.insert(0,str(H.parent/'3dobjectnew/server'))
import movie_db as m
job=json.loads((D/'job-status.json').read_text());ids=[i for s in job['result']['shots'] for i in s['image_ids']]
with m.SessionLocal() as db:
 rows=db.query(m.MovieSceneShotImage).filter(m.MovieSceneShotImage.id.in_(ids)).all()
 if len(rows)!=len(ids):raise RuntimeError('Missing preview images')
 for row in rows:row.status='approved'
 db.commit()
print('Reviewed demo takes marked approved:',len(ids))
