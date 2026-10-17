import json,urllib.request
from pathlib import Path
root=Path(__file__).parent.resolve();bank=json.loads((root/'reference_bank.json').read_text())
for name,item in bank['references'].items():
    path=root/item['file']
    if not path.is_file():
        request=urllib.request.Request(item['download'],headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.pexels.com/'})
        with urllib.request.urlopen(request,timeout=90) as response,path.open('wb') as output:
            while chunk:=response.read(1024*1024):output.write(chunk)
    print('REFERENCE_READY',name,path.stat().st_size,flush=True)
