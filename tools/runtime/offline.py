"""OS-enforced offline workers, including their subprocesses."""
import platform
import shutil

def offline_command(command: list[str], allow_loopback=False) -> list[str]:
    if platform.system() == 'Darwin' and shutil.which('sandbox-exec'):
        profile='(version 1)(allow default)(deny network*)'
        if allow_loopback:
            profile+='(allow network-inbound (local ip "localhost:*"))(allow network-outbound (remote ip "localhost:*"))'
        return ['sandbox-exec','-p',profile,*command]
    raise RuntimeError('No tested OS-level offline runner on this host; refusing implicit network access')
