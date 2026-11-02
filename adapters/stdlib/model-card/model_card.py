"""model_card.py: a card naming the model behind an assistant, its hash on the record.

    python adapters/stdlib/model-card/model_card.py add --box DIR --from CARD [--now TS]
    python adapters/stdlib/model-card/model_card.py check --box DIR --from CARD
    python adapters/stdlib/model-card/model_card.py list --box DIR

A card is a markdown file with a `willow-model` header, the one
weights-card writes, with what a person adds by hand:

    <!-- willow-model
    name: Gemma 3 4b It
    sha256: 9c1e…          the weights file's, or
    model version: 2025-03  a hosted model's version, where there is no file
    runs: http://127.0.0.1:8080/v1
    licence: gemma
    limits: makes up dates; English only
    -->

It must name the model (`name`) and say which one (`sha256` or `model
version`). `add` appends the SHA-256 of the card's bytes through the
kernel, with the name, the weights' hash or version, and where it runs;
never the card's text. A suggestion can then say which card stood behind
it by that hash. `check` holds a card file to its latest row: `same`,
`changed` or `never added`. `list` says each name's latest card.

Exit codes, the kernel's: 0 added (or already there), the card the same,
or cards listed; 42 a card changed or never added, or none on the record;
2 refused (a bad command line, not a box, a record that doesn't verify, a
card that doesn't name its model or say which).
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = (
    "usage: model_card.py add --box DIR --from CARD [--now TS]\n"
    "       model_card.py check --box DIR --from CARD\n"
    "       model_card.py list --box DIR"
)
KIND = "model-card"
MARKER = "<!-- willow-model"
MISSING = "not in the header"
SHA = re.compile(r"[0-9a-f]{64}")


def header(text: str) -> dict[str, str]:
    """The card's header lines, key to value; a value it doesn't hold is absent."""
    start = text.find(MARKER)
    end = text.find("-->", start)
    if start < 0 or end < 0:
        return {}
    fields = {}
    for line in text[start + len(MARKER) : end].splitlines():
        key, sep, value = line.partition(":")
        value = value.strip()
        if sep and value and value != MISSING:
            fields[key.strip()] = value
    return fields


def card_of(path: Path) -> tuple[dict[str, str], str]:
    """(the row's fields, why it can't be one) for a card file."""
    raw = path.read_bytes()
    try:
        fields = header(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return {}, "it isn't UTF-8 text"
    if not fields:
        return {}, "it has no willow-model header"
    if "name" not in fields:
        return {}, "it doesn't name the model (name:)"
    weights = fields.get("sha256", "")
    if weights and not SHA.fullmatch(weights):
        return {}, "its sha256 isn't one"
    if not weights and "model version" not in fields:
        return {}, "it doesn't say which model (sha256: or model version:)"
    return {
        "name": fields["name"],
        "card": hashlib.sha256(raw).hexdigest(),
        "weights": weights or None,
        "model_version": fields.get("model version"),
        "runs": fields.get("runs"),
    }, ""


def latest(rows: list[dict]) -> dict[str, dict]:
    """Each model name's latest card row."""
    return {r["name"]: r for r in rows if r["kind"] == KIND}


def which(row: dict) -> str:
    said = (
        f"weights={row['weights']}"
        if row["weights"]
        else f"version {row['model_version']}"
    )
    runs = f", runs at {row['runs']}" if row["runs"] else ", where it runs not said"
    return f"{said}{runs}"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    verb = args[0] if len(args) == 1 else ""
    needs_card = verb in ("add", "check")
    if (verb not in ("add", "check", "list") or not opts.get("--box")
            or needs_card != bool(opts.get("--from")) or "" in opts.values()
            or ("--now" in opts and verb != "add")):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        print(
            "refused: the record doesn't verify:", *breaks, sep="\n  ", file=sys.stderr
        )
        return kernel.REFUSED
    cards = latest(rows)
    if verb == "list":
        for name, row in sorted(cards.items()):
            print(f"{name}  card={row['card']}  {which(row)}  (row {row['n']})")
        if not cards:
            print("nothing there: no model card on the record")
            return kernel.ESCALATE
        return kernel.ALIVE
    path = Path(opts["--from"])
    if not path.is_file():
        print(f"refused: not a file: {path}", file=sys.stderr)
        return kernel.REFUSED
    fields, why = card_of(path)
    if why:
        print(f"refused: {path.name} is not a model card: {why}", file=sys.stderr)
        return kernel.REFUSED
    name, row = fields["name"], cards.get(fields["name"])
    if verb == "check":
        if row is None:
            print(f"never added  {name}  card={fields['card']}")
            return kernel.ESCALATE
        if row["card"] != fields["card"]:
            print(
                f"changed      {name}  card={fields['card']}, the record has {row['card']} (row {row['n']})"
            )
            return kernel.ESCALATE
        print(f"same         {name}  card={fields['card']} (row {row['n']})")
        return kernel.ALIVE
    if row is not None and row["card"] == fields["card"]:
        print(f"already there  {name}  card={fields['card']} (row {row['n']})")
        return kernel.ALIVE
    ts = opts.get("--now") or kernel.now()
    new = kernel.append(box, ts, KIND, who="model-card", **fields)
    replaced = f", replacing row {row['n']}" if row is not None else ""
    print(
        f"added  {name}  card={fields['card']}  {which(new)}  (row {new['n']}{replaced})"
    )
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
