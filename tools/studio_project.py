"""Durable, source-preserving production studio state."""
from datetime import datetime, timezone
import json
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit
import uuid
from PIL import Image

from .jobs import file_hash


def now():
    return datetime.now(timezone.utc).isoformat()


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} must be nonempty text')
    return value.strip()


def location(value):
    return Path(text(value, 'path')).expanduser().resolve()


def state_path(project):
    return project / 'work/studio/project.json'


def create(project, params):
    if state_path(project).exists():
        raise ValueError('Project already exists; open it instead')
    title = text(params.get('title'), 'title')
    for folder in ('source', 'revisions', 'output', 'work/studio', 'work/transcript', 'work/transcripts', 'work/audio', 'work/analysis', 'work/quality', 'work/frames'):
        (project / folder).mkdir(parents=True, exist_ok=True)
    return dict(schema_version=1, project=str(project), title=title, brief={}, assets=[], revisions=[], annotations=[], resources=[], routes={}, thread_id=None, stage_reviews={}, podcast=None, podcast_settings_revision=0)


def read(project):
    data = json.loads(state_path(project).read_text())
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported project schema')
    # Relocate internal paths when a portable project folder has moved.
    old = Path(data['project'])
    for item in data['assets'] + data['revisions']:
        path = Path(item['path'])
        if path.is_relative_to(old): item['path'] = str(project / path.relative_to(old))
    for item in data['annotations']:
        if item.get('frame_path') and Path(item['frame_path']).is_relative_to(old):
            item['frame_path'] = str(project / Path(item['frame_path']).relative_to(old))
    captures = {}
    for capture in data.get('captures', {}).values():
        path = Path(capture['path'])
        if path.is_relative_to(old): capture['path'] = str(project / path.relative_to(old))
        captures[capture['path']] = capture
    data['captures'] = captures
    # Additive schema-v1 migration. An unconfigured podcast must remain equivalent
    # to the original general-production state for workflow evidence binding.
    data.setdefault('podcast', None)
    data.setdefault('podcast_settings_revision', 0)
    data['project'] = str(project)
    return data


def probe(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)], capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError('Media could not be decoded by ffprobe')
    info = json.loads(result.stdout)
    streams = info.get('streams', [])
    stream_types = [kind for kind in ('audio', 'video') if any(s.get('codec_type') == kind for s in streams)]
    if not stream_types:
        raise ValueError('No audio or video stream')
    duration = float(info.get('format', {}).get('duration', 0))
    if not math.isfinite(duration) or duration < 0:
        raise ValueError('Invalid media duration')
    return round(duration * 1000), stream_types


def import_asset(project, params, revision=False):
    source = location(params.get('path'))
    if not source.is_file() or not source.stat().st_size:
        raise ValueError('Source must be a nonempty file')
    role = 'revision' if revision else text(params.get('role', 'source'), 'role')
    target_dir = project / ('revisions' if revision else 'source')
    # Validate the exact staged bytes, never change the source, and publish atomically.
    fd, name = tempfile.mkstemp(prefix='.import-', dir=target_dir)
    os.close(fd)
    staged = Path(name)
    try:
        shutil.copyfile(source, staged)
        digest = file_hash(staged)
        if role == 'document':
            if source.suffix.lower() not in ('.txt', '.md', '.pdf', '.json', '.csv', '.docx'):
                raise ValueError('Unsupported document format')
            duration = None
            stream_types = []
        else:
            duration, stream_types = probe(staged)
        target = target_dir / (digest + source.suffix.lower())
        if target.exists() and file_hash(target) != digest:
            raise ValueError('Existing staged source has changed')
        if not target.exists(): os.replace(staged, target)
        return dict(id=uuid.uuid4().hex, path=str(target), sha256=digest, source_path=str(source), label=text(params.get('label', source.name), 'label'), role=role, duration_ms=duration, stream_types=stream_types)
    finally:
        staged.unlink(missing_ok=True)


def asset_by_id(data, asset_id):
    for item in data['assets'] + data['revisions']:
        if item['id'] == asset_id:
            if file_hash(Path(item['path'])) != item['sha256']:
                raise ValueError('Selected asset changed; register a new revision')
            return item
    raise ValueError('Unknown asset')


