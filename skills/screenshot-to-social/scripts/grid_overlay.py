#!/usr/bin/env python3
"""Help measure screenshot coordinates for highlights, zones and camera focus.

  python grid_overlay.py <screenshot> <out_dir>              # full image with a labelled 100px grid
  python grid_overlay.py <screenshot> <out_dir> x y w h ...  # also save crops of each rect (verify a highlight)

Coordinates are in the screenshot's own pixels, which is what beats.json expects.
Look at the grid image to estimate a rect, then crop it to confirm it hugs the text.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    W, H = im.size
    g = im.copy()
    d = ImageDraw.Draw(g)
    for x in range(0, W, 100):
        d.line([(x, 0), (x, H)], fill=(255, 80, 80) if x % 500 == 0 else (255, 160, 60), width=2 if x % 500 == 0 else 1)
        d.text((x + 3, 3), str(x), fill=(255, 255, 0))
    for y in range(0, H, 100):
        d.line([(0, y), (W, y)], fill=(255, 80, 80) if y % 500 == 0 else (255, 160, 60), width=2 if y % 500 == 0 else 1)
        d.text((3, y + 3), str(y), fill=(255, 255, 0))
    g.save(out / "grid.png")
    print(f"{src.name}: {W}x{H}  grid -> {out / 'grid.png'}")
    nums = [int(v) for v in sys.argv[3:]]
    for i in range(0, len(nums) - 3, 4):
        x, y, w, h = nums[i:i + 4]
        pad = 12
        crop = im.crop((max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)))
        cd = ImageDraw.Draw(crop)
        cd.rectangle([min(pad, x), min(pad, y), min(pad, x) + w, min(pad, y) + h], outline=(255, 120, 60), width=2)
        p = out / f"rect-{x}-{y}-{w}-{h}.png"
        crop.save(p)
        print("crop ->", p)


if __name__ == "__main__":
    main()
