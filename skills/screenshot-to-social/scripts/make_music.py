#!/usr/bin/env python3
"""Music bed for the composition: pick a mood, generate (or reuse) a ~30 s seed, then loop/trim it
to the exact lengths the variants need, with fades and loudness normalization.

  python make_music.py <project_dir> [--mood punchy] [--prompt "..."] [--seed-only] [--from-seed x.wav] [--fresh]

Mood resolution: --prompt > --mood > beats.json "music": {"mood"|"prompt"} > beats.json "energy" > "calm".
See references/music.md for how to choose. The seed is regenerated only when the prompt changes
(or with --fresh); seed.json remembers which prompt made it.

Prefer a library track when the HeyGen CLI is signed in (`/media-use` resolve --type bgm) or the
owner supplies one they have rights to: save it as assets/bgm/seed.wav and pass --from-seed.
Offline generation needs torch, transformers, soundfile and numpy, plus ffmpeg. The first run downloads
facebook/musicgen-small (~300 MB). CPU generation takes a few minutes, so start it early in the background.
"""
import argparse
import json
import subprocess
from pathlib import Path

# MusicGen prompts per mood. Keep "no vocals" (lyrics fight on-screen text) and name the tempo.
MOODS = {
    "calm": "warm minimal lo-fi electronic, soft rhodes electric piano chords, gentle analog pads, light brushed hip hop beat, "
            "curious and thoughtful, late night studio, 88 bpm, clean mix, no vocals",
    "lively": "bright modern electronic pop instrumental, plucky synth arpeggio, warm bass, crisp claps and hi-hats, "
              "optimistic and curious, 108 bpm, clean punchy mix, no vocals",
    "punchy": "energetic electronic instrumental, driving four on the floor kick, tight snare, punchy synth bass, bright stabs, "
              "confident and exciting, 122 bpm, big clean mix, no vocals",
    "reflective": "slow ambient piano and soft strings, sparse, warm and hopeful, 72 bpm, intimate, no drums, no vocals",
    "cinematic": "cinematic hybrid score, pulsing synth ostinato, low strings, building tension then release, 100 bpm, no vocals",
    "playful": "playful quirky instrumental, pizzicato, marimba, light percussion, whistling synth lead, bouncy, 112 bpm, no vocals",
}
ENERGY_TO_MOOD = {"calm": "calm", "lively": "lively", "punchy": "punchy"}


def generate_seed(out, prompt):
    try:
        import soundfile as sf
        import torch
        from transformers import AutoProcessor, MusicgenForConditionalGeneration
    except ImportError as e:
        raise SystemExit(f"STOP: MusicGen needs {e.name}. Run: pip install torch transformers soundfile numpy. "
                         "Or use a track you have rights to: save it as assets/bgm/seed.wav and rerun with "
                         "--from-seed assets/bgm/seed.wav")
    torch.manual_seed(7)  # fixed seed: the same prompt gives the same track on a rerun
    proc = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
    inputs = proc(text=[prompt], padding=True, return_tensors="pt")
    audio = model.generate(**inputs, max_new_tokens=1500, do_sample=True, guidance_scale=3.5)  # 50 tokens/s → ~30 s seed; 3.5 = MusicGen default prompt adherence
    sf.write(out, audio[0, 0].cpu().numpy(), model.config.audio_encoder.sampling_rate)


def bed(seed, out, length):
    fade_out = 2.5 if length < 45 else 3.2
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", str(seed), "-i", str(seed), "-i", str(seed),
        "-filter_complex",
        f"[0][1]acrossfade=d=4:c1=tri:c2=tri[a];[a][2]acrossfade=d=4:c1=tri:c2=tri,atrim=0:{length},"
        # music must be audible from frame 1: a short fade-in, never a slow build
        f"afade=t=in:d=0.25,afade=t=out:st={max(0, length - fade_out)}:d={fade_out},"
        "loudnorm=I=-18:TP=-2:LRA=11,aresample=44100,aformat=channel_layouts=stereo",
        str(out)], check=True)
    print("wrote", out, f"{length}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--mood", choices=sorted(MOODS))
    ap.add_argument("--prompt")
    ap.add_argument("--from-seed")
    ap.add_argument("--seed-only", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="regenerate the seed even if the prompt is unchanged")
    a = ap.parse_args()
    proj = Path(a.project)
    cfg = {}
    if (proj / "beats.json").exists():
        cfg = json.loads((proj / "beats.json").read_text(encoding="utf-8"))
    music = cfg.get("music", {})
    mood = a.mood or music.get("mood") or ENERGY_TO_MOOD.get(cfg.get("energy", "calm"), "calm")
    prompt = a.prompt or music.get("prompt") or MOODS[mood]

    bgm = proj / "assets" / "bgm"
    bgm.mkdir(parents=True, exist_ok=True)
    if a.from_seed:
        seed = Path(a.from_seed)
        (bgm / "seed.json").write_text(json.dumps({"source": str(seed), "note": "supplied track"}, indent=2), encoding="utf-8")
    else:
        seed, meta = bgm / "seed.wav", bgm / "seed.json"
        old = json.loads(meta.read_text(encoding="utf-8")).get("prompt") if meta.exists() else None
        if a.fresh or not seed.exists() or (old is not None and old != prompt):
            print(f"generating seed ({mood}): {prompt}")
            generate_seed(seed, prompt)
            meta.write_text(json.dumps({"mood": mood, "prompt": prompt}, indent=2), encoding="utf-8")
        elif old is None:
            print(f"WARNING: reusing assets/bgm/seed.wav with no record of its mood. If it isn't a track you chose, "
                  f"rerun with --fresh to generate the '{mood}' mood.")
        else:
            print("reusing seed:", old)
    if a.seed_only:
        return
    vmeta = json.loads((proj / "variants.json").read_text(encoding="utf-8"))
    lengths = {"bed.wav": vmeta["main_duration"]}
    longest = max(v["duration"] for v in vmeta["variants"].values())
    if longest > vmeta["main_duration"]:
        lengths["bed-long.wav"] = longest
    for name, length in lengths.items():
        bed(seed, bgm / name, length)


if __name__ == "__main__":
    main()
