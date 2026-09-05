import subprocess
import pytest


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()


def test_audit_classifies_changes_and_does_not_modify_checkout(tmp_path):
    from tools.upstream_audit import upstream_audit
    git(tmp_path,'init','-q');git(tmp_path,'config','user.name','Fixture');git(tmp_path,'config','user.email','fixture@example.invalid')
    (tmp_path/'README.md').write_text('base');git(tmp_path,'add','.');git(tmp_path,'commit','-qm','base');base=git(tmp_path,'rev-parse','HEAD')
    folder=tmp_path/'.claude/skills/new';folder.mkdir(parents=True);(folder/'SKILL.md').write_text('new')
    (tmp_path/'tools').mkdir();(tmp_path/'tools/gen_video.py').write_text('provider')
    (tmp_path/'remotion').mkdir();(tmp_path/'remotion/package.json').write_text('{}')
    git(tmp_path,'add','.');git(tmp_path,'commit','-qm','candidate');candidate=git(tmp_path,'rev-parse','HEAD')
    (tmp_path/'README.md').write_text('uncommitted work')
    before=git(tmp_path,'status','--porcelain')
    result=upstream_audit(base,candidate,tmp_path)
    assert result['base_sha']==base and result['candidate_sha']==candidate
    assert {r['category'] for r in result['changes']}=={'skills','dependencies','tools'}
    assert result['requires_review'] is True
    assert git(tmp_path,'status','--porcelain')==before
    assert git(tmp_path,'rev-parse','HEAD')==candidate


def test_invalid_ref_is_rejected(tmp_path):
    from tools.upstream_audit import upstream_audit
    git(tmp_path,'init','-q')
    with pytest.raises(ValueError):upstream_audit('--help','missing',tmp_path)
