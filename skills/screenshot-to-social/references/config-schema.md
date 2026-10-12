# beats.json schema

`assets/example-beats.json` is a complete, working example; copy it and edit.

```jsonc
{
  "title": "Behind the Terminal",            // <title> only
  "screenshot": "assets/img/shot.png",       // path inside the project
  "shot_w": 1842, "shot_h": 989,             // real pixel size of the screenshot
  "alt": "Two Claude Code sessions side by side",
  "topbar": "Behind the screen",             // small label, top left
  "palette": { "bg": "#15110e", "paper": "#f2ece4", "muted": "#b3a89c",
               "accent": "#e58a66", "accent_deep": "#e07a55",
               "monitor_bg": "#1e1e1e" },   // optional; default is warm clay on near-black. Highlights, markers, pins and glow derive from accent
  "style": "bold",                           // "bold" (default: heavy display type, readable in motion) or "editorial" (quiet serif)
  "energy": "calm",                          // "calm" | "lively" | "punchy": camera speed, impact hits, default music mood (references/music.md)
  "music": { "mood": "punchy" },             // optional; or { "prompt": "..." } for a custom MusicGen prompt
  "snap_to_music": true,                     // scene changes snap to strong music beats once `npx hyperframes beats` has run
  "allow_long": false,                       // the generator warns above 59 s unless this is true
  "music_volume": 0.85,                      // optional
  "beats": [ ... ],
  "bookends": { "outro": {...} }             // optional; adds the recap card (Reel + LinkedIn variants)
}
```

## Beat types

Every beat has `type`, `camera` and optionally `dur` (seconds). **Leave `dur` out**: it is then set automatically from reading time (about 3 words a second, plus entrance and a short hold, clamped per type). Only set it to hold a moment on purpose. The `camera` field takes (`"full"`, `{"focus": [x, y, w, h]}`, or an explicit `{"s", "cx", "cy"}`). A `focus` rect wider than the frame (a timeline, a toolbar) zooms to its height and crops the sides, so it never falls back to the whole screenshot. The optional screenshot overlays, all in screenshot pixels, are:
- `highlights: [[x, y, w, h], ...]`: accent-coloured boxes that draw on and fade before the beat ends. The first box of each beat is a **spotlight**: it dims everything else on the screenshot. Set `"spotlight": false` on the beat to turn that off.
- `zones: [{"rect": [x, y, w, h], "label": "AI LEELA"}]`: dashed region plus a pill label (good on `"full"` beats).
- `rings: [[x, y, w, h], ...]`: ellipses around small items such as status chips.

| type | fields | notes |
| --- | --- | --- |
| `hook` | `kicker`, `lines[]`, `accent_line` | First beat. No number. 2–3 lines, each 15 characters or fewer |
| `point` | `kicker`, `take`, `sub` | **The default beat.** `take` is the plain headline (6 words or fewer is ideal), and `sub` is one everyday sentence that explains it (fragments are fine). There's no evidence panel; the spotlight on the screenshot is the evidence |
| `rows` | `kicker`, `rows: [[label, text], ...]`, `take`, `sub` | 2–3 rows. Label 12 characters or fewer, text 45 or fewer. `*accent*` works in text |
| `quote` | `kicker`, `who`, `quote`, `take`, `sub`, `typed` | `typed: true` types the quote out (use for the owner's own prompt; no marks). Otherwise `[[highlight]]` and `~~strike~~` animate in order |
| `statement` | `kicker` (optional), `lines[]`, `accent_line`, `sub` | An unnumbered emphasis beat: big words above the screenshot (the owner's reaction, a turn). Use at most one, usually just before the close |
| `close` | `lines[]`, `accent_line`, `sub` | Last beat. Big words above the screenshot, then a fade to the background colour |

`sub` works on `point`, `rows` and `quote` beats, and lands after the evidence. Numbered beats (everything except hook, statement and close) get `01`, `02`… kickers and a progress dot each.

### Layout: where the screenshot sits

Each beat can set `"layout"`. The screenshot panel glides between positions at each beat change, and that movement is part of what holds attention, so vary it.

| layout | screenshot | words | default for |
| --- | --- | --- | --- |
| `center` | large (1.06×), in the middle of the frame | kicker + take above it, evidence (quote/rows) below | most numbered beats |
| `split` | top of the frame | everything in the panel below | the hook, and every third numbered beat (a reading beat) |
| `low` | drops to the bottom of the frame, full brightness | big words in the open space above it | `statement` and `close` (landscape screenshots) |
| `overlay` | centred and dimmed | big words on top of it | `statement` and `close`, only when the screenshot is portrait |

**Words go beside the screenshot, not on it.** A landscape (16:9) screenshot leaves a lot of free space above and below the panel, so every layout except `overlay` puts the text there and the screenshot stays fully readable. Use `overlay` only when the screenshot is portrait and fills the frame, so there's no free space left; the generator picks it automatically in that case. Don't set `overlay` by hand on a landscape shot.

Leave `layout` out to get that rotation. Override it when a beat's evidence is long (use `split`, which has the most room) or when a point is a single punch (use `center` with a short take).

## Type size is automatic

The generator measures the real font and sizes each headline, sub-line and hook to the largest size that fits its zone: up to 120 px for headlines, 56 px for sub-lines and 150 px for hook and statement lines. Short words therefore come out huge, and empty space becomes big type. You control size through the word count: fewer words, bigger type. If something comes out small (under about 56 px for a headline), cut words rather than squeezing.

## Layout limits (1080×1350 stage, 60 px gutters)

Type size is automatic, so the limits are about word counts:
- **take (headline):** 2–6 words; it comes out 78–120 px. Above about 45 characters it drops toward the 48 px floor.
- **sub:** one sentence, 70 characters or fewer.
- **quote:** 140 characters or fewer in `split`, 100 in `center` (the evidence zone below the screenshot is about 280 px).
- **rows:** 2–3; with a fourth, the take no longer fits.
- **hook, statement, close lines:** about 15 characters per line, 2–3 lines plus the accent line.

If the snapshot shows overflow or a small headline, cut words rather than shrinking the type. Feed viewers read on phones.

## Bookends (recap)

```jsonc
"outro": { "dur": 5.0, "kicker": "What you just saw", "sub": "Not autopilot. A collaboration.",
           "items": [ { "text": "Two projects, moving in parallel",
                        "boxes": [[x, y, w, h], ...],          // outlined on the screenshot
                        "pins": [[x, y], ...] } ] }            // optional; defaults to each box's top-right
```
Use 3–5 recap items, each 45 characters or fewer, in the same order as the numbered beats. The video never opens on an "intro" card, because the hook already points at the work. An `"intro"` bookend (`kicker`, `title`, `accent`, `sub`, `dur`) is still supported for the rare piece that is genuinely a puzzle, but leave it out by default.

## Timing that the generator derives

The generator places each beat after the previous one, with camera legs about 0.1 s before each beat. Typing runs at about 22 ms per character (0.8–2 s). Marks start 1.1 s into a beat, 0.65 s apart. The take lands after the last mark or the typing. It also places SFX automatically: a whoosh at each beat change, typing and a key press, a click per mark or ring, a pop per row, and a chime on the close. `variants.json` records the final durations for `make_music.py` and `finish.py`.
