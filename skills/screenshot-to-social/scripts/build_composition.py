#!/usr/bin/env python3
"""Generate a HyperFrames "behind the screen" composition and its platform variants
from a beats config (see references/config-schema.md).

Usage:
  python build_composition.py <beats.json> <project_dir>                 # all variants (for rendering)
  python build_composition.py <beats.json> <project_dir> --master-only   # index.html only (for check/snapshot)
  python build_composition.py <beats.json> <project_dir> --preview reel  # a variant AS index.html (to snapshot it)

`hyperframes check` and `snapshot` accept one root composition per folder, so iterate with
--master-only / --preview, then rebuild without flags right before `hyperframes render -c <file>`.

Writes into <project_dir>:
  index.html       4:5  1080x1350  the video alone (master; X)
  story-9x16.html  9:16 1080x1920  the video alone, reframed for Stories
  recap-4x5.html   4:5  1080x1350  video + recap card outro (LinkedIn)      [when bookends.outro is set]
  reel-9x16.html   9:16 1080x1920  video + recap card outro (Reels)         [when bookends.outro is set]
  variants.json    durations and timings consumed by make_music.py and finish.py
Placeholder silent music is written if assets/bgm/*.wav is missing, so checks work before the music exists.
Also copies fonts and the SFX it uses into <project_dir>/assets.
"""
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SFX_SRC = Path.home() / ".claude" / "skills" / "media-use" / "audio" / "assets" / "sfx"
SFX_DUR = {"whoosh-short": 0.57, "pop": 0.7, "click-soft": 0.36, "typing": 1.54, "key-press": 0.43, "chime": 2.5, "impact-bass-1": 2.12}

STAGE_W, STAGE_H = 1080, 1350
MON_X, MON_Y, MON_W, MON_H = 60, 124, 960, 560
MAX_ZOOM = 1.6  # raster screenshots soften beyond this

# Monitor poses per layout: (y offset from the split position, scale, monitor opacity).
# split   = screenshot top, words below (reading beats)
# center  = screenshot large in the middle, words above and evidence below (the default for points)
# low     = screenshot drops to the bottom, big words in the open space above it (emphasis, close)
# overlay = screenshot centred and dimmed, big words on top of it. Only for portrait screenshots,
#           which fill the frame and leave no free space; a landscape shot always leaves room for the words.
POSES = {"split": (0, 1.0, 1.0), "center": (271, 1.06, 1.0), "low": (606, 1.0, 1.0), "overlay": (271, 1.06, 0.2)}


FONTS = SKILL / "assets" / "fonts"
STYLES = {
    # bold (default): heavy display type that stays readable while the frame moves
    "bold": {"display": '"Archivo Black", sans-serif', "dstyle": "normal", "dfile": "ArchivoBlack-Regular.ttf",
             "sub": '"JetBrains Mono", monospace', "subw": 700, "subfile": ("JetBrainsMono-wght.ttf", 700), "track": "-0.015em"},
    # editorial: the quieter serif look
    "editorial": {"display": '"Instrument Serif", serif', "dstyle": "italic", "dfile": "InstrumentSerif-Italic.ttf",
                  "sub": '"Instrument Serif", serif', "subw": 400, "subfile": ("InstrumentSerif-Regular.ttf", None), "track": "-0.01em"},
}
STYLE = STYLES["bold"]
TEXT_W = 960 * 0.94  # browser wrapping differs slightly from PIL; keep a margin
_font_cache = {}


def _font(fname, size, weight=None):
    from PIL import ImageFont
    key = (fname, size, weight)
    if key not in _font_cache:
        f = ImageFont.truetype(str(FONTS / fname), size)
        if weight:
            f.set_variation_by_axes([weight])
        _font_cache[key] = f
    return _font_cache[key]


def _plain(t):
    return re.sub(r"\*|\[\[|\]\]|~~", "", t)


def fit(text, fname, box_h, max_px, min_px, lh, weight=None, hard_lines=None, box_w=TEXT_W):
    """Largest font size (px) at which the text fits box_w x box_h. hard_lines keeps authored line breaks."""
    for size in range(int(max_px), int(min_px) - 1, -2):
        f = _font(fname, size, weight)
        if hard_lines is not None:
            if max(f.getlength(_plain(l)) for l in hard_lines) > box_w:
                continue
            n = len(hard_lines)
        else:
            lines, cur, ok = 1, "", True
            for w in _plain(text).split():
                trial = (cur + " " + w).strip()
                if f.getlength(trial) <= box_w:
                    cur = trial
                elif f.getlength(w) > box_w:
                    ok = False
                    break
                else:
                    lines, cur = lines + 1, w
            if not ok:
                continue
            n = lines
        if n * size * lh <= box_h:
            return size
    return int(min_px)


