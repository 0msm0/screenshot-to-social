# Story craft: finding what's worth noticing

## Why this works

People scroll past polished promos. They stop for a real artefact: a messy terminal, a half-finished doc. The screenshot is the evidence, and the video's job is to point at it directly and make each point land, not to replace it. Don't make viewers hunt for the points first; owners want the points made, and feeds decide in the first second. Every beat should answer "where on the screenshot is that?", and the camera should show exactly that spot.

## Point types

Scan the screenshot for these. Most good screenshots hold three to five.

| Type | What it looks like on screen | Example takeaway |
| --- | --- | --- |
| **Parallelism** | several panes, tabs or sessions; agent counts; background jobs | "Both moving at once. *Four agents each.*" |
| **Human steering** | the owner's own prompt, especially a question, a doubt or a correction | "Sometimes the best prompt is *a doubt.*" |
| **Reasoning** | the agent explaining *why*, finding a flaw, weighing trade-offs, a table it designed | "It didn't just agree. *It found why.*" |
| **Redesign or output** | a schema, plan, diff, table or result that came out of the exchange | "One doubt. *Three clean layers.*" |
| **Honesty** | caveats, "not tested yet", stubs, failing checks, limits stated plainly | "It tells me what it *hasn't* tested." |
| **Role or persona** | the agent acting as someone (reviewer, reader, critic, user) | "Three simulated readers. *None of them see my notes.*" |
| **The catch** | a bug, plot hole, inconsistency or regression found before a human saw it | "A plot hole, caught *before any real reader saw it.*" |
| **Scale or speed** | test counts, file counts, time stamps, "+104 lines" | use sparingly, and only with a number that's on screen |

### Pick only what matters

A screenshot always holds more than the story needs. For every candidate beat ask: *does this make the owner's theme land harder?* If not, cut it, however true or visible it is.

- Cut incidental status: lint or warning counts, error badges, version numbers, timestamps, ports, file names, unread counts. They pull attention to housekeeping, and viewers may read them as problems. Keep one only when the theme is about it (a post about fixing a failing build can show the red badge).
- Cut filler that merely confirms what an earlier beat already showed.
- Fewer, stronger beats beat a complete inventory. Four sharp points in 35 s outperform six in 50 s.

Example: in the HyperFrames trial the theme was "a pleasant surprise: HeyGen has an agentic editor and Opus can drive it". A "Lint: 97" beat was accurate but off-theme, so it was cut.

Prefer points that teach something transferable, such as "a doubt makes a good prompt" or "give the agent a persona", over ones that only brag.

When the owner names what they want noticed, those become the beats, in their order of importance. Add at most one of your own and say it was your addition.

## Beat recipe

- **Hook (3–3.5 s):** already a point, not a teaser. Three short lines; the last one in the accent colour carries the twist ("Two terminals. Two projects. *One of me.*"). The screenshot is visible from the first frame and all hook lines land within about 1 s (the generator handles that), so a scroller who stops for one second already has the first point. The camera starts slightly pushed in, then eases out to the full screenshot.
- **Point beats (4–6.5 s each):**
  - a kicker naming the point ("It reasons", "It plays a role")
  - usually a `point`: a plain headline plus one everyday sentence (see Copy below)
  - a verbatim `quote` only when the exact words are the point, and `rows` only for a few human-readable parallel items
  - the punch phrase in `*accent*`

  The camera moves to the region, and a highlight box draws on the exact lines.
- **Staging:** move the screenshot, not just the camera inside it. Most points sit large in the centre of the frame, with the words above and the evidence below. Every third point switches to the split layout (screenshot up top, words below), which gives a reading beat. The spotlight dims everything except the highlighted part. The panel's glide between positions is what catches a scrolling eye, so don't hold one layout for the whole video.
- **Statement (optional, 3–4 s, at most one):** big words in the open space above the screenshot, which drops low, for the owner's reaction or a turn ("I didn't know HeyGen had this.").
- **Close (5–5.5 s):** a two-line thesis ("Not autopilot. *A collaboration.*") plus one quiet line about what's next, only if the owner wants to tease something. The camera pulls back to the full screenshot, which stays sharp below the words.
- **Total:** 30–50 s for 3–5 points, set by reading time; 59 s is the ceiling for feeds. Shorter than ~30 s can't hold several points.

