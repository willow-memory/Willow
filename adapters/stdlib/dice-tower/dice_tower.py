"""dice_tower.py: a die dropped in the tower, only a hash on the record until it's out. Python 3.9+.

    python adapters/stdlib/dice-tower/dice_tower.py --box DIR drop --dice DICE --to DIEFILE [--for TEXT] [--now TS]
    python adapters/stdlib/dice-tower/dice_tower.py --box DIR out --die DIEFILE [--now TS]
    python adapters/stdlib/dice-tower/dice_tower.py --box DIR check
    python adapters/stdlib/dice-tower/dice_tower.py --box DIR page --to PAGE

A roll seeded by the record's tip can be read off the record before it's
thrown, and a row written first (a ruling, a note) changes it. A dice tower
is the other way: everyone sees the die go in, nobody sees it tumble, and it
lands in the tray for all. `drop` draws a fresh secret, puts only its SHA-256
on the record (a `tower-drop` row, with the dice and what they're for), and
writes the secret to DIEFILE, outside the box. `out` puts the secret on the
record (a `tower-out` row) and throws the dice from it, in play-dice5e's
notation and stream. The faces come from the secret alone, so nothing written
between the drop and the out changes them, and nobody reading the record can
know them first. It's a commitment and its reveal: a cup, drawn as a tower.

    in the tower (row 41): 2d6, for Mira climbs, under 3f9a0c7d21e4
    2d6: 4 + 6 = 10, out of the tower from row 41   (row 47)

`check` holds every die out to its drop: the secret's hash is the one dropped
in before it, a die comes out once, and the faces are what the secret gives.
Every die still in the tower is named, so ten dropped and the one liked taken
out shows. `page` draws the tower as one HTML page, written new at PAGE: the
dice still inside, the dice in the tray, and whether every one holds.

Whoever holds DIEFILE can look inside the tower: that is the game master's
screen, not a seal. Keep it where the table doesn't look. Hiding a roll from
the one who dropped it too takes more than a tower.

Exit codes, the kernel's: 0 dropped, out, drawn, or every die holds; 2
refused: dice it can't read, a die file that isn't one or is already there,
a die out twice or not this box's, a page already there, a record that
doesn't verify, or a die that doesn't hold.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parent / "play-dice"))
sys.path.insert(0, str(HERE.parent / "play-dice5e"))
import kernel  # noqa: E402
import play_dice5e  # noqa: E402

DROP, OUT, WHO = "tower-drop", "tower-out", "dice-tower"
USAGE = __doc__.split("\n\n")[1]


def commit(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def said(out: dict, drop: int) -> str:
    return f"{play_dice5e.said(out)}, out of the tower from row {drop}"


def new_file(to: Path, box: Path, what: str) -> str | None:
    """Why TO can't be written new, outside the box; or None."""
    if to.exists():
        return f"{to} is already there; {what} is never written over"
    if not to.parent.is_dir():
        return f"{to.parent} isn't a folder"
    if to.resolve().is_relative_to(box.resolve()):
        return f"{what} goes outside the box"
    return None


def drop(box: Path, dice: str, to: Path, why: str, ts: str) -> int:
    try:
        play_dice5e.parse(dice)
    except ValueError as e:
        return refuse(str(e))
    bad = new_file(to, box, "a die file")
    if bad:
        return refuse(bad + (", so the record never holds the secret" if "outside" in bad else ""))  # fmt: skip
    secret = secrets.token_hex(32)
    held = {"dice": dice, "commit": commit(secret), "secret": secret}
    try:  # made new and readable only by you in one step: never over one, never open to others
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return refuse(f"{to} is already there; a die file is never written over")
    except OSError as e:
        return refuse(f"{to} can't be written: {e.strerror}")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        try:  # the secret is kept, whole, before its hash goes on the record, or neither is
            f.write(json.dumps(held) + "\n")
            f.flush()
            os.fsync(f.fileno())
            row = kernel.append(box, ts, DROP, who=WHO, dice=dice, commit=held["commit"], **({"for": why} if why else {}))  # fmt: skip
        except OSError as e:
            to.unlink(missing_ok=True)
            return refuse(
                f"the die wasn't dropped, and {to} is gone again: {e.strerror or e}"
            )
        except BaseException:
            to.unlink(missing_ok=True)
            raise
    print(f"in the tower (row {row['n']}): {dice}{', for ' + why if why else ''}, under {row['commit'][:12]}")  # fmt: skip
    return kernel.ALIVE