def source_asset_by_id(data, asset_id):
    """Resolve an immutable imported source, excluding revisions and documents."""
    asset = next((item for item in data['assets'] if item['id'] == asset_id), None)
    if asset is None or asset.get('role') == 'document':
        raise ValueError('Podcast sources must identify imported media assets')
    path = Path(asset['path'])
    if file_hash(path) != asset['sha256']:
        raise ValueError('Selected asset changed; register a new revision')
    streams = asset.get('stream_types')
    if streams is None:
        duration, streams = probe(path)
        asset['duration_ms'] = duration
        asset['stream_types'] = streams
    if not isinstance(streams, list) or not streams or any(kind not in ('audio', 'video') for kind in streams):
        raise ValueError('Selected asset has invalid stream metadata')
    return asset


def set_podcast_settings(data, params):
    """Patch the audio-first source selection while preserving future fields."""
    known = {'primary_audio_asset_id', 'camera_asset_id', 'visual_density'}
    if not params or not set(params) <= known:
        raise ValueError('Podcast settings contain unsupported fields')
    existing = data.get('podcast')
    if existing is None:
        current = dict(schema_version=1, kind='solo_audio_first', camera_asset_id=None)
    elif not isinstance(existing, dict) or existing.get('schema_version') != 1 or existing.get('kind') != 'solo_audio_first':
        raise ValueError('Unsupported podcast settings')
    else:
        current = existing
    updated = dict(current)
    updated.setdefault('visual_density', 'balanced')
    updated.update(params)
    density = updated['visual_density']
    if not isinstance(density, str) or density not in ('restrained', 'balanced', 'illustrative'):
        raise ValueError('Podcast visual density must be restrained, balanced, or illustrative')
    audio = source_asset_by_id(data, updated.get('primary_audio_asset_id'))
    if 'audio' not in audio['stream_types']:
        raise ValueError('Primary podcast source must contain audio')
    camera_id = updated.get('camera_asset_id')
    if camera_id is not None:
        camera = source_asset_by_id(data, camera_id)
        if 'video' not in camera['stream_types']:
            raise ValueError('Optional podcast camera source must contain video')
    if updated != existing:
        data['podcast'] = updated
        data['podcast_settings_revision'] = podcast_settings_revision(data) + 1


def podcast_settings_revision(data):
    revision = data.get('podcast_settings_revision', 0)
    if type(revision) is not int or revision < 0:
        raise ValueError('Invalid podcast settings revision')
    return revision


def clear_podcast_settings(data):
    """Clear configured sources without reviving evidence for an older null state."""
    revision = podcast_settings_revision(data)
    if data.get('podcast') is not None:
        data['podcast'] = None
        data['podcast_settings_revision'] = revision + 1
    else:
        data['podcast_settings_revision'] = revision


def add_annotation(project, data, params):
    asset = asset_by_id(data, params.get('asset_id'))
    start, end = params.get('time_ms'), params.get('end_ms')
    duration = asset.get('duration_ms')
    if type(start) is not int or duration is None or not 0 <= start <= duration:
        raise ValueError('Annotation time is outside selected media')
    if end is not None and (type(end) is not int or not start <= end <= duration):
        raise ValueError('Invalid annotation end time')
    rect = params.get('rect')
    if rect is not None:
        if not isinstance(rect, dict) or set(rect) != {'x','y','width','height'}:
            raise ValueError('Rectangle requires x, y, width, height')
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in rect.values()):
            raise ValueError('Rectangle coordinates must be finite')
        if min(rect['x'],rect['y']) < 0 or min(rect['width'],rect['height']) <= 0 or rect['x']+rect['width'] > 1 or rect['y']+rect['height'] > 1:
            raise ValueError('Rectangle is outside normalized video bounds')
    frame = params.get('frame_path')
    if frame:
        frame = location(frame)
        if not frame.is_relative_to(project) or not frame.is_file() or not frame.stat().st_size:
            raise ValueError('Frame must be a nonempty project-local capture')
        try:
            with Image.open(frame) as image:
                if image.format not in ('PNG', 'JPEG'): raise ValueError('Frame must be PNG or JPEG')
                image.verify()
        except OSError as error:
            raise ValueError('Invalid captured frame') from error
        frame = str(frame)
        receipt = data.get('captures', {}).get(frame)
        if not receipt or receipt['asset_id'] != asset['id'] or receipt['asset_sha256'] != asset['sha256'] or receipt['time_ms'] != start or receipt['sha256'] != file_hash(Path(frame)):
            raise ValueError('Frame must have a capture receipt for this exact asset and time')
    anchors = params.get('transcript_ids', [])
    if not isinstance(anchors, list) or any(not isinstance(x, str) for x in anchors):
        raise ValueError('Transcript IDs must be strings')
    return dict(id=uuid.uuid4().hex, asset_id=asset['id'], asset_sha256=asset['sha256'], time_ms=start, end_ms=end, rect=rect, text=text(params.get('text'),'annotation text'), frame_path=frame, frame_sha256=file_hash(Path(frame)) if frame else None, transcript_ids=anchors, status='open', resolution_revision_id=None, history=[{'status':'open','time':now()}])


