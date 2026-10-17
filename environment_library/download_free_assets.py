"""Download official CC0 starter kits; inventory filenames, never model contents."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent / 'assets'
PACKS = [
    ('furniture-kit', 'https://kenney.nl/assets/furniture-kit', 'https://kenney.nl/media/pages/assets/furniture-kit/440e0608a4-1677580847/kenney_furniture-kit.zip'),
    ('city-kit-industrial', 'https://kenney.nl/assets/city-kit-industrial', 'https://kenney.nl/media/pages/assets/city-kit-industrial/0ec35b139d-1788171848/kenney_city-kit-industrial_2.0.zip'),
    ('city-kit-suburban', 'https://kenney.nl/assets/city-kit-suburban', 'https://kenney.nl/media/pages/assets/city-kit-suburban/2c871b7af2-1745479373/kenney_city-kit-suburban_20.zip'),
]

def main():
    records = []
    for name, page, url in PACKS:
        archive = ROOT / 'downloads' / (name + '.zip')
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            temporary = archive.with_suffix('.part')
            urllib.request.urlretrieve(url, temporary)
            temporary.replace(archive)
        destination = (ROOT / 'source' / name).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (destination / member.filename).resolve()
                if not target.is_relative_to(destination) or (member.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Unsafe archive path')
            bundle.extractall(destination)
        counts = {}
        licenses = []
        for file in destination.rglob('*'):
            if file.is_file():
                counts[file.suffix.lower()] = counts.get(file.suffix.lower(), 0) + 1
                if 'license' in file.name.lower():
                    licenses.append(str(file.relative_to(ROOT)))
        record = dict(name=name, creator='Kenney', source=page, download_url=url,
                      license='CC0-1.0', license_files=licenses, bytes=archive.stat().st_size,
                      sha256=hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest(),
                      directory=str(destination), file_extensions=counts,
                      downloaded_at=datetime.now(timezone.utc).isoformat(),
                      unreal_imported=False)
        records.append(record)
        print(json.dumps(record), flush=True)
        (ROOT / 'manifest.json').write_text(json.dumps(records, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
