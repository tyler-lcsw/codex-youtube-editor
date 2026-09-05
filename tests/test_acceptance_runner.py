import json
from pathlib import Path
import sys
import pytest


def fake_cli(tmp_path,behavior):
    path=tmp_path/'codex'
    path.write_text('#!'+sys.executable+'\nimport sys,time\nfrom pathlib import Path\nif "--version" in sys.argv:\n print("codex-cli fixture");sys.exit(0)\n'+behavior+'\n');path.chmod(0o755);return path


def test_completed_run_is_not_automatically_quality_approved(tmp_path):
    from tools.run_acceptance import run_acceptance
    cli=fake_cli(tmp_path,'Path(sys.argv[sys.argv.index("-o")+1]).write_text("Review result")\nprint("{}")')
    receipt=run_acceptance('codex','gpt-5.6-sol','discovery',tmp_path/'out',cli,10)
    assert receipt['status']=='completed_unreviewed'
    assert receipt['quality_approved'] is False
    assert receipt['report_sha256'] and Path(receipt['report']).read_text()=='Review result'
    assert Path(receipt['receipt']).is_file()


def test_failed_run_keeps_logs_and_does_not_reuse_previous_success(tmp_path):
    from tools.run_acceptance import run_acceptance
    cli=fake_cli(tmp_path,'print("fixture failure",file=sys.stderr)\nsys.exit(7)')
    receipt=run_acceptance('codex','gpt-6-astra','discovery',tmp_path/'out',cli,10)
    assert receipt['status']=='failed' and receipt['exit_code']==7
    assert 'fixture failure' in Path(receipt['stderr']).read_text()


def test_timeout_retains_receipt(tmp_path):
    from tools.run_acceptance import run_acceptance
    cli=fake_cli(tmp_path,'time.sleep(30)')
    receipt=run_acceptance('codex','gpt-6-astra','discovery',tmp_path/'out',cli,.1)
    assert receipt['status']=='timed_out'


def test_unsupported_scope_fails_before_starting_cli(tmp_path):
    from tools.run_acceptance import run_acceptance
    with pytest.raises(ValueError):run_acceptance('cloud','gpt-6-astra','discovery',tmp_path/'out',tmp_path/'absent',10)
