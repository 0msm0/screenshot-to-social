# Music: choosing, shaping and syncing the bed

Feeds autoplay muted, so the words carry the story. Music is for the people who unmute, and its job is to set the energy of the owner's theme. Pick it deliberately, never by default.

## 1. Choose the mood from the theme

Read the owner's own words for energy, and match the music to that, not to the subject.

| Owner's theme sounds like | `energy` | Music mood (`make_music.py --mood`) | Tempo | Feel |
| --- | --- | --- | --- | --- |
| A quiet observation, a reflection, "here's how I work" | `calm` | `calm`: lo-fi rhodes, soft pads, brushed beat | 80–92 BPM | thoughtful, unhurried |
| Pleased, curious, "this is neat" | `lively` | `lively`: bright pop electronics, pluck arpeggio | 100–112 BPM | optimistic, moving |
| Excited, surprised, "this is powerful", exclamation marks | `punchy` | `punchy`: driving electronic, four on the floor, synth bass | 118–126 BPM | confident, big |
| Personal, emotional, a milestone | `calm` | `reflective`: sparse piano and strings | 68–76 BPM | warm, intimate |
| A reveal or a tension-and-release story | `lively` | `cinematic`: pulsing ostinato, low strings | 95–105 BPM | building |
| Light-hearted, a funny catch | `lively` | `playful`: pizzicato, marimba, bounce | 108–116 BPM | cheeky |

Set `"energy"` in beats.json. The music mood follows it unless you set `"music": {"mood": "..."}` or a custom `"prompt"`. Energy also tunes the visuals: `punchy` makes camera moves faster and adds a bass impact on the statement and close, while `calm` keeps everything unhurried.

Example: "Feels Pau Pau Powerful…" is surprise and excitement, so it's `punchy`. A screenshot of a careful refactor with "quietly proud of this one" is `calm`.

## 2. Shape it to the edit

- **Start at frame 1.** Use a 0.25 s fade-in, never a slow build; the first second decides the scroll. When a library track opens quietly, trim from its first strong section instead.
- **Land the end.** Use a 2.5–3 s fade-out that finishes exactly on the last frame. Don't let the music cut mid-phrase or keep going into silence.
- **Lift at the turn.** A `statement` or close beat should feel like a moment. With `punchy` energy, the impact hit sits on it.
- **One bed per video.** Don't change tracks mid-video; scene changes come from the cuts and the panel moving.
- **Keep it under the words.** Use no vocals, ever, because lyrics compete with on-screen text, and keep the melody simple.

## 3. Sync scene changes to the beat

`scripts/run_pipeline.py` does this for you: it trims the bed, runs `npx hyperframes beats` to detect the beat grid, rebuilds so each scene change moves onto the strongest music beat within ±0.35 s (never leaving a beat shorter than 2.5 s), and re-trims the bed to the new length. The camera glide and the whoosh then land on the music. Set `"snap_to_music": false` for a free-time ambient bed with no clear beat.

## 4. Mix

- The bed is normalized to about -18 LUFS before the mix, and `finish.py` brings the final videos to -14 LUFS, the social standard.
- SFX (whooshes, clicks, pops, typing) sit around 0.3–0.55 volume. They mark actions; they aren't music.
- There's no voiceover, so there's no ducking. If the owner adds a voice, carve the bed under it with `/hyperframes-audio`.

## 5. Sourcing and rights

Prefer these, in order:
1. **A track the owner owns or has licensed.** Save it as `assets/bgm/seed.wav` and run `make_music.py --from-seed`.
2. **The HeyGen music library**, when `npx hyperframes auth status` is signed in (`/media-use` resolve `--type bgm` with a mood query).
3. **Offline MusicGen** (`make_music.py`), which is always available but plainer. It generates once per prompt, and `seed.json` records which prompt made it.

Never use a commercial song the owner doesn't have rights to. Feeds can mute or take down the post.

**Platform music:** an Instagram Reel can add a trending track in the app *on top of* this bed at low volume, which can help reach. Keep the original audio, because the clicks, typing and whooshes carry the edit. Use X and LinkedIn as uploaded.

## 6. Check before you hand over

- The music is audible within the first 0.5 s, so there's no dead air at the start.
- It ends in the last 0.3 s, not before.
- Integrated loudness is about -14 LUFS (`finish.py` prints it).
- Snap points line up: spot-check two scene changes in the render against the beat file.
- The mood matches the theme. If an excited theme sits on a sleepy lo-fi bed, change `energy` or `--mood`.

MusicGen can't be listened to inside an agent run. Say so in the hand-over, and tell the owner the mood, the tempo and how to swap the track.
