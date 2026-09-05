"""Local project tracker; canonical project files can rebuild the SQLite index."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def upsert_project(index: Path, project_id: str, properties: dict, script: str, apply: bool=False) -> dict:
    if not project_id.strip():raise ValueError('Stable project ID required')
    result={'project_id':project_id,'properties':properties,'script':script,'applied':apply}
    if not apply:return result
    index.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(index) as db:
        db.execute('CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, properties TEXT NOT NULL, script TEXT NOT NULL)')
        db.execute('INSERT INTO projects VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET properties=excluded.properties, script=excluded.script',
                   (project_id,json.dumps(properties,ensure_ascii=False),script))
    return result

def list_projects(index: Path, stage: str | None=None) -> list[dict]:
    if not index.exists():return []
    with sqlite3.connect(f'file:{index.resolve()}?mode=ro',uri=True) as db:
        rows=[{'project_id':pid,'properties':json.loads(props),'script':script} for pid,props,script in db.execute('SELECT id,properties,script FROM projects ORDER BY id')]
    return [r for r in rows if stage is None or r['properties'].get('stage')==stage]

def sync_project(project: Path, index: Path, apply: bool, stage: str | None=None, props_only: bool=False):
    project=project.resolve(); path=project/'tracker.json'
    source=path if path.exists() else project/'notion.json'
    properties=json.loads(source.read_text()) if source.exists() else {'title':project.name,'stage':'idea'}
    if stage:properties['stage']=stage
    pid=properties.get('project_id') or hashlib.sha256(str(project).encode()).hexdigest()[:16]
    script_path=project/'script/script.md';script=script_path.read_text() if script_path.exists() else ''
    if props_only:
        prior=next((p for p in list_projects(index) if p['project_id']==pid),None)
        script=prior['script'] if prior else ''
    if apply:
        properties['project_id']=pid
        from tools.run_state import atomic_json
        atomic_json(path,properties)
    return upsert_project(index,pid,properties,script,apply)

if __name__=='__main__':
    import sys
    sys.path.insert(0,str(ROOT))
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project',nargs='?',type=Path)
    p.add_argument('--index',type=Path,default=ROOT/'work/tracker.sqlite');p.add_argument('--apply',action='store_true')
    p.add_argument('--list',action='store_true');p.add_argument('--stage');p.add_argument('--props-only',action='store_true')
    p.add_argument('--resync',action='store_true',help='Re-read the canonical local script and properties')
    a=p.parse_args()
    if a.list:r=list_projects(a.index,a.stage)
    elif a.project:r=sync_project(a.project,a.index,a.apply,a.stage,a.props_only)
    else:p.error('Supply a project or --list')
    print(json.dumps(r,indent=2,ensure_ascii=False))