def evidence_height(b):
    if b["type"] == "quote":
        q = _plain(b.get("quote", ""))
        lines = max(1, -(-len(q) // int(896 / (32 * 0.6))))
        return (34 if b.get("who") else 0) + lines * 48 + 52
    if b["type"] == "rows":
        return len(b["rows"]) * 58
    return 0


def type_sizes(b):
    """Font sizes that fill the empty space of this beat's layout (big words wherever there is room)."""
    lay, t = b["layout"], b["type"]
    dfile = STYLE["dfile"]
    sfile, sw = STYLE["subfile"]
    out = {}
    if t in ("hook", "statement", "close"):
        lines = list(b.get("lines", [])) + ([b["accent_line"]] if b.get("accent_line") else [])
        has_sub = bool(b.get("sub"))
        if lay == "split":
            box_h = 546 - (68 if b.get("kicker") else 0) - (110 if has_sub else 0)
        elif lay == "low":
            box_h = 560 - (68 if b.get("kicker") else 0) - (110 if has_sub else 0)
        else:
            box_h = 600 - (110 if has_sub else 0)
        out["big"] = fit("", dfile, box_h, 150, 64, 1.0, hard_lines=lines)
        return out
    ev = evidence_height(b)
    if lay == "center":
        take_h = 188
        sub_h = 286 - (ev + 16 if ev else 0)
    else:
        remaining = 546 - 68 - (ev + 28 if ev else 0)
        if b.get("sub"):
            take_h, sub_h = remaining * 0.6 - 14, remaining * 0.4 - 14
        else:
            take_h, sub_h = remaining, 0
    if b.get("take"):
        out["take"] = fit(b["take"], dfile, take_h, 120, 48, 1.04)
    if b.get("sub"):
        out["sub"] = fit(b["sub"], sfile, max(60, sub_h), 56, 28, 1.3, weight=sw)
    return out


def auto_duration(b, energy):
    """Long enough to read on a phone and no longer: ~3 words a second, plus entrance and a short hold."""
    text = " ".join(filter(None, [b.get("take"), b.get("sub"), b.get("quote"), b.get("accent_line")]
                         + list(b.get("lines", [])) + [" ".join(r) for r in b.get("rows", [])]))
    words = len(re.findall(r"[\w']+", _plain(text)))
    d = 1.1 + words / 3.0 + 0.7
    if b.get("typed"):
        d += min(2.0, max(0.8, len(b.get("quote", "")) * 0.022)) + 0.3
    d += 0.4 * len(re.findall(r"\[\[|~~", b.get("quote", "")))
    lo, hi = {"hook": (3.0, 4.0), "statement": (2.8, 4.0), "close": (4.0, 5.5), "point": (3.5, 6.0),
              "quote": (4.5, 7.5), "rows": (4.5, 7.0)}.get(b["type"], (3.5, 6.5))
    if energy == "punchy":
        d *= 0.9
    return round(max(lo, min(hi, d)) * 2) / 2


def snap_to_beats(beats, grid):
    """Move each scene change onto the strongest nearby music beat (within 0.35 s)."""
    strong = [g for g in grid if g.get("strength", 0) >= 0.45]
    t = 0.0
    for i, b in enumerate(beats):
        end = t + b["dur"]
        if i < len(beats) - 1 and strong:
            near = [g for g in strong if abs(g["time"] - end) <= 0.35]
            if near:
                best = max(near, key=lambda g: (g["strength"], -abs(g["time"] - end)))
                if best["time"] - t >= 2.5:
                    end = best["time"]
        b["dur"] = round(end - t, 3)
        t = end


def esc(t):
    return html.escape(t, quote=False)


def rich(t):
    """*accent*  [[marker highlight]]  ~~strike~~  in authored text."""
    t = esc(t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t


def quote_html(t, beat_id):
    marks = []
    t = esc(t)

    def repl(m):
        kind, text = ("mk", m.group(1)) if m.group(1) is not None else ("strike", m.group(2))
        mid = f"{beat_id}-m{len(marks)}"
        marks.append((kind, mid))
        return f'<span class="{kind}" id="{mid}">{text}</span>'

    t = re.sub(r"\[\[(.+?)\]\]|~~(.+?)~~", repl, t)
    return t, marks


class Shot:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.full = min(MON_W / w, MON_H / h)

    def camera(self, spec):
        if spec in (None, "full"):
            return {"s": round(self.full, 4), "cx": self.w / 2, "cy": self.h / 2}
        if "s" in spec:
            return spec
        x, y, w, h = spec["focus"]
        fw, fh = (MON_W - 60) / w, (MON_H - 40) / h
        s = max(self.full, min(MAX_ZOOM, fw, fh))
        if s <= self.full * 1.02 and fh > self.full * 1.15:
            # a region wider than the frame (a timeline, a toolbar): crop the sides and zoom to its
            # height instead of falling back to the whole screenshot
            s = min(MAX_ZOOM, fh, self.full * 1.45)
        cx, cy = x + w / 2, y + h / 2
        hw, hh = MON_W / 2 / s, MON_H / 2 / s
        cx = self.w / 2 if self.w * s <= MON_W else min(max(cx, hw), self.w - hw)
        cy = self.h / 2 if self.h * s <= MON_H else min(max(cy, hh), self.h - hh)
        return {"s": round(s, 4), "cx": round(cx, 1), "cy": round(cy, 1)}


CSS = r"""
      @font-face { font-family: "Instrument Serif"; src: url("assets/fonts/InstrumentSerif-Regular.ttf") format("truetype"); font-weight: 400; font-style: normal; }
      @font-face { font-family: "Instrument Serif"; src: url("assets/fonts/InstrumentSerif-Italic.ttf") format("truetype"); font-weight: 400; font-style: italic; }
      :root { --display: %(display)s; --dstyle: %(dstyle)s; --subfont: %(subfont)s; --subw: %(subw)s; --track: %(track)s; --bg: %(bg)s; --paper: %(paper)s; --muted: %(muted)s; --clay: %(accent)s; --clay-deep: %(accent_deep)s; --line: rgba(%(paper_rgb)s,0.14); }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: %(W)spx; height: %(H)spx; overflow: hidden; background: var(--bg); }
      #root { position: relative; width: 100%%; height: 100%%; overflow: hidden; background: var(--bg); color: var(--paper); font-family: "JetBrains Mono", monospace; }
      #stage { position: absolute; left: 0; top: %(stage_top)spx; width: 1080px; height: 1350px; }
      #canvas-glow { position: absolute; left: -200px; bottom: -260px; width: 1100px; height: 900px; border-radius: 50%%; background: radial-gradient(closest-side, %(glow)s, rgba(0,0,0,0) 100%%); opacity: 0.7; }
      #glow { position: absolute; left: 40px; top: 60px; width: 1000px; height: 760px; border-radius: 50%%; background: radial-gradient(closest-side, %(glow)s, rgba(0,0,0,0) 100%%); }
      #glow2 { position: absolute; left: 520px; top: 900px; width: 760px; height: 620px; border-radius: 50%%; background: radial-gradient(closest-side, %(glow)s, rgba(0,0,0,0) 100%%); opacity: 0.55; }
      #grain { position: absolute; left: 0; top: -%(stage_top)spx; width: 1080px; height: %(H)spx; opacity: 0.07;
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' seed='4'/></filter><rect width='100%%' height='100%%' filter='url(%%23n)'/></svg>"); }
      .reg { position: absolute; width: 26px; height: 26px; border-color: rgba(242,236,228,0.35); border-style: solid; border-width: 0; }
      #reg-tl { left: 30px; top: calc(30px - %(stage_top)spx); border-left-width: 2px; border-top-width: 2px; }
      #reg-tr { right: 30px; top: calc(30px - %(stage_top)spx); border-right-width: 2px; border-top-width: 2px; }
      #reg-bl { left: 30px; bottom: calc(30px - %(below)spx); border-left-width: 2px; border-bottom-width: 2px; }
      #reg-br { right: 30px; bottom: calc(30px - %(below)spx); border-right-width: 2px; border-bottom-width: 2px; }
      #topbar { position: absolute; left: 60px; right: 60px; top: 52px; height: 40px; display: flex; align-items: center; justify-content: space-between; font-size: 24px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }
      #topbar .left { display: flex; align-items: center; gap: 14px; }
      #rec { display: block; width: 14px; height: 14px; border-radius: 50%%; background: var(--clay-deep); }
      #dots { display: flex; gap: 10px; align-items: center; }
      .dot { display: block; width: 12px; height: 12px; border-radius: 50%%; background: rgba(242,236,228,0.18); }
      #monitor-wrap { position: absolute; left: 60px; top: 124px; width: 960px; height: 560px; }
      #monitor { position: absolute; inset: 0; border-radius: 22px; overflow: hidden; background: %(monitor_bg)s; border: 2px solid var(--line); box-shadow: 0 30px 80px rgba(0,0,0,0.55); }
      #world { position: absolute; left: 0; top: 0; width: %(sw)spx; height: %(sh)spx; transform-origin: 0 0; will-change: transform; }
      #shot { position: absolute; left: 0; top: 0; width: %(sw)spx; height: %(sh)spx; display: block; }
      .hl { position: absolute; border-radius: 6px; background: rgba(%(acc_rgb)s,0.2); border: %(hl_border)spx solid var(--clay); opacity: 0; transform-origin: left center; }
      .ring { position: absolute; border-radius: 50%%; border: %(ring_border)spx solid var(--clay); opacity: 0; }
      .zone { position: absolute; border: %(ring_border)spx dashed var(--clay); border-radius: 18px; opacity: 0; }
      .zone-tag { position: absolute; left: 24px; top: -%(tag_off)spx; padding: 10px 26px; border-radius: 999px; background: var(--clay-deep); color: #1a120d; font-size: %(tag_size)spx; font-weight: 700; letter-spacing: 0.06em; white-space: nowrap; }
      #monitor-sheen { position: absolute; inset: 0; border-radius: 22px; background: radial-gradient(120%% 80%% at 50%% 0%%, rgba(255,255,255,0.05), rgba(255,255,255,0) 60%%); }
      #rule { position: absolute; left: 60px; top: 712px; width: 960px; height: 2px; background: var(--line); transform-origin: left center; }
      .beat { position: absolute; left: 60px; top: 744px; width: 960px; height: 546px; }
      .inner { position: absolute; inset: 0; display: flex; flex-direction: column; gap: 28px; }
      .w { opacity: 0; }
      #monitor-wrap { transform-origin: 50%% 50%%; }
      .beat.L-center, .beat.L-overlay { top: 0; height: 1350px; }
      .L-center .inner { display: block; }
      .ztop { position: absolute; left: 0; right: 0; top: 116px; display: flex; flex-direction: column; gap: 16px; }
      .zbot { position: absolute; left: 0; right: 0; top: 1004px; display: flex; flex-direction: column; gap: 16px; }
      .subline { font-family: var(--subfont); font-weight: var(--subw); font-size: 40px; line-height: 1.3; color: var(--paper); opacity: 0.92; }
      .subline em { font-style: normal; color: var(--clay); }
      .L-center .rows { gap: 12px; }
      .L-overlay .inner { justify-content: center; padding-bottom: 40px; }
      .beat.L-low { top: 108px; height: 600px; }
      .L-low .inner { justify-content: center; }
      .L-overlay .big, .L-overlay .sub { text-shadow: 0 4px 30px rgba(%(bg_rgb)s,0.9); }
      .hl.spot { box-shadow: 0 0 0 4000px rgba(%(bg_rgb)s,0.62); background: transparent; }
      .kicker { display: flex; align-items: center; gap: 16px; font-size: 24px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--clay); }
      .kicker .num { display: block; padding: 6px 12px; border: 2px solid var(--clay); border-radius: 8px; letter-spacing: 0.04em; }
      .quote { font-size: 30px; line-height: 1.5; color: #ddd3c7; background: rgba(242,236,228,0.045); border: 2px solid rgba(242,236,228,0.1); border-radius: 16px; padding: 24px 30px; }
      .quote .who { display: block; font-size: 24px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
      .take { font-family: var(--display); font-style: var(--dstyle); font-size: 76px; line-height: 1.04; letter-spacing: var(--track); color: var(--paper); }
      .take em, .row .txt em { font-style: var(--dstyle); color: var(--clay); }
      .mk { background-image: linear-gradient(rgba(%(acc_rgb)s,0.42), rgba(%(acc_rgb)s,0.42)); background-repeat: no-repeat; background-position: 0 100%%; background-size: 0%% 100%%; color: var(--paper); border-radius: 4px; }
      .strike { background-image: linear-gradient(var(--clay), var(--clay)); background-repeat: no-repeat; background-position: 0 58%%; background-size: 0%% 4px; }
      .rows { display: flex; flex-direction: column; gap: 18px; }
      .row { display: flex; align-items: baseline; gap: 22px; }
      .row .lab { display: block; flex: 0 0 260px; font-size: 26px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--clay); }
      .row .txt { display: block; font-family: var(--display); font-style: var(--dstyle); font-size: 40px; line-height: 1.1; letter-spacing: var(--track); color: var(--paper); }
      .big { font-family: var(--display); font-style: var(--dstyle); font-size: 112px; line-height: 1; letter-spacing: var(--track); color: var(--paper); }
      .big.it { color: var(--clay); }
      .sub { font-family: var(--subfont); font-weight: var(--subw); font-size: 34px; line-height: 1.4; color: var(--paper); opacity: 0.85; }
      .typed { white-space: pre-wrap; }
      .caret { display: inline-block; width: 16px; height: 32px; vertical-align: -6px; background: var(--clay); }
      #fade { position: absolute; inset: 0; background: var(--bg); opacity: 0; }
      .book { position: absolute; inset: 0; background: var(--bg); }
      .book-inner { position: absolute; inset: 0; padding: 0 60px; display: flex; flex-direction: column; justify-content: center; gap: 30px; }
      .book .big { font-size: 96px; }
      .shot-frame { position: relative; width: 960px; height: %(frame_h)spx; border-radius: 18px; overflow: hidden; border: 2px solid var(--line); background: %(monitor_bg)s; box-shadow: 0 30px 80px rgba(0,0,0,0.55); }
      .shot-frame img { position: absolute; left: 0; top: 0; width: 100%%; height: 100%%; display: block; }
      .abox { position: absolute; border: 3px solid var(--clay); border-radius: 5px; background: rgba(%(acc_rgb)s,0.14); opacity: 0; }
      .apin { position: absolute; width: 44px; height: 44px; margin: -22px 0 0 -22px; border-radius: 50%%; background: var(--clay-deep); color: #1a120d; font-size: 24px; font-weight: 700; display: flex; align-items: center; justify-content: center; opacity: 0; box-shadow: 0 4px 14px rgba(0,0,0,0.5); }
      .legend { display: flex; flex-direction: column; gap: 16px; }
      .lrow { display: flex; align-items: center; gap: 22px; opacity: 0; }
      .lnum { display: flex; flex: 0 0 48px; width: 48px; height: 48px; border-radius: 50%%; background: var(--clay-deep); color: #1a120d; font-size: 26px; font-weight: 700; align-items: center; justify-content: center; }
      .ltxt { display: block; font-family: var(--display); font-style: var(--dstyle); font-size: 38px; line-height: 1.1; letter-spacing: var(--track); color: var(--paper); }
      .bar { display: block; width: 960px; height: 6px; border-radius: 3px; background: rgba(242,236,228,0.12); overflow: hidden; }
      .bar span { display: block; width: 100%%; height: 100%%; background: var(--clay); transform-origin: left center; }
      .bk-w { opacity: 0; }
"""

DEFAULT_PALETTE = {"bg": "#15110e", "paper": "#f2ece4", "muted": "#b3a89c", "accent": "#e58a66", "accent_deep": "#e07a55",
                   "monitor_bg": "#1e1e1e"}


def hex_rgb(h):
    h = h.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def plan(cfg):
    """Resolve beat start times, numbering, cameras."""
    shot = Shot(cfg["shot_w"], cfg["shot_h"])
    t, n = 0.0, 0
    beats = []
    energy = cfg.get("energy", "calm")
    raw = [dict(b) for b in cfg["beats"]]
    for b in raw:
        if b.get("dur") in (None, "auto"):
            b["dur"] = auto_duration(b, energy)
    if cfg.get("_beat_grid"):
        snap_to_beats(raw, cfg["_beat_grid"])
    portrait = cfg["shot_h"] > cfg["shot_w"]
    for i, b in enumerate(raw):
        b["id"] = f"b{i}"
        b["start"] = round(t, 3)
        b["end"] = round(t + b["dur"], 3)
        if b["type"] not in ("hook", "close", "statement"):
            n += 1
            b["num"] = n
        b["cam"] = shot.camera(b.get("camera", "full"))
        if "layout" not in b:
            # vary the screen position so the panel's own movement pulls the eye:
            # most points sit centred and large, every third reads as a split
            if b["type"] in ("close", "statement"):
                # words go beside the screenshot, never on it, unless a portrait shot leaves no room
                b["layout"] = "overlay" if portrait else "low"
            elif b["type"] == "hook":
                b["layout"] = "split"
            else:
                b["layout"] = "split" if b["num"] % 3 == 2 else "center"
        beats.append(b)
        t += b["dur"]
    return shot, beats, round(t, 3), n


def beat_html(b):
    bid = b["id"]
    k = b.get("kicker", "")
    numk = f'<div class="kicker w"><span class="num">{b["num"]:02d}</span>{esc(k)}</div>' if "num" in b else (f'<div class="kicker w">{esc(k)}</div>' if k else "")
    parts, extra = [], {}
    lay = b["layout"]
    sz = type_sizes(b)
    big_style = f' style="font-size: {sz["big"]}px"' if "big" in sz else ""
    if b["type"] in ("hook", "close", "statement"):
        style = ' style="gap: 14px"'
        if numk:
            parts.append(numk)
        for j, line in enumerate(b.get("lines", [])):
            mt = f' style="font-size: {sz["big"]}px; margin-top: 20px"' if j == 0 else big_style
            parts.append(f'<div class="big w"{mt}>{esc(line)}</div>')
        if b.get("accent_line"):
            parts.append(f'<div class="big it w"{big_style}>{esc(b["accent_line"])}</div>')
        if b.get("sub"):
            parts.append(f'<div class="sub w" style="margin-top: 34px">{esc(b["sub"])}</div>')
    else:
        style = ""
        parts.append(numk)
        if b["type"] == "rows":
            rows = "".join(f'<div class="row w"><span class="lab">{esc(l)}</span><span class="txt">{rich(tx)}</span></div>' for l, tx in b["rows"])
            parts.append(f'<div class="rows">{rows}</div>')
        elif b["type"] == "quote":
            who = f'<span class="who">{esc(b["who"])}</span>' if b.get("who") else ""
            if b.get("typed"):
                parts.append(f'<div class="quote w">{who}<span class="typed" id="{bid}-typed"></span><span class="caret" id="{bid}-caret"></span></div>')
            else:
                q, marks = quote_html(b["quote"], bid)
                extra["marks"] = marks
                parts.append(f'<div class="quote w">{who}{q}</div>')
        if b.get("take"):
            parts.append(f'<div class="take w" style="font-size: {sz.get("take", 76)}px">{rich(b["take"])}</div>')
        if b.get("sub"):
            parts.append(f'<div class="subline w" style="font-size: {sz.get("sub", 40)}px">{rich(b["sub"])}</div>')
        if lay == "center":
            # words above the screenshot, evidence below it
            top = [x for x in parts if 'class="kicker' in x or 'class="take' in x]
            bot = [x for x in parts if x not in top]
            parts = [f'<div class="ztop">{"".join(top)}</div>', f'<div class="zbot">{"".join(bot)}</div>']
    return (f'      <section class="beat clip L-{lay}" id="{bid}" data-start="__S_{bid}__" data-duration="{b["dur"]}" data-track-index="1">\n'
            f'        <div class="inner"{style}>{"".join(parts)}</div>\n      </section>'), extra


def world_overlays(beats):
    out = []
    for b in beats:
        for j, (x, y, w, h) in enumerate(b.get("highlights", [])):
            spot = " spot" if j == 0 and b.get("spotlight", True) else ""
            out.append(f'<div class="hl{spot}" id="{b["id"]}-hl{j}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>')
        for j, z in enumerate(b.get("zones", [])):
            x, y, w, h = z["rect"]
            out.append(f'<div class="zone" id="{b["id"]}-z{j}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"><div class="zone-tag">{esc(z["label"])}</div></div>')
        for j, (x, y, w, h) in enumerate(b.get("rings", [])):
            out.append(f'<div class="ring" id="{b["id"]}-r{j}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>')
    return "\n            ".join(out)


def timeline_js(beats, extras, total):
    js, sfx = [], []
    first = beats[0]["cam"]

    def add_sfx(name, t, vol):
        sfx.append((name, round(t, 2), vol))

    P0 = POSES[beats[0]["layout"]]
    js.append(f"const cam = {{ s: {round(first['s'] * 1.15, 4)}, cx: {first['cx']}, cy: {first['cy']} }};")
    js.append("applyCamera();")
    legs, prev = [], None
    for i, b in enumerate(beats):
        c = b["cam"]
        if i == 0:
            legs.append((0, 3.0, c, "power2.out"))
        elif c != prev:
            dur = 1.6 if b["type"] == "close" else (1.3 if abs(c["cx"] - prev["cx"]) > 400 else 1.05)
            dur = round(dur * {"calm": 1.0, "lively": 0.85, "punchy": 0.72}.get(ENERGY, 1.0), 2)
            legs.append((b["start"] - 0.1, dur, c, "power3.inOut"))
        prev = c
    js.append("const legs = " + json.dumps([[l[0], l[1], l[2], l[3]] for l in legs]) + ";")
    js.append("""let prev = { s: cam.s, cx: cam.cx, cy: cam.cy };
        legs.forEach(function (leg) {
          const to = leg[2];
          tl.fromTo(cam, { s: prev.s, cx: prev.cx, cy: prev.cy }, { s: to.s, cx: to.cx, cy: to.cy, duration: leg[1], ease: leg[3], onUpdate: applyCamera, immediateRender: false }, leg[0]);
          prev = { s: to.s, cx: to.cx, cy: to.cy };
        });""")
    js.append(f"""tl.fromTo("#glow", {{ scale: 0.94, opacity: 0.75 }}, {{ scale: 1.06, opacity: 1, duration: 4, ease: "sine.inOut", yoyo: true, repeat: {max(0, int(total // 4) - 1)} }}, 0);
        tl.fromTo("#glow2", {{ x: 0, y: 0 }}, {{ x: -60, y: -30, duration: 6, ease: "sine.inOut", yoyo: true, repeat: {max(0, int(total // 6) - 1)} }}, 0);
        tl.fromTo("#rec", {{ opacity: 1 }}, {{ opacity: 0.25, duration: 0.6, ease: "steps(1)", yoyo: true, repeat: {max(0, int(total // 0.6) - 2)} }}, 0);
        tl.fromTo("#monitor-wrap", {{ y: {P0[0] + 16}, opacity: 0.45, scale: {round(P0[1] * 0.985, 4)} }}, {{ y: {P0[0]}, opacity: 1, scale: {P0[1]}, duration: 0.6, ease: "power3.out" }}, 0);
        tl.set("#monitor", {{ opacity: {P0[2]} }}, 0); tl.set("#rule", {{ opacity: {1 if beats[0]["layout"] == "split" else 0} }}, 0);
        tl.fromTo("#rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.9, ease: "power2.inOut" }}, 0.3);
        tl.fromTo("#topbar", {{ opacity: 0.4, y: -8 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }}, 0);""")
    add_sfx("whoosh-short", 0.15, 0.35)

    for i, b in enumerate(beats):
        bid, s, e = b["id"], b["start"], b["end"]
        last = i == len(beats) - 1
        if "num" in b:
            js.append(f'tl.fromTo("#dot-{b["num"]}", {{ backgroundColor: "rgba(242,236,228,0.18)", scale: 1 }}, {{ backgroundColor: "{PAL["accent"]}", scale: 1.35, duration: 0.3, ease: "back.out(2)", immediateRender: false }}, {s + 0.1});')
        if i > 0:
            add_sfx("whoosh-short", s - 0.15, 0.35)
        t = b["type"]
        take_at = None
        if i > 0 and b["layout"] != beats[i - 1]["layout"]:
            py, ps, pd = POSES[b["layout"]]
            js.append(f'tl.to("#monitor-wrap", {{ y: {py}, scale: {ps}, duration: 0.9, ease: "power3.inOut" }}, {s - 0.15});')
            blur = "blur(2px)" if b["layout"] == "overlay" else "blur(0px)"
            js.append(f'tl.to("#monitor", {{ opacity: {pd}, filter: "{blur}", duration: 0.6, ease: "power2.inOut" }}, {s - 0.1});')
            js.append(f'tl.to("#rule", {{ opacity: {1 if b["layout"] == "split" else 0}, duration: 0.4 }}, {s - 0.1});')
        if t in ("statement", "close") and ENERGY == "punchy":
            add_sfx("impact-bass-1", s + 0.35, 0.45)
        if t in ("hook", "statement"):
            js.append(f'cascade("#{bid} .w", {s + 0.1}, 0.28, 70);')  # the hook must land inside the first second
        elif t == "close":
            if b["layout"] == "overlay":
                js.append(f'tl.to("#monitor", {{ filter: "blur(3px)", duration: 1.4, ease: "power2.inOut" }}, {s + 0.6});')
            elif b["layout"] == "low":
                pass  # the screenshot stays sharp below the words
            else:
                js.append(f'tl.to("#monitor", {{ opacity: 0.5, filter: "blur(3px)", duration: 1.4, ease: "power2.inOut" }}, {s + 0.6});')
            js.append(f'cascade("#{bid} .w", {s + 0.5}, 0.55, 70);')
            add_sfx("chime", s + 1.2, 0.35)
        elif t == "rows":
            js.append(f'cascade("#{bid} .w:not(.take):not(.subline)", {s + 0.2}, 0.36, 46);')
            for j in range(len(b["rows"])):
                add_sfx("pop", s + 0.2 + 0.36 * (j + 1), 0.3)
            take_at = s + 0.2 + 0.36 * (len(b["rows"]) + 1) + 0.15
        elif t == "point":
            js.append(f'cascade("#{bid} .kicker", {s + 0.2}, 0.2, 46);')
            take_at = s + 0.4
            js.append(f'tl.set("#{bid} .subline", {{ opacity: 1, y: 30 }}, {s + 1.0}); tl.to("#{bid} .subline", {{ y: 0, duration: 0.45, ease: "power4.out" }}, {s + 1.0});')
        elif t == "quote":
            js.append(f'cascade("#{bid} .w:not(.take):not(.subline)", {s + 0.25}, 0.2, 46);')
            if b.get("typed"):
                text = b["quote"]
                tdur = round(min(2.0, max(0.8, len(text) * 0.022)), 2)
                ts = s + 0.75
                js.append(f"""(function () {{
          const el = document.getElementById("{bid}-typed"); const full = {json.dumps(text)}; const p = {{ n: 0 }};
          tl.set(el, {{ textContent: "" }}, 0);
          tl.fromTo(p, {{ n: 0 }}, {{ n: full.length, duration: {tdur}, ease: "none", immediateRender: false, onUpdate: function () {{ el.textContent = full.slice(0, Math.round(p.n)); }} }}, {ts});
          tl.fromTo("#{bid}-caret", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.4, ease: "steps(1)", yoyo: true, repeat: {max(1, int((e - ts - tdur - 0.5) / 0.4))}, immediateRender: false }}, {ts + tdur});
        }})();""")
                add_sfx("typing", ts, 0.55)
                add_sfx("key-press", ts + tdur, 0.5)
                take_at = ts + tdur + 0.3
            else:
                marks = extras[bid].get("marks", [])
                mt = s + 1.1
                for kind, mid in marks:
                    if kind == "mk":
                        js.append(f'tl.fromTo("#{mid}", {{ backgroundSize: "0% 100%" }}, {{ backgroundSize: "100% 100%", duration: 0.6, ease: "power2.inOut", immediateRender: false }}, {mt});')
                    else:
                        js.append(f'tl.fromTo("#{mid}", {{ backgroundSize: "0% 4px", color: "#ddd3c7" }}, {{ backgroundSize: "100% 4px", color: "#8f857a", duration: 0.45, ease: "power2.out", immediateRender: false }}, {mt});')
                    add_sfx("click-soft", mt, 0.5)
                    mt += 0.65
                take_at = max(s + 1.6, mt + 0.2)
        if t in ("quote", "rows") and b.get("sub"):
            st = (take_at or s + 1.6) + 0.5
            js.append(f'tl.set("#{bid} .subline", {{ opacity: 1, y: 30 }}, {st}); tl.to("#{bid} .subline", {{ y: 0, duration: 0.45, ease: "power4.out" }}, {st});')
        if take_at is not None and b.get("take"):
            js.append(f'tl.set("#{bid} .take", {{ opacity: 1, y: 46 }}, {take_at}); tl.to("#{bid} .take", {{ y: 0, duration: 0.45, ease: "power4.out" }}, {take_at});')
        # screenshot overlays
        for j, _ in enumerate(b.get("highlights", [])):
            on = s + 0.9 + 0.12 * j
            js.append(f'tl.fromTo("#{bid}-hl{j}", {{ opacity: 0, scaleX: 0.2 }}, {{ opacity: 1, scaleX: 1, duration: 0.45, ease: "power3.out", immediateRender: false }}, {on}); tl.to("#{bid}-hl{j}", {{ opacity: 0, duration: 0.35 }}, {e - 0.5});')
        zt = s + 0.5
        for j, _ in enumerate(b.get("zones", [])):
            js.append(f'tl.fromTo("#{bid}-z{j}", {{ opacity: 0, scale: 0.97 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.6)", immediateRender: false }}, {zt}); tl.to("#{bid}-z{j}", {{ opacity: 0, duration: 0.4 }}, {e - 0.45});')
            zt += 0.45
        for j, _ in enumerate(b.get("rings", [])):
            js.append(f'tl.fromTo("#{bid}-r{j}", {{ opacity: 0, scale: 1.6, rotation: -6 }}, {{ opacity: 1, scale: 1, rotation: -3, duration: 0.55, ease: "back.out(1.7)", immediateRender: false }}, {zt + 0.3 + 0.15 * j}); tl.to("#{bid}-r{j}", {{ opacity: 0, duration: 0.4 }}, {e - 0.45});')
        if b.get("rings"):
            add_sfx("click-soft", zt + 0.3, 0.5)
        if not last:
            js.append(f'tl.to("#{bid} .inner", {{ opacity: 0, y: -18, duration: 0.32, ease: "power2.in" }}, {e - 0.38});')
        else:
            js.append(f'tl.to("#fade", {{ opacity: 1, duration: 0.7, ease: "power1.in" }}, {e - 0.7});')
    return "\n        ".join(js), sfx


def bookend_parts(cfg, intro, outro, main_dur, shot):
    if not (intro or outro):
        return "", "", []
    bk = cfg.get("bookends", {})
    h, js, sfx = [], [], []
    if intro:
        i = bk.get("intro", {})
        h.append(f"""
      <section class="clip book" id="intro" data-start="0" data-duration="{intro}" data-track-index="2">
        <div class="book-inner">
          <div class="kicker bk-w" id="in-k">{esc(i.get("kicker", "Before you watch"))}</div>
          <div class="big bk-w" id="in-1">{esc(i.get("title", "Look closely."))}</div>
          <div class="big it bk-w" id="in-2">{esc(i.get("accent", "What do you notice?"))}</div>
          <div class="shot-frame bk-w" id="in-shot"><img id="in-img" src="{cfg["screenshot"]}" alt="The original screenshot" /></div>
          <div class="sub bk-w" id="in-sub">{esc(i.get("sub", "A few things worth spotting. Answers at the end."))}</div>
          <div class="bar bk-w" id="in-barwrap"><span id="in-bar"></span></div>
        </div>
      </section>""")
        js.append(f"""master.set("#stage", {{ opacity: 0 }}, 0); master.set("#stage", {{ opacity: 1 }}, {intro});
        [["#in-k", 0.1, 50], ["#in-1", 0.3, 70], ["#in-2", 0.55, 70], ["#in-shot", 0.8, 60], ["#in-sub", 1.1, 40], ["#in-barwrap", 1.1, 0]].forEach(function (e) {{
          master.set(e[0], {{ opacity: 1, y: e[2] }}, e[1]); master.to(e[0], {{ y: 0, duration: 0.45, ease: "power4.out" }}, e[1]);
        }});
        master.fromTo("#in-img", {{ scale: 1 }}, {{ scale: 1.05, duration: {intro}, ease: "none" }}, 0);
        master.fromTo("#in-bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {round(intro - 1.1, 2)}, ease: "none" }}, 1.1);""")
        sfx.append(("whoosh-short", 0.25, 0.35))
    if outro:
        o = bk["outro"]
        ot = round(intro + main_dur, 3)
        pct = lambda v, tot: f"{100 * v / tot:.3f}%"
        boxes, pins, rows = [], [], []
        for n, item in enumerate(o["items"], 1):
            for (x, y, w, hh) in item.get("boxes", []):
                boxes.append(f'<div class="abox ab-{n}" style="left:{pct(x, shot.w)};top:{pct(y, shot.h)};width:{pct(w, shot.w)};height:{pct(hh, shot.h)}"></div>')
            pin_pts = item.get("pins") or [[min(shot.w - 24, bx + bw + 8), by + 8] for (bx, by, bw, bh) in item.get("boxes", [])]
            for (x, y) in pin_pts:
                pins.append(f'<div class="apin ap-{n}" style="left:{pct(x, shot.w)};top:{pct(y, shot.h)}">{n}</div>')
            rows.append(f'<div class="lrow" id="lr-{n}"><span class="lnum">{n}</span><span class="ltxt">{esc(item["text"])}</span></div>')
        h.append(f"""
      <section class="clip book" id="outro" data-start="{ot}" data-duration="{outro}" data-track-index="2">
        <div class="book-inner">
          <div class="kicker bk-w" id="out-k">{esc(o.get("kicker", "What you just saw"))}</div>
          <div class="shot-frame bk-w" id="out-shot"><img src="{cfg["screenshot"]}" alt="The screenshot, annotated" />{"".join(boxes)}{"".join(pins)}</div>
          <div class="legend">{"".join(rows)}</div>
          <div class="sub bk-w" id="out-sub">{esc(o.get("sub", ""))}</div>
        </div>
      </section>""")
        n_items = len(o["items"])
        step = min(0.55, 2.4 / max(1, n_items))
        js.append(f"""master.set("#stage", {{ opacity: 0 }}, {ot});
        [["#out-k", 0.1, 50], ["#out-shot", 0.2, 60]].forEach(function (e) {{
          master.set(e[0], {{ opacity: 1, y: e[2] }}, {ot} + e[1]); master.to(e[0], {{ y: 0, duration: 0.45, ease: "power4.out" }}, {ot} + e[1]);
        }});
        for (let n = 1; n <= {n_items}; n++) {{
          const t = {ot} + 0.7 + (n - 1) * {step};
          master.fromTo(".ab-" + n, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out", immediateRender: false }}, t);
          master.fromTo(".ap-" + n, {{ opacity: 0, scale: 0 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(2.2)", immediateRender: false }}, t);
          master.set("#lr-" + n, {{ opacity: 1, x: -40 }}, t); master.to("#lr-" + n, {{ x: 0, duration: 0.45, ease: "power4.out" }}, t);
        }}
        master.set("#out-sub", {{ opacity: 1, y: 30 }}, {ot + 0.9 + n_items * step}); master.to("#out-sub", {{ y: 0, duration: 0.45, ease: "power4.out" }}, {ot + 0.9 + n_items * step});""")
        sfx.append(("whoosh-short", ot + 0.1, 0.35))
        for n in range(n_items):
            sfx.append(("pop", ot + 0.7 + n * step, 0.3))
    return "".join(h), "\n        ".join(js), sfx


def document(cfg, W, H, stage_top, intro, outro, bgm):
    shot, beats, main_dur, n_numbered = plan(cfg)
    total = round(intro + main_dur + outro, 3)
    full_s = shot.full
    vals = dict(PAL)
    vals.setdefault("glow", f"rgba({hex_rgb(PAL['accent_deep'])},0.22)")
    vals.update(display=STYLE["display"], dstyle=STYLE["dstyle"], subfont=STYLE["sub"], subw=STYLE["subw"], track=STYLE["track"])
    vals.update(acc_rgb=hex_rgb(PAL["accent"]), paper_rgb=hex_rgb(PAL["paper"]), bg_rgb=hex_rgb(PAL["bg"]))
    vals.update(W=W, H=H, stage_top=stage_top, below=H - stage_top - STAGE_H, sw=shot.w, sh=shot.h,
                hl_border=max(3, round(2 / full_s)), ring_border=max(4, round(3.5 / full_s)),
                tag_size=round(22 / full_s), tag_off=round(24 / full_s), frame_h=round(960 * shot.h / shot.w))
    sections, extras = [], {}
    for b in beats:
        s_html, ex = beat_html(b)
        sections.append(s_html.replace(f'__S_{b["id"]}__', str(round(b["start"] + intro, 3))))
        extras[b["id"]] = ex
    js, sfx = timeline_js(beats, extras, main_dur)
    bk_html, bk_js, bk_sfx = bookend_parts(cfg, intro, outro, main_dur, shot)
    dots = "".join(f'<span class="dot" id="dot-{k}"></span>' for k in range(1, n_numbered + 1))
    audio = [f'<audio id="bgm" src="{bgm}" data-start="0" data-duration="{total}" data-track-index="10" data-volume="{cfg.get("music_volume", 0.85)}"></audio>']
    for k, (name, t, vol) in enumerate([(n, t + intro, v) for n, t, v in sfx] + bk_sfx):
        audio.append(f'<audio id="sfx-{k}-{name}" src="assets/sfx/{name}.mp3" data-start="{round(t, 2)}" data-duration="{SFX_DUR[name]}" data-track-index="{11 + k % 8}" data-volume="{vol}"></audio>')
    used_sfx = sorted({n for n, _, _ in sfx + bk_sfx})

    doc = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>{esc(cfg.get("title", "Behind the Screen"))}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{CSS % vals}    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="{W}" data-height="{H}">
      <div id="canvas-glow"></div>
      <div id="stage"{' style="opacity: 0"' if intro else ""}>
      <div id="glow"></div><div id="glow2"></div><div id="grain"></div>
      <div class="reg" id="reg-tl"></div><div class="reg" id="reg-tr"></div><div class="reg" id="reg-bl"></div><div class="reg" id="reg-br"></div>
      <div id="topbar"><div class="left"><span id="rec"></span><span>{esc(cfg.get("topbar", "Behind the screen"))}</span></div><div id="dots">{dots}</div></div>
      <div id="monitor-wrap">
        <div id="monitor">
          <div id="world" data-layout-allow-overflow>
            <img id="shot" src="{cfg["screenshot"]}" alt="{esc(cfg.get("alt", "Screenshot"))}" />
            {world_overlays(beats)}
          </div>
          <div id="monitor-sheen"></div>
        </div>
      </div>
      <div id="rule"></div>
{chr(10).join(sections)}
      </div>
      <div id="fade"></div>{bk_html}
      {chr(10) + "      ".join(audio)}
    </div>
    <script>
      (function () {{
        const master = gsap.timeline({{ paused: true }});
        const tl = gsap.timeline();
        const MON_W = {MON_W}, MON_H = {MON_H};
        const world = document.getElementById("world");
        function applyCamera() {{
          world.style.transform = "translate(" + (MON_W / 2 - cam.s * cam.cx) + "px," + (MON_H / 2 - cam.s * cam.cy) + "px) scale(" + cam.s + ")";
        }}
        function cascade(sel, t0, gap, travel) {{
          let t = t0;
          document.querySelectorAll(sel).forEach(function (el, i) {{
            tl.set(el, {{ opacity: 1, y: travel * (i === 0 ? 1.4 : 1) }}, t);
            tl.to(el, {{ y: 0, duration: 0.42, ease: "power4.out" }}, t);
            t += gap;
          }});
        }}
        {js}
        master.add(tl, {intro});
        {bk_js}
        window.__timelines["main"] = master;
      }})();
    </script>
  </body>
</html>
"""
    return doc, total, main_dur, used_sfx


def main():
    global PAL, STYLE, ENERGY
    cfg_path, proj = Path(sys.argv[1]), Path(sys.argv[2])
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    PAL = dict(DEFAULT_PALETTE, **cfg.get("palette", {}))
    STYLE = STYLES[cfg.get("style", "bold")]
    ENERGY = cfg.get("energy", "calm")
    # snap scene changes to the music once `npx hyperframes beats` has analysed the bed
    grid_file = proj / "beats" / "assets" / "bgm" / "bed.wav.json"
    if grid_file.exists() and cfg.get("snap_to_music", True) and "--master-only" not in sys.argv:
        cfg["_beat_grid"] = json.loads(grid_file.read_text(encoding="utf-8")).get("beats", [])
        print(f"snapping scene changes to {len(cfg['_beat_grid'])} detected music beats")
    bk = cfg.get("bookends", {})
    # Default flow points straight at the work: no intro. An "intro" bookend is still honoured if configured.
    intro = bk["intro"].get("dur", 3.5) if bk.get("intro") else 0
    outro = bk["outro"].get("dur", 5.0) if bk.get("outro") else 0
    variants = [
        ("index.html", 1080, 1350, 0, 0, 0, "assets/bgm/bed.wav"),
        ("story-9x16.html", 1080, 1920, 240, 0, 0, "assets/bgm/bed.wav"),
    ]
    if outro or intro:
        variants += [
            ("recap-4x5.html", 1080, 1350, 0, intro, outro, "assets/bgm/bed-long.wav"),
            ("reel-9x16.html", 1080, 1920, 240, intro, outro, "assets/bgm/bed-long.wav"),
        ]
    roots = [v[0] for v in variants] + ["sequenced-4x5.html"]
    if "--master-only" in sys.argv or "--preview" in sys.argv:
        # `hyperframes check`/`snapshot` only accept one root composition per folder
        for stale in roots[1:]:
            (proj / stale).unlink(missing_ok=True)
        if "--preview" in sys.argv:
            want = sys.argv[sys.argv.index("--preview") + 1]
            pick = next(v for v in variants if v[0].startswith(want))
            variants = [("index.html",) + pick[1:]]
            print(f"previewing {pick[0]} as index.html (rebuild without --preview before rendering)")
        else:
            variants = variants[:1]
    meta, used = {"variants": {}}, set()
    for name, W, H, top, i, o, bgm in variants:
        doc, total, main_dur, u = document(cfg, W, H, top, i, o, bgm)
        used |= set(u)
        (proj / name).write_text(doc, encoding="utf-8")
        meta["variants"][name] = {"w": W, "h": H, "duration": total, "intro": i, "outro": o}
        meta["main_duration"] = main_dur
        meta["cover_time"] = round(plan(cfg)[1][0]["dur"] - 0.6, 2)
        print(f"wrote {name}  {W}x{H}  {total}s")
    (proj / "assets" / "fonts").mkdir(parents=True, exist_ok=True)
    for f in (SKILL / "assets" / "fonts").glob("*.ttf"):
        shutil.copy(f, proj / "assets" / "fonts" / f.name)
    (proj / "assets" / "sfx").mkdir(parents=True, exist_ok=True)
    for n in used:
        src = SFX_SRC / f"{n}.mp3"
        if src.exists():
            shutil.copy(src, proj / "assets" / "sfx" / src.name)
        else:
            print(f"warning: missing SFX {src} (install media-use: npx hyperframes skills update media-use)")
    if "--preview" not in sys.argv:
        (proj / "variants.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    bgm_dir = proj / "assets" / "bgm"
    bgm_dir.mkdir(parents=True, exist_ok=True)
    for name, length in (("bed.wav", meta["main_duration"]), ("bed-long.wav", round(intro + meta["main_duration"] + outro, 3))):
        if not (bgm_dir / name).exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(length), str(bgm_dir / name)], check=True)
            print(f"placeholder silence -> assets/bgm/{name} (make_music.py replaces it)")
    if meta["main_duration"] > 59 and not cfg.get("allow_long"):
        print(f"WARNING: the video runs {meta['main_duration']}s. Keep feed videos to 59 s or less: cut a beat or tighten copy "
              "(set \"allow_long\": true only when the message genuinely needs the time).")
    print("beat durations:", ", ".join(f"{b['type']} {b['dur']}s" for b in plan(cfg)[1]))
    print(f"main video {meta['main_duration']}s; music needed: bed.wav {meta['main_duration']}s" + (f", bed-long.wav {round(intro + meta['main_duration'] + outro, 2)}s" if outro else ""))


PAL = DEFAULT_PALETTE
ENERGY = "calm"
if __name__ == "__main__":
    main()
