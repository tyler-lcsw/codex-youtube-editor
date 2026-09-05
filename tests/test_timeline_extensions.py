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


def test_registered_effects_preserve_timeline_duration():
    from tools.timeline_extensions import apply_timeline_extensions
    source=legacy();source['preview'].update(fps=30,width=320,height=180,out='out.mp4')
    source['extensions']=[{'id':'color-grade','version':1,'target':'output','time_policy':'preserve','start_frame':0,'end_frame':30,'parameters':{'brightness':.1}}]
    assert apply_timeline_extensions(source)==source


def test_effect_rejects_time_change_and_unknown_parameter():
    from tools.timeline_extensions import apply_timeline_extensions
    source=legacy();source['preview']['fps']=30
    e={'id':'punch-in','version':1,'target':'output','time_policy':'overlap','start_frame':0,'end_frame':30,'parameters':{'zoom':1.5}}
    source['extensions']=[e]
    with pytest.raises(ValueError):apply_timeline_extensions(source)
    e['time_policy']='preserve';e['parameters']['typo']=1
    with pytest.raises(ValueError):apply_timeline_extensions(source)


def test_crossfade_cannot_be_shadowed_by_another_visual():
    from tools.timeline_extensions import apply_timeline_extensions
    source=legacy();source['preview']['fps']=30
    source['shots']=[{'id':'a','type':'cutaway','master_in_s':0,'master_out_s':2},{'id':'b','type':'overlay','master_in_s':1,'master_out_s':2}]
    source['extensions']=[{'id':'crossfade','version':1,'target':'a','time_policy':'preserve','start_frame':0,'end_frame':60,'parameters':{'in_frames':10,'out_frames':10}}]
    with pytest.raises(ValueError,match='overlap'):apply_timeline_extensions(source)
