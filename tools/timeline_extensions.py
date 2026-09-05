"""Validate legacy timelines without discarding unknown fields or ignoring extensions."""
from copy import deepcopy
import json
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA=Path(__file__).resolve().parents[1]/'schemas/timeline.schema.json'


def apply_timeline_extensions(timeline: dict) -> dict:
    """Validate registered versioned effects; all v1 effects preserve timeline time."""
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
        validate_extension(extension,timeline)
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


PARAMETERS={
    'crossfade':{'in_frames':(0,600),'out_frames':(0,600)},
    'punch-in':{'zoom':(1,4),'center_x':(0,1),'center_y':(0,1)},
    'color-grade':{'brightness':(-1,1),'contrast':(0,2),'saturation':(0,3)},
}


def validate_extension(e, timeline):
    if e['id'] not in PARAMETERS or e['version']!=1:
        raise ValueError(f"Unsupported timeline extension {e['id']!r} version {e['version']}")
    if e['time_policy']!='preserve':raise ValueError('Version 1 effects require time_policy=preserve')
    if e['end_frame']<=e['start_frame']:raise ValueError('Effect must end after its start frame')
    fps=timeline['preview'].get('fps')
    if not fps:raise ValueError('Effects require explicit preview fps')
    p=e['parameters'];limits=PARAMETERS[e['id']]
    if set(p)-set(limits):raise ValueError('Unknown effect parameter')
    for key,value in p.items():
        lo,hi=limits[key]
        if type(value) not in (int,float) or not lo<=value<=hi:raise ValueError(f'Invalid effect parameter {key}')
    if e['id']=='crossfade':
        matches=[s for s in timeline['shots'] if s['id']==e['target'] and s['type']=='cutaway']
        if len(matches)!=1:raise ValueError('Crossfade target must identify one unique cutaway')
        shot=matches[0]
        for other in timeline['shots']:
            if other is not shot and other['type']!='insert' and max(shot['master_in_s'],other['master_in_s'])<min(shot['master_out_s'],other['master_out_s']):
                raise ValueError('Crossfade cutaway cannot overlap another visual shot; compose those layers in Remotion')
        if (e['start_frame'],e['end_frame'])!=(round(shot['master_in_s']*fps),round(shot['master_out_s']*fps)):
            raise ValueError('Crossfade range must equal the cutaway master-clock range')
        for key in ('in_frames','out_frames'):
            if type(p.get(key,0)) is not int:raise ValueError('Crossfade durations must be integer frames')
        length=p.get('in_frames',0)+p.get('out_frames',0)
        if not 0<length<=e['end_frame']-e['start_frame']:raise ValueError('Crossfade durations exceed shot range or are empty')
        if sum(x['id']=='crossfade' and x['target']==e['target'] for x in timeline['extensions'])!=1:
            raise ValueError('Only one crossfade declaration per cutaway')
    else:
        if e['target']!='output':raise ValueError('Grade/punch-in target must be output')
        total=timeline['preview']['end_s']+sum(s['duration_s'] for s in timeline['shots'] if s['type']=='insert' and s['master_at_s']<timeline['preview']['end_s'])
        if e['end_frame']>round(total*fps):raise ValueError('Effect exceeds output frame range')


def crossfade_filter(e, offset, width, height, fps):
    p=e['parameters'];span=e['end_frame']-e['start_frame']
    frame=f'((T+{offset:.9f})*{fps})'
    fade_in=f'clip({frame}/{p["in_frames"]},0,1)' if p.get('in_frames') else '1'
    fade_out=f'clip(({span}-{frame})/{p["out_frames"]},0,1)' if p.get('out_frames') else '1'
    weight=f'({fade_in}*{fade_out})'
    common=f'scale={width}:{height},fps={fps},setpts=PTS-STARTPTS,format=yuv420p'
    return f"[0:v]{common}[master];[1:v]{common}[shot];[master][shot]blend=all_expr='A*(1-{weight})+B*{weight}'[v]"


def output_effect_filter(effects,width,height,fps):
    parts=[];previous='0:v';index=0
    for e in effects:
        if e['target']!='output' or e['id']=='crossfade':continue
        p=e['parameters'];output=f'fx{index}';enabled=f'gte(t,{e["start_frame"]}/{fps})*lt(t,{e["end_frame"]}/{fps})'
        if e['id']=='color-grade':
            parts.append(f"[{previous}]eq=brightness={p.get('brightness',0)}:contrast={p.get('contrast',1)}:saturation={p.get('saturation',1)}:enable='{enabled}'[{output}]")
        else:
            zoom=p.get('zoom',1.5);cx=p.get('center_x',.5);cy=p.get('center_y',.5)
            parts.append(f'[{previous}]split=2[original{index}][crop{index}]')
            parts.append(f"[crop{index}]crop=w=iw/{zoom}:h=ih/{zoom}:x='clip(iw*{cx}-ow/2,0,iw-ow)':y='clip(ih*{cy}-oh/2,0,ih-oh)',scale={width}:{height}[zoom{index}]")
            condition=enabled.replace('t,','T,')
            parts.append(f"[original{index}][zoom{index}]blend=all_expr='if({condition},B,A)'[{output}]")
        previous=output;index+=1
    return (';'.join(parts),f'[{previous}]') if parts else None
