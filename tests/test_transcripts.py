import json
import pytest

def test_seconds_and_unknown_confidence():
    from tools.transcripts import normalize_word
    w=normalize_word('um',1.25,1.45,None)
    assert (w['start'],w['end'])==(1250,1450)
    assert w['confidence'] is None
    assert w['alignment_confidence'] is None

def test_untimed_words_survive_but_cannot_be_cut(tmp_path):
    from tools.transcripts import normalize_word
    from tools.cutlib import load_words
    w=normalize_word('propernoun',None,None,None)
    assert w['text']=='propernoun' and w['needs_review']
    folder=tmp_path/'work/transcripts';folder.mkdir(parents=True)
    (folder/'clip.json').write_text(json.dumps({'words':[w]}))
    with pytest.raises(ValueError,match='tim'):load_words(tmp_path,'clip')

def test_explicit_transcript_selection_wins(tmp_path):
    from tools.cutlib import load_words
    for name,text in [('transcripts-u35','stale'),('transcripts','current')]:
        p=tmp_path/'work'/name;p.mkdir(parents=True)
        (p/'clip.json').write_text(json.dumps({'words':[{'text':text,'start':0,'end':100}]}))
    (tmp_path/'work/transcript-selection.json').write_text(json.dumps({'directory':'transcripts'}))
    assert load_words(tmp_path,'clip')[0]['text']=='current'

def test_invalid_times_are_rejected():
    from tools.transcripts import normalize_word
    for start,end in [(2,1),(-1,1),(float('nan'),1)]:
        with pytest.raises(ValueError):normalize_word('x',start,end,None)

def test_alignment_preserves_original_text_and_unmatched_tokens():
    from tools.transcripts import attach_alignment
    result=attach_alignment('Hello, um mysterious name.', [{'text':'Hello','start':0,'end':.2},{'text':'um','start':.2,'end':.4},{'text':'name','start':.8,'end':1}])
    assert [w['text'] for w in result]==['Hello,','um','mysterious','name.']
    assert result[2]['start'] is None and result[2]['needs_review']
    assert result[3]['start']==800

@pytest.mark.parametrize('word', [
    {'text':'a','start':300,'end':300,'needs_review':True},
    {'text':'a','start':300,'end':400,'needs_review':True},
])
def test_unresolved_alignment_blocks_cutting(word):
    from tools.transcripts import validate_words
    with pytest.raises(ValueError,match='timing'):validate_words([word])
