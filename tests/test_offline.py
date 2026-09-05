import subprocess
import sys

def test_offline_worker_denies_child_network():
    from tools.runtime.offline import offline_command
    command=offline_command([sys.executable,'-c',"import socket; s=socket.socket(); s.settimeout(1)\ntry:s.connect(('1.1.1.1',443))\nexcept PermissionError:print('denied')"])
    r=subprocess.run(command,capture_output=True,text=True)
    assert r.returncode==0 and 'denied' in r.stdout


def test_renderer_can_reach_loopback_but_not_external_network():
    import socket
    import subprocess
    import sys
    from tools.runtime.offline import offline_command
    with socket.socket() as server:
        server.bind(('127.0.0.1',0));server.listen()
        port=server.getsockname()[1]
        code=f'import socket;s=socket.create_connection(("127.0.0.1",{port}),timeout=1);s.close()'
        subprocess.run(offline_command([sys.executable,'-c',code],allow_loopback=True),check=True)
    code='import socket;socket.create_connection(("1.1.1.1",443),timeout=1)'
    result=subprocess.run(offline_command([sys.executable,'-c',code],allow_loopback=True),capture_output=True)
    assert result.returncode!=0 and b'Operation not permitted' in result.stderr
