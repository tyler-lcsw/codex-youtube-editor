import json
from pathlib import Path
import pytest
from PIL import Image

def setup_request(tmp_path):
    from tools.codex_image_handoff import prepare_request
    ref=tmp_path/'ref.png';Image.new('RGB',(64,64),'blue').save(ref)
    return prepare_request(tmp_path/'project','Three thumbnail bets',[ref],'thumbnail')

def test_no_generation_reservation_without_approval(tmp_path):
    from tools.codex_image_handoff import claim_generation
    p=setup_request(tmp_path)
    with pytest.raises(PermissionError):claim_generation(p,tmp_path/'absent.json')

def test_reserved_scope_reused_and_import_is_project_owned(tmp_path):
    from tools.codex_image_handoff import claim_generation,import_codex_image,begin_generation
    p=setup_request(tmp_path);request=json.loads(p.read_text())
    approval=tmp_path/'approval.json'
    approval.write_text(json.dumps({'id':'human-1','approved':True,'provider':'codex_builtin','purpose':'thumbnail','references':request['references'],'max_generations':1,'used_generations':0}))
    claim_generation(p,approval);claim_generation(p,approval)
    assert json.loads(approval.read_text())['used_generations']==1
    begin_generation(p)
    generated=tmp_path/'native.png';Image.new('RGB',(1280,720),'red').save(generated)
    result=import_codex_image(p,generated,None)
    asset=Path(result['artifacts'][0]['path'])
    assert asset.is_relative_to(tmp_path/'project') and asset.is_file()
    assert result['provenance']['reported_model']=='unknown'
    assert import_codex_image(p,generated,None)==result
    claim_generation(p,approval)
    assert json.loads(p.read_text())["status"]=="succeeded"

def test_changed_reference_blocks_claim(tmp_path):
    from tools.codex_image_handoff import claim_generation
    p=setup_request(tmp_path);r=json.loads(p.read_text())
    approval=tmp_path/'approval.json';approval.write_text(json.dumps({'id':'ok','approved':True,'provider':'codex_builtin','purpose':'thumbnail','references':r['references'],'max_generations':1,'used_generations':0}))
    Image.new('RGB',(64,64),'green').save(tmp_path/'ref.png')
    with pytest.raises(ValueError,match='reference'):claim_generation(p,approval)


def reserved_request(tmp_path):
    from tools.codex_image_handoff import claim_generation
    path=setup_request(tmp_path);r=json.loads(path.read_text());approval=tmp_path/'approval.json'
    approval.write_text(json.dumps({'id':'ok','approved':True,'provider':'codex_builtin','purpose':'thumbnail','references':r['references'],'max_generations':1,'used_generations':0}))
    claim_generation(path,approval);return path,approval


def test_dispatch_is_one_time_and_reclaim_does_not_reset_it(tmp_path):
    from tools.codex_image_handoff import begin_generation,claim_generation
    path,approval=reserved_request(tmp_path)
    first=begin_generation(path)
    assert first['status']=='generation_in_flight'
    claim_generation(path,approval)
    with pytest.raises(PermissionError,match='already dispatched'):begin_generation(path)
    assert json.loads(approval.read_text())['used_generations']==1


def test_corrupt_import_can_be_repaired_without_new_generation(tmp_path):
    from tools.codex_image_handoff import begin_generation,import_codex_image
    path,approval=reserved_request(tmp_path);begin_generation(path)
    image=tmp_path/'native.png';Image.new('RGB',(64,64),'red').save(image)
    result=import_codex_image(path,image,None)
    asset=Path(result['artifacts'][0]['path']);asset.write_bytes(b'corrupt')
    repaired=import_codex_image(path,image,None)
    assert Path(repaired['artifacts'][0]['path']).read_bytes()==image.read_bytes()
    assert asset.read_bytes()==b'corrupt'
    assert json.loads(approval.read_text())['used_generations']==1


def test_changed_approval_scope_blocks_import(tmp_path):
    from tools.codex_image_handoff import begin_generation,import_codex_image
    path,approval=reserved_request(tmp_path);begin_generation(path)
    a=json.loads(approval.read_text());a['purpose']='unrelated';approval.write_text(json.dumps(a))
    image=tmp_path/'native.png';Image.new('RGB',(64,64),'red').save(image)
    with pytest.raises(PermissionError):import_codex_image(path,image,None)


def test_completed_import_revalidates_approval_scope(tmp_path):
    from tools.codex_image_handoff import begin_generation,import_codex_image
    path,approval=reserved_request(tmp_path);begin_generation(path)
    image=tmp_path/'native.png';Image.new('RGB',(64,64),'red').save(image)
    import_codex_image(path,image,None)
    a=json.loads(approval.read_text());a['approved']=False;approval.write_text(json.dumps(a))
    with pytest.raises(PermissionError):import_codex_image(path,image,None)
