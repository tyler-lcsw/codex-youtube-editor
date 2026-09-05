"""Provider-independent word normalization. Unknown timing never reaches cut arithmetic."""
import math

def normalize_word(text: str, start_s: float | None, end_s: float | None, score: float | None) -> dict:
    unknown = start_s is None or end_s is None
    if not unknown and (not math.isfinite(start_s) or not math.isfinite(end_s) or start_s < 0 or end_s < start_s):
        raise ValueError('Invalid word timing')
    return {'text':text,'start':None if unknown else round(start_s*1000),'end':None if unknown else round(end_s*1000),
            'confidence':score,'alignment_confidence':None,'needs_review':unknown}

def validate_words(words: list[dict]) -> None:
    for w in words:
        start, end = w.get('start'),w.get('end')
        if type(start) is not int or type(end) is not int or start < 0 or end <= start or w.get("needs_review", False):
            raise ValueError(f'Unresolved or invalid timing for word {w.get("text", "?")!r}; correct/re-align before cutting')

def attach_alignment(text: str, aligned: list[dict]) -> list[dict]:
    import difflib
    import re
    tokens=text.split()
    norm=lambda s:re.sub(r'[^\w]', '',s.casefold())
    matches=difflib.SequenceMatcher(None,[norm(t) for t in tokens],[norm(w['text']) for w in aligned],autojunk=False)
    times={}
    for a,b,n in matches.get_matching_blocks():
        for i in range(n): times[a+i]=aligned[b+i]
    return [normalize_word(t, times[i]['start'] if i in times else None,times[i]['end'] if i in times else None,None) for i,t in enumerate(tokens)]
