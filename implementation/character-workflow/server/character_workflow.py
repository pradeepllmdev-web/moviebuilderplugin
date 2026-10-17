"""Opt-in image -> facial character -> diagnostic demos. Originals are immutable."""
import asyncio
import hashlib
import json
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from movie_db import FileMetadata, get_session

router = APIRouter(prefix='/api/character-workflows', tags=['character-workflows'])
ROOT = Path(__file__).parent / 'character_workflows'
FILES = Path(__file__).parent / 'movie_files'
ACTIVE = {}
WORKER = asyncio.Semaphore(1)
STAGES = ['preflight', 'model_and_body_rig', 'face_landmarks', 'facial_controls', 'animation_library', 'validation', 'demo_videos']


def folder(job_id):
    if len(job_id) != 32 or any(c not in '0123456789abcdef' for c in job_id):
        raise HTTPException(404, 'Unknown character job')
    return ROOT / job_id


def read(job_id):
    path = folder(job_id) / 'job.json'
    if not path.is_file():
        raise HTTPException(404, 'Unknown character job')
    job = json.loads(path.read_text())
    if job['status'] in ('queued', 'running') and job_id not in ACTIVE:
        job['status'] = 'interrupted'
        job['error'] = 'The server stopped. Resume this job; saved Meshy task IDs are reused.'
    return job


def save(job):
    job['updated_at'] = time.time()
    path = folder(job['id']) / 'job.json'
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(job, indent=2), encoding='utf-8')
    for attempt in range(10):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 9: raise
            time.sleep(.1 * (attempt + 1))


def validate_landmarks(face):
    boxes = face.get('boxes', {})
    for part in ('image_left_eye', 'image_right_eye', 'mouth_opening', 'nose', 'chin', 'head'):
        box = boxes.get(part)
        if not isinstance(box, dict) or not all(isinstance(box.get(k), (int, float)) for k in ('x0', 'y0', 'x1', 'y1')):
            raise ValueError('Missing or invalid facial landmark: ' + part)
        if not (0 <= box['x0'] < box['x1'] <= 1000 and 0 <= box['y0'] < box['y1'] <= 1000):
            raise ValueError('Facial landmark outside image: ' + part)
    eyes = [boxes[p] for p in ('image_left_eye', 'image_right_eye')]
    if boxes['mouth_opening']['y0'] <= min(b['y0'] for b in eyes):
        raise ValueError('Mouth landmark overlaps the upper face; needs review')


def inspect_model(path):
    import pygltflib
    g = pygltflib.GLTF2().load(str(path))
    names = set()
    for m in g.meshes or []:
        names.update((m.extras or {}).get('targetNames', []))
    required = {'jawOpen', 'eyeBlinkLeft', 'eyeBlinkRight'}
    if not g.skins or not required.issubset(names):
        raise ValueError('The model is missing a skin or required jaw/blink controls')
    return {'skinned': True, 'facial_controls': sorted(names), 'structural_checks_passed': True,
            'visual_checks_passed': False, 'production_approved': False,
            'review_items': ['lip closure and mouth position', 'eyelid coverage and color', 'teeth/tongue intersections', 'foot contact and turn quality']}


def encode(frames, audio, out, fps, duration, lead):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, '-y', '-v', 'error', '-framerate', str(fps), '-i', str(frames / '%05d.png'),
                    '-i', str(audio), '-filter_complex', f'[1:a]adelay={round(lead*1000)}:all=1,apad[a]',
                    '-map', '0:v', '-map', '[a]', '-t', str(duration), '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-movflags', '+faststart', str(out)], check=True, timeout=600)
    subprocess.run([ff, '-v', 'error', '-i', str(out), '-f', 'null', '-'], check=True, timeout=600)


