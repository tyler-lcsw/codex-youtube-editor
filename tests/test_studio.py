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
