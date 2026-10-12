#!/usr/bin/env python3
"""Turn the variant renders into a ready-to-post folder.

  python finish.py <project_dir>

Expects renders/<variant>.mp4 for each variant in variants.json (render with
`npx hyperframes render -c <variant>.html -q delivery -o renders/<variant>.mp4`).
Writes <project_dir>/renders/post/ with:
  - every video loudness-normalized to -14 LUFS (social standard), video stream copied
  - stills: a cover frame (the hook, already pointing at the work) and the recap card, in 9:16 and 4:5
  - the original screenshot at full resolution
Named by platform so the posting playbook can refer to them directly.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

NAMES = {
    "index.html": ["x-2-video_4x5.mp4"],
    "story-9x16.html": ["instagram-story-2-video_9x16.mp4"],
    "recap-4x5.html": ["linkedin-video_4x5.mp4"],
    "sequenced-4x5.html": ["linkedin-video_4x5.mp4"],
    "reel-9x16.html": ["instagram-reel_9x16.mp4"],
}


def run(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    lines = [l for l in r.stderr.splitlines() if l.strip().startswith("I:")]
    return lines[-1].strip() if lines else "?"


def main():
    proj = Path(sys.argv[1])
    meta = json.loads((proj / "variants.json").read_text(encoding="utf-8"))
    renders, post = proj / "renders", proj / "renders" / "post"
    post.mkdir(parents=True, exist_ok=True)
    for variant, info in meta["variants"].items():
        src = renders / (Path(variant).stem + ".mp4")
        if not src.exists():
            print("missing render:", src)
            continue
        for name in NAMES.get(variant, [Path(variant).stem + ".mp4"]):
            out = post / name
            run("-i", str(src), "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                "-ar", "48000", "-movflags", "+faststart", str(out))
            print(f"{name}: {info['w']}x{info['h']} {info['duration']}s  {loudness(out)}")
        tag = "9x16" if info["h"] / info["w"] > 1.5 else "4x5"
        if not info["intro"] and not info["outro"]:
            # cover / thumbnail: the hook once its lines have landed, so it already points at the work
            cover = post / f"cover_{tag}.png"
            run("-ss", str(meta.get("cover_time", 2.8)), "-i", str(src), "-frames:v", "1", str(cover))
            print("still:", cover.name)
        if info["intro"]:
            notice = post / f"notice-card_{tag}.png"
            run("-ss", str(round(info["intro"] * 0.5, 2)), "-i", str(src), "-frames:v", "1", str(notice))
            print("still:", notice.name)
        if info["outro"]:
            recap = post / f"recap-card_{tag}.png"
            run("-ss", str(round(info["duration"] - 0.25, 2)), "-i", str(src), "-frames:v", "1", str(recap))
            print("still:", recap.name)
    shots = list((proj / "assets" / "img").glob("*"))
    if shots:
        shutil.copy(shots[0], post / ("original-screenshot" + shots[0].suffix))
    print("post folder ->", post)


if __name__ == "__main__":
    main()
