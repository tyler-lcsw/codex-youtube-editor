"""Validate legacy timelines without discarding unknown fields or ignoring extensions."""
from copy import deepcopy
import json
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA=Path(__file__).resolve().parents[1]/'schemas/timeline.schema.json'


def apply_timeline_extensions(timeline: dict) -> dict:
    """Return a validated copy. No declarative effects are registered yet.

    Historic TSX effects remain in their rendered shots. Future extension handlers
    must implement and qualify timing behavior before their declarations are accepted.
    """
    schema=json.loads(SCHEMA.read_text())
    error=next(iter(Draft202012Validator(schema).iter_errors(timeline)),None)
    if error:
        location='.'.join(map(str,error.absolute_path)) or 'timeline'
        raise ValueError(f'Invalid timeline at {location}: {error.message}')
    # JSON allows neither NaN nor Infinity; Python's permissive parser otherwise lets
    # them reach frame rounding and filter expressions. Preserve valid unknown fields.
    try:json.dumps(timeline,allow_nan=False)
    except (ValueError,TypeError) as error:raise ValueError('Timeline must contain finite JSON values') from error
    for shot in timeline['shots']:
        if shot['type']!='insert' and shot['master_out_s']<=shot['master_in_s']:
            raise ValueError(f'Shot {shot["id"]} must end after it starts')
    for extension in timeline.get('extensions',[]):
        raise ValueError(f'Unsupported timeline extension {extension["id"]!r} version {extension["version"]}; implement and qualify its renderer/time policy first')
    return deepcopy(timeline)


def validate_bake_settings(timeline: dict):
    preview=timeline['preview']
    for key in ('width','height','fps','out'):
        if key not in preview:raise ValueError(f'Bake preview requires {key}')
    if preview['width']%2 or preview['height']%2:raise ValueError('Bake dimensions must be even for yuv420p')
    for shot in timeline['shots']:
        if shot['type']=='split':
            box=shot['master_box']
            if round(box['w']*preview['width']/1920)<2 or round(box['h']*preview['height']/1080)<2:
                raise ValueError(f'Split box for {shot["id"]} is smaller than two output pixels')
