"""Transcribe extracted WAVs locally with Qwen MLX recognition and alignment.

Usage:
  python tools/transcribe.py video-1                     # all clips
  python tools/transcribe.py video-1 --clips 0233        # specific clip(s)
  python tools/transcribe.py video-1 --outdir transcripts-u35 --force

Optional AssemblyAI requires --provider assemblyai --allow-cloud after explicit approval.
Reads:  <project>/work/audio/*.wav
Writes: <project>/work/<outdir>/<id>.json  (normalized words and provider provenance)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import requests

API_BASE = "https://api.assemblyai.com/v2"

SPEECH_MODELS = ["universal-3-5-pro", "universal-2"]
# Generic — true for every solo-tutorial recording, so it stays global.
PROMPT = (
    "Verbatim transcription of a solo YouTube tutorial recording with multiple takes. "
    "Transcribe exactly as spoken: keep false starts, repeated words, self-corrections, "
    "and filler words (um, uh) — do not clean them up."
)


def load_keyterms(project: Path) -> list[str]:
    """Per-video vocabulary that biases the recognizer toward this video's proper
    nouns / product / tech names (AssemblyAI keyterms_prompt). Read from
    <project>/work/keyterms.txt — one term or phrase per line, blank lines and
    '#' comments ignored. Missing file → [] (transcription still works, just with
    more errors on specialty words). Draft it per video from the topic; never
    hardcode a video's terms here."""
    f = project / "work" / "keyterms.txt"
    if not f.exists():
        return []
    terms = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    return terms


def load_env_key(repo_root: Path, name: str) -> str:
    for line in (repo_root / ".env").read_text().splitlines():
        line = line.strip()
        if line.startswith(name + "="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    sys.exit(f"{name} not found in .env")


def upload(headers: dict, wav: Path) -> str:
    with open(wav, "rb") as f:
        r = requests.post(f"{API_BASE}/upload", headers=headers, data=f, timeout=300)
    r.raise_for_status()
    return r.json()["upload_url"]


def submit(headers: dict, audio_url: str, keyterms: list[str]) -> str:
    payload = {
        "audio_url": audio_url,
        "speech_models": SPEECH_MODELS,
        "language_detection": True,
        "punctuate": True,
        "format_text": True,
        "disfluencies": True,
        "prompt": PROMPT,
    }
    if keyterms:  # omit entirely when empty — never send [] to the API
        payload["keyterms_prompt"] = keyterms
    r = requests.post(f"{API_BASE}/transcript", headers=headers, json=payload, timeout=60)
    if r.status_code == 400:
        # older param not accepted alongside the new models -> retry without it
        print(f"  400 ({r.json().get('error', '?')}), retrying without disfluencies flag")
        payload.pop("disfluencies")
        r = requests.post(f"{API_BASE}/transcript", headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["id"]


def local_cache_key(audio: Path, language, terms, revisions) -> str:
    from hashlib import sha256
    digest=sha256()
    with audio.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return sha256(json.dumps({'audio':digest.hexdigest(),'language':language,
        'terms':terms,'models':revisions,'adapter':'qwen-mlx-v1'},sort_keys=True).encode()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--provider", choices=["qwen_mlx", "assemblyai"], default="qwen_mlx")
    ap.add_argument("--language")
    ap.add_argument("--allow-cloud", action="store_true", help="Use only after explicit approval of hosted transcription")
    ap.add_argument("--clips", nargs="*", help="clip ids, default all")
    ap.add_argument("--outdir", default="transcripts")
    ap.add_argument("--force", action="store_true", help="re-transcribe even if output exists")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    project = repo_root / args.project
    audio_dir = project / "work" / "audio"
    out_dir = project / "work" / args.outdir
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.provider == "qwen_mlx":
        import subprocess
        try:
            from .runtime.offline import offline_command
        except ImportError:
            from runtime.offline import offline_command
        worker = repo_root / ".envs/audio/bin/python"
        if not worker.is_file():
            sys.exit("Local ASR not installed; see docs/setup-macos.md. No cloud fallback.")
        wavs = [w for w in sorted(audio_dir.glob("*.wav")) if not args.clips or w.stem in args.clips]
        if not wavs:
            sys.exit(f"No selected WAV files in {audio_dir}")
        locks=json.loads((repo_root / 'config/models.lock.json').read_text())['models']
        revisions={key:locks[key]['revision'] for key in ('asr','aligner')}
        for wav in wavs:
            cache_key=local_cache_key(wav,args.language,load_keyterms(project),revisions)
            output = out_dir / (wav.stem + ".json")
            if output.exists() and not args.force:
                old = json.loads(output.read_text())
                if old.get("cache_key") == cache_key:
                    print(f"cached: {wav.stem}")
                    continue
            cmd = [sys.executable, "-m", "tools.media", "asr", "--audio", str(wav), "--out", str(output),
                   "--keyterms", str(project / "work/keyterms.txt")]
            if args.language: cmd += ["--language", args.language]
            subprocess.run(cmd, cwd=repo_root, check=True, timeout=650)
            completed=json.loads(output.read_text());completed['cache_key']=cache_key
            sys.path.insert(0,str(repo_root))
            from tools.run_state import atomic_json
            atomic_json(output,completed)
        (project / "work/transcript-selection.json").write_text(json.dumps({"directory": args.outdir}))
        return
    if not args.allow_cloud:
        sys.exit("AssemblyAI requires explicit approval and --allow-cloud; local ASR is default")
    headers = {"authorization": load_env_key(repo_root, "ASSEMBLYAI_API_KEY")}

    keyterms = load_keyterms(project)
    print(f"keyterms: {len(keyterms)} loaded from work/keyterms.txt"
          if keyterms else "keyterms: none (no work/keyterms.txt) — add this video's terms for better accuracy")

    jobs = {}
    for wav in sorted(audio_dir.glob("*.wav")):
        clip = wav.stem
        if args.clips and clip not in args.clips:
            continue
        if not args.force and (out_dir / f"{clip}.json").exists():
            print(f"{clip}: transcript exists, skipping")
            continue
        print(f"{clip}: uploading {wav.stat().st_size // 1024} KB...")
        jobs[clip] = submit(headers, upload(headers, wav), keyterms)
        print(f"{clip}: submitted, transcript id {jobs[clip]}")

    pending = dict(jobs)
    while pending:
        time.sleep(5)
        for clip, tid in list(pending.items()):
            r = requests.get(f"{API_BASE}/transcript/{tid}", headers=headers, timeout=60)
            r.raise_for_status()
            data = r.json()
            if data["status"] == "completed":
                (out_dir / f"{clip}.json").write_text(json.dumps(data, indent=1))
                model = data.get("speech_model_used") or data.get("speech_model") or "?"
                print(f"{clip}: completed, {len(data.get('words') or [])} words, model={model}")
                del pending[clip]
            elif data["status"] == "error":
                print(f"{clip}: ERROR {data.get('error')}")
                del pending[clip]

    print("done")


if __name__ == "__main__":
    main()
