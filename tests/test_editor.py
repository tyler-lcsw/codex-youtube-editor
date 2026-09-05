import importlib.util
import sys
from pathlib import Path


def test_editor_rerender_keeps_nested_project_path(monkeypatch,tmp_path):
    project=tmp_path/'videos/project';project.mkdir(parents=True)
    monkeypatch.setattr(sys,'argv',['server.py',str(project),'8765'])
    spec=importlib.util.spec_from_file_location('editor_server',Path('tools/editor/server.py'))
    server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
    commands=[]
    class Process:
        stdout=[];returncode=0
        def wait(self):return 0
    def launch(command,**kwargs):commands.append(command);return Process()
    monkeypatch.setattr(server.subprocess,'Popen',launch)
    server.run_render('natural')
    assert commands[0][2]==str(project)
