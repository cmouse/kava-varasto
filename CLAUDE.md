Storage bookkeeping system for Karhunvartijat ry
================================================

Instructions
------------

- Use python3 and django framework
- Keep commits so that they try to change only one thing. Avoid commits that say "change this and that".
- Do not add Co-Authored-By header
- Keep commit messages short
- Always commit code automatically
- When a change is user-visible, add a line to `src/kava_varasto/whatsnew.py`'s
  `WHATS_NEW` in the same commit -- English only, 1-3 sentences, newest-first
  (create the next version's entry if it doesn't exist yet). Refactors,
  deploy/CI scripts, dependency bumps, tests and docs get no entry.
  `pyproject.toml`'s version bump is separate, landing later at the release
  branch's tip.

This software has to be relocatable, so we want to make an installable package that can be mounted as http://webhost/something

Keep DESIGN.md and CLAUDE.md up to date.
