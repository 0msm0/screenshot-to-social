---
name: screenshot-to-social
description: Turns a screenshot of real work in progress (Claude Code or other AI agent sessions, terminals, IDEs, dashboards, docs, design tools) into a ready-to-post behind-the-scenes social package. Produces a motion-design video with music built on the real screenshot, Instagram Reel, Story, LinkedIn and X versions, cover and recap stills, a caption for each platform and a step-by-step posting playbook. Use when someone shares a screenshot and wants a post, reel, teaser, build-in-public update or a peek behind the scenes, even if they only say "make something I can post from this" or "help people notice what's going on here". Also use for follow-up posts in the same series. Not for promo videos made from a website URL, edits to existing footage, or caption-only requests with no screenshot.
compatibility: Claude Code on a local machine. Needs Node.js 18+ (npx hyperframes), ffmpeg, Python 3.10+ with Pillow; optional torch, transformers and soundfile for offline music. Pairs with the hyperframes and media-use skills.
metadata:
  author: Manas
  version: 1.0.0
  repository: https://github.com/0msm0/screenshot-to-social
---

# Screenshot → behind-the-scenes social package

A screenshot of real work is proof: nobody staged it. Don't turn it into an ad. **Point straight at what's worth noticing** (parallel work, reasoning, human steering, a persona the agent plays, an honest caveat, a catch), one point at a time, then recap.

Shape: **hook → one beat per point → statement → close → recap card.** The hook is already a point; never open with "look closely". Reels and LinkedIn end on a recap card (the screenshot with every point pinned and numbered); Stories and X threads post that card as a separate item.

## Output

In `videos/<slug>/` (a HyperFrames project):
- `renders/post/`: every upload, named by platform: four videos, covers, recap cards, the original screenshot.
- `renders/post/POSTING.md`: steps, captions, alt text, stickers and first comment for each platform.
- `beats.json` plus the generated compositions, editable in HyperFrames Studio. Regenerate from `beats.json` rather than editing HTML by hand.

## Workflow

Copy this checklist into your reply and tick it off:

```
- [ ] 1. Read the screenshot, pick 3–5 points, confirm with the owner
- [ ] 2. Write beats.json and measure coordinates
- [ ] 3. Check the master and look at snapshots
- [ ] 4. Run the pipeline (music, beat-sync, renders, finish)
- [ ] 5. Write POSTING.md and hand over
```

### 1. Read the screenshot like an editor

View it at full size; for large images run `python scripts/grid_overlay.py <shot> <dir>` and crop regions. Note the regions (which pane belongs to which project), verbatim lines worth quoting (the owner's prompts, the agent's key sentences, numbers on screen) and the **points**: what a smart outsider should notice. See [story-craft.md](references/story-craft.md) for point types.

Keep only points that make the owner's theme land harder. Cut incidental status (lint or warning counts, badges, versions, timestamps, file names) unless the theme is about it. More than 5 points dilutes the piece.

Then, briefly, ask only what the screenshot can't tell you: project names and what's public, which points matter most, anything private to blur. If the owner already named their points, use them and add at most one of yours, flagged as a suggestion.

### 2. Write `beats.json`

Start from [assets/example-beats.json](assets/example-beats.json), a finished piece in the current style. The schema, beat types and layouts are in [config-schema.md](references/config-schema.md); read the "Copy: translate, don't transcribe" section of [story-craft.md](references/story-craft.md) before writing copy. Rules that matter most:

- Mostly `point` beats: a 2–6 word bold headline plus one everyday sentence. Type auto-fits the free space, so fewer words means bigger type.
- No file names, URLs, IDs or field lists on screen unless they are the surprise.
- Quotes are verbatim from the screenshot (trim with "…"). Takeaways are in the owner's voice: first person, plain, unhyped.
- No claim the screenshot or the owner doesn't support.
- Leave out `dur`: pacing comes from reading time. Feed videos stay at 59 s or less unless `"allow_long": true` is genuinely needed.
- Set `"energy"` (`calm`, `lively`, `punchy`) from the owner's tone; it drives camera speed and the music mood. See [music.md](references/music.md).

**Measure coordinates; don't guess.** Estimate each rect on the grid, then confirm with a crop: `python scripts/grid_overlay.py <shot> <dir> x y w h`. A highlight 20 px off looks sloppy once zoomed. Each beat's `"focus": [x, y, w, h]` frames the camera; the generator handles zoom (max 1.6×) and pan.

