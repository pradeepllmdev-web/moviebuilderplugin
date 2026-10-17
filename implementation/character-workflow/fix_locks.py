from pathlib import Path
base=Path('implementation/character-workflow/server')
p=base/'character_meshy_jobs.py';t=p.read_text();t=t.replace('    temporary.replace(path)', '''    for attempt in range(10):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 9: raise
            time.sleep(.1 * (attempt + 1))''');p.write_text(t)
p=base/'character_workflow.py';t=p.read_text();t=t.replace('    temporary.replace(path)', '''    for attempt in range(10):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 9: raise
            time.sleep(.1 * (attempt + 1))''');p.write_text(t)
