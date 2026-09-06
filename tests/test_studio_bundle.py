import plistlib
import pytest

def test_bundle_preserves_engine_reference_without_shipping_project_data(tmp_path):
    from tools.build_studio_app import assemble
    exe=tmp_path/'binary';exe.write_bytes(b'fixture binary');exe.chmod(0o755)
    root=tmp_path/'engine';(root/'tools').mkdir(parents=True);(root/'tools/studio.py').write_text('fixture')
    app=tmp_path/'Codex Studio.app'
    assemble(exe,root,app,sign=False)
    info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    assert info['StudioEnginePath']==str(root)
    assert (app/'Contents/MacOS/CodexStudio').read_bytes()==b'fixture binary'
    assert not (app/'source').exists()

def test_invalid_bundle_inputs_do_not_create_partial_app(tmp_path):
    from tools.build_studio_app import assemble
    app=tmp_path/'bad.app'
    with pytest.raises(ValueError):assemble(tmp_path/'missing',tmp_path,app,sign=False)
    assert not app.exists()
