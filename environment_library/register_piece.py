"""Register a new scene type everywhere it has to appear: set_pieces.SET_PIECES (keywords, beats, limits), ASSET_PIECES, story_plan.DEFAULT_SECONDS.

    import register_piece; register_piece.register(id, title, script, keywords_regex, beats, limits, seconds, needs=...)
Then run: python set_pieces.py --write-docs"""
import sys,json
def register(id_,title,script,keywords,beats,limits,seconds,needs='scenes/ship_assets (python build_ship_assets.py)'):
 from pathlib import Path
 H=str(Path(__file__).resolve().parent)+'/'
 s=open(H+'set_pieces.py',encoding='utf-8').read()
 entry=" %r:dict(title=%r,script=%r,keywords=%r,\n  needs=[%r],\n  beats=%r,limits=%r),\n"%(id_,title,script,keywords,needs,beats,limits)
 if "'%s':dict("%id_ not in s:s=s.replace(" 'horse_herd':",entry+" 'horse_herd':",1)
 import re
 if "'%s'"%id_ not in re.search(r"ASSET_PIECES=\(([^)]*)\)",s).group(1):s=re.sub(r"ASSET_PIECES=\(([^)]*)\)",lambda m:"ASSET_PIECES=(%s,'%s')"%(m.group(1),id_),s,1)
 open(H+'set_pieces.py','w',encoding='utf-8').write(s)
 p=open(H+'story_plan.py',encoding='utf-8').read()
 if "'%s':"%id_ not in p.split('DEFAULT_SECONDS=')[1].split('\n')[0]:p=p.replace("DEFAULT_SECONDS={","DEFAULT_SECONDS={'%s':%d,"%(id_,seconds),1)
 open(H+'story_plan.py','w',encoding='utf-8').write(p)
