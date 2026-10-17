"""Install only the reviewed performance update; preserve unrelated app files."""
from pathlib import Path
import hashlib,shutil,datetime,json
S=Path(__file__).resolve().parent
R=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew')
mapping={**{S/'server'/n:R/'server'/n for n in ['character_workflow.py','character_workflow_face.py','character_workflow_performance.py']},S/'server/character_workflow_demo.py':R/'server/blender_scripts/character_workflow_demo.py',S/'client/CharacterWorkflow.tsx':R/'client/src/components/CharacterWorkflow.tsx'}
backup=R/'server/character_workflow_backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
report=[]
for src,dst in mapping.items():
 if dst.exists():
  old=backup/dst.relative_to(R);old.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dst,old)
 dst.write_bytes(src.read_bytes());report.append({'file':str(dst.relative_to(R)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
(S/'performance-install.json').write_text(json.dumps({'backup':str(backup),'files':report},indent=2))
print('Installed 5 performance files; previous files backed up.')
