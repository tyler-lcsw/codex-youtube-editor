"""Real bridge regressions: preserve media, reject invalid feedback and stale evidence."""
import json
from pathlib import Path
import subprocess
import wave
import pytest

from tools.studio import dispatch

@pytest.fixture
def project(tmp_path):
    p = tmp_path / 'project'
    dispatch({'method': 'create', 'project': str(p), 'params': {'title': 'Review'}})
    return p

@pytest.fixture
def media(tmp_path):
    p = tmp_path / 'source.wav'
    with wave.open(str(p), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(8000); f.writeframes(b'\0\0' * 8000)
    return p

def call(p, method, **params):
    return dispatch({'method': method, 'project': str(p), 'params': params})

def test_brief_and_thread_survive_reopen(project):
    call(project, 'update_brief', brief={'audience': 'Learners', 'purpose': 'Explain'})
    call(project, 'set_thread', thread_id='thread-123')
    state = call(project, 'open')
    assert state['title'] == 'Review'
    assert state['brief']['audience'] == 'Learners'
    assert state['thread_id'] == 'thread-123'
    assert (project / 'work/transcript').is_dir()

def test_import_preserves_original_and_rejects_corrupt(project, media, tmp_path):
    original = media.read_bytes()
    state = call(project, 'import_media', path=str(media), role='source')
    asset = state['assets'][0]
    assert media.read_bytes() == original
    assert Path(asset['path']).read_bytes() == original
    assert asset['path'] != str(media)
    assert asset['duration_ms'] == 1000
    assert asset['source_path'] == str(media)
    for content in (b'', b'not real video'):
        invalid = tmp_path / 'bad.mp4'; invalid.write_bytes(content)
        with pytest.raises(ValueError): call(project, 'import_media', path=str(invalid), role='source')
    assert len(call(project, 'open')['assets']) == 1

def test_links_routes_and_handoff(project, media):
    for url in ('file:///etc/passwd', 'javascript:alert(1)', 'https://'):
        with pytest.raises(ValueError): call(project, 'add_resource', url=url, label='Bad', role='reference')
    call(project, 'add_resource', url='https://example.com/video', label='Reference', role='reference')
    call(project, 'import_media', path=str(media), role='source')
    with pytest.raises(ValueError): call(project, 'set_route', task='images', provider='openai-api')
    call(project, 'set_route', task='images', provider='native-codex')
    handoff = call(project, 'export_handoff')
    assert str(media) in handoff['text']
    assert 'native-codex' in handoff['text']
    assert 'not approval' in handoff['text']
    assert Path(handoff['path']).read_text() == handoff['text']

def test_annotation_bounds_and_revision_binding(project, media):
    asset = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    args = dict(asset_id=asset['id'], time_ms=200, text='Tighten pause', rect={'x':0.1,'y':0.2,'width':0.3,'height':0.4})
    for change in ({'time_ms':1001}, {'end_ms':100}, {'rect':{'x':0.8,'y':0,'width':0.3,'height':0.4}}):
        with pytest.raises(ValueError): call(project, 'add_annotation', **(args | change))
    annotation = call(project, 'add_annotation', **args)['annotations'][0]
    rev = call(project, 'add_revision', path=str(media), label='Revision 1')['revisions'][0]
    assert call(project, 'open')['annotations'][0] == annotation
    with pytest.raises(ValueError): call(project, 'update_annotation', id=annotation['id'], status='addressed', resolution_revision_id='missing', note='fixed')
    state = call(project, 'update_annotation', id=annotation['id'], status='addressed', resolution_revision_id=rev['id'], note='Shortened')
    assert state['annotations'][0]['asset_sha256'] == asset['sha256']
    assert state['annotations'][0]['resolution_revision_id'] == rev['id']
    with pytest.raises(ValueError): call(project, 'update_annotation', id=annotation['id'], status='accepted', note='auto')

def test_workflow_prerequisites_evidence_and_staleness(project, media):
    call(project, 'import_media', path=str(media), role='source')
    evidence = project / 'work/report.md'; evidence.write_text('Source reviewed: one-second silent fixture, no speech.')
    with pytest.raises(ValueError): call(project, 'record_stage', stage='source_understanding', evidence=[str(evidence)], reason='review')
    with pytest.raises(ValueError): call(project, 'record_stage', stage='intake', evidence=[], reason='review')
    call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Source imported')
    (project / 'work/analysis/source-understanding.md').write_text('Synthetic source has no speech; content limitations recorded.')
    (project / 'work/analysis/content-map.json').write_text('{"segments": [], "reason": "Synthetic fixture"}')
    call(project, 'record_stage', stage='source_understanding', evidence=[str(evidence)], reason='Silence assessed')
    assert call(project, 'workflow')['stages'][1]['status'] == 'complete'
    call(project, 'update_brief', brief={'purpose':'New objective'})
    assert call(project, 'workflow')['stages'][1]['status'] == 'stale'
    call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='New brief reviewed')
    evidence.write_text('Changed findings')
    assert call(project, 'workflow')['stages'][0]['status'] == 'stale'
    assert not call(project, 'quality')['gates']['after']['passed']

