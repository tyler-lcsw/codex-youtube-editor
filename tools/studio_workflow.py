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
        artifacts = stage.get('artifacts', [])
        if not isinstance(artifacts, list) or any(not isinstance(p, str) or not p.strip() or Path(p).is_absolute() or '..' in Path(p).parts or '\\' in p for p in artifacts):
            raise ValueError('Required artifacts must use safe project-relative paths')
        if 'instructions' in stage and (not isinstance(stage['instructions'], str) or not stage['instructions'].strip()):
            raise ValueError('Stage instructions must be nonempty text')
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
    inputs = dict(brief=data['brief'], assets=files, resources=data['resources'], routes=data['routes'], annotations=data['annotations'], workflow=file_hash(WORKFLOW), rules=file_hash(quality.RULES))
    # A null additive migration is equivalent to the legacy general-production
    # state. Once configured, podcast source semantics are review-bound inputs.
    podcast_revision = data.get('podcast_settings_revision', 0)
    if data.get('podcast') is not None or podcast_revision:
        inputs['podcast'] = data['podcast']
        inputs['podcast_settings_revision'] = podcast_revision
    return digest(inputs)


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
        if stage['id'] == 'final_review' and status == 'complete':
            try:
                quality.require_complete(project)
            except (ValueError, OSError, KeyError):
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
    resolved.extend((project / p).resolve() for p in stage.get('artifacts', []))
    resolved = list(dict.fromkeys(resolved))
    if any(not p.is_relative_to(project) for p in resolved): raise ValueError('Evidence must be project-local')
    if stage['id'] == 'final_review':
        quality.require_complete(project)
    data['stage_reviews'][stage['id']] = dict(binding=binding(data), prerequisites={p:digest(data['stage_reviews'][p]) for p in stage['requires']}, evidence=quality.snapshot(resolved), reason=reason)


def quality_status(project):
    policy = quality.read_rules()
    try:
        quality.require_complete(project)
        complete = True
    except (ValueError, FileNotFoundError):
        complete = False
    return dict(rules_path=policy['path'], rules=policy['rules'], gates={p:quality.gate(project,p) for p in quality.PHASES}, complete=complete)


def require_action(project, stage):
    """Check the declared action stage against current Studio prerequisites.

    Stage classification is the caller's editorial responsibility, not command
    inference or an operating-system sandbox. This never records a review.
    """
    from .studio_project import read
    from .run_state import file_lock
    project = Path(project).resolve()
    with file_lock(project / 'work/studio/.lock'):
        stages = workflow(project, read(project))['stages']
        selected = next((item for item in stages if item['id'] == stage), None)
        if selected is None:
            raise ValueError('Unknown Studio action stage')
        states = {item['id']:item['status'] for item in stages}
        if any(states[prerequisite] != 'complete' for prerequisite in selected['requires']):
            raise ValueError('Studio action prerequisites require current completed reviews')


def completion_binding(project):
    """Snapshot completion inputs without consulting workflow/final QA recursively.

    Atomic project reads are intentional: callers can already hold the Studio
    state lock while computing final-stage validity.
    """
    from .studio_project import read
    data = read(Path(project).resolve())
    reviews = {stage:review for stage,review in data['stage_reviews'].items() if stage != 'final_review'}
    if any(not quality.current(review['evidence']) for review in reviews.values()):
        raise ValueError('Studio prerequisite review evidence is stale')
    return {'inputs':binding(data), 'pre_final_reviews':digest(reviews)}
