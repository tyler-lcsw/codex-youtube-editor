"""Explicit download/verification of one pinned project model. HF downloads need .envs/image."""
import argparse
import hashlib
import io
import json
import stat
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from tools.jobs import file_hash
from tools.run_state import file_lock

ROOT=Path(__file__).resolve().parents[1]


def verify_files(spec: dict, target: Path):
    for name,digest in spec['files'].items():
        f=target/name
        if not f.is_file() or f.is_symlink() or file_hash(f)!=digest:
            raise ValueError(f'Pinned model hash verification failed: {name}')


def install_archive(data: bytes, spec: dict, target: Path):
    """Verify before installing; extract only pinned regular files into a staged directory."""
    if hashlib.sha256(data).hexdigest()!=spec['archive_sha256']:
        raise ValueError('Archive hash differs from the pinned release')
    target=Path(target)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names=[]
        for entry in archive.infolist():
            path=PurePosixPath(entry.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in entry.filename or ':' in entry.filename:
                raise ValueError('Unsafe archive path')
            if stat.S_ISLNK(entry.external_attr >> 16):raise ValueError('Archive path is a symlink')
            names.append(entry.filename)
        if len(names)!=len(set(names)):raise ValueError('Duplicate archive path')
        target.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.model-stage-',dir=target.parent) as folder:
            staged=Path(folder)/target.name;staged.mkdir()
            for name,digest in spec['files'].items():
                relative=PurePosixPath(name)
                if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe pinned file path')
                content=archive.read(f'{target.name}/{name}')
                if hashlib.sha256(content).hexdigest()!=digest:raise ValueError(f'Model file hash differs: {name}')
                f=staged/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(content)
            verify_files(spec,staged)
            if target.exists():
                # An existing valid install needs no mutation. Do not discard a damaged
                # or user-modified install silently; it can be moved aside for repair.
                verify_files(spec,target)
            else:staged.rename(target)


def main():
    models=json.loads((ROOT/'config/models.lock.json').read_text())['models']
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',choices=models)
    p.add_argument('--verify-only',action='store_true');a=p.parse_args();spec=models[a.model]
    target=Path(spec['path']).expanduser()
    if not target.is_absolute():target=ROOT/target
    with file_lock(ROOT/'work/local-inference.lock'):
        if not a.verify_only:
            if spec.get('archive_url'):
                with urllib.request.urlopen(spec['archive_url'],timeout=60) as response:
                    data=response.read(64*1024*1024+1)
                if len(data)>64*1024*1024:raise ValueError('Model archive exceeds setup limit')
                install_archive(data,spec,target)
            else:
                from huggingface_hub import snapshot_download
                snapshot_download(spec['repo'],revision=spec['revision'],local_dir=target)
        verify_files(spec,target)
    print(f'Verified {a.model}: {spec["revision"]}')


if __name__=='__main__':main()
