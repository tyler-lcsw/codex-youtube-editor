"""Timing evidence; missing audiovisual landmarks never count as a pass."""
import math

def check_av_timing(streams: dict, landmarks: list[tuple[float,float]], tolerance_ms: float=40) -> dict:
    start_drift=abs(streams['video_start']-streams['audio_start'])*1000
    duration_drift=abs(streams['video_duration']-streams['audio_duration'])*1000
    drift=max((abs(v-a)*1000 for v,a in landmarks),default=None)
    passed=(drift is not None and all(math.isfinite(x) and x<=tolerance_ms for x in (drift,start_drift,duration_drift)))
    return {'passed':passed,'start_drift_ms':start_drift,'duration_drift_ms':duration_drift,
            'max_landmark_drift_ms':drift,'landmarks_checked':len(landmarks),'tolerance_ms':tolerance_ms}


def confidence_findings(words, threshold=.7):
    low=[];unknown=[]
    for word in words:
        score=word.get('confidence')
        if not isinstance(score,(int,float)) or not math.isfinite(score):unknown.append(word)
        elif score<threshold:low.append(word)
    return low,unknown


def transcript_drift(expected, actual, tolerance_ms=40):
    import re
    from difflib import SequenceMatcher
    normalize=lambda w:re.sub(r'[^\w]','',w['text'].casefold())
    matches=SequenceMatcher(None,list(map(normalize,expected)),list(map(normalize,actual)),autojunk=False)
    rows=[]
    for a,b,n in matches.get_matching_blocks():
        for i in range(n):
            x,y=expected[a+i],actual[b+i]
            if any(type(w.get(k)) is not int for w in (x,y) for k in ('start','end')):continue
            drift=max(abs(y[k]-x[k]) for k in ('start','end'))
            rows.append({'text':x['text'],'start_ms':y['start'],'drift_ms':drift,'flag':drift>tolerance_ms})
    return {'matched':len(rows),'flags':sum(r['flag'] for r in rows),'tolerance_ms':tolerance_ms,'rows':rows}


def require_render_binding(transcript, master_sha256):
    if transcript.get('source_media_sha256') != master_sha256:
        raise ValueError('Render ASR is not bound to this master; run tools.verify_render for a fresh pass')
