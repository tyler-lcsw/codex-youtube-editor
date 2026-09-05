"""Explicit download/verification of one pinned project model. Run in .envs/image."""
import argparse
import json
from pathlib import Path
from tools.jobs import file_hash
from huggingface_hub import snapshot_download

ROOT=Path(__file__).resolve().parents[1]


def main():
    models=json.loads((ROOT/'config/models.lock.json').read_text())['models']
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',choices=models)
    p.add_argument('--verify-only',action='store_true');a=p.parse_args();spec=models[a.model]
    target=Path(spec['path']).expanduser()
    if not target.is_absolute():target=ROOT/target
    if not a.verify_only:
        if not spec.get('repo','').startswith(('mlx-community/','mflux-community/')):
            p.error('This model uses a separate upstream archive; follow docs/setup-macos.md')
        snapshot_download(spec['repo'],revision=spec['revision'],local_dir=target)
    for name,digest in spec['files'].items():
        f=target/name
        if not f.is_file() or file_hash(f)!=digest:raise RuntimeError(f'Pinned model verification failed: {a.model}/{name}')
    print(f'Verified {a.model}: {spec["revision"]}')


if __name__=='__main__':main()