def out(box: Path, rows: list[dict], diefile: Path, ts: str) -> int:
    try:
        held = json.loads(diefile.read_text(encoding="utf-8"))
        secret = str(held["secret"])
        n = (
            int(held["drop"]) if "drop" in held else None
        )  # a die file made before this named its row
    except (OSError, ValueError, KeyError, TypeError):
        return refuse(f"{diefile} isn't a die file")
    if n is None:  # the drop whose hash it is
        n = next((r["n"] for r in rows if r["kind"] == DROP and r.get("commit") == commit(secret)), None)  # fmt: skip
        if n is None:
            return refuse(f"{diefile} isn't a die dropped in this box")
    dropped = rows[n] if 0 <= n < len(rows) else None
    if dropped is None or dropped["kind"] != DROP or dropped.get("commit") != commit(secret):  # fmt: skip
        return refuse(f"{diefile} isn't a die dropped in this box")
    if any(r["kind"] == OUT and r.get("drop") == n for r in rows):
        return refuse(f"the die dropped at row {n} is out already")
    got = play_dice5e.throw(dropped["dice"], secret)
    row = kernel.append(box, ts, OUT, who=WHO, drop=n, secret=secret, **{k: got[k] for k in ("dice", "generator", "faces", "kept", "add", "total")})  # fmt: skip
    print(f"{said(row, n)}   (row {row['n']})")
    return kernel.ALIVE


def check(rows: list[dict]) -> tuple[int, list[dict], str | None]:
    """(how many dice out hold, the dice still in, why the first that doesn't fails)."""
    done, held = set(), 0
    for r in rows:
        if r["kind"] != OUT:
            continue
        n = r.get("drop")
        dropped = rows[n] if isinstance(n, int) and 0 <= n < r["n"] else None
        if dropped is None or dropped["kind"] != DROP:
            return held, [], f"row {r['n']}: it brings out no die dropped before it"
        if n in done:
            return held, [], f"row {r['n']}: the die dropped at row {n} is out twice"
        if commit(str(r.get("secret"))) != dropped.get("commit"):
            return held, [], f"row {r['n']}: its secret isn't the one dropped in at row {n}"  # fmt: skip
        try:
            again = play_dice5e.throw(dropped["dice"], r["secret"])
        except (ValueError, KeyError) as e:
            return held, [], f"row {r['n']}: {e}"
        if r.get("dice") != dropped["dice"] or (again["faces"], again["kept"], again["total"]) != (r.get("faces"), r.get("kept"), r.get("total")):  # fmt: skip
            return (
                held,
                [],
                f"row {r['n']}: its faces aren't what the dropped secret gives",
            )
        done.add(n)
        held += 1
    inside = [r for r in rows if r["kind"] == DROP and r["n"] not in done]
    return held, inside, None


