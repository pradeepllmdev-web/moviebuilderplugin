"""Resumable image-to-body generation. Credentials never enter task manifests."""
import argparse, base64, hashlib, json, os, time, urllib.request, urllib.error
from pathlib import Path

API = 'https://api.meshy.ai/openapi/v1'

def credential(env_file=None):
    key = os.environ.get('MESHY_API_KEY', '').strip()
    if not key and env_file:
        for line in Path(env_file).read_text(encoding='utf-8-sig').splitlines():
            if line.startswith('MESHY_API_KEY='):
                key = line.split('=', 1)[1].strip().strip('\"\'')
    if not key: raise ValueError('Set MESHY_API_KEY or provide --env-file')
    return key

def call(key, method, path, body=None):
    request = urllib.request.Request(API+'/'+path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization':'Bearer '+key, 'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=90) as response: return json.load(response)
    except urllib.error.HTTPError as error:
        # Do not automatically retry POST: a lost response may already have created a paid task.
        raise RuntimeError('Meshy HTTP '+str(error.code)+' for '+method+' '+path) from None

def save(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2), encoding='utf-8')
    for attempt in range(10):
        try:
            temporary.replace(path)
            break
        except PermissionError:
            if attempt == 9: raise
            time.sleep(.1 * (attempt + 1))

def run(image, output, key):
    output.mkdir(parents=True, exist_ok=True)
    manifest = output/'generation.json'
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    state = json.loads(manifest.read_text()) if manifest.exists() else {
        'schema':'character-generation/1', 'image_sha256':digest,
        'anatomy':'biped', 'facial_status':'not-evaluated', 'tasks':{}}
    if state['image_sha256'] != digest: raise ValueError('Use a new output folder for a different image')
    for stage in ('image-to-3d', 'rigging'):
        task = state['tasks'].get(stage)
        if not task:
            if stage == 'image-to-3d':
                mime = 'image/jpeg' if image.suffix.lower() in ('.jpg','.jpeg') else 'image/png'
                body = {'image_url':'data:'+mime+';base64,'+base64.b64encode(image.read_bytes()).decode(),
                    'ai_model':'meshy-7.1', 'should_texture':True, 'enable_pbr':True,
                    'should_remesh':True, 'topology':'triangle', 'target_polycount':30000, 'pose_mode':'a-pose'}
            else: body = {'input_task_id':state['tasks']['image-to-3d']['id'], 'height_meters':1.72}
            # Persist intent before POST. An interrupted create requires reconciliation, never blind resubmission.
            state['tasks'][stage] = {'status':'SUBMITTING'}; save(manifest,state)
            response = call(key,'POST',stage,body)
            task = state['tasks'][stage] = {'id':response['result'], 'status':'PENDING'}
            save(manifest,state)
        if 'id' not in task: raise RuntimeError('Uncertain submission: reconcile Meshy task list before retrying '+stage)
        deadline=time.monotonic()+2400; last=None
        while time.monotonic()<deadline:
            response=call(key,'GET',stage+'/'+task['id'])
            task.update(status=response['status'],progress=response.get('progress',0))
            save(manifest,state)
            notice=(task['status'],task['progress'])
            if notice!=last: print(stage, *notice, flush=True); last=notice
            if task['status']=='SUCCEEDED': break
            if task['status'] in ('FAILED','CANCELED'): raise RuntimeError(stage+' '+task['status'])
            time.sleep(8)
        else: raise TimeoutError('Resume the saved task later')
        result=response.get('result',response)
        downloads = {'model.glb':result['model_urls']['glb']} if stage=='image-to-3d' else {
            'rigged.glb':result['rigged_character_glb_url']}
        if stage=='image-to-3d' and result.get('thumbnail_url'): downloads['model-preview.png']=result['thumbnail_url']
        for name,url in downloads.items():
            destination=output/name
            if not destination.exists():
                with urllib.request.urlopen(url,timeout=300) as source: data=source.read()
                temporary=destination.with_suffix(destination.suffix+'.part'); temporary.write_bytes(data); temporary.replace(destination)
            task.setdefault('files',{})[name]={'bytes':destination.stat().st_size}
        task['consumed_credits']=response.get('consumed_credits')
        save(manifest,state)
    print('Generation and body rig ready; facial capability still requires Blender evaluation.', flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--image',type=Path,required=True); parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--env-file',type=Path)
    args=parser.parse_args(); run(args.image,args.output,credential(args.env_file))
