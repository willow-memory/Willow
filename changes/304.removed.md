`github`: create_pr.py no longer writes a number into a new CHANGELOG.md entry,
which changelog.py refuses anyway; it reads what owes an entry from changelog.py
itself, and its card's writes are now changes/* alone
