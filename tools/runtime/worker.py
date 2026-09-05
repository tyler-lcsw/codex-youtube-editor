"""Bounded worker process groups: timeout/cancellation terminates descendants too."""
import os
import signal
import subprocess
from .offline import offline_command


def run_worker(command, timeout=600, offline=True, cwd=None):
    command=offline_command(command) if offline else command
    process=subprocess.Popen(command,cwd=cwd,start_new_session=True)
    try:
        code=process.wait(timeout=timeout)
        if code:raise subprocess.CalledProcessError(code,command)
    except BaseException:
        try:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            process.wait()
        raise
