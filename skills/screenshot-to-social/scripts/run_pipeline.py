#!/usr/bin/env python3
"""Build, score, render and package a screenshot-to-social project in one go.

  python run_pipeline.py <project_dir>               # full run: check → music → beat-sync → render ×4 → finish
  python run_pipeline.py <project_dir> --check-only  # build the master and run `hyperframes check`, nothing else
  python run_pipeline.py <project_dir> --no-render   # everything up to the renders (for a quick look in Studio)
  python run_pipeline.py --env                       # only verify the toolchain

Expects <project_dir>/beats.json and the screenshot it names. Stops at the first failing stage and says how to fix it.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def npx():
    # Windows needs npx.cmd; subprocess does not resolve it from "npx"
    exe = shutil.which("npx") or shutil.which("npx.cmd")
    if not exe:
        sys.exit("STOP: npx not found. Install Node.js 18+ (https://nodejs.org), then rerun.")
    return exe


def run(cmd, cwd, what):
    print(f"\n== {what}\n   $ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=cwd)
    if r.returncode != 0:
        sys.exit(f"STOP: {what} failed (exit {r.returncode}). Fix the error above, then rerun this script.")


def check_env(need_music):
    ok = True
    for tool, hint in (("ffmpeg", "install ffmpeg and put it on PATH"), ("node", "install Node.js 18+")):
        if not shutil.which(tool):
            print(f"missing: {tool} ({hint})")
            ok = False
    if importlib.util.find_spec("PIL") is None:
        print("missing: Pillow (pip install pillow); it measures the fonts so headlines fit")
        ok = False
    sfx = Path.home() / ".claude" / "skills" / "media-use" / "audio" / "assets" / "sfx"
    if not sfx.exists():
        print("note: media-use SFX not found; the video will have no clicks or whooshes "
              "(npx hyperframes skills update media-use)")
    if need_music and not all(importlib.util.find_spec(m) for m in ("torch", "transformers", "soundfile")):
        print("note: MusicGen packages missing, so no music can be generated. Either "
              "pip install torch transformers soundfile numpy, or supply a track: "
              "save it as assets/bgm/seed.wav and run make_music.py <project> --from-seed assets/bgm/seed.wav")
    if not ok:
        sys.exit("STOP: install the missing tools above, then rerun.")
    print("toolchain ok")


def main():
    args = sys.argv[1:]
    if "--env" in args:
        check_env(True)
        return
    if not args:
        sys.exit(__doc__)
    proj = Path(args[0]).resolve()
    beats = proj / "beats.json"
    if not beats.exists():
        sys.exit(f"STOP: {beats} not found. Write it first (start from assets/example-beats.json).")
    seed = proj / "assets" / "bgm" / "seed.wav"
    check_env(need_music=not seed.exists())
    py, hf = sys.executable, npx()
    build = HERE / "build_composition.py"
    music = HERE / "make_music.py"

    run([py, build, beats, proj, "--master-only"], proj, "build the master")
    run([hf, "--yes", "hyperframes", "check"], proj, "hyperframes check")
    if "--check-only" in args:
        print("\nmaster checks out. Snapshot beats with: npx hyperframes snapshot --at <t1>,<t2> --no-end")
        return

    run([py, build, beats, proj], proj, "build all variants")
    if not seed.exists() and not all(importlib.util.find_spec(m) for m in ("torch", "transformers", "soundfile")):
        sys.exit("STOP: no music seed and no MusicGen. See the note above, then rerun.")
    run([py, music, proj], proj, "music bed at the exact lengths")
    cfg = json.loads(beats.read_text(encoding="utf-8"))
    if cfg.get("snap_to_music", True):
        run([hf, "--yes", "hyperframes", "beats"], proj, "detect the music's beat grid")
        run([py, build, beats, proj], proj, "rebuild with scene changes snapped to the beat")
        run([py, music, proj], proj, "re-trim the bed to the snapped lengths")
    if "--no-render" in args:
        print("\nbuilt without rendering. Preview: npx hyperframes preview --background")
        return

    variants = json.loads((proj / "variants.json").read_text(encoding="utf-8"))["variants"]
    (proj / "renders").mkdir(exist_ok=True)
    for name in variants:
        out = Path("renders") / (Path(name).stem + ".mp4")
        run([hf, "--yes", "hyperframes", "render", "-c", name, "-q", "delivery", "-o", out], proj, f"render {name}")
    run([py, HERE / "finish.py", proj], proj, "normalize loudness, extract stills, name files for each platform")
    print(f"\ndone: {proj / 'renders' / 'post'}  (next: write POSTING.md from references/platforms.md)")


if __name__ == "__main__":
    main()
