# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-10

### Added
- `screenshot-to-social` skill: a screenshot plus a theme becomes a behind-the-scenes motion video with music.
  - Four platform videos: Instagram Reel and Story (9:16), LinkedIn and X (4:5).
  - Covers, recap cards, captions, alt text and a posting playbook (`POSTING.md`).
- One-command pipeline (`run_pipeline.py`): build, check, music, beat sync, render and finish. It stops with a fix on failure.
- Text placement: text sits in the free space above or below landscape screenshots. It goes on the screenshot only for full-frame portrait shots.
- Layouts rotate between `center`, `split` and `low`. Type auto-fits the free space with bold display headlines.
- Point selection: off-theme details such as lint counts, badges, versions and file names are left out.
- Music moods from tone (`calm`, `lively`, `punchy` and more), with scene changes snapped to the beat. Loudness is normalised to -14 LUFS.
- Claude Code plugin and marketplace manifests.
- Evals:
  - three functional scenarios
  - a 16-query trigger test set
  - a cross-platform trigger tester
- A complete example run (`examples/hyperframes-studio`).
