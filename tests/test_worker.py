import sys
import subprocess
import pytest


def test_worker_timeout_stops_child(tmp_path):
    from tools.runtime.worker import run_worker
    marker=tmp_path/'late'
    code=f'import time;from pathlib import Path;time.sleep(1);Path({str(marker)!r}).write_text("bad")'
    with pytest.raises(subprocess.TimeoutExpired):run_worker([sys.executable,'-c',code],timeout=.05,offline=False)
    assert not marker.exists()


def test_worker_propagates_failure():
    from tools.runtime.worker import run_worker
    with pytest.raises(subprocess.CalledProcessError):run_worker([sys.executable,'-c','raise SystemExit(7)'],offline=False)