def test_cli_reports_errors_without_losing_next_request(project):
    process = subprocess.run([__import__('sys').executable, '-m', 'tools.studio'], input='{}\n'+json.dumps({'method':'open','project':str(project)})+'\n', text=True, capture_output=True)
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert 'error' in responses[0]
    assert responses[1]['result']['title'] == 'Review'

def test_rule_workflow_and_source_changes_stale_reviews(project, media, tmp_path, monkeypatch):
    from tools import studio_workflow as flow
    rules = tmp_path / 'rules.md'; rules.write_bytes(flow.quality.RULES.read_bytes())
    config = tmp_path / 'workflow.json'; config.write_bytes(flow.WORKFLOW.read_bytes())
    monkeypatch.setattr(flow.quality, 'RULES', rules)
    monkeypatch.setattr(flow, 'WORKFLOW', config)
    asset = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    evidence = project / 'work/review.md'; evidence.write_text('Inspected original fixture.')
    for changed in (rules, config, Path(asset['path'])):
        call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Inspected current inputs')
        assert call(project, 'workflow')['stages'][0]['status'] == 'complete'
        changed.write_bytes(changed.read_bytes() + b'\n')
        assert call(project, 'workflow')['stages'][0]['status'] == 'stale'

def test_unopened_project_request_does_not_create_directory(tmp_path):
    missing = tmp_path / 'missing'
    with pytest.raises((ValueError, FileNotFoundError)):
        call(missing, 'open')
    assert not missing.exists()

def test_changed_frame_cannot_be_silently_accepted(project, video):
    asset = call(project, 'import_media', path=str(video), role='source')['assets'][0]
    frame = Path(call(project, 'capture_frame', asset_id=asset['id'], time_ms=100)['path'])
    annotation = call(project, 'add_annotation', asset_id=asset['id'], time_ms=100, text='Fix', frame_path=str(frame))['annotations'][0]
    rev = call(project, 'add_revision', path=str(video), label='Second')['revisions'][0]
    call(project, 'update_annotation', id=annotation['id'], status='addressed', resolution_revision_id=rev['id'], note='Fixed')
    call(project, 'update_annotation', id=annotation['id'], status='ready_for_review', note='Ready')
    frame.write_bytes(b'different capture')
    with pytest.raises(ValueError):
        call(project, 'update_annotation', id=annotation['id'], status='accepted', note='Seen', user_action=True)

def test_cli_envelope_matches_native_client(project):
    process = subprocess.run([__import__('sys').executable, '-m', 'tools.studio'], input='{}\n'+json.dumps({'method':'open','project':str(project)})+'\n', text=True, capture_output=True)
    failure, success = [json.loads(line) for line in process.stdout.splitlines()]
    assert failure['ok'] is False and isinstance(failure['error'], str)
    assert success['ok'] is True


def test_invalid_frame_rejected(project, media):
    asset = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    frame = project / 'work/frames/invalid.png'; frame.write_bytes(b'not png')
    with pytest.raises(ValueError):
        call(project, 'add_annotation', asset_id=asset['id'], time_ms=100, text='Fix', frame_path=str(frame))

def test_project_has_engine_audio_and_transcript_directories(project):
    assert (project / 'work/audio').is_dir()
    assert (project / 'work/transcripts').is_dir()