## Copy: translate, don't transcribe

This matters more than any animation. The viewer is a smart stranger scrolling on a phone, and they don't know the tool. Each beat should say **what this is, or why it matters**, in words a friend would use if you showed them your screen over your shoulder.

- **Default to `point` beats:** a plain headline plus one everyday sentence. The spotlight on the screenshot is the evidence, so the words don't need to repeat what's visible.
- **Translate identifiers into meaning.** Don't put file names, URLs, paths, track names, IDs, timestamps or version strings on screen unless that exact detail is the surprise. Fix "`index`, `linkedin-4x5`, `9x16`" as "One project. Four formats."
- **Quote only words that carry the point by themselves:** the owner's own prompt, a sharp sentence from the agent, or a UI label that is the punchline ("Describe a change to the agent"). If the quote needs explaining, write the explanation instead.
- **Use rows only for a few parallel things a non-expert would recognise,** with human labels (Page-Turner / Critic / Skeptic). Never use rows to list technical fields.
- **Headlines are plain statements, not puns.** "A real timeline." beats "It's code, on a timeline I can touch." Save the clever phrasing for one or two beats at most.
- **Short sentences and fragments,** like speech: "A video editor. Running on localhost. On my machine."

Lessons from the HyperFrames trial, where the plain version won:

| Transcribed (weaker) | Translated (stronger) |
| --- | --- |
| rows: `index` → "the master, index.html", `linkedin-4x5` → "the feed cut" | **One project. Four formats.** / "16:9, 4:5, reel, story. Opus built all four." |
| quote: "localhost:3002/#project/behind-the-terminal" | **This is HeyGen HyperFrames Studio.** / "A video editor. Running on localhost. On my machine." |
| rows: "Tracks: Rec · Dots · Dot 1 · Dot 2", "Length: 00:46 / 00:46" | **A real timeline.** / "Tracks, keyframes, effects. Every layer is code the agent wrote." |

## Type and pacing

- **Big and bold wherever there's room.** The default `bold` style uses heavy display type, and the generator auto-fits every headline to its empty space. Thin or small type disappears while the panel and camera move. Keep headlines to 2–6 words so they come out large; use the `editorial` serif only for calm, quiet pieces.
- **Read time sets the pace.** Leave beat durations out and the generator sizes each beat for about 3 words a second, plus the entrance and a short hold. Don't speed beats up to look energetic, because unreadable is worse than slow. Don't let a beat linger past its read either.
- **Length:** 59 s or less for feed posts. Short messages (3–4 points) usually land at 30–45 s. Go past 59 s only when the message genuinely needs it (`"allow_long": true`), and say so in the hand-over. If you're over 59 s, cut the weakest point before tightening every beat.
- **Energy** (`calm` / `lively` / `punchy`) follows the owner's theme. It sets camera speed, the impact hits and the music mood (see `music.md`).

## Voice

- Two voices, on purpose: **monospace is the machine** (quotes, labels, kickers), and **serif italic is the person** (takeaways, hook, close). Keep them separate; the contrast is part of the message.
- First person, plain, slightly wry. Use no hype words ("revolutionary", "game-changer", "insane"), and keep exclamation marks out of the video.
- Quotes are verbatim. Trim with "…" and mark highlights with `[[…]]` or strikes with `~~…~~`, but never change the words.
- Takeaways should be true from the screenshot alone. If a claim needs context the screenshot doesn't show, it belongs in the caption, not the video.
- The owner's own stated reaction or theme ("Feels Pau Pau Powerful", "I didn't know it could do this") is fair game for the hook and close. It's their voice, not a factual claim, so use their words.
- Match the energy of the owner's theme. A wry observation suits the calm default. An excited theme wants a punchier hook and close: shorter lines, the owner's exclamation verbatim, and the payoff word alone on the accent line.

## Privacy pass (before building)

Check for, and ask about anything you find:
- personal names or emails
- client or company names
- API keys, tokens, URLs with IDs
- unreleased story details
- file paths with usernames

Blur or skip these. Quoting a character or project name in a public post is the owner's call, so flag it in the hand-over.
