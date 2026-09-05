"""Bounded worker process groups: timeout/cancellation terminates descendants too."""
import os
import signal
import subprocess
from .offline import offline_command


def terminate_group(process, grace=3):
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:process.wait(timeout=grace)
    except subprocess.TimeoutExpired:pass
    # A reaped leader does not imply its group is empty: descendants may ignore TERM.
    try:os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    process.wait()


def run_worker(command, timeout=600, offline=True, cwd=None):
    command=offline_command(command) if offline else command
    process=subprocess.Popen(command,cwd=cwd,start_new_session=True)
    try:
        code=process.wait(timeout=timeout)
        if code:raise subprocess.CalledProcessError(code,command)
    except BaseException:
        terminate_group(process)
        raise
