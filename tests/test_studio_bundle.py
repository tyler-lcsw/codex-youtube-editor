import plistlib
import subprocess
import pytest

def test_bundle_preserves_engine_reference_without_shipping_project_data(tmp_path):
    from tools.build_studio_app import assemble
    exe=tmp_path/'binary';exe.write_bytes(b'fixture binary');exe.chmod(0o755)
    root=tmp_path/'engine';(root/'tools').mkdir(parents=True);(root/'tools/studio.py').write_text('fixture')
    app=tmp_path/'Codex Studio.app'
    assemble(exe,root,app,sign=False)
    info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    assert info['StudioEnginePath']==str(root)
    assert info['StudioEngineRevision']=='unavailable'
    assert (app/'Contents/MacOS/CodexStudio').read_bytes()==b'fixture binary'
    assert not (app/'source').exists()

def test_bundle_records_exact_engine_git_revision_for_native_identification(tmp_path):
    from tools.build_studio_app import assemble
    exe=tmp_path/'binary';exe.write_bytes(b'fixture binary');exe.chmod(0o755)
    root=tmp_path/'engine';(root/'tools').mkdir(parents=True);(root/'tools/studio.py').write_text('fixture')
    subprocess.run(['git','init',str(root)],check=True,capture_output=True)
    subprocess.run(['git','-C',str(root),'add','tools/studio.py'],check=True)
    subprocess.run([
        'git','-C',str(root),'-c','user.name=Studio Test','-c','user.email=studio@example.invalid',
        'commit','-m','fixture',
    ],check=True,capture_output=True)
    revision=subprocess.check_output(['git','-C',str(root),'rev-parse','--verify','HEAD'],text=True).strip()
    app=tmp_path/'Codex Studio.app'
    assemble(exe,root,app,sign=False)
    info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    assert info['StudioEngineRevision']==revision

def test_invalid_bundle_inputs_do_not_create_partial_app(tmp_path):
    from tools.build_studio_app import assemble
    app=tmp_path/'bad.app'
    with pytest.raises(ValueError):assemble(tmp_path/'missing',tmp_path,app,sign=False)
    assert not app.exists()

def test_bundle_includes_registered_application_identity(tmp_path):
    from tools.build_studio_app import assemble
    exe=tmp_path/'binary';exe.write_bytes(b'fixture binary');exe.chmod(0o755)
    root=tmp_path/'engine';(root/'tools').mkdir(parents=True);(root/'tools/studio.py').write_text('fixture')
    app=tmp_path/'Codex Studio.app'
    assemble(exe,root,app,sign=False)
    info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
    icon=app/'Contents/Resources'/info['CFBundleIconFile']
    assert icon.read_bytes().startswith(b'icns')
    assert (app/'Contents/Resources/StudioMark.png').read_bytes().startswith(b'\x89PNG')
