import json
import pytest

def test_revision_and_input_content_invalidate_cache(tmp_path):
    from tools.jobs import job_key, file_hash
    p=tmp_path/'a';p.write_text('first')
    r={'inputs':{'sha256':file_hash(p)}}
    first=job_key(r,'v1')
    assert first != job_key(r,'v2')
    p.write_text('changed');r['inputs']['sha256']=file_hash(p)
    assert first != job_key(r,'v1')

def test_job_validates_cache_and_preserves_prior_output(tmp_path):
    from tools.jobs import run_job
    from tools.providers.contracts import MediaResult
    calls=[]
    def render(out):
        calls.append(1); p=out/'result.txt';p.write_text('good')
        return MediaResult([{'path':str(p)}],{}, {'provider':'test'})
    r=run_job(tmp_path, {'task':'test'}, 'v1',render)
    again=run_job(tmp_path, {'task':'test'}, 'v1',render)
    assert len(calls)==1 and r==again
    from pathlib import Path
    Path(r['artifacts'][0]['path']).write_text('corrupt')
    run_job(tmp_path, {'task':'test'}, 'v1',render)
    assert len(calls)==2

def test_failure_cannot_become_success(tmp_path):
    from tools.jobs import run_job
    from tools.providers.contracts import MediaResult, InvalidMediaResult
    with pytest.raises(InvalidMediaResult):
        run_job(tmp_path, {'task':'test'}, 'v1', lambda out:MediaResult([{'path':str(out/'absent')}],{},{}))
    states=list(tmp_path.glob('*/state.json'))
    assert len(states)==1 and json.loads(states[0].read_text())['status']=='failed'