def test_rereview_prerequisite_does_not_revive_downstream(project):
    intake = project / 'work/intake.md'; intake.write_text('Original input finding')
    understanding = project / 'work/understanding.md'; understanding.write_text('Original interpretation')
    call(project, 'record_stage', stage='intake', evidence=[str(intake)], reason='Original intake')
    (project / 'work/analysis/source-understanding.md').write_text('Synthetic source has no speech; content limitations recorded.')
    (project / 'work/analysis/content-map.json').write_text('{"segments": [], "reason": "Synthetic fixture"}')
    call(project, 'record_stage', stage='source_understanding', evidence=[str(understanding)], reason='Original understanding')
    intake.write_text('Corrected input finding')
    call(project, 'record_stage', stage='intake', evidence=[str(intake)], reason='Corrected intake')
    assert call(project, 'workflow')['stages'][1]['status'] == 'stale'


def test_unknown_resolution_reopen_preserves_annotation(project, media):
    asset = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    annotation = call(project, 'add_annotation', asset_id=asset['id'], time_ms=100, text='Fix')['annotations'][0]
    revision = call(project, 'add_revision', path=str(media), label='Second')['revisions'][0]
    before = call(project, 'update_annotation', id=annotation['id'], status='addressed', resolution_revision_id=revision['id'], note='Changed')
    with pytest.raises(ValueError):
        call(project, 'update_annotation', id=annotation['id'], status='open', resolution_revision_id='missing', note='Reopen')
    assert call(project, 'open')['annotations'] == before['annotations']


@pytest.fixture
def video(tmp_path):
    output = tmp_path / 'fixture.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=32x32:rate=10:duration=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(output)], check=True)
    return output


@pytest.fixture
def muxed_media(tmp_path):
    output = tmp_path / 'muxed.mp4'
    subprocess.run([
        'ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
        'testsrc2=size=32x32:rate=10:duration=1', '-f', 'lavfi', '-i',
        'sine=frequency=440:sample_rate=8000:duration=1', '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest', str(output)
    ], check=True)
    return output


def test_podcast_settings_bind_canonical_audio_and_optional_camera(project, media, video):
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    camera = call(project, 'import_media', path=str(video), role='source')['assets'][1]

    assert audio['stream_types'] == ['audio']
    assert camera['stream_types'] == ['video']

    state = call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'], camera_asset_id=camera['id'])
    assert state['podcast'] == {
        'schema_version': 1,
        'kind': 'solo_audio_first',
        'primary_audio_asset_id': audio['id'],
        'camera_asset_id': camera['id'],
        'visual_density': 'balanced',
    }
    assert call(project, 'open')['podcast'] == state['podcast']
    assert audio['id'] in call(project, 'export_handoff')['text']


def test_podcast_settings_patch_preserves_extensions_and_can_be_cleared(project, media, video):
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    camera = call(project, 'import_media', path=str(video), role='source')['assets'][1]
    call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])
    stored = json.loads((project / 'work/studio/project.json').read_text())
    stored['podcast']['future_extension'] = {'value': 3}
    (project / 'work/studio/project.json').write_text(json.dumps(stored))

    state = call(project, 'set_podcast_settings', camera_asset_id=camera['id'])
    assert state['podcast']['primary_audio_asset_id'] == audio['id']
    assert state['podcast']['camera_asset_id'] == camera['id']
    assert state['podcast']['future_extension'] == {'value': 3}
    assert call(project, 'clear_podcast_settings')['podcast'] is None


def test_podcast_settings_validate_streams_sources_and_exact_bytes(project, media, video, muxed_media):
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    camera = call(project, 'import_media', path=str(video), role='source')['assets'][1]
    muxed = call(project, 'import_media', path=str(muxed_media), role='source')['assets'][2]
    revision = call(project, 'add_revision', path=str(media), label='Audio revision')['revisions'][0]
    document = project / 'notes.txt'; document.write_text('reference')
    document_asset = call(project, 'import_media', path=str(document), role='document')['assets'][3]

    for params in (
        {'primary_audio_asset_id': 'missing'},
        {'primary_audio_asset_id': camera['id']},
        {'primary_audio_asset_id': revision['id']},
        {'primary_audio_asset_id': document_asset['id']},
        {'primary_audio_asset_id': audio['id'], 'camera_asset_id': audio['id']},
    ):
        with pytest.raises(ValueError):
            call(project, 'set_podcast_settings', **params)

    same_asset = call(project, 'set_podcast_settings', primary_audio_asset_id=muxed['id'], camera_asset_id=muxed['id'])
    assert same_asset['podcast']['primary_audio_asset_id'] == same_asset['podcast']['camera_asset_id']

    Path(audio['path']).write_bytes(b'changed')
    with pytest.raises(ValueError):
        call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])


