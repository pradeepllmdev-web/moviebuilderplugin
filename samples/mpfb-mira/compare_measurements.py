"""Descriptive single-view likeness diagnostics; not an identity score."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
source=json.loads((HERE/'appearance.json').read_text())['ratios']
preview=json.loads((ROOT/'.verification/mpfb/mira-preview-measurements.json').read_text())['ratios']
report={'method':'MediaPipe ratios on reference and neutral rendered preview; projection/landmark uncertainty applies',
    'ratios':{name:{'reference':value,'render':preview[name],'relative_difference_percent':round(100*(preview[name]-value)/value,2)} for name,value in source.items()},
    'conclusion':'Approximate proportions; rendered eyes remain smaller than the stylized reference. Hair and garments are substitutes.',
    'identity_match_certified':False}
(HERE/'likeness.json').write_text(json.dumps(report,indent=2))
print(report['conclusion'])
