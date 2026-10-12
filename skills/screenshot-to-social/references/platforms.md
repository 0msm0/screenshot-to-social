# Platforms: what to post where, and the playbook template

`finish.py` names the files in `renders/post/`:

| File | Size | Used for |
| --- | --- | --- |
| `instagram-reel_9x16.mp4` | 1080×1920, video + recap card | Instagram Reel (also fits TikTok and YouTube Shorts) |
| `instagram-story-2-video_9x16.mp4` | 1080×1920, video only | Story frame 1 |
| `recap-card_9x16.png` | 1080×1920 | Story frame 2 |
| `cover_9x16.png` | 1080×1920 | Reel cover (the hook, already pointing at the work) |
| `linkedin-video_4x5.mp4` | 1080×1350, video + recap card | LinkedIn native video |
| `cover_4x5.png` | 1080×1350 | LinkedIn thumbnail |
| `x-2-video_4x5.mp4` | 1080×1350, video only | X post 1 |
| `recap-card_4x5.png` | 1080×1350 | X post 2; LinkedIn first comment |
| `original-screenshot.*` | native | X post 2 (second image), for zooming in |

All audio is normalized to -14 LUFS. Videos stay under 60 s, so they fit a single Story segment and play fully on X and LinkedIn.

## The flow on each platform

Every platform opens on the points themselves, never on a "can you spot it?" prompt. Make the points first, then recap them.

- **Instagram Reel:** one file, so the recap card is built into the end of the video. Reels loop, and the loop goes from the recap straight back into the hook.
- **Instagram Story:** the video first, then the recap card as its own frame, with a Poll or Question sticker asking which point surprised people most. The last frame shares the Reel.
- **X:** a 2-post thread. Post 1 is the video, with the points written out in the text. Post 2 is the recap card plus the full-resolution original, for people who want to zoom in.
- **LinkedIn:** one native video per post (the recap version), with the cover frame as its thumbnail and the recap card in the first comment. Links go in comments, never the body.

## Caption guidance

- Lead with the strongest point or the owner's reaction ("Didn't know HeyGen had a full video editor. Even less that Opus could drive it."). Don't open with "look closely" or "what do you notice?".
- Briefly name what's on screen: which projects, which tool.
- Write it as a short personal note, not a feature list. Use first person and plain words, in the same register as the video's headlines. Fold the points into a few short lines or sentences. A plain numbered list is fine for the recap (X post 2, the LinkedIn body), but every item must read like speech ("One project, four formats, all written by the agent"), never like an inventory. Leave out arrow bullets, file names, paths and code identifiers.
- Close with the thesis line from the video, plus the tease only if the owner wants one.
- **Instagram:** up to about 2,200 characters. Use 5–8 hashtags at the end. Pin a comment that invites a reaction ("Which of these surprised you most?").
- **X:** each post is 280 characters or fewer. Count them, including spaces and arrows. Use no hashtags, or one at most.
- **LinkedIn:** the first ~210 characters show before "…see more", so the first two lines carry the strongest point. Use 3–5 hashtags at the end. Write in a reflective first person, with one concrete detail per point.
- Every claim in a caption must be true from the screenshot or something the owner told you.
- Alt text is for people who can't see the image, so describe what's visible in plain words ("HeyGen HyperFrames Studio open in a browser: a list of video formats, a preview, a timeline and a box for asking the agent for changes"). A visible name or label may appear when it helps; skip raw paths and IDs.

## POSTING.md template

Write this into `renders/post/POSTING.md`, filled in with this piece's captions and alt text.

```markdown
# Posting playbook: <title>

<one line: the points this piece makes>

| File | Use |  (table of the files above)

Suggested order: Instagram Reel → Instagram Story (right after) → X thread → LinkedIn (same day or the next working morning). Post at the times your own analytics show your audience is most active.

## 1. Instagram Reel
1. + → Reel → instagram-reel_9x16.mp4. Don't trim it, and don't add text or stickers: everything is inside the safe zones already.
2. Keep the original audio. A trending track can sit underneath at low volume, but don't replace the original.
3. Edit cover → Add from camera roll → cover_9x16.png.
4. Paste the caption. Add alt text in Advanced settings → Accessibility.
5. Share, then pin a comment: "Which of these surprised you most?"
<caption>

## 2. Instagram Story (3 frames)
1. instagram-story-2-video_9x16.mp4. Keep the middle clear; optionally add a small text at the top.
2. recap-card_9x16.png + a Poll sticker in the lower third ("Which surprised you most?" with two of the points) or a Question sticker.
3. Share the Reel to your story: "Full reel ↓". Optionally save the frames as a Highlight.

## 3. X thread
Post 1: x-2-video_4x5.mp4 (alt text). <text: the strongest point first, then the rest briefly>
Post 2 (reply): recap-card_4x5.png + original-screenshot (alt text on both). <numbered points + thesis>

## 4. LinkedIn
1. Upload linkedin-video_4x5.mp4 natively (not a link).
2. On desktop: edit the video → Thumbnail → cover_4x5.png.
3. Paste the caption. Keep links out of the body.
4. First comment: recap-card_4x5.png + "The points in one picture, plus the original screenshot below if you want to zoom in."
<caption>

## After posting (first hour)
Reply to early comments, share the Story poll result, and note which platform got the most saves or shares, so the next post follows that format.
```

## Other destinations (when asked)

- **TikTok / YouTube Shorts:** reuse `instagram-reel_9x16.mp4`. Add on-platform captions, and on TikTok use the in-app text for the hook.
- **Threads / Bluesky:** follow the X thread pattern. Threads allows 500 characters per post.
- **Square feed (1:1):** add a variant to `build_composition.py` (1080×1080, stage scaled 0.8). Rarely needed now, since 4:5 is accepted everywhere.
