

def test_unknown_scores_are_review_findings_not_certainty():
    from tools.media_qa import confidence_findings
    words=[{'text':'a','start':0,'end':100,'confidence':None},{'text':'b','start':100,'end':200,'confidence':.5},{'text':'c','start':200,'end':300,'confidence':.9}]
    low,unknown=confidence_findings(words)
    assert [w['text'] for w in low]==['b']
    assert [w['text'] for w in unknown]==['a']


def test_word_timing_drift_never_gets_a_growing_budget():
    from tools.media_qa import transcript_drift
    expected=[{'text':'hello','start':0,'end':100},{'text':'goodbye','start':600000,'end':600300}]
    actual=[{'text':'hello','start':0,'end':100},{'text':'goodbye','start':600200,'end':600500}]
    report=transcript_drift(expected,actual)
    assert report['flags']==1 and report['tolerance_ms']==40
    assert not transcript_drift(expected,[])['matched']


def test_render_asr_must_be_bound_to_current_master():
    import pytest
    from tools.media_qa import require_render_binding
    with pytest.raises(ValueError,match='fresh'):
        require_render_binding({'source_media_sha256':'old'},'current')
    require_render_binding({'source_media_sha256':'current'},'current')
