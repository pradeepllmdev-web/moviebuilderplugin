"""Official MPFB asset packs, isolated under .verification; no geometry output."""
import hashlib,json,urllib.request,zipfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.verification/mpfb';OUT.mkdir(parents=True,exist_ok=True)
revision='d0a32e57a7f915cb2f2b95410e2117648c7bbb7e'
if not (OUT/'source').exists():
    subprocess.run(['git','clone','--depth','1','--branch','v2.0.18','https://github.com/makehumancommunity/mpfb2.git',str(OUT/'source')],check=True)
actual=subprocess.check_output(['git','-C',str(OUT/'source'),'rev-parse','HEAD'],text=True).strip()
if actual!=revision:raise ValueError('Expected the pinned MPFB 2.0.18 revision')
sources={'faceunits01':'https://files2.makehumancommunity.org/functional/faceunits01.zip',
         'makehuman_system_assets':'https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip'}
manifest={'mpfb':{'url':'https://github.com/makehumancommunity/mpfb2','tag':'v2.0.18','commit':revision,'source_license':'GPL-3.0'}}
for name,url in sources.items():
    archive=OUT/(name+'.zip')
    if not archive.exists():
        print('Downloading',name,flush=True)
        with urllib.request.urlopen(url,timeout=180) as response,archive.with_suffix('.part').open('wb') as destination:
            while chunk:=response.read(1024*1024):destination.write(chunk)
        archive.with_suffix('.part').replace(archive)
    with zipfile.ZipFile(archive) as pack:
        target=(OUT/'assets').resolve()
        for member in pack.infolist():
            resolved=(target/member.filename).resolve()
            if not resolved.is_relative_to(target):raise ValueError('Unsafe archive path')
        pack.extractall(target)
    manifest[name]={'url':url,'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
    print('Ready',name,archive.stat().st_size,flush=True)
(Path(__file__).parent/'asset-sources.json').write_text(json.dumps(manifest,indent=2))
