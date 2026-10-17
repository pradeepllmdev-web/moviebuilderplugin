"""Resolve explicit character capabilities without scanning model assets."""
import json
from pathlib import Path
from .characters import load_profile
from .body import load_body_profile

def resolve_character(name,required_body_actions=(),catalog_path=None):
    path=Path(catalog_path) if catalog_path else Path(__file__).with_name('catalog.json')
    data=json.loads(path.read_text())
    if data.get('schema')!='production-characters/1':raise ValueError('Unsupported character catalog')
    if name not in data['characters']:raise ValueError('Character requires a registered rig profile: '+name)
    entry=data['characters'][name]
    unsupported=set(required_body_actions)-set(entry.get('body_actions',[]))
    if unsupported:raise ValueError('Body actions not verified for '+name+': '+', '.join(sorted(unsupported)))
    return dict(entry,face=load_profile(path.parent/entry['face_profile']),body=load_body_profile(path.parent/entry['body_profile']))
