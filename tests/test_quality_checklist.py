"""every guard named in QUALITY_CHECKLIST.md still exists in the code"""
import os,re
ENV=os.path.join(os.path.dirname(__file__),'..','environment_library')
def _source():
    return '\n'.join(open(os.path.join(ENV,f),encoding='utf-8',errors='ignore').read() for f in sorted(os.listdir(ENV)) if f.endswith('.py'))
def test_every_guard_in_the_checklist_is_in_the_code():
    rows=[l for l in open(os.path.join(ENV,'QUALITY_CHECKLIST.md'),encoding='utf-8').read().splitlines() if l.startswith('| ') and not l.startswith('| Complaint') and not l.startswith('|---')]
    assert len(rows)>=15;src=_source();missing=[]
    for l in rows:
        cells=[c.strip() for c in l.strip('|').split('|')]
        g=re.findall(r'`([^`]+)`',cells[1]) if not cells[1].startswith('Manual') else []
        for guard in g:
            if guard.endswith('.html') or guard.endswith('.py'):continue
            if guard not in src:missing.append((cells[0][:50],guard))
    assert missing==[],missing
