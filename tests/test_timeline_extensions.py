import pytest


def legacy():
    return {'master':'master.mp4','shots':[], 'preview':{'end_s':12},'custom_note':{'owner':'preserve me'}}


def test_legacy_timeline_remains_unchanged_and_independent():
    from tools.timeline_extensions import apply_timeline_extensions
    source=legacy();result=apply_timeline_extensions(source)
    assert result==source
    result['custom_note']['owner']='changed'
    assert source['custom_note']['owner']=='preserve me'


def test_unimplemented_extension_is_not_silently_ignored():
    from tools.timeline_extensions import apply_timeline_extensions
    source=legacy();source['extensions']=[{'id':'crossfade','version':999,'target':'master','time_policy':'preserve','start_frame':0,'end_frame':10,'parameters':{}}]
    with pytest.raises(ValueError,match='Unsupported timeline extension'):apply_timeline_extensions(source)


@pytest.mark.parametrize('shot',[
    {'id':'x','type':'typo','master_in_s':0,'master_out_s':1},
    {'id':'x','type':'cutaway','master_in_s':2,'master_out_s':1},
    {'id':'x','type':'insert','master_at_s':0,'duration_s':-1},
    {'id':'x','type':'split','master_in_s':0,'master_out_s':1,'master_box':{'x':0,'y':0,'w':0,'h':100}},
])
def test_invalid_shots_are_rejected(shot):
    from tools.timeline_extensions import apply_timeline_extensions
    source=legacy();source['shots']=[shot]
    with pytest.raises(ValueError):apply_timeline_extensions(source)


@pytest.mark.parametrize('value',[float('nan'),float('inf'),0,-1])
def test_invalid_preview_duration_is_rejected(value):
    from tools.timeline_extensions import apply_timeline_extensions
    source=legacy();source['preview']['end_s']=value
    with pytest.raises(ValueError):apply_timeline_extensions(source)


def test_reused_shot_asset_ids_remain_supported():
    from tools.timeline_extensions import apply_timeline_extensions
    source=legacy();source['shots']=[{'id':'same','type':'cutaway','master_in_s':i,'master_out_s':i+1} for i in (0,1)]
    assert apply_timeline_extensions(source)==source
