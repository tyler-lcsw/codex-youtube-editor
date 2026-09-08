"""Build/test the native development app without changing global developer tools."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile

try:
    from tools.install_studio_app import install_studio_app
except ModuleNotFoundError:  # Direct `python tools/build_studio_app.py` invocation.
    from install_studio_app import install_studio_app

ROOT=Path(__file__).resolve().parents[1]


def engine_revision(engine):
    try:
        result=subprocess.run(
            ['git','-C',str(engine),'rev-parse','--verify','HEAD'],
            capture_output=True,text=True,check=False,
        )
    except OSError:
        return 'unavailable'
    revision=result.stdout.strip()
    if result.returncode or len(revision) not in (40,64) or any(character not in '0123456789abcdefABCDEF' for character in revision):
        return 'unavailable'
    return revision.lower()


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


def assemble(executable,engine,output,sign=True,backup_root=None):
    executable,engine,output=map(lambda p:Path(p).resolve(),(executable,engine,output))
    if not executable.is_file() or not os.access(executable,os.X_OK):raise ValueError('Missing executable')
    if not (engine/'tools/studio.py').is_file():raise ValueError('Choose the production engine repository')
    if output.suffix!='.app':raise ValueError('Output must be an .app bundle')
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.studio-bundle-',dir=output.parent))/'Codex Media Studio.app'
    try:
        contents=stage/'Contents';binary=contents/'MacOS/CodexStudio';binary.parent.mkdir(parents=True)
        shutil.copy2(executable,binary)
        resources=contents/'Resources';resources.mkdir()
        for name in ('AppIcon.icns','StudioMark.png'):
            shutil.copy2(ROOT/'macos/Resources'/name,resources/name)
        shutil.copy2(ROOT/'docs/user-guide.json',resources/'user-guide.json')
        (contents/'Info.plist').write_bytes(plistlib.dumps({
            'CFBundleExecutable':'CodexStudio','CFBundleIdentifier':'local.tyler.codex-studio',
            'CFBundleName':'Codex Media Studio','CFBundleDisplayName':'Codex Media Studio',
            'CFBundleIconFile':'AppIcon.icns','CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.2.0','CFBundleVersion':'3',
            'LSMinimumSystemVersion':'14.0','NSHighResolutionCapable':True,
            'StudioEnginePath':str(engine),'StudioEngineRevision':engine_revision(engine),
        }))
        if sign:subprocess.run(['codesign','--force','--sign','-',str(stage)],check=True)
        install_studio_app(
            stage,
            output,
            backup_root=backup_root or output.parent/'.studio-backups',
            verify_signature=sign,
        )
        return output
    finally:shutil.rmtree(stage.parent,ignore_errors=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',type=Path,default=ROOT);p.add_argument('--output',type=Path)
    p.add_argument('--install',action='store_true',help='update the canonical app in ~/Applications without invalidating its Dock alias')
    p.add_argument('--checks',action='store_true');p.add_argument('--probe',action='store_true');p.add_argument('--account-only',action='store_true')
    a=p.parse_args()
    special_modes=[a.install,a.checks,a.probe,a.account_only]
    if sum(bool(mode) for mode in special_modes)>1 or (a.output and any(special_modes)):
        p.error('--install, --output, --checks, --probe and --account-only are mutually exclusive')
    if a.checks or a.probe or a.account_only:
        product='StudioChecks' if a.checks else 'StudioProbe'
        extra=['--account-only'] if a.account_only else []
        subprocess.run(swift_command('run',product,*extra),check=True,cwd=ROOT);return
    subprocess.run(swift_command('build','-c','release','--product','CodexStudio'),check=True,cwd=ROOT)
    executable=ROOT/'macos/.build/release/CodexStudio'
    output=Path.home()/'Applications/Codex Media Studio.app' if a.install else (a.output or ROOT/'work/apps/Codex Media Studio.app')
    backup_root=(Path.home()/'Library/Application Support/Codex Media Studio/Backups') if a.install else None
    print(assemble(executable,a.engine,output,backup_root=backup_root))

if __name__=='__main__':main()