def test_legacy_assets_are_probed_on_selection_and_unknown_fields_survive(project, media):
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    state_path = project / 'work/studio/project.json'
    stored = json.loads(state_path.read_text())
    stored.pop('podcast')
    stored['future_project_field'] = {'kept': True}
    stored['assets'][0].pop('stream_types')
    stored['assets'][0]['future_asset_field'] = 'kept'
    state_path.write_text(json.dumps(stored))

    opened = call(project, 'open')
    assert opened['podcast'] is None
    configured = call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])
    assert configured['assets'][0]['stream_types'] == ['audio']
    assert configured['assets'][0]['future_asset_field'] == 'kept'
    assert configured['future_project_field'] == {'kept': True}


def test_podcast_settings_conditionally_participate_in_workflow_binding(project, media):
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    evidence = project / 'work/intake.md'; evidence.write_text('Reviewed canonical source choice.')
    call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Reviewed sources')
    assert call(project, 'workflow')['stages'][0]['status'] == 'complete'

    # Opening an unconfigured project performs the additive null migration without
    # invalidating evidence recorded by the general Studio workflow.
    assert call(project, 'open')['podcast'] is None
    assert call(project, 'workflow')['stages'][0]['status'] == 'complete'

    call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])
    assert call(project, 'workflow')['stages'][0]['status'] == 'stale'


def test_clearing_podcast_settings_cannot_revive_pre_podcast_review(project, media):
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    evidence = project / 'work/intake.md'; evidence.write_text('Reviewed source mode.')
    call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='General intake reviewed')

    configured = call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])
    assert configured['podcast_settings_revision'] == 1
    assert call(project, 'workflow')['stages'][0]['status'] == 'stale'
    call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Podcast intake reviewed')
    assert call(project, 'workflow')['stages'][0]['status'] == 'complete'

    cleared = call(project, 'clear_podcast_settings')
    assert cleared['podcast'] is None
    assert cleared['podcast_settings_revision'] == 2
    assert call(project, 'workflow')['stages'][0]['status'] == 'stale'
    call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Cleared mode reviewed')

    reconfigured = call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])
    assert reconfigured['podcast_settings_revision'] == 3
    assert call(project, 'workflow')['stages'][0]['status'] == 'stale'


def test_identical_podcast_settings_are_idempotent_for_workflow_evidence(project, media):
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    configured = call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])
    evidence = project / 'work/intake.md'; evidence.write_text('Reviewed podcast source selection.')
    call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Podcast intake reviewed')
    assert call(project, 'workflow')['stages'][0]['status'] == 'complete'

    unchanged = call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'], camera_asset_id=None)
    assert unchanged['podcast_settings_revision'] == configured['podcast_settings_revision']
    assert call(project, 'workflow')['stages'][0]['status'] == 'complete'


def test_podcast_visual_density_defaults_validates_and_changes_workflow_binding(project, media):
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    configured = call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])
    assert configured['podcast']['visual_density'] == 'balanced'
    assert configured['podcast_settings_revision'] == 1

    evidence = project / 'work/intake.md'; evidence.write_text('Reviewed balanced visual density.')
    call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Podcast settings reviewed')
    unchanged = call(project, 'set_podcast_settings', visual_density='balanced')
    assert unchanged['podcast_settings_revision'] == 1
    assert call(project, 'workflow')['stages'][0]['status'] == 'complete'

    before = call(project, 'open')
    for invalid in (None, 3, '', 'dense'):
        with pytest.raises(ValueError):
            call(project, 'set_podcast_settings', visual_density=invalid)
        assert call(project, 'open') == before

    illustrative = call(project, 'set_podcast_settings', visual_density='illustrative')
    assert illustrative['podcast']['visual_density'] == 'illustrative'
    assert illustrative['podcast_settings_revision'] == 2
    assert call(project, 'workflow')['stages'][0]['status'] == 'stale'


