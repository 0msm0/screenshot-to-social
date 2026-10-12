#!/usr/bin/env python3
"""Check that Claude Code picks the skill for the right requests, and only those.

  python tools/trigger_test.py                       # evals/trigger-evals.json, 2 runs per query
  python tools/trigger_test.py --runs 3 --evals my-queries.json

Install the skill first. Each query runs through `claude -p` in a temp folder that holds a copy of the
example screenshot as shot.png: without an image, Claude asks for one instead of loading the skill.
Works on Windows, macOS and Linux.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def triggered(claude, query, cwd, env):
    try:
        out = subprocess.run([claude, "-p", query, "--output-format", "stream-json", "--verbose", "--max-turns", "1"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=180, cwd=cwd, env=env).stdout
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use" and "screenshot-to-social" in json.dumps(c.get("input", {})):
                    return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evals", default=ROOT / "evals" / "trigger-evals.json")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    claude = shutil.which("claude") or shutil.which("claude.cmd")
    if not claude:
        sys.exit("claude CLI not found on PATH")
    queries = json.loads(Path(a.evals).read_text(encoding="utf-8"))
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}  # allow running from inside a session

    with tempfile.TemporaryDirectory() as cwd:
        shutil.copy(ROOT / "examples" / "hyperframes-studio" / "input.png", Path(cwd) / "shot.png")
        jobs = [(i, q["query"]) for i, q in enumerate(queries) for _ in range(a.runs)]
        with ThreadPoolExecutor(a.workers) as ex:
            res = list(ex.map(lambda j: (j[0], triggered(claude, j[1], cwd, env)), jobs))

    passed = 0
    for i, q in enumerate(queries):
        hits = sum(r for k, r in res if k == i)
        ok = (hits / a.runs >= 0.5) == q["should_trigger"]
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {hits}/{a.runs}  want={'Y' if q['should_trigger'] else 'N'}  {q['query'][:80]}")
    print(f"{passed}/{len(queries)} passed")
    sys.exit(0 if passed == len(queries) else 1)


if __name__ == "__main__":
    main()