def demo(job, path):
    import blender_runner
    import speech_visemes
    import talk_animation
    outputs = []
    lines = {'standing': job['text'], 'walking': 'Now I am walking and talking. Watch my steps and my face.',
             'running': 'Now I am running and talking. Watch my arms, my stride, and my balance.',
             'circle': 'Around the track I go. Watch my turns as I run and talk.',
             'scene': job['text']}
    for mode, text in lines.items():
        work = path / 'demo' / mode
        work.mkdir(parents=True, exist_ok=True)
        output = work / 'demo.mp4'
        if output.is_file():
            outputs.append({'mode': mode, 'url': f"/api/character-workflows/{job['id']}/files/demo/{mode}/demo.mp4"})
            continue
        spoken = speech_visemes.read_timeline(work) if (work/'voice.wav').is_file() and (work/'visemes.csv').is_file() else speech_visemes.sapi_speak(text, work, 'Microsoft David Desktop', -1)
        track = talk_animation.build_track(spoken['visemes'], spoken['duration'], emotion='warm', intensity=1.05)
        track_file = work / 'track.json'
        track_file.write_text(json.dumps(track))
        result = blender_runner.run('character_workflow_demo.py', {'glb': str(path / 'character.glb'),
            'track': str(track_file), 'frames_dir': str(work / 'frames'), 'mode': mode,
            'size': 512, 'front': job.get('front', 1), 'gesture_strength': job.get('gesture_strength', .18)}, timeout=3600)
        audio=spoken['wav']
        if mode=='scene':
            from character_workflow_performance import scene_soundtrack
            audio=scene_soundtrack(audio,work/'soundtrack.wav')
        encode(work / 'frames', audio, output, track['fps'], track['frames']/track['fps'], track['lead'])
        outputs.append({'mode': mode, 'url': f"/api/character-workflows/{job['id']}/files/demo/{mode}/demo.mp4", 'scene_url': f"/api/character-workflows/{job['id']}/files/demo/{mode}/demo.blend", 'performance_url': f"/api/character-workflows/{job['id']}/files/demo/{mode}/performance.glb" if mode in ('standing','scene') else None, 'diagnostics': result})
        job['demos'] = outputs
        save(job)
    return outputs


async def execute(job_id):
    async with WORKER:
        job = read(job_id)
        path = folder(job_id)
        try:
            for stage in STAGES:
                if stage in job['completed']:
                    continue
                job.update(status='running', stage=stage, error=None)
                save(job)
                if stage == 'preflight':
                    import blender_runner, local_provider, character_meshy_jobs
                    blender_runner.blender_path()
                    character_meshy_jobs.credential(Path(__file__).parent / '.env')
                    async with local_provider._client() as client:
                        response = await client.get('/v1/health')
                        response.raise_for_status()
                        if not response.json().get('ollama', {}).get('up'):
                            raise RuntimeError('Start Ollama and the facial vision model before generating a paid model')
                elif stage == 'model_and_body_rig':
                    import character_meshy_jobs
                    await asyncio.to_thread(character_meshy_jobs.run, path / job['reference'], path / 'meshy',
                        character_meshy_jobs.credential(Path(__file__).parent / '.env'))
                elif stage == 'face_landmarks':
                    import meshy_character, character3d_api, face_on_glb
                    data, _ = meshy_character.rename_bones((path / 'meshy/rigged.glb').read_bytes())
                    (path / 'body-rig.glb').write_bytes(data)
                    import character_workflow_landmarks
                    face = await character_workflow_landmarks.detect(path / 'body-rig.glb', path)
                    validate_landmarks(face)
                    face.update(separate_eyes=False, separate_mouth=True)
                    face['source_mouth'] = job.get('source_mouth', 'auto')
                    (path / 'face.json').write_text(json.dumps(face, indent=2))
                    job['front'] = face['front']
                elif stage == 'facial_controls':
                    import character_workflow_face
                    face = json.loads((path / 'face.json').read_text())
                    job['face_report'] = await asyncio.to_thread(character_workflow_face.fit,
                        path / 'body-rig.glb', path / 'character.glb', face)
                elif stage == 'animation_library':
                    import character3d_api
                    result = await asyncio.to_thread(character3d_api._finish_model, 'workflow-' + job_id,
                        (path / 'character.glb').read_bytes(), {'joints_outside_mesh': [], 'snapped': 0, 'engine': 'meshy'})
                    shutil.copy2(character3d_api.SAVED_MODELS_DIR / result['animated'], path / 'character.glb')
                    job['model'] = {'url': f'/api/saved_models/{result["animated"]}', 'clips': result['clips']}
                elif stage == 'validation':
                    job['validation'] = await asyncio.to_thread(inspect_model, path / 'character.glb')
                    assert hashlib.sha256((path / job['reference']).read_bytes()).hexdigest() == job['reference_sha256']
                elif stage == 'demo_videos':
                    job['demos'] = await asyncio.to_thread(demo, job, path)
                job['completed'].append(stage)
                save(job)
            job.update(status='needs_review', stage=None)
        except Exception as exc:
            job.update(status='needs_attention', error=f'{job.get("stage")}: {str(exc)[:400]}')
        finally:
            save(job)
            ACTIVE.pop(job_id, None)


