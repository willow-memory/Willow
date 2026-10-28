"""spread.py: each gap's questions over the other repositories. Not in bite 2.

Phase 5 of the plan (README.md): a finding generator, written to a private
file only. Until it is built this exits 2 and says so.
"""

from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    print("refused: spread.py is not in bite 2", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
