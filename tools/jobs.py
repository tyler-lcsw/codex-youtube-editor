"""Content-based local jobs. Failed attempts never overwrite prior successful assets."""
import hashlib
import json
import uuid
from dataclasses import asdict
from pathlib import Path
from .providers.contracts import InvalidMediaResult
from .run_state import atomic_json, file_lock

def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): digest.update(chunk)
    return digest.hexdigest()

def job_key(request: dict, provider_revision: str) -> str:
    return hashlib.sha256(json.dumps({'request':request,'revision':provider_revision}, sort_keys=True, separators=(',',':'),allow_nan=False).encode()).hexdigest()

def valid_result(result: dict) -> bool:
    try:
        return bool(result['artifacts']) and all(Path(a['path']).is_file() and Path(a['path']).stat().st_size > 0 and file_hash(Path(a['path'])) == a['sha256'] for a in result['artifacts'])
    except (KeyError, TypeError, OSError): return False

def run_job(root: Path, request: dict, revision: str, run) -> dict:
    key = job_key(request, revision); folder = Path(root) / key
    folder.mkdir(parents=True, exist_ok=True)
    with file_lock(folder / '.lock'):
        state_path = folder / 'state.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        if state.get('status') == 'succeeded' and valid_result(state.get('result',{})):
            return state['result']
        attempt = folder / ('attempt-' + uuid.uuid4().hex)
        attempt.mkdir()
        state = {'schema_version':1,'job_id':key,'request':request,'revision':revision,'status':'running','attempt':str(attempt)}
        atomic_json(state_path, state)
        try:
            result = asdict(run(attempt))
            for artifact in result['artifacts']:
                p = Path(artifact['path']).resolve()
                if not p.is_relative_to(attempt.resolve()) or not p.is_file() or p.stat().st_size == 0:
                    raise InvalidMediaResult('Provider returned absent, empty or out-of-job artifact')
                artifact.update(path=str(p),sha256=file_hash(p))
            if not valid_result(result): raise InvalidMediaResult('Result has no valid artifacts')
            state.update(status='succeeded',result=result)
            atomic_json(state_path,state)
            return result
        except BaseException as e:
            state.update(status='cancelled' if isinstance(e,KeyboardInterrupt) else 'failed',error_type=type(e).__name__)
            atomic_json(state_path,state)
            raise
