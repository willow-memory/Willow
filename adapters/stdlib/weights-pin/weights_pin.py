"""weights_pin.py: a weights file held to the hash on its model card.

    python adapters/stdlib/weights-pin/weights_pin.py --card CARD --from FILE

CARD is a model card with a `willow-model` header, as weights-card writes
one; its `sha256` and `bytes` lines are the pin. FILE is the weights file
about to be run. The size is compared first, so a file of another size is
told apart without reading it; then the whole file is hashed.

    same     gemma.gguf  sha256=9c1e… (as on its card)
    differs  gemma.gguf: its card says sha256=9c1e… (2489757856 bytes);
             the file is sha256=04ab… (2489757856 bytes)

Run it before the model, so a file that differs never runs:

    weights_pin.py --card gemma.md --from gemma.gguf && llama-server -m gemma.gguf

Exit codes, the kernel's: 0 the file is the one on its card; 42 it differs;
2 refused (a bad command line, FILE not a file, CARD not a model card with a
sha256 and a size).
"""

from __future__ import annotations

import hashlib
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: weights_pin.py --card CARD --from FILE"
MARKER = "<!-- willow-model"
SHA = re.compile(r"[0-9a-f]{64}")


def pin_of(text: str) -> dict[str, str]:
    """The card's header lines, key to value; empty when there is none."""
    start = text.find(MARKER)
    end = text.find("-->", start)
    if start < 0 or end < 0:
        return {}
    fields = {}
    for line in text[start + len(MARKER) : end].splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(io.DEFAULT_BUFFER_SIZE), b""):
            h.update(block)
    return h.hexdigest()


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--card", "--from"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--card") or not opts.get("--from") or args:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    card, src = Path(opts["--card"]), Path(opts["--from"])
    if not src.is_file():
        print(f"refused: not a file: {src}", file=sys.stderr)
        return kernel.REFUSED
    try:
        pin = pin_of(card.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as e:
        print(f"refused: could not read the card: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    want, size = pin.get("sha256", ""), pin.get("bytes", "")
    if not SHA.fullmatch(want) or not size.isdigit():
        print(
            f"refused: {card.name} is not a model card with a sha256 and a size",
            file=sys.stderr,
        )
        return kernel.REFUSED
    got_size = src.stat().st_size
    got = sha256_file(src) if got_size == int(size) else "not read, another size"
    if got == want:
        print(f"same     {src.name}  sha256={got} (as on its card)")
        return kernel.ALIVE
    print(f"differs  {src.name}: its card says sha256={want} ({size} bytes);")
    print(f"         the file is sha256={got} ({got_size} bytes)")
    named = pin.get("file", "")
    if named and named != src.name:
        print(f"         its card names {named}")
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