class Start(BaseModel):
    reference_file_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    text: str = Field(default='Hello! I am ready for my character animation test.', min_length=1, max_length=500)
    anatomy: str = Field(default='biped', pattern='^biped$')
    source_mouth: str = Field(default='auto', pattern='^(auto|open|closed)$')
    gesture_strength: float = Field(default=.18, ge=0, le=.35)


@router.post('', status_code=202)
async def start(body: Start, db: Session = Depends(get_session)):
    row = db.get(FileMetadata, body.reference_file_id)
    if not row or not (row.mime_type or '').startswith('image/'):
        raise HTTPException(400, 'Choose a stored character image')
    source = (FILES / row.filename).resolve()
    if FILES.resolve() not in source.parents or not source.is_file():
        raise HTTPException(404, 'Character image is missing')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    for job_id in list(ACTIVE):
        existing = read(job_id)
        if existing['reference_sha256'] == digest:
            return existing
    job_id = uuid.uuid4().hex
    path = folder(job_id)
    path.mkdir(parents=True)
    reference = 'reference' + ('.jpg' if row.mime_type == 'image/jpeg' else '.png')
    shutil.copy2(source, path / reference)
    job = {'id': job_id, 'name': body.name, 'text': body.text, 'anatomy': body.anatomy,
           'reference_file_id': body.reference_file_id, 'reference': reference, 'reference_sha256': digest,
           'source_mouth': body.source_mouth, 'gesture_strength': body.gesture_strength,
           'performance_version': 'character-performance/2',
           'status': 'queued', 'stage': None, 'completed': [], 'stages': STAGES, 'demos': [], 'created_at': time.time()}
    save(job)
    ACTIVE[job_id] = asyncio.create_task(execute(job_id))
    return job


@router.get('')
def jobs():
    return [read(p.parent.name) for p in sorted(ROOT.glob('*/job.json'), key=lambda p:p.stat().st_mtime, reverse=True)][:100]


@router.get('/{job_id}')
def status(job_id: str):
    return read(job_id)


@router.post('/{job_id}/resume', status_code=202)
async def resume(job_id: str):
    job = read(job_id)
    if job_id in ACTIVE or job['status'] == 'needs_review':
        raise HTTPException(409, 'This job is already running or has a demo ready')
    job.update(status='queued', error=None)
    save(job)
    ACTIVE[job_id] = asyncio.create_task(execute(job_id))
    return job


@router.get('/{job_id}/files/{name:path}')
def artifact(job_id: str, name: str):
    base = folder(job_id).resolve()
    path = (base / name).resolve()
    if base not in path.parents or not path.is_file() or path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.mp4', '.glb', '.blend'):
        raise HTTPException(404, 'No such character artifact')
    return FileResponse(path)




