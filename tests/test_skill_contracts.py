from pathlib import Path

def test_codex_skill_tree_is_usable():
    from tools.skill_audit import audit
    assert audit(Path(__file__).resolve().parents[1]) == []

def test_audit_reports_broken_local_reference(tmp_path):
    from tools.skill_audit import audit
    skill = tmp_path / '.agents/skills/example'
    skill.mkdir(parents=True)
    (skill / 'SKILL.md').write_text('---\nname: example\ndescription: Example operation\n---\n[details](references/missing.md)\n')
    errors = audit(tmp_path, required={'example'})
    assert any('missing.md' in e for e in errors)
