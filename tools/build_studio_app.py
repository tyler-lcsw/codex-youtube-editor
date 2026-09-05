"""Build/test the native development app without changing global developer tools."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def swift_command(action, *arguments):
    command=['swift',action,'--package-path',str(ROOT/'macos')]
    # Some CLT upgrades leave old private manifest interfaces next to newer public ones.
    # A project-local VFS overlay uses the matching public interface without editing CLT.
    swift=Path(subprocess.check_output(['xcrun','--find','swift'],text=True).strip())
    manifests=swift.parent.parent/'lib/swift/pm/ManifestAPI'
    roots=[]
    for private in manifests.glob('*.swiftmodule/*.private.swiftinterface'):
        public=Path(str(private).replace('.private.swiftinterface','.swiftinterface'))
        if public.exists() and private.read_bytes()!=public.read_bytes():
            roots.append({'type':'file','name':str(private),'external-contents':str(public)})
    if roots:
        folder=ROOT/'work/studio-build';folder.mkdir(parents=True,exist_ok=True)
        overlay=folder/'manifest-overlay.json';overlay.write_text(json.dumps({'version':0,'roots':roots}))
        for flag in ('-vfsoverlay',str(overlay),'-module-cache-path',str(folder/'module-cache')):
            command.extend(['-Xbuild-tools-swiftc',flag])
    return command+list(arguments)


def assemble(executable,engine,output,sign=True):
    executable,engine,output=map(lambda p:Path(p).resolve(),(executable,engine,output))
    if not executable.is_file() or not os.access(executable,os.X_OK):raise ValueError('Missing executable')
    if not (engine/'tools/studio.py').is_file():raise ValueError('Choose the production engine repository')
    if output.suffix!='.app':raise ValueError('Output must be an .app bundle')
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.studio-bundle-',dir=output.parent))/'Codex Studio.app'
    try:
        contents=stage/'Contents';binary=contents/'MacOS/CodexStudio';binary.parent.mkdir(parents=True)
        shutil.copy2(executable,binary)
        (contents/'Info.plist').write_bytes(plistlib.dumps({
            'CFBundleExecutable':'CodexStudio','CFBundleIdentifier':'local.tyler.codex-studio',
            'CFBundleName':'Codex Studio','CFBundleDisplayName':'Codex Studio',
            'CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.1.0','CFBundleVersion':'1',
            'LSMinimumSystemVersion':'14.0','NSHighResolutionCapable':True,
            'StudioEnginePath':str(engine),
        }))
        if sign:subprocess.run(['codesign','--force','--sign','-',str(stage)],check=True)
        backup=output.with_suffix('.app.previous')
        if backup.exists():shutil.rmtree(backup)
        if output.exists():output.rename(backup)
        try:stage.rename(output)
        except BaseException:
            if backup.exists():backup.rename(output)
            raise
        return output
    finally:shutil.rmtree(stage.parent,ignore_errors=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',type=Path,default=ROOT);p.add_argument('--output',type=Path,default=ROOT/'work/apps/Codex Studio.app')
    p.add_argument('--checks',action='store_true');p.add_argument('--probe',action='store_true');p.add_argument('--account-only',action='store_true')
    a=p.parse_args()
    if a.checks or a.probe or a.account_only:
        product='StudioChecks' if a.checks else 'StudioProbe'
        extra=['--account-only'] if a.account_only else []
        subprocess.run(swift_command('run',product,*extra),check=True,cwd=ROOT);return
    subprocess.run(swift_command('build','-c','release','--product','CodexStudio'),check=True,cwd=ROOT)
    executable=ROOT/'macos/.build/release/CodexStudio'
    print(assemble(executable,a.engine,a.output))

if __name__=='__main__':main()
