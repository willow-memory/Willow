"""outside.py: the same method on cpython's CVE fixes. Not in bite 2.

Phase 6 of the plan (README.md): needs an egress lease for the advisory text.
Until it is built this exits 2 and says so.
"""

from __future__ import annotations

import sys


def main(argv: list[str]) -> int:
    print("refused: outside.py is not in bite 2", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