def test_legacy_podcast_settings_gain_density_on_next_successful_set(project, media):
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    configured = call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])
    path = project / 'work/studio/project.json'
    stored = json.loads(path.read_text())
    stored['podcast'].pop('visual_density', None)
    stored['podcast']['future_extension'] = {'kept': True}
    path.write_text(json.dumps(stored))

    normalized = call(project, 'set_podcast_settings', primary_audio_asset_id=audio['id'])
    assert normalized['podcast']['visual_density'] == 'balanced'
    assert normalized['podcast']['future_extension'] == {'kept': True}
    assert normalized['podcast_settings_revision'] == configured['podcast_settings_revision'] + 1


def test_capture_receipt_binds_exact_asset_time_and_bytes(project, video, media):
    asset = call(project, 'import_media', path=str(video), role='source')['assets'][0]
    revision = call(project, 'add_revision', path=str(video), label='Second')['revisions'][0]
    capture = call(project, 'capture_frame', asset_id=asset['id'], time_ms=200)
    assert capture['asset_sha256'] == asset['sha256'] and capture['time_ms'] == 200
    assert Path(capture['path']).is_file()
    for mismatch in ({'asset_id':revision['id']}, {'time_ms':300}):
        params = dict(asset_id=asset['id'], time_ms=200, frame_path=capture['path'], text='Fix') | mismatch
        with pytest.raises(ValueError): call(project, 'add_annotation', **params)
    state = call(project, 'add_annotation', asset_id=asset['id'], time_ms=200, frame_path=capture['path'], text='Fix')
    assert state['annotations'][0]['frame_path'] == capture['path']
    audio = call(project, 'import_media', path=str(media), role='source')['assets'][-1]
    with pytest.raises(ValueError): call(project, 'capture_frame', asset_id=audio['id'], time_ms=200)


def test_unregistered_valid_image_is_not_capture(project, video):
    from PIL import Image
    asset = call(project, 'import_media', path=str(video), role='source')['assets'][0]
    frame = project / 'work/frames/unrelated.png'; Image.new('RGB',(32,32),'red').save(frame)
    with pytest.raises(ValueError):
        call(project, 'add_annotation', asset_id=asset['id'], time_ms=100, frame_path=str(frame), text='Fix')


def test_capture_reports_frame_time_and_survives_project_move(project, video):
    import shutil
    asset = call(project, 'import_media', path=str(video), role='source')['assets'][0]
    capture = call(project, 'capture_frame', asset_id=asset['id'], time_ms=215)
    assert capture['time_ms'] == 300
    relocated = project.with_name('moved-project')
    shutil.move(str(project), str(relocated))
    frame = relocated / Path(capture['path']).relative_to(project)
    state = call(relocated, 'add_annotation', asset_id=asset['id'], time_ms=300, frame_path=str(frame), text='Moved project capture')
    assert state['annotations'][0]['frame_path'] == str(frame)


def test_runtime_required_artifacts_are_nonempty_hashed_and_project_local(project, tmp_path, monkeypatch):
    from tools import studio_workflow as flow
    config = tmp_path / 'workflow.json'
    config.write_text(json.dumps({'stages':[{'id':'intake','label':'Intake','requires':[], 'artifacts':['work/custom.md'], 'instructions':'Document source findings.'}], 'routes':{}}))
    monkeypatch.setattr(flow, 'WORKFLOW', config)
    evidence = project / 'work/reason.md'; evidence.write_text('Read source')
    for content in (None, ''):
        if content is not None: (project / 'work/custom.md').write_text(content)
        with pytest.raises(ValueError): call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Reviewed')
    artifact = project / 'work/custom.md'; artifact.write_text('Detailed source findings')
    call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Reviewed')
    assert call(project, 'workflow')['stages'][0]['status'] == 'complete'
    artifact.write_text('Corrected finding')
    assert call(project, 'workflow')['stages'][0]['status'] == 'stale'
    artifact.unlink(); artifact.symlink_to(evidence.parent.parent.parent / 'outside.md')
    artifact.resolve().write_text('Outside project')
    with pytest.raises(ValueError): call(project, 'record_stage', stage='intake', evidence=[str(evidence)], reason='Reviewed')


