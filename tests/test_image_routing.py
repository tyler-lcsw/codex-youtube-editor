def test_visual_complexity_alone_does_not_force_local():
    from tools.image_routing import recommend_image_route
    assert recommend_image_route({'profile':'hybrid','native_available':True,'multiple_references':True,'complex_artwork':True})=='codex_builtin'
    for key in ['unattended','control_maps','pinned_seed_required','integrated_multi_shot']:
        assert recommend_image_route({'profile':'hybrid','native_available':True,key:True})=='local'
    assert recommend_image_route({'profile':'local','native_available':True})=='local'
