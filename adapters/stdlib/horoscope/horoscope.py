"""horoscope.py: a daily horoscope, the same for the same name and day. Python 3.9+.

    python adapters/stdlib/horoscope/horoscope.py NAME [--date YYYY-MM-DD] [--coder]

    Today, Ana: the letter you've been meaning to write is shorter than you think.

The reading is picked by the SHA-256 of "NAME:DATE", so the same name on the
same day gets the same reading, on any machine, always, and anyone can check
it. It's willow-bot's horoscope (horoscope.py), the bot's own lines kept for
--coder, and a set for everyone else beside them. It predicts nothing; it's
a toy that can't be rigged, which is the point.

The date is today in UTC unless --date says. It reads nothing and writes
nothing. Exit codes, the kernel's: 0 a reading; 2 a bad command line.
"""

from __future__ import annotations

import hashlib
import sys
from datetime import date as Date
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

#: for everyone
LINES = [
    "the letter you've been meaning to write is shorter than you think",
    "a drawer you open today holds the thing you lost last month",
    "the call you're putting off will take four minutes",
    "someone is about to remember you kindly",
    "today favours lists with three things on them, not ten",
    "the receipt you need is in the last place, so look there first",
    "an appointment you forgot about has not forgotten you",
    "a small repair now saves a large one later",
    "the answer is already written down somewhere you keep things",
    "today is a good day to back something up",
    "a plant in your care would like some water",
    "the form is easier than it looks, apart from page two",
    "you will find the charger, but not the cable",
    "a neighbour's question will be the one you were about to ask",
    "the kettle knows what kind of day it will be",
    "a date in your calendar is closer than it appears",
    "the password you're trying is the old one",
    "today rewards reading the small print, slowly",
    "a photo from years ago will make you laugh",
    "the queue you choose will move fastest, briefly",
    "something you put somewhere safe is still there",
    "a postponed walk wants to happen today",
    "the renewal notice is worth opening",
    "a recipe will turn out better than the picture",
    "today is for finishing, not starting",
    "you already know what you'd tell a friend in your place",
    "an old note in your own hand will settle an argument",
    "the bin goes out tonight",
    "a kindness you did is about to come back around",
    "the thing you are worried about is smaller on paper",
]

#: willow-bot's own, unchanged
CODER = [
    "a variable you named in haste will forgive you",
    "the pull request you are avoiding is not going anywhere",
    "your tests know something you don't",
    "today is not the day for a rebase",
    "the bug is not where you think it is",
    "a comment you wrote six months ago is about to be read aloud",
    "the merge conflict is smaller than it looks",
    "someone will approve your PR without reading it, and that is fine",
    "the log you need is the one you did not think to add",
    "a dependency will update itself without asking",
    "the meeting could have been a commit message",
    "your CI will pass on the third try, not the first",
    "the branch you deleted was the one you needed",
    "silence from the reviewer is not agreement",
    "the config file is lying to you, gently",
    "today favors small diffs",
    "a typo will cost you forty minutes and teach you nothing",
    "the thing you refactored will not be touched again for a year",
    "your instincts about the flaky test are correct",
    "the documentation is wrong, but only slightly",
    "a stale branch will outlive you",
    "the fix is one line, but finding it is not",
    "today is a good day to read the error message fully",
    "the code review will be kinder than you expect",
    "your commit history will be judged, quietly",
    "the feature flag you forgot about is still on",
    "a coworker will ask a question you asked yourself last week",
    "the deploy will go smoothly, which will worry you",
    "today rewards the person who reads the diff twice",
    "the ticket is more finished than the ticket admits",
]


def reading(name: str, day: str, lines: list[str] = LINES) -> str:
    """The bot's pick: the first 8 hex digits of SHA-256("name:day")."""
    digest = hashlib.sha256(f"{name}:{day}".encode()).hexdigest()
    return lines[int(digest[:8], 16) % len(lines)]


def main(argv: list[str]) -> int:
    opts, args, coder, it = {}, [], False, iter(argv)
    for a in it:
        if a == "--date":
            opts[a] = next(it, "")
        elif a == "--coder":
            coder = True
        else:
            args.append(a)
    if len(args) != 1 or not args[0].strip() or args[0].startswith("--"):
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    day = opts.get("--date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        Date.fromisoformat(day)
    except ValueError:
        print(f"refused: --date {day!r} isn't a date, YYYY-MM-DD", file=sys.stderr)
        return kernel.REFUSED
    name = args[0].strip()
    print(f"Today, {name}: {reading(name, day, CODER if coder else LINES)}.")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
