"""Durable, agent-mediated native image handoff. This module never calls an image API."""
import argparse
import json
from datetime import datetime, timezone
import shutil
import uuid
from pathlib import Path
from PIL import Image
from .jobs import file_hash, job_key, valid_result
from .providers.policy import authorize_hybrid_image
from .run_state import atomic_json,file_lock

def prepare_request(project: Path, prompt: str, refs: list[Path], purpose: str) -> Path:
    project=Path(project).resolve()
    if not prompt.strip() or not purpose.strip():raise ValueError('Prompt and purpose required')
    reference_files=[]
    for p in refs:
        p=Path(p).resolve()
        with Image.open(p) as im:im.verify()
        reference_files.append({'path':str(p),'sha256':file_hash(p)})
    request={'schema_version':1,'provider':'codex_builtin','profile':'hybrid','purpose':purpose,'prompt':prompt,
             'reference_files':reference_files,'references':[r['sha256'] for r in reference_files],
             'project':str(project),'requested_model':'gpt-image-2','request_id':uuid.uuid4().hex,'status':'awaiting_approval'}
    path=project/'work/image-requests'/request['request_id']/'request.json'
    atomic_json(path,request);return path

def validate_references(request: dict):
    for r in request['reference_files']:
        if not Path(r['path']).is_file() or file_hash(Path(r['path']))!=r['sha256']:
            raise ValueError('Selected reference changed; prepare a new request and approval')

def claim_generation(request_path: Path, approval_path: Path) -> dict:
    if not approval_path.is_file():raise PermissionError('Scoped user approval is required')
    # Consistent lock order: request, then approval. Reserved ids survive interruption.
    with file_lock(request_path.with_suffix('.lock')):
        r=json.loads(request_path.read_text());validate_references(r)
        with file_lock(approval_path.with_suffix('.lock')):
            a=json.loads(approval_path.read_text())
            reservations=a.get('reservations',{})
            fingerprint=job_key({k:r[k] for k in ('prompt','purpose','references','provider')},'native-handoff-v1')
            if r['request_id'] in reservations:
                if reservations[r['request_id']]!=fingerprint:raise PermissionError('Reserved request changed')
                if not a.get('approved') or any(a.get(k)!=r[k] for k in ('purpose','references','provider')):raise PermissionError('Approval changed')
            else:
                if not authorize_hybrid_image(r,a):raise PermissionError('Request is outside approved scope')
                a['used_generations']+=1;reservations[r['request_id']]=fingerprint;a['reservations']=reservations
                atomic_json(approval_path,a)
            if r.get('status') == 'succeeded' or r.get('dispatch_id'):
                return r
            r.update(status='awaiting_codex_image',approval_id=a.get('id'),approval_path=str(approval_path.resolve()),reserved_fingerprint=fingerprint)
            atomic_json(request_path,r)
        return r

def validate_reservation(request):
    fingerprint=job_key({k:request[k] for k in ('prompt','purpose','references','provider')},'native-handoff-v1')
    approval=json.loads(Path(request['approval_path']).read_text())
    if (approval.get('approved') is not True
        or any(approval.get(k)!=request[k] for k in ('purpose','references','provider'))
        or approval.get('reservations',{}).get(request['request_id'])!=fingerprint):
        raise PermissionError('Generation reservation or approval scope missing or changed')


def begin_generation(request_path: Path) -> dict:
    """Reserve one dispatch before the native call. An interruption remains uncertain."""
    with file_lock(request_path.with_suffix('.lock')):
        request=json.loads(request_path.read_text());validate_references(request)
        if request.get('dispatch_id') or request.get('status')=='succeeded':
            raise PermissionError('Generation already dispatched; recover/import its artifact or prepare a new approved request')
        if request.get('status')!='awaiting_codex_image':raise PermissionError('Claim scoped approval before dispatch')
        validate_reservation(request)
        request.update(status='generation_in_flight',dispatch_id=uuid.uuid4().hex,
            dispatched_at=datetime.now(timezone.utc).isoformat(),
            dispatch_note='Marker recorded before native call; does not prove the call completed. Never blindly repeat it.')
        atomic_json(request_path,request);return request


def import_codex_image(request_path: Path, output_path: Path, reported_model: str | None) -> dict:
    with file_lock(request_path.with_suffix('.lock')):
        r=json.loads(request_path.read_text());validate_references(r)
        if r.get('status') not in {'generation_in_flight','succeeded'}:raise PermissionError('Begin approved generation before importing')
        validate_reservation(r)
        if r.get('status')=='succeeded' and valid_result(r.get('result',{})):return r['result']
        with Image.open(output_path) as im:
            im.verify()
        with Image.open(output_path) as im:
            width,height=im.size;fmt=im.format
        if fmt not in {'PNG','JPEG','WEBP'}:raise ValueError('Unsupported generated image format')
        folder=Path(r['project'])/'media/generated'/r['request_id']/('import-'+uuid.uuid4().hex);folder.mkdir(parents=True,exist_ok=True)
        asset=folder/('native.'+{'PNG':'png','JPEG':'jpg','WEBP':'webp'}[fmt])
        shutil.copyfile(output_path,asset)
        with Image.open(asset) as im:
            jpg=folder/'preview.jpg';im.convert('RGB').save(jpg,quality=90,optimize=True)
        result={'artifacts':[{'path':str(asset),'sha256':file_hash(asset),'width':width,'height':height,'format':fmt},
                             {'path':str(jpg),'sha256':file_hash(jpg),'role':'preview'}],
                'metrics':{},'provenance':{'provider':'codex_builtin','reported_model':reported_model or 'unknown',
                  'requested_model':r['requested_model'],'dispatch_id':r.get('dispatch_id'),'approval_id':r['approval_id'],'references':r['references'],'prompt':r['prompt']}}
        atomic_json(folder/'provenance.json',result)
        r.update(status='succeeded',result=result);atomic_json(request_path,r)
        return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    new=sub.add_parser('prepare');new.add_argument('project',type=Path);new.add_argument('--prompt-file',type=Path,required=True);new.add_argument('--ref',type=Path,action='append',default=[]);new.add_argument('--purpose',default='thumbnail')
    claim=sub.add_parser('claim');claim.add_argument('request',type=Path);claim.add_argument('--approval',type=Path,required=True)
    begin=sub.add_parser('begin');begin.add_argument('request',type=Path)
    imp=sub.add_parser('import');imp.add_argument('request',type=Path);imp.add_argument('output',type=Path);imp.add_argument('--reported-model')
    a=p.parse_args()
    if a.cmd=='prepare':print(prepare_request(a.project,a.prompt_file.read_text(),a.ref,a.purpose))
    elif a.cmd=='claim':print(json.dumps(claim_generation(a.request,a.approval),indent=2))
    elif a.cmd=='begin':print(json.dumps(begin_generation(a.request),indent=2))
    else:print(json.dumps(import_codex_image(a.request,a.output,a.reported_model),indent=2))
