# The same two counts as src/main.rs, for wasi-python: every file under the
# folder, lines naming Johnson (any case) and lines dated March or April 2026.
import os

johnson = spring = 0
for d, dirs, files in os.walk("{pile}"):
    dirs.sort()
    for f in sorted(files):
        with open(os.path.join(d, f), "rb") as fh:
            for line in fh.read().split(b"\n"):
                johnson += b"johnson" in line.lower()
                spring += b"2026-03" in line or b"2026-04" in line
print(johnson)
print(spring)
