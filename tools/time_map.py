"""Map immutable source words through actual rendered sample boundaries."""
from fractions import Fraction

def remap_word(word: dict, segments: list[dict]) -> list[dict]:
    if word.get('start') is None or word.get('end') is None:
        raise ValueError('Resolve source word timing before remapping')
    result=[]
    for index, seg in enumerate(segments):
        if seg['clip_id'] != word['clip_id']: continue
        sr=seg['source_sample_rate']; out_sr=seg['output_sample_rate']
        start=Fraction(word['start']*sr,1000); end=Fraction(word['end']*sr,1000)
        left=max(start,seg['source_in_sample']);right=min(end,seg['source_out_sample'])
        if right <= left: continue
        base=Fraction(seg['output_in_sample'],out_sr)
        result.append({**word,'id':f'{word.get("id", "word")}@{index}', 'source_word_id':word.get('id'),
            'start':round((base+Fraction(left-seg['source_in_sample'],sr))*1000),
            'end':round((base+Fraction(right-seg['source_in_sample'],sr))*1000),
            'needs_review':word.get('needs_review',False) or left!=start or right!=end})
    return result
