"""Runtime workflow evidence is bound to current inputs, policy and artifacts."""
import hashlib
import json
from pathlib import Path
import re
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


def _podcast_artifact_binding(project):
    """Hash semantic planning state and the current bytes it references."""
    project = Path(project).resolve()
    podcast = project / 'work/podcast'
    paths = {
        'stage': podcast / 'stage.json',
        'episode_map': podcast / 'episode-map.json',
        'score_pointer': podcast / 'visual-score/current.json',
        'decisions': podcast / 'visual-score/decisions.json',
        'reviewed_stage': podcast / 'stage-reviewed.json',
    }
    result = {name: file_hash(path) if path.is_file() else None for name,path in paths.items()}

    episode = None
    if paths['episode_map'].is_file():
        try: episode = json.loads(paths['episode_map'].read_text())
        except (OSError, ValueError, TypeError): episode = None
    transcript = episode.get('transcript') if isinstance(episode, dict) else None
    if isinstance(transcript, dict) and isinstance(transcript.get('path'), str):
        candidate = (project / transcript['path']).resolve()
        result['transcript_current'] = file_hash(candidate) if candidate.is_relative_to(project) and candidate.is_file() else None

    score = None
    if paths['score_pointer'].is_file():
        try:
            pointer = json.loads(paths['score_pointer'].read_text())
            revision_id = pointer.get('revision_id') if isinstance(pointer, dict) else None
            revisions = (podcast / 'visual-score/revisions').resolve()
            if not isinstance(revision_id, str) or re.fullmatch(r'[0-9a-f]{64}', revision_id) is None:
                raise ValueError('Invalid current score revision')
            revision = (revisions / f'{revision_id}.json').resolve()
            if not revision.is_relative_to(revisions):
                raise ValueError('Current score revision escaped its directory')
            result['score_revision'] = file_hash(revision) if revision.is_file() else None
            score = json.loads(revision.read_text()) if revision.is_file() else None
        except (OSError, ValueError, TypeError):
            result['score_revision'] = None
    previews = score.get('representative_previews', []) if isinstance(score, dict) else []
    result['preview_files'] = [
        {
            'path': item.get('path'),
            'registered': item.get('sha256'),
            'current': file_hash(candidate) if candidate.is_relative_to(project) and candidate.is_file() else None,
        }
        for item in previews if isinstance(item, dict) and isinstance(item.get('path'), str)
        for candidate in [(project / item['path']).resolve()]
    ]
    events = score.get('visual_events', []) if isinstance(score, dict) else []
    result['visual_asset_files'] = [
        {
            'path': asset.get('path'),
            'registered': asset.get('sha256'),
            'current': file_hash(candidate) if candidate.is_relative_to((ROOT / 'media').resolve()) and candidate.is_file() else None,
        }
        for event in events if isinstance(event, dict)
        for treatment in [event.get('treatment')]
        if isinstance(treatment, dict)
        for asset in [treatment.get('asset')]
        if isinstance(asset, dict) and isinstance(asset.get('path'), str)
        for candidate in [((ROOT / 'media') / asset['path']).resolve()]
    ]
    return result


def binding(project, data):
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
        inputs['podcast_artifacts'] = _podcast_artifact_binding(project)
    return digest(inputs)


def workflow(project, data):
    result = definitions()
    current = binding(project, data)
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
    data['stage_reviews'][stage['id']] = dict(binding=binding(project, data), prerequisites={p:digest(data['stage_reviews'][p]) for p in stage['requires']}, evidence=quality.snapshot(resolved), reason=reason)


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
    return {'inputs':binding(project, data), 'pre_final_reviews':digest(reviews)}
