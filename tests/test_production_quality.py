import json
import sys
from pathlib import Path
import pytest
from tools import production_quality as qa

@pytest.fixture
def setup(tmp_path):
    rules=tmp_path/'rules.md';rules.write_text('# Rules\n\n## R01\n\nDO preserve meaning.\n\n## R02\n\nDO listen.\n')
    project=tmp_path/'project';project.mkdir();evidence=project/'review.md';evidence.write_text('Specific review evidence')
    return project,rules,evidence

def records(project,rules,evidence,phase,status):
    entries=[{'id':r['id'],'status':status,'reason':'Reviewed for this fixture','evidence':[str(evidence)]} for r in qa.read_rules(rules)['rules']]
    qa.record(project,phase,entries,'test reviewer',rules)

def test_dynamic_rule_changes_require_new_checklists(setup):
    p,r,e=setup;records(p,r,e,'before','planned');assert qa.gate(p,'before',r)['passed']
    r.write_text(r.read_text()+'\n## R03\n\nDO inspect the source.\n')
    assert [x['id'] for x in qa.checklist(p,'before',r)['rules']]==['R01','R02','R03']
    assert not qa.gate(p,'before',r)['passed']

def test_completion_needs_each_phase_and_current_deliverables(setup):
    p,r,e=setup
    with pytest.raises(ValueError):qa.finalize(p,r)
    records(p,r,e,'before','planned');records(p,r,e,'during','pass')
    out=p/'film.mp4';out.write_bytes(b'fixture media');qa.set_deliverables(p,[out],r)
    records(p,r,e,'after','pass');assert qa.finalize(p,r)['status']=='qa_complete'
    out.write_bytes(b'changed media');assert not qa.gate(p,'after',r)['passed']
    with pytest.raises(ValueError):qa.finalize(p,r)

def test_changed_evidence_and_pending_review_block(setup):
    p,r,e=setup;records(p,r,e,'before','planned');e.write_text('changed review')
    assert not qa.gate(p,'before',r)['passed']
    with pytest.raises(ValueError):qa.record(p,'after',[{'id':'R01','status':'pass','reason':'','evidence':[]}],'reviewer',r)
    records(p,r,e,'after','pending');assert not qa.gate(p,'after',r)['passed']

def test_action_requires_plan_logs_failures_and_invalidates_final_review(setup):
    p,r,e=setup;cmd=[sys.executable,'-c','raise SystemExit(3)']
    with pytest.raises(ValueError):qa.run_action(p,cmd,['R01'],'test action',[e],r)
    records(p,r,e,'before','planned')
    result=qa.run_action(p,cmd,['R01'],'test action',[e],r)
    assert result['exit_code']==3
    state=json.loads((p/'work/quality/state.json').read_text());assert len(state['actions'])==1
    assert not qa.gate(p,'during',r)['passed']

def test_malformed_rule_file_fails_closed(setup):
    p,r,e=setup;r.write_text('## R01\n\nPerhaps inspect.\n')
    with pytest.raises(ValueError):qa.read_rules(r)

def test_not_applicable_needs_evidence_and_reason(setup):
    p,r,e=setup
    with pytest.raises(ValueError):qa.record(p,'before',[{'id':'R01','status':'not_applicable','reason':'irrelevant','evidence':[]}],'reviewer',r)

def test_editable_required_final_rules_cannot_be_waived(setup):
    p,r,e=setup
    r.write_text('<!-- final-required: R02 -->\n'+r.read_text())
    records(p,r,e,'after','not_applicable')
    assert any(x['id']=='R02' for x in qa.gate(p,'after',r)['failures'])
    r.write_text(r.read_text().replace('R02 -->','R99 -->'))
    with pytest.raises(ValueError):qa.read_rules(r)

def test_tracker_requires_fresh_receipt_and_new_action_invalidates_it(tmp_path):
    from tools.tracker import sync_project
    p=tmp_path/'project';p.mkdir();e=p/'fixture.txt';e.write_text('Synthetic coordinator test evidence, not a production review.')
    index=tmp_path/'index.sqlite'
    with pytest.raises(ValueError):sync_project(p,index,True,'complete')
    records(p,qa.RULES,e,'before','planned')
    qa.run_action(p,[sys.executable,'-c','pass'],['R01'],'Synthetic action',[e])
    records(p,qa.RULES,e,'during','pass');qa.set_deliverables(p,[e])
    records(p,qa.RULES,e,'after','pass');qa.finalize(p)
    assert sync_project(p,index,True,'complete')['applied']
    qa.run_action(p,[sys.executable,'-c','pass'],['R01'],'Second synthetic action',[e])
    with pytest.raises(ValueError):sync_project(p,index,True,'complete')

def test_failed_action_requires_durable_resolution(setup):
    p,r,e=setup;records(p,r,e,'before','planned')
    action=qa.run_action(p,[sys.executable,'-c','raise SystemExit(2)'],['R01'],'Failure fixture',[e],r)
    records(p,r,e,'during','pass')
    assert not qa.gate(p,'during',r)['passed']
    resolution=p/'resolution.md';resolution.write_text('Synthetic failure reviewed and recovered for coordinator test.')
    qa.resolve_action(p,action['id'],'Fixture recovery',[resolution])
    assert qa.gate(p,'during',r)['passed']
    resolution.write_text('Changed recovery evidence')
    assert not qa.gate(p,'during',r)['passed']

def test_unknown_heading_does_not_silently_drop_a_rule(setup):
    p,r,e=setup;r.write_text('## MissingID\nDO inspect.\n'+r.read_text())
    with pytest.raises(ValueError):qa.read_rules(r)

def test_all_production_skills_reference_authority():
    root=Path(__file__).resolve().parents[1]
    for skill in (root/'.agents/skills').glob('*/SKILL.md'):
        assert 'docs/production-rules.md' in skill.read_text(), skill
