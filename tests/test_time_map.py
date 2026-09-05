import pytest

def test_actual_offsets_and_repeated_clip_occurrences():
    from tools.time_map import remap_word
    seg={'clip_id':'a','source_in_sample':480000,'source_out_sample':576000,'source_sample_rate':48000,'output_in_sample':144000,'output_sample_rate':48000}
    word={'clip_id':'a','id':'w1','text':'hello','start':10500,'end':10700}
    result=remap_word(word,[seg,{**seg,'output_in_sample':480000}])
    assert [(w['start'],w['end']) for w in result]==[(3500,3700),(10500,10700)]
    assert len({w['id'] for w in result})==2

def test_cut_crossing_word_is_flagged():
    from tools.time_map import remap_word
    seg={'clip_id':'a','source_in_sample':0,'source_out_sample':24000,'source_sample_rate':48000,'output_in_sample':0,'output_sample_rate':48000}
    w={'clip_id':'a','text':'crossing','start':400,'end':600}
    result=remap_word(w,[seg])
    assert result[0]['needs_review'] and result[0]['end']==500
    assert remap_word({**w,'start':500,'end':600},[seg])==[]

def test_equal_durations_do_not_hide_offset():
    from tools.media_qa import check_av_timing
    r=check_av_timing({'video_start':0,'audio_start':.2,'video_duration':10,'audio_duration':10},[(0,.2),(5,5.2),(9,9.2)])
    assert not r['passed'] and r['max_landmark_drift_ms']>=199
    assert not check_av_timing({'video_start':0,'audio_start':0,'video_duration':10,'audio_duration':10},[])['passed']
