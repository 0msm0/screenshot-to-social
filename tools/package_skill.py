#!/usr/bin/env python3
"""Zip the skill into dist/screenshot-to-social.skill (a zip with the skill folder at its root).

  python tools/package_skill.py

Upload the result to claude.ai (Settings > Capabilities > Skills) or attach it to a GitHub release.
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "screenshot-to-social"
OUT = ROOT / "dist" / "screenshot-to-social.skill"


def main():
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(SKILL.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, f.relative_to(SKILL.parent).as_posix())
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
