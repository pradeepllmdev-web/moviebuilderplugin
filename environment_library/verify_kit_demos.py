"""Build and capture three examples without retrying editor mutations."""
import json, time, urllib.request
from pathlib import Path
from demo_client import command, BASE
H = Path(__file__).resolve().parent
deadline = time.time() + 360
while time.time() < deadline:
    path = H / 'assets/unreal-import.json'
    report = json.loads(path.read_text()) if path.exists() else {}
    if report.get('errors'):
        raise RuntimeError(report['errors'])
    if report.get('finished_at'):
        break
    time.sleep(2)
else:
    raise TimeoutError('Import not finished; do not retry automatically')
for pack in report['packs']:
    assert len(pack['meshes']) == pack['expected'], pack['name']
    assert all(m['materials_present'] for m in pack['meshes']), pack['name']
    name = 'FreeKit_' + pack['name'].replace('-', '_')
    previous = H / 'demos' / name / 'build-result.json'
    old_finished = json.loads(previous.read_text()).get('finished_at',0) if previous.exists() else 0
    (H / 'assets/kit-request.json').write_text(json.dumps({'id':name,'pack':pack['name']}))
    command('console_command', {'command':'py '+str(H / 'build_kit_demo_unreal.py').replace('\\','/')})
    result = H / 'demos' / name / 'build-result.json'
    deadline = time.time()+180
    while (not result.exists() or json.loads(result.read_text()).get('finished_at',0)<=old_finished) and time.time()<deadline:
        time.sleep(2)
    if not result.exists() or json.loads(result.read_text()).get('finished_at',0)<=old_finished:
        raise TimeoutError('Build not finished; inspect kit-error.txt')
    time.sleep(4)
    with urllib.request.urlopen(BASE+'/snapshot?clean=1&size=1280x720',timeout=60) as response:
        data = response.read()
    assert data.startswith(b'\x89PNG')
    (result.parent / 'preview.png').write_bytes(data)
    print(name + ': saved level and preview', flush=True)
print('PASS: 217 imported meshes, materials assigned, three saved demo levels and PNG previews',flush=True)
