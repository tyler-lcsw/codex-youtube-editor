"""Runtime workflow evidence is bound to current inputs, policy and artifacts."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from . import production_quality as quality
from . import editing_styles
from . import studio_workflows
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


def binding(project, data, workflow_instance=None):
    if workflow_instance is not None:
        scoped = studio_workflows.effective_inputs(data, workflow_instance)
        asset_ids = set(scoped['asset_ids'])
        revision_ids = set(scoped['revision_ids'])
        selected_assets = [item for item in data['assets'] if item['id'] in asset_ids]
        selected_revisions = [item for item in data['revisions'] if item['id'] in revision_ids]
        selected_annotations = studio_workflows._relevant_annotations(data, studio_workflows._inputs(data, scoped))
    else:
        selected_assets = data['assets']
        selected_revisions = data['revisions']
        selected_annotations = data['annotations']
    files = []
    for asset in selected_assets + selected_revisions:
        p = Path(asset['path'])
        files.append({'id':asset['id'], 'registered':asset['sha256'], 'current':file_hash(p) if p.is_file() else None})
    inputs = dict(brief=data['brief'], assets=files, resources=data['resources'], routes=data['routes'], annotations=selected_annotations, workflow=file_hash(WORKFLOW), rules=file_hash(quality.RULES))
    if workflow_instance is not None:
        inputs['workflow_template_id'] = workflow_instance['template_id']
        inputs['workflow_template_catalog'] = file_hash(studio_workflows.TEMPLATES)
    style_binding = editing_styles.active_binding(project)
    if style_binding is not None:
        inputs['editing_style'] = style_binding
    # A null additive migration is equivalent to the legacy general-production
    # state. Once configured, podcast source semantics are review-bound inputs.
    podcast_revision = data.get('podcast_settings_revision', 0)
    podcast_workflow = workflow_instance is None or workflow_instance.get('template_id') == 'solo_podcast' or workflow_instance.get('input_mode') == 'all_project'
    if podcast_workflow and (data.get('podcast') is not None or podcast_revision):
        inputs['podcast'] = data['podcast']
        inputs['podcast_settings_revision'] = podcast_revision
        inputs['podcast_artifacts'] = _podcast_artifact_binding(project)
    return digest(inputs)


def workflow(project, data, workflow_id=None):
    result = definitions()
    guide = studio_workflows.status(project, data)
    selected = studio_workflows.by_id(data, workflow_id)
    reviews = selected['stage_reviews']
    current = binding(project, data, selected)
    statuses = {}
    template = next(item for item in guide['templates'] if item['id'] == selected['template_id'])
    presentation = {item['stage_id']:item for item in template['guide_stages']}
    for stage in result['stages']:
        if selected['id'] != studio_workflows.LEGACY_ID:
            stage['artifacts'] = [
                path if path == 'work/quality/completion.json'
                else str(Path('work/workflows') / selected['id'] / Path(path).relative_to('work'))
                for path in stage.get('artifacts', [])
            ]
        review_present = stage['id'] in reviews
        review = reviews.get(stage['id'])
        prerequisites = all(statuses[p] == 'complete' for p in stage['requires'])
        status = 'pending' if prerequisites else 'blocked'
        stale_reasons = []
        if review_present:
            prerequisite_hashes = {p:digest(reviews.get(p)) for p in stage['requires']}
            if not isinstance(review, dict):
                stale_reasons.append({'code':'invalid_review', 'message':'The saved stage review is not readable.'})
            else:
                if not prerequisites:
                    stale_reasons.append({'code':'prerequisite_incomplete', 'message':'A prerequisite stage is not currently complete.'})
                if review.get('prerequisites') != prerequisite_hashes:
                    stale_reasons.append({'code':'prerequisite_evidence_changed', 'message':'Prerequisite evidence changed after this review.'})
                if review.get('binding') != current:
                    stale_reasons.append({'code':'workflow_binding_changed', 'message':'Workflow inputs, policy, style, or template guidance changed.'})
                try:
                    evidence_current = quality.current(review.get('evidence'))
                except (KeyError, TypeError, ValueError, OSError):
                    evidence_current = False
                if not evidence_current:
                    stale_reasons.append({'code':'evidence_changed', 'message':'Stage evidence is missing, changed, or invalid.'})
            status = 'stale' if stale_reasons else 'complete'
        if stage['id'] == 'final_review' and status == 'complete':
            if selected['id'] != data['active_workflow_id']:
                status = 'stale'
                stale_reasons.append({'code':'workflow_not_active', 'message':'Select this workflow before validating its final production-quality receipt.'})
            else:
                try:
                    quality.require_complete(project)
                except (ValueError, OSError, KeyError):
                    status = 'stale'
                    stale_reasons.append({'code':'production_quality_incomplete', 'message':'The current production-quality completion receipt is unavailable.'})
        stage.update(status=status, review=review, stale_reason=stale_reasons[0] if stale_reasons else None, stale_reasons=stale_reasons)
        if stage['id'] in presentation:
            stage.update({key:value for key,value in presentation[stage['id']].items() if key != 'stage_id'})
        statuses[stage['id']] = status
    selected_status = next(item for item in guide['workflow_instances'] if item['id'] == selected['id'])
    return dict(result, path=str(WORKFLOW), sha256=file_hash(WORKFLOW), templates=guide['templates'], instances=guide['instances'], workflow_instances=guide['workflow_instances'], active_workflow_id=selected['id'], active_workflow=selected_status, project_active_workflow_id=guide['active_workflow_id'], workflow_id=selected['id'])


def record_stage(project, data, params):
    selected = studio_workflows.by_id(data, params.get('workflow_id'))
    stages = workflow(project, data, selected['id'])['stages']
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
        if selected['id'] != data['active_workflow_id']:
            raise ValueError('Select this workflow as the active workflow before recording final review')
        quality.require_complete(project)
    reviews = selected['stage_reviews']
    selected['input_binding'] = studio_workflows.input_binding(
        project, data, studio_workflows.effective_inputs(data, selected), selected['template_id']
    )
    reviews[stage['id']] = dict(binding=binding(project, data, selected), prerequisites={p:digest(reviews[p]) for p in stage['requires']}, evidence=quality.snapshot(resolved), reason=reason)
    # Preserve the legacy project field for existing callers while instance-local
    # reviews are the authority used by workflow().
    if selected['id'] == data['active_workflow_id']:
        data['stage_reviews'] = deepcopy(reviews)


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
    selected = studio_workflows.active(data)
    reviews = {stage:review for stage,review in selected['stage_reviews'].items() if stage != 'final_review'}
    try:
        current = all(isinstance(review, dict) and quality.current(review.get('evidence')) for review in reviews.values())
    except (KeyError, TypeError, ValueError, OSError):
        current = False
    if not current: raise ValueError('Studio prerequisite review evidence is stale')
    return {'inputs':binding(project, data, selected), 'pre_final_reviews':digest(reviews)}
