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


def test_cancellation_kills_child_even_when_parent_exits(tmp_path):
    import os,signal,sys,time,subprocess
    import pytest
    from tools.runtime.worker import run_worker
    marker=tmp_path/'survived';pidfile=tmp_path/'child.pid'
    script=f'''import os,signal,time
from pathlib import Path
pid=os.fork()
if pid==0:
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
 Path({str(pidfile)!r}).write_text(str(os.getpid()))
 time.sleep(1)
 Path({str(marker)!r}).write_text('alive')
 time.sleep(20)
else:
 time.sleep(20)
'''
    try:
        with pytest.raises(subprocess.TimeoutExpired):run_worker([sys.executable,'-c',script],timeout=.2,offline=False)
        time.sleep(1.1)
        assert not marker.exists()
    finally:
        if pidfile.exists():
            try:os.kill(int(pidfile.read_text()),signal.SIGKILL)
            except ProcessLookupError:pass