@pytest.mark.parametrize('unsafe', ['../outside.md', '/tmp/outside.md', 'work/../../outside.md', ''])
def test_required_artifact_paths_reject_escape(project, tmp_path, monkeypatch, unsafe):
    from tools import studio_workflow as flow
    config = tmp_path / 'workflow.json'
    config.write_text(json.dumps({'stages':[{'id':'intake','requires':[], 'artifacts':[unsafe]}], 'routes':{}}))
    monkeypatch.setattr(flow, 'WORKFLOW', config)
    with pytest.raises(ValueError): call(project, 'workflow')


def test_final_stage_requires_completion_receipt_even_if_gates_pass(project, tmp_path, monkeypatch):
    from tools import studio_workflow as flow
    config = tmp_path / 'workflow.json'
    config.write_text(json.dumps({'stages':[{'id':'final_review','requires':[]}], 'routes':{}}))
    monkeypatch.setattr(flow, 'WORKFLOW', config)
    # Isolate distinction between gate results and actual finalization receipt.
    monkeypatch.setattr(flow.quality, 'gate', lambda *args: {'passed':True})
    evidence = project / 'work/report.md'; evidence.write_text('Synthetic test evidence')
    with pytest.raises(ValueError): call(project, 'record_stage', stage='final_review', evidence=[str(evidence)], reason='Gate alone is insufficient')


def test_validate_asset_rejects_changed_media_after_reopen_preserves_history(project, media):
    asset = call(project, 'import_media', path=str(media), role='source')['assets'][0]
    annotation = call(project, 'add_annotation', asset_id=asset['id'], time_ms=100, text='Historical feedback')['annotations'][0]
    assert call(project, 'validate_asset', asset_id=asset['id']) == asset
    Path(asset['path']).write_bytes(b'changed bytes')
    assert call(project, 'open')['annotations'][0] == annotation
    with pytest.raises(ValueError): call(project, 'validate_asset', asset_id=asset['id'])
    assert call(project, 'open')['annotations'][0] == annotation
    Path(asset['path']).unlink()
    with pytest.raises((ValueError, FileNotFoundError)): call(project, 'validate_asset', asset_id=asset['id'])


@pytest.fixture
def before_plans(project):
    from tools import production_quality as quality
    evidence = project / 'work/test-action-plan.md'
    evidence.write_text('Engineering fixture only: write a marker to verify the production action prerequisite boundary. No media generation or acceptance.')
    quality.record(project, 'before', [{'id':rule['id'], 'status':'planned', 'reason':f"Synthetic action plan coverage for {rule['id']}", 'evidence':[str(evidence)]} for rule in quality.read_rules()['rules']], 'test-fixture')
    return evidence


