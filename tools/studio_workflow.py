"""Runtime workflow evidence is bound to current inputs, policy and artifacts."""
import hashlib
import json
from pathlib import Path
from . import production_quality as quality
from .jobs import file_hash

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / 'config/studio-workflow.json'
ROUTES = {'editorial': {'codex-astra','codex-sol','local-pair'}, 'transcription': {'local-qwen'}, 'cleanup': {'local-deepfilternet'}, 'images': {'local-klein','native-codex'}, 'rendering': {'local-ffmpeg','local-remotion'}}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def definitions():
    data = json.loads(WORKFLOW.read_text())
    seen = set()
    for stage in data['stages']:
        if stage['id'] in seen or not set(stage['requires']) <= seen:
            raise ValueError('Workflow stages must have unique IDs and earlier prerequisites')
        seen.add(stage['id'])
    if not seen: raise ValueError('Workflow cannot be empty')
    for task, providers in data['routes'].items():
        if task not in ROUTES or not set(providers) <= ROUTES[task]:
            raise ValueError('Workflow contains an unsupported provider')
    return data


def binding(data):
    files = []
    for asset in data['assets'] + data['revisions']:
        p = Path(asset['path'])
        files.append({'id':asset['id'], 'registered':asset['sha256'], 'current':file_hash(p) if p.is_file() else None})
    return digest(dict(brief=data['brief'], assets=files, resources=data['resources'], routes=data['routes'], annotations=data['annotations'], workflow=file_hash(WORKFLOW), rules=file_hash(quality.RULES)))


def workflow(project, data):
    result = definitions()
    current = binding(data)
    statuses = {}
    for stage in result['stages']:
        review = data['stage_reviews'].get(stage['id'])
        prerequisites = all(statuses[p] == 'complete' for p in stage['requires'])
        status = 'pending' if prerequisites else 'blocked'
        if review:
            prerequisite_hashes = {p:digest(data['stage_reviews'].get(p)) for p in stage['requires']}
            status = 'complete' if prerequisites and review.get('prerequisites') == prerequisite_hashes and review['binding'] == current and quality.current(review['evidence']) else 'stale'
        if stage['id'] == 'final_review' and status == 'complete' and not all(quality.gate(project, phase)['passed'] for phase in quality.PHASES):
            status = 'stale'
        stage.update(status=status, review=review)
        statuses[stage['id']] = status
    return dict(result, path=str(WORKFLOW), sha256=file_hash(WORKFLOW))


def record_stage(project, data, params):
    stages = workflow(project, data)['stages']
    stage = next((s for s in stages if s['id'] == params.get('stage')), None)
    if stage is None: raise ValueError('Unknown workflow stage')
    if any(next(s for s in stages if s['id'] == p)['status'] != 'complete' for p in stage['requires']):
        raise ValueError('Stage prerequisites require current evidence')
    reason = params.get('reason')
    if not isinstance(reason, str) or not reason.strip(): raise ValueError('Stage review needs a reason')
    paths = params.get('evidence')
    if not isinstance(paths, list) or not paths: raise ValueError('Stage review requires evidence files')
    resolved = [Path(p).expanduser().resolve() for p in paths]
    if any(not p.is_relative_to(project) for p in resolved): raise ValueError('Evidence must be project-local')
    if stage['id'] == 'final_review' and not all(quality.gate(project, phase)['passed'] for phase in quality.PHASES):
        raise ValueError('All production quality gates must pass before final review')
    data['stage_reviews'][stage['id']] = dict(binding=binding(data), prerequisites={p:digest(data['stage_reviews'][p]) for p in stage['requires']}, evidence=quality.snapshot(resolved), reason=reason)


def quality_status(project):
    policy = quality.read_rules()
    try:
        quality.require_complete(project)
        complete = True
    except (ValueError, FileNotFoundError):
        complete = False
    return dict(rules_path=policy['path'], rules=policy['rules'], gates={p:quality.gate(project,p) for p in quality.PHASES}, complete=complete)
