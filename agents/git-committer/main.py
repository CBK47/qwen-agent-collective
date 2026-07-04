"""Compatibility entrypoint for the Track 3 git-committer agent.

The canonical implementation lives in ``review.py``. This file remains so
older docs and demos that call ``python agents/git-committer/main.py`` still run
the same multi-role reviewer instead of a stale Flask prototype.
"""

from __future__ import annotations

from review import main


if __name__ == "__main__":
    raise SystemExit(main())