def test_studio_action_default_edit_requires_strategy_but_explicit_intake_runs(project, before_plans):
    from tools import production_quality as quality
    marker = project / 'work/ran.txt'
    command = [__import__('sys').executable, '-c', 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("ran")', str(marker)]
    assert quality.gate(project, 'before')['passed']
    with pytest.raises(ValueError):
        quality.run_action(project, command, ['R04'], 'Check default edit gate', [str(before_plans)])
    assert not marker.exists()
    with pytest.raises(ValueError):
        quality.run_action(project, command, ['R04'], 'Reject unknown stage', [str(before_plans)], stage='unknown')
    assert not marker.exists()
    result = quality.run_action(project, command, ['R04'], 'Inspect during intake', [str(before_plans)], stage='intake')
    assert result['exit_code'] == 0 and marker.read_text() == 'ran'
    assert call(project, 'open')['stage_reviews'] == {}


def test_action_uses_dynamic_workflow_prerequisites(project, before_plans, tmp_path, monkeypatch):
    from tools import production_quality as quality
    from tools import studio_workflow as flow
    config = tmp_path / 'workflow.json'
    config.write_text(json.dumps({'stages':[{'id':'inspect','requires':[]}, {'id':'edit','requires':['inspect']}], 'routes':{}}))
    monkeypatch.setattr(flow, 'WORKFLOW', config)
    command = [__import__('sys').executable, '-c', 'pass']
    with pytest.raises(ValueError): quality.run_action(project, command, ['R04'], 'Check dynamic prerequisite', [str(before_plans)])
    call(project, 'record_stage', stage='inspect', evidence=[str(before_plans)], reason='Inspected fixture')
    assert quality.run_action(project, command, ['R04'], 'Run after inspection', [str(before_plans)])['exit_code'] == 0
    before_plans.write_text('Corrected fixture findings')
    # Restore current before QA to isolate the stale Studio prerequisite.
    quality.record(project, 'before', [{'id':rule['id'], 'status':'planned', 'reason':f"Updated synthetic coverage for {rule['id']}", 'evidence':[str(before_plans)]} for rule in quality.read_rules()['rules']], 'test-fixture')
    with pytest.raises(ValueError): quality.run_action(project, command, ['R04'], 'Stale inspection blocks', [str(before_plans)])


def test_studio_action_cli_accepts_explicit_intake_stage(project, before_plans):
    result = subprocess.run([__import__('sys').executable, '-m', 'tools.production_quality', 'run', str(project), '--stage', 'intake', '--rules', 'R04', '--reason', 'Synthetic CLI gate check', '--evidence', str(before_plans), '--', __import__('sys').executable, '-c', 'pass'], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['exit_code'] == 0


@pytest.fixture
def qa_ready_studio(project):
    from tools import production_quality as quality
    evidence = project / 'work/synthetic-qa.md'
    evidence.write_text('Synthetic unit-test receipt fixture only; not real production acceptance.')
    deliverable = project / 'output/synthetic.txt'; deliverable.write_text('Synthetic delivery bytes')
    quality.set_deliverables(project, [str(deliverable)])
    for phase in quality.PHASES:
        quality.record(project, phase, [{'id':rule['id'], 'status':'planned' if phase == 'before' else 'pass', 'reason':f"Synthetic test disposition for {rule['id']} in {phase}", 'evidence':[str(evidence)]} for rule in quality.read_rules()['rules']], 'unit-test-fixture')
    return project


def prepare_studio_stages(project):
    report = project / 'work/stage-findings.md'; report.write_text('Synthetic stage finding')
    (project / 'work/analysis/source-understanding.md').write_text('Synthetic source understanding')
    (project / 'work/analysis/content-map.json').write_text('{"segments":[]}')
    (project / 'work/edit-plan.md').write_text('Synthetic edit plan')
    for stage in ('intake','source_understanding','editorial_strategy','edit'):
        call(project, 'record_stage', stage=stage, evidence=[str(report)], reason=f'Synthetic {stage} finding')
    return report


def test_finalize_studio_requires_current_pre_final_stages(qa_ready_studio):
    from tools import production_quality as quality
    assert all(quality.gate(qa_ready_studio, phase)['passed'] for phase in quality.PHASES)
    with pytest.raises(ValueError): quality.finalize(qa_ready_studio)


@pytest.mark.parametrize('change', ['brief','workflow','evidence','review'])
def test_studio_completion_receipt_invalidates_inputs_without_qa_changes(qa_ready_studio, tmp_path, monkeypatch, change):
    from tools import production_quality as quality
    from tools import studio_workflow as flow
    config = tmp_path / 'workflow.json'; config.write_bytes(flow.WORKFLOW.read_bytes())
    monkeypatch.setattr(flow, 'WORKFLOW', config)
    project = qa_ready_studio
    report = prepare_studio_stages(project)
    quality.finalize(project)
    assert quality.require_complete(project)['status'] == 'qa_complete'
    call(project, 'record_stage', stage='final_review', evidence=[str(report)], reason='Synthetic final review')
    assert quality.require_complete(project)['status'] == 'qa_complete'
    assert call(project, 'workflow')['stages'][-1]['status'] == 'complete'
    if change == 'brief': call(project, 'update_brief', brief={'purpose':'Changed objective'})
    elif change == 'workflow': config.write_bytes(config.read_bytes()+b'\n')
    elif change == 'review': call(project, 'record_stage', stage='intake', evidence=[str(report)], reason='New intake interpretation')
    else: report.write_text('Corrected stage finding')
    assert all(quality.gate(project, phase)['passed'] for phase in quality.PHASES)
    with pytest.raises(ValueError): quality.require_complete(project)
