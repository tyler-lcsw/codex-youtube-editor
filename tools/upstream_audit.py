"""Read-only comparison of two local Git commits; never fetches, checks out or merges."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
from .run_state import atomic_json

ROOT=Path(__file__).resolve().parents[1]


def resolve_commit(repo: Path, ref: str) -> str:
    result=subprocess.run(['git','-C',str(repo),'rev-parse','--verify','--end-of-options',ref+'^{commit}'],capture_output=True,text=True)
    if result.returncode:raise ValueError(f'Commit is unavailable locally: {ref!r}; fetch the intended source explicitly first')
    return result.stdout.strip()


def category(path: str) -> str:
    name=Path(path).name
    if name in {'package.json','package-lock.json','pyproject.toml','uv.lock'} or name.startswith('requirements'):
        return 'dependencies'
    if path.startswith(('.claude/skills/','.agents/skills/')):return 'skills'
    if path.startswith(('schemas/','config/')):return 'schemas_and_config'
    if path.startswith('tools/'):return 'tools'
    if path.startswith('remotion/'):return 'remotion'
    if path.startswith('media/'):return 'assets'
    if path.startswith(('docs/','plan/')) or path.endswith('.md'):return 'documentation'
    return 'other'


def upstream_audit(base_sha: str, candidate_sha: str, repo: Path=ROOT) -> dict:
    repo=Path(repo);base=resolve_commit(repo,base_sha);candidate=resolve_commit(repo,candidate_sha)
    raw=subprocess.check_output(['git','-C',str(repo),'diff','--name-status','-z','--no-renames',base,candidate,'--']).decode('utf-8')
    fields=raw.split('\0');changes=[]
    for i in range(0,len(fields)-1,2):
        status,path=fields[i:i+2]
        changes.append({'status':status,'path':path,'category':category(path)})
    counts=dict(sorted(Counter(row['category'] for row in changes).items()))
    return {'schema_version':1,'base_sha':base,'candidate_sha':candidate,'changes':changes,
            'counts':counts,'requires_review':bool(changes),
            'limitations':'Path classification only; does not prove API compatibility, licensing or provider safety.',
            'review_steps':[
                'Port changed Claude skills to Codex and preserve owner project/brand state.',
                'Inspect provider calls and dependencies; do not enable hosted fallback.',
                'Check historical cut/timeline formats, timing and Remotion compatibility.',
                'Run focused regressions and a real fixture for each changed capability.',
                'Retain publication code; publication testing remains waived for this migration.',
            ] if changes else []}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',required=True);p.add_argument('--candidate',required=True)
    p.add_argument('--output',type=Path);a=p.parse_args()
    result=upstream_audit(a.base,a.candidate)
    if a.output:atomic_json(a.output,result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
