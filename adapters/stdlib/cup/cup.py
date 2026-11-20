"""cup.py: dice shaken into a cup, only a hash on the record until it's lifted. Python 3.9+.

    python adapters/stdlib/cup/cup.py --box DIR shake --dice DICE --to CUPFILE [--for TEXT] [--now TS]
    python adapters/stdlib/cup/cup.py --box DIR lift --cup CUPFILE [--now TS]
    python adapters/stdlib/cup/cup.py --box DIR check

A roll seeded by the record's tip can be read off the record before it's
thrown, and a row written first (a ruling, a note) changes it. The cup is
the other way: `shake` draws a fresh secret, puts only its SHA-256 on the
record (a `cup` row, with the dice and what it's for), and writes the secret
to CUPFILE, outside the box. `lift` puts the secret on the record (a
`cup-lift` row) and throws the dice from it, in play-dice5e's notation and
stream. The faces come from the secret alone, so nothing written between the
shake and the lift changes them, and nobody reading the record can know them
before the lift.

    the die is in the cup (row 41): 2d6, for Mira climbs, under 3f9a0c7d21e4
    2d6: 4 + 6 = 10, lifted from the cup at row 41   (row 47)

`check` holds every lift to its cup: the secret's hash is the one shaken in
before it, a cup is lifted once, and the faces are what the secret gives.
Every cup still down is named, so ten shaken and the one liked lifted shows.

Whoever holds CUPFILE can look under the cup: that is the game master's
screen, not a seal. Keep it where the table doesn't look. Hiding a roll from
the one who shook it too takes more than a cup.

Exit codes, the kernel's: 0 shaken, lifted, or every lift holds; 2 refused:
dice it can't read, a cup file that isn't one or is already there, a cup
lifted twice or not this box's, a record that doesn't verify, or a lift that
doesn't hold.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "play-dice"))
sys.path.insert(0, str(HERE.parent / "play-dice5e"))
import kernel  # noqa: E402
import play_dice5e  # noqa: E402

SHAKE, LIFT, WHO = "cup", "cup-lift", "cup"
USAGE = __doc__.split("\n\n")[1]


def commit(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def said(lift: dict, cup: int) -> str:
    return f"{play_dice5e.said(lift)}, lifted from the cup at row {cup}"


def shake(box: Path, rows: list[dict], dice: str, to: Path, why: str, ts: str) -> int:
    try:
        play_dice5e.parse(dice)
    except ValueError as e:
        return refuse(str(e))
    if to.exists():
        return refuse(f"{to} is already there; a cup is never written over")
    if not to.parent.is_dir():
        return refuse(f"{to.parent} isn't a folder")
    if to.resolve().is_relative_to(box.resolve()):
        return refuse(
            "the cup file goes outside the box, so the record never holds the secret"
        )
    secret = secrets.token_hex(32)
    row = kernel.append(box, ts, SHAKE, who=WHO, dice=dice, commit=commit(secret), **({"for": why} if why else {}))  # fmt: skip
    to.write_text(json.dumps({"cup": row["n"], "dice": dice, "commit": row["commit"], "secret": secret}) + "\n", encoding="utf-8")  # fmt: skip
    to.chmod(0o600)
    print(f"the die is in the cup (row {row['n']}): {dice}{', for ' + why if why else ''}, under {row['commit'][:12]}")  # fmt: skip
    return kernel.ALIVE


def lift(box: Path, rows: list[dict], cupfile: Path, ts: str) -> int:
    try:
        held = json.loads(cupfile.read_text(encoding="utf-8"))
        n, secret = int(held["cup"]), str(held["secret"])
    except (OSError, ValueError, KeyError, TypeError):
        return refuse(f"{cupfile} isn't a cup file")
    cup = rows[n] if 0 <= n < len(rows) else None
    if cup is None or cup["kind"] != SHAKE or cup.get("commit") != commit(secret):
        return refuse(f"{cupfile} isn't a cup shaken in this box")
    if any(r["kind"] == LIFT and r.get("cup") == n for r in rows):
        return refuse(f"the cup at row {n} is lifted already")
    got = play_dice5e.throw(cup["dice"], secret)
    row = kernel.append(box, ts, LIFT, who=WHO, cup=n, secret=secret, **{k: got[k] for k in ("dice", "generator", "faces", "kept", "add", "total")})  # fmt: skip
    print(f"{said(row, n)}   (row {row['n']})")
    return kernel.ALIVE


def check(rows: list[dict]) -> tuple[int, list[dict], str | None]:
    """(how many lifts hold, the cups still down, why the first that doesn't fails)."""
    lifted, held = set(), 0
    for r in rows:
        if r["kind"] != LIFT:
            continue
        n = r.get("cup")
        cup = rows[n] if isinstance(n, int) and 0 <= n < r["n"] else None
        if cup is None or cup["kind"] != SHAKE:
            return held, [], f"row {r['n']}: it lifts no cup shaken before it"
        if n in lifted:
            return held, [], f"row {r['n']}: the cup at row {n} is lifted twice"
        if commit(str(r.get("secret"))) != cup.get("commit"):
            return (
                held,
                [],
                f"row {r['n']}: its secret isn't the one shaken into the cup at row {n}",
            )
        try:
            again = play_dice5e.throw(cup["dice"], r["secret"])
        except (ValueError, KeyError) as e:
            return held, [], f"row {r['n']}: {e}"
        if r.get("dice") != cup["dice"] or (again["faces"], again["kept"], again["total"]) != (r.get("faces"), r.get("kept"), r.get("total")):  # fmt: skip
            return (
                held,
                [],
                f"row {r['n']}: its faces aren't what the cup's secret gives",
            )
        lifted.add(n)
        held += 1
    down = [r for r in rows if r["kind"] == SHAKE and r["n"] not in lifted]
    return held, down, None


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--dice", "--to", "--for", "--cup", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--box") or args not in (["shake"], ["lift"], ["check"]):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if args == ["shake"] and not (opts.get("--dice") and opts.get("--to")):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if args == ["lift"] and not opts.get("--cup"):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").is_file():
        return refuse(f"{box} isn't a box: make one with kernel.py init")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse("the record doesn't verify: " + "; ".join(breaks))
    ts = opts.get("--now") or kernel.now()
    if args == ["shake"]:
        return shake(
            box, rows, opts["--dice"], Path(opts["--to"]), opts.get("--for", ""), ts
        )
    if args == ["lift"]:
        return lift(box, rows, Path(opts["--cup"]), ts)
    held, down, why = check(rows)
    if why:
        return refuse(why)
    still = "; ".join(f"row {r['n']}, {r['dice']}{', ' + chr(34) + r['for'] + chr(34) if r.get('for') else ''}" for r in down)  # fmt: skip
    print(f"{held} cup{'s' if held != 1 else ''} lifted, every one holds" + (f"; {len(down)} still down ({still})" if down else ""))  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