### 3. Check the master

```bash
npx hyperframes init videos/<slug> --non-interactive --example=blank --skill=general-video
# copy the screenshot into videos/<slug>/assets/img/ and write beats.json there
python <skill>/scripts/run_pipeline.py videos/<slug> --check-only
cd videos/<slug> && npx hyperframes snapshot --at <midpoint of each beat> --no-end
```

The build prints each beat's duration; snapshot each midpoint. Look at the sheet and confirm: highlights hug their text, no text overflows, every camera framing shows the line being discussed, and text sits beside the screenshot, not on it. To snapshot a 9:16 or recap variant, build it with `python <skill>/scripts/build_composition.py beats.json . --preview reel|story|recap`, then rerun the pipeline afterwards. Fix and repeat until the sheet is clean.

This skill is the brief, so skip the `/hyperframes` intent interview and storyboard. Load `/hyperframes-core` only to change generated HTML by hand.

### 4. Run the pipeline

Start the music early: MusicGen on CPU takes minutes. Run `python <skill>/scripts/make_music.py videos/<slug> --seed-only` in the background once `beats.json` has its `energy`. If HeyGen is signed in (`npx hyperframes auth status`) or the owner has a track, prefer that (see music.md). Then:

```bash
python <skill>/scripts/run_pipeline.py videos/<slug>
```

It builds all variants, trims the music to length, snaps scene changes to the beat, renders four videos and runs `finish.py` (-14 LUFS, stills, platform file names). It stops at the first failure with the fix. Afterwards, check the first second of each video (it must already point at something) and the recap card.

### 5. Write the playbook and hand over

Write `renders/post/POSTING.md` from [platforms.md](references/platforms.md), using this piece's captions, durations and alt text; count X characters. When the owner is present, open `npx hyperframes preview --background` so they can make small edits. Tell them:
- the post folder and the playbook
- the posting order
- each caption, ready to paste
- what you decided for them: music source and mood, points you cut, privacy calls

Say that you can't listen to the music, and flag anything that reveals unreleased details.

## Examples

**Owner names the points.** "Two Claude Code sessions: the AI Leela pipeline pivot and my novel's beta-reader skill. People should notice the parallel projects, the reasoning, my own prompt, and the agent acting as a reader." → no re-asking; one beat per named point, in their order; `calm` energy; quote the owner's prompt verbatim; recap card with four pins.

**Owner gives a theme only.** "Opus drove HeyGen's video editor, pleasant surprise, feels Pau Pau Powerful." → pick the 3–4 points that prove the theme (it's an editor, four formats, a real timeline, a box for the agent) and skip the lint badge; `punchy` energy; statement "I didn't know HeyGen had this."; close on the owner's own words. This is the bundled example.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `check` or `snapshot` complains about several root compositions | Variant files sit next to `index.html` | Build with `--master-only` or `--preview`; `run_pipeline.py --check-only` already does |
| "WARNING: the video runs 6x s" | Too many points or long copy | Cut the weakest point or tighten headlines; set `allow_long` only when the message needs it |
| "reusing assets/bgm/seed.wav with no record of its mood" | An old seed survived a mood change | Rerun `make_music.py <proj> --fresh`, or `--from-seed` if it's the owner's track |
| "MusicGen needs torch" | Offline music packages missing | `pip install torch transformers soundfile numpy`, or supply a track with `--from-seed` |
| "missing SFX" | media-use skill not installed | `npx hyperframes skills update media-use`; the video still renders without clicks |
| Headline comes out small (< 56 px) | Too many words for the zone | Cut words; never shrink type by hand |
| Edits made in Studio vanish | The pipeline regenerates HTML from `beats.json` | Put changes in `beats.json`, or stop using the pipeline for that project |

## Notes

- Staging rotates the screenshot between `center`, `split` and `low`, with a spotlight on each beat's first highlight. Words go in the free space beside the screenshot; `overlay` (words on the image) is used only for portrait screenshots that fill the frame.
- Set `palette.accent` to a colour from the screenshot when it suits the subject; highlights, markers and pins derive from it.
- Feeds autoplay muted, so the on-screen words carry the story and the music sets the energy. Skip voiceover unless asked; it breaks the "peek" feeling.
- 4:5 (1080×1350) is the safest feed format. 9:16 variants offset the stage 240 px down to clear the Reels interface.