def update_annotation(data, params):
    annotation = next((a for a in data['annotations'] if a['id'] == params.get('id')), None)
    if annotation is None: raise ValueError('Unknown annotation')
    asset_by_id(data, annotation['asset_id'])
    if annotation.get('frame_path'):
        frame = Path(annotation['frame_path'])
        if not frame.is_file() or file_hash(frame) != annotation['frame_sha256']:
            raise ValueError('Annotation frame changed; original capture must be preserved')
    status = params.get('status')
    transitions = {'open': {'addressed'}, 'addressed': {'open','ready_for_review'}, 'ready_for_review': {'open','addressed','accepted'}, 'accepted': {'open'}}
    if status not in transitions[annotation['status']]: raise ValueError('Invalid annotation status transition')
    revision = params.get('resolution_revision_id', annotation['resolution_revision_id'])
    if status != 'open' or revision is not None:
        if revision not in {r['id'] for r in data['revisions']} or revision == annotation['asset_id']:
            raise ValueError('Resolution must identify an existing replacement revision')
        asset_by_id(data, revision)
    if status == 'accepted' and params.get('user_action') is not True:
        raise ValueError('Acceptance requires an explicit user action')
    note = text(params.get('note'), 'resolution note')
    annotation.update(status=status, resolution_revision_id=revision)
    annotation['history'].append(dict(status=status, resolution_revision_id=revision, note=note, time=now()))


def add_resource(params):
    url = text(params.get('url'), 'URL')
    parsed = urlsplit(url)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Resource must be an HTTP(S) URL without credentials')
    return dict(id=uuid.uuid4().hex, url=url, label=text(params.get('label'),'label'), role=text(params.get('role'),'role'))


def capture_frame(project, data, params):
    """Decode a source frame and retain its actual presentation time and provenance."""
    asset = asset_by_id(data, params.get('asset_id'))
    requested = params.get('time_ms')
    duration = asset.get('duration_ms')
    if type(requested) is not int or duration is None or not 0 <= requested < duration:
        raise ValueError('Capture time is outside selected media')
    target = project / 'work/frames' / (uuid.uuid4().hex + '.png')
    try:
        result = subprocess.run([
            'ffmpeg', '-nostdin', '-v', 'info', '-i', asset['path'], '-map', '0:v:0',
            '-vf', f'select=gte(t\\,{requested / 1000}),showinfo', '-frames:v', '1',
            '-fps_mode', 'vfr', str(target)
        ], capture_output=True, text=True, timeout=120)
        times = re.findall(r'Parsed_showinfo[^\n]*pts_time:([0-9.+eE-]+)', result.stderr)
        if result.returncode or not target.is_file() or not times:
            raise ValueError('Cannot capture a video frame at this time; selected asset must contain video')
        with Image.open(target) as image: image.verify()
        # Revalidate the immutable input after extraction before recording provenance.
        asset_by_id(data, asset['id'])
        receipt = dict(path=str(target), time_ms=round(float(times[0]) * 1000), requested_time_ms=requested,
                       asset_id=asset['id'], asset_sha256=asset['sha256'], sha256=file_hash(target))
        data.setdefault('captures', {})[str(target)] = receipt
        return receipt
    except BaseException:
        target.unlink(missing_ok=True)
        raise
