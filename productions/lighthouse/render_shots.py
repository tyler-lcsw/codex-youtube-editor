"""Render named story compositions offline with one Chromium worker."""
import subprocess,sys,time,uuid,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from tools.runtime.offline import offline_command
NODE=Path('/Users/tyler-lcsw/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
A=R/'media/projects/lighthouse';O=R/'videos/lighthouse/work/shots';O.mkdir(parents=True,exist_ok=True)
subprocess.run([NODE,R/'remotion/scripts/gen-registry.mjs'],check=True,cwd=R)
subprocess.run([NODE,R/'remotion/node_modules/typescript/bin/tsc','--noEmit','-p',R/'remotion/tsconfig.json'],check=True,cwd=R)
for name in sys.argv[1:]:
    started=time.monotonic()
    still=name.startswith(('LighthousePanel','LighthouseThumb'))
    alpha=name in ['LighthouseTitle','LighthouseRepair','LighthouseEnd']
    out=(A/(name+'.png')) if still else O/(name+('.mov' if alpha else '.mp4'))
    attempt=O/('attempt-'+uuid.uuid4().hex);attempt.mkdir()
    staged=attempt/out.name
    args=[str(NODE),str(R/'remotion/node_modules/@remotion/cli/remotion-cli.js'),'still' if still else 'render','src/index.ts',name,str(staged)]
    args+=['--frame=0'] if still else ['--concurrency=1']
    if alpha:args+=['--codec=prores','--prores-profile=4444','--pixel-format=yuva444p10le','--image-format=png']
    with (O/(name+'.log')).open('w') as log:
        subprocess.run(offline_command(args,allow_loopback=True),cwd=R/'remotion',stdout=log,stderr=subprocess.STDOUT,check=True)
    os.replace(staged,out)
    print(f'{out} — {time.monotonic()-started:.2f}s',flush=True)
