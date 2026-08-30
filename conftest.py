"""Path strategy for the repo-dev pytest run.

Priority: shared rtai_core at repo ROOT wins over per-project vendored copies,
so the whole suite exercises one core module identity. Standalone runs from
inside a single project folder resolve to that folder's vendored core instead
(nothing here is needed in that mode).
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent

for path in reversed([ROOT, *sorted(p for p in ROOT.glob("0*") if p.is_dir())]):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
