# Contributing

Thanks for helping improve Screenshot to Social.

## Reporting a problem

Open an issue with:
- what you asked Claude, and the screenshot type (landscape or portrait; terminal, IDE, dashboard and so on)
- what you expected and what happened
- the last lines of `run_pipeline.py` output if it stopped
- your OS and versions of Node, Python, ffmpeg and Claude Code

Please don't attach screenshots that show private work. Describe them, or use a mock-up.

## Making a change

1. Fork the repository and create a branch.
2. Edit the skill under `skills/screenshot-to-social/`.
3. Follow Anthropic's skill guidance:
   - Keep `SKILL.md` lean; put detail in `references/`, one level deep.
   - Use scripts for deterministic steps.
   - The description says what the skill does, when to use it and when not to (1024 characters or fewer, no angle brackets).
4. Test:
   - Run `python skills/screenshot-to-social/scripts/run_pipeline.py <project> --check-only` on a project, and a full run if you touched rendering, music or layout.
   - Run `python tools/trigger_test.py --runs 2` if you changed the description or `SKILL.md`. All queries should pass.
   - If you changed behaviour, add or update a scenario in `evals/evals.json`.
5. Bump `version` in these three places, and add a `CHANGELOG.md` entry:
   - `skills/screenshot-to-social/SKILL.md`
   - `.claude-plugin/plugin.json`
   - `.claude-plugin/marketplace.json`
6. Open a pull request that describes the change and what you tested.

## Releasing

```bash
python tools/package_skill.py   # dist/screenshot-to-social.skill
```

Tag the version (`v1.0.0`) and attach the `.skill` file and the example videos to the GitHub release.