def page(rows: list[dict], held: int, inside: list[dict], why: str | None) -> str:
    """The tower as one HTML page: the dice inside, the tray, and whether they hold."""
    e = html.escape
    drops = {r["n"]: r for r in rows if r["kind"] == DROP}
    tray = [r for r in rows if r["kind"] == OUT]

    def what(d: dict) -> str:
        return f'<span class="for">{e(d["for"])}:</span> ' if d.get("for") else ""

    ins = "".join(f'<li><span class="die" aria-hidden="true">?</span> {what(d)}{e(d["dice"])} <code>row {d["n"]}, under {d["commit"][:12]}</code></li>' for d in inside)  # fmt: skip
    outs = "".join(f'<li><span class="die" aria-hidden="true">{r.get("total")}</span> {what(drops.get(r.get("drop"), {}))}{e(play_dice5e.said(r))} <code>row {r["n"]}, dropped at row {r.get("drop")}</code></li>' for r in reversed(tray))  # fmt: skip
    state = f'<p class="bad">{e(why)}</p>' if why else f'<p class="ok">{held} out of the tower, every one holds; {len(inside)} still inside.</p>'  # fmt: skip
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dice tower</title>
<style>
:root {{ --bg: #faf7f2; --fg: #2b2620; --wood: #8a5a32; --tray: #efe4d2; --ok: #2f6b3a; --bad: #9b2c2c; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg: #1d1a17; --fg: #ece6dc; --wood: #b07a4a; --tray: #2c2620; --ok: #7fc28b; --bad: #f08a8a; }} }}
body {{ background: var(--bg); color: var(--fg); font: 16px/1.5 system-ui, sans-serif; margin: 0 auto; max-width: 42rem; padding: 1rem; }}
.tower {{ border: 4px solid var(--wood); border-bottom: none; border-radius: 8px 8px 0 0; padding: 1rem; }}
.tray {{ background: var(--tray); border: 4px solid var(--wood); border-radius: 0 0 12px 12px; padding: 1rem; }}
h2 {{ font-size: 1rem; margin: 0 0 .5rem; }} ul {{ list-style: none; margin: 0; padding: 0; }} li {{ margin: .4rem 0; }}
.die {{ border: 2px solid var(--wood); border-radius: 6px; display: inline-block; font-weight: bold; min-width: 1.8rem; text-align: center; }}
.for {{ font-style: italic; }} code {{ font-size: .8rem; opacity: .75; }} .ok {{ color: var(--ok); }} .bad {{ color: var(--bad); font-weight: bold; }}
</style></head><body>
<h1>Dice tower</h1>
<section class="tower"><h2>In the tower: dropped, not yet out</h2><ul>{ins or "<li>empty</li>"}</ul></section>
<section class="tray"><h2>In the tray: out, newest first</h2><ul>{outs or "<li>empty</li>"}</ul></section>
{state}
</body></html>
"""


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--dice", "--to", "--for", "--die", "--now"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    need = {
        "drop": ("--dice", "--to"),
        "out": ("--die",),
        "check": (),
        "page": ("--to",),
    }
    if not opts.get("--box") or len(args) != 1 or args[0] not in need or not all(opts.get(k) for k in need[args[0]]):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").is_file():
        return refuse(f"{box} isn't a box: make one with kernel.py init")
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return refuse("the record doesn't verify: " + "; ".join(breaks))
    ts = opts.get("--now") or kernel.now()
    if args == ["drop"]:
        return drop(box, opts["--dice"], Path(opts["--to"]), opts.get("--for", ""), ts)
    if args == ["out"]:
        return out(box, rows, Path(opts["--die"]), ts)
    held, inside, why = check(rows)
    if args == ["page"]:
        bad = new_file(Path(opts["--to"]), box, "a page")
        if bad:
            return refuse(bad)
        Path(opts["--to"]).write_text(page(rows, held, inside, why), encoding="utf-8")
        print(f"the tower is drawn at {opts['--to']}: {held} out, {len(inside)} inside" + ("; one doesn't hold" if why else ""))  # fmt: skip
        return kernel.ALIVE
    if why:
        return refuse(why)
    still = "; ".join(f"row {r['n']}, {r['dice']}{', ' + chr(34) + r['for'] + chr(34) if r.get('for') else ''}" for r in inside)  # fmt: skip
    print(f"{held} {'die' if held == 1 else 'dice'} out of the tower, every one holds" + (f"; {len(inside)} still inside ({still})" if inside else ""))  # fmt: skip
    return kernel.ALIVE


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
