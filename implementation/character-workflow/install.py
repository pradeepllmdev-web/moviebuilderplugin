from pathlib import Path
ROOT=Path('C:/Users/nagal/OneDrive/Documents/GitHub/3dobjectnew')
SRC=Path(__file__).resolve().parent
for name in ('character_workflow.py','character_meshy_jobs.py','character_workflow_face.py','character_workflow_landmarks.py','character_workflow_performance.py'):
 (ROOT/'server'/name).write_bytes((SRC/'server'/name).read_bytes())
(ROOT/'server/blender_scripts/character_workflow_demo.py').write_bytes((SRC/'server/character_workflow_demo.py').read_bytes())
(ROOT/'client/src/components/CharacterWorkflow.tsx').write_bytes((SRC/'client/CharacterWorkflow.tsx').read_bytes())
p=ROOT/'server/main.py';t=p.read_text(encoding='utf-8')
if 'character_workflow.router' not in t:t=t.replace('app.include_router(character3d_api.router)', 'app.include_router(character3d_api.router)\nimport character_workflow\napp.include_router(character_workflow.router)')
p.write_text(t,encoding='utf-8')
p=ROOT/'client/src/components/Character3DPanel.tsx';t=p.read_text(encoding='utf-8')
if "from './CharacterWorkflow'" not in t:
 t="import { CharacterWorkflow } from './CharacterWorkflow'\n"+t
 t=t.replace('<h2>🧊 3D Character</h2>','<h2>🧊 3D Character</h2>\n    <CharacterWorkflow apiBase={apiBase} />')
p.write_text(t,encoding='utf-8')
p=ROOT/'client/src/components/SeriesPanel.tsx';t=p.read_text(encoding='utf-8')
if "from './CharacterWorkflow'" not in t:
 t="import { CharacterWorkflow } from './CharacterWorkflow'\n"+t
 needle="<span>{c.character_type}{c.voice_name ? ` · ${c.voice_name}` : ''}</span>"
 assert needle in t
 t=t.replace(needle,needle+'\n                {c.picture_file_ids[0] && <CharacterWorkflow apiBase={apiBase} fileId={c.picture_file_ids[0]} name={c.name} compact />}')
p.write_text(t,encoding='utf-8')
print('Installed workflow API, Blender demo renderer, upload panel, and series image buttons.')


