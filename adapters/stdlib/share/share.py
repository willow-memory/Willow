"""share.py: a sealed answer packed for one person, checkable by anyone, passed on.

    python adapters/stdlib/share/share.py id      --to IDFILE
    python adapters/stdlib/share/share.py send    --box DIR --id IDFILE --answer proposal:<sha256>[,...] --for KEY --to FILE [--note TEXT] [--replaces PACKAGE] [--now TS]
    python adapters/stdlib/share/share.py forward --box DIR --id IDFILE --package FILE --for KEY --to FILE [--note TEXT] [--replaces PACKAGE] [--now TS]
    python adapters/stdlib/share/share.py receive --box DIR --id IDFILE --package FILE [--now TS]
    python adapters/stdlib/share/share.py check   --package FILE
    python adapters/stdlib/share/share.py log     --box DIR
    python adapters/stdlib/share/share.py witness --box DIR --package FILE[,...]

A seal is an HMAC under your key: only that key can check it, so it can't
travel. A package can. `id` makes you an identity of your own, an Ed25519
key that is not your seal key, and prints its public half (KEY), the one you
give people. `send` packs answers you sealed, one or more, for one KEY: each answer, the
passages it cites by fingerprint and place (never their text), the record's
proposal and seal rows, where your record stood, and your signature over all
of it. Your record gets a `sent` row naming the package.

`receive` checks a package, and says who signed each layer and whether you
have had that key before; your record gets a `received` row either way, so
what came in and what didn't hold are both on your chain. It is never your
approval: nothing received is sealed but by you, through the kernel.

`forward` passes on a package you received, inside a layer of your own:
your note, your `received` row, your signature. Nobody can change the inner
layers, only add one outside them. `--replaces` names a package you sent
before that this one corrects; when one arrives, `receive` says who you
passed the old one on to, so the correction can follow it.

`check` reads a package alone, every layer, and `log` lists what your record
says you sent and received.

`witness` holds a box's record to the packages other people kept. Each layer
of a package is signed over where its sender's record stood when it was
packed, so whoever holds one holds a signed pin of that record, out of its
writer's reach. For each layer signed for this box's chain it says `holds`
(the row is the one signed, and the next is its `sent` row), `rewritten`,
`cut short`, or `another key` (signed for this chain by a key the record
never sent with). It reads, and writes nothing.

Exit codes, the kernel's: 0 done or a package that holds, or a record every
witness holds to; 42 a package that doesn't hold, or isn't for you, or a
record a witness doesn't hold to, and waits on you; 2 refused.

It never reads your seal key, and refuses an IDFILE that is it. It writes
only FILE or IDFILE, new, in a folder that exists, never in the box or your
folder; and the record, through the kernel. It never goes online: how a
package travels (mail, a stick, a shared folder) is yours.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ed25519  # noqa: E402

MARK = b"willow-share/1\x1f"  # what a signature is over, before the layer
LAYER = {"share", "from", "for", "chain", "ts", "note", "replaces",
         "answers", "wraps", "rows", "sig"}  # fmt: skip
ANSWER = {"path", "data", "cites", "claim", "bite_key", "places", "rows"}
CHAIN = {"start", "rows", "tip"}
DEEPEST = 64  # layers a package may have
BIGGEST = 10_000_000  # bytes a package may be
HEX = set("0123456789abcdef")
FLAGS = {
    "id": ({"--to"}, set()),
    "send": ({"--box", "--id", "--answer", "--for", "--to"}, {"--note", "--replaces", "--now"}),
    "forward": ({"--box", "--id", "--package", "--for", "--to"}, {"--note", "--replaces", "--now"}),
    "receive": ({"--box", "--id", "--package"}, {"--now"}),
    "check": ({"--package"}, set()),
    "log": ({"--box"}, set()),
    "witness": ({"--box", "--package"}, set()),
}  # fmt: skip


def refuse(why: str) -> int:
    print(f"refused: {why}", file=sys.stderr)
    return kernel.REFUSED


def is_hex(s: object, n: int) -> bool:
    return isinstance(s, str) and len(s) == n and not set(s) - HEX


def is_package_id(s: object) -> bool:
    return isinstance(s, str) and s.startswith("package:") and is_hex(s[8:], 64)


def package_id(pkg: dict) -> str:
    return "package:" + kernel.h256(kernel.canon(pkg))


def short(s: str) -> str:
    return (
        s[:12] + "…"
        if is_hex(s, 64)
        else s.split(":")[0] + ":" + s.split(":")[-1][:12] + "…"
    )


# ── the identity: not the seal key ──────────────────────────────────────────
def read_id(path: Path, box: Path | None) -> tuple[bytes | None, str | None]:
    """(the seed, why not). An IDFILE that is the box's seal key is refused
    by name before it is opened: this never reads the seal key."""
    if box is not None:
        key = Path(kernel.config(box)["key"])
        if os.path.realpath(key) == os.path.realpath(path):
            return (
                None,
                "IDFILE is your seal key; an identity is a key of its own (make one with id)",
            )
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return None, f"could not read {path} as an identity: {type(e).__name__}"
    head, _, seed = text.strip().partition(" ")
    if head != "ed25519" or not is_hex(seed, 64):
        return None, f"{path} is not an identity (make one with id)"
    return bytes.fromhex(seed), None


def new_file(to: Path, text: str, mode: int, box: Path | None = None) -> str | None:
    """Write TEXT to a new file at TO, or say why not. Never over a file,
    never into a folder that isn't there, never in the box or its folder."""
    if box is not None:
        for name, root in (
            ("your folder", Path(kernel.config(box)["pile"])),
            ("the box", box),
        ):
            if to.resolve().is_relative_to(root.resolve()):
                return f"{to} is inside {name}; this never writes there"
    if to.exists():
        return f"{to} exists; this never overwrites"
    if not to.resolve().parent.is_dir():
        return f"{to.parent} is not a folder; this never makes one"
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    except OSError as e:
        return f"could not write {to}: {type(e).__name__}"
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return None


def do_id(to: Path) -> int:
    seed = os.urandom(32)
    why = new_file(to, f"ed25519 {seed.hex()}\n", 0o600)
    if why:
        return refuse(why)
    print(ed25519.public(seed).hex())
    print(
        f"your identity is in {to}; give people the line above, keep the file",
        file=sys.stderr,
    )
    return kernel.ALIVE


# ── a package, checked ──────────────────────────────────────────────────────
def signed_part(layer: dict) -> bytes:
    return MARK + kernel.canon({k: v for k, v in layer.items() if k != "sig"}).encode()


def row_holds(row: object) -> bool:
    """A record row that hashes to its own hash. It shows the row is the one
    its sender's chain linked; not that it is in that chain."""
    if not isinstance(row, dict) or not kernel.ROW_KEYS <= row.keys():
        return False
    body = {k: v for k, v in row.items() if k != "hash"}
    return row["hash"] == kernel.h256(kernel.canon(body))


def problems(pkg: object, depth: int = 0) -> list[str]:
    """Why a package doesn't hold, every layer down; an empty list means it
    holds. Layer 0 is the outside, the last one the sender of the answer."""
    at = f"layer {depth}"
    if depth >= DEEPEST:
        return [f"{at}: more than {DEEPEST} layers"]
    if not isinstance(pkg, dict) or pkg.keys() != LAYER or pkg["share"] != 1:
        return [f"{at}: not a share package"]
    out = []
    if not is_hex(pkg["from"], 64) or not is_hex(pkg["for"], 64):
        return [f"{at}: from and for are public keys"]
    if not is_hex(pkg["sig"], 128) or not ed25519.check(
        bytes.fromhex(pkg["from"]), signed_part(pkg), bytes.fromhex(pkg["sig"])
    ):
        out.append(f"{at}: the signature isn't {short(pkg['from'])}'s over this layer")
    chain = pkg["chain"]
    if (
        not isinstance(chain, dict) or chain.keys() != CHAIN
        or not is_hex(chain["start"], 64) or not is_hex(chain["tip"], 64)
        or isinstance(chain["rows"], bool) or not isinstance(chain["rows"], int)
        or chain["rows"] < 1
    ):  # fmt: skip
        return out + [
            f"{at}: chain is where the sender's record stood: start, rows, tip"
        ]
    if not isinstance(pkg["ts"], str) or not isinstance(pkg["note"], str):
        out.append(f"{at}: ts and note are text")
    if pkg["replaces"] is not None and not is_package_id(pkg["replaces"]):
        out.append(f"{at}: replaces names a package")
    answers, rows = pkg["answers"], pkg["rows"]
    if not isinstance(answers, list) or not isinstance(rows, list):
        return out + [f"{at}: answers and rows are lists"]
    if bool(answers) == (pkg["wraps"] is not None) or bool(answers) == bool(rows):
        return out + [f"{at}: a layer holds answers or wraps a package, one of the two"]
    every = rows + [r for a in answers if isinstance(a, dict) and isinstance(a.get("rows"), list)
                    for r in a["rows"]]  # fmt: skip
    if not all(row_holds(r) for r in every):
        return out + [f"{at}: a record row that doesn't hash to its own hash"]
    if any(isinstance(r["n"], bool) or not isinstance(r["n"], int)
           or not 0 <= r["n"] < chain["rows"] for r in every):  # fmt: skip
        out.append(f"{at}: a row past where the sender's record stood")
    if answers:
        for i, a in enumerate(answers):
            out += answer_problems(a, f"{at}, answer {i}")
        return out
    inner = pkg["wraps"]
    inner_id = package_id(inner) if isinstance(inner, dict) else None
    if not (
        len(rows) == 1 and rows[0]["kind"] == "received"
        and rows[0].get("package") == inner_id and rows[0].get("verdict") == "good"
    ):  # fmt: skip
        out.append(
            f"{at}: its row isn't the sender's record of receiving what it wraps"
        )
    if isinstance(inner, dict) and inner.get("for") != pkg["from"]:
        out.append(f"{at}: what it wraps was for someone else, not its sender")
    return out + problems(inner, depth + 1)


def answer_problems(ans: object, at: str) -> list[str]:
    if not isinstance(ans, dict) or ans.keys() != ANSWER:
        return [f"{at}: an answer is {', '.join(sorted(ANSWER))}"]
    rows = ans["rows"]
    if not isinstance(rows, list):
        return [f"{at}: an answer's rows are a list"]
    if not isinstance(ans["cites"], list) or not isinstance(ans["places"], dict):
        return [f"{at}: cites is a list and places a table"]
    subj = kernel.subject_of(ans)
    out = []
    if not (
        len(rows) == 2 and rows[0]["kind"] == "proposal" and rows[1]["kind"] == "seal"
        and rows[0].get("subject") == subj and rows[0].get("verdict") == "pass"
        and rows[1].get("subject") == subj and rows[1]["who"] == "human"
        and rows[1]["standing"] == "sealed" and rows[0]["n"] < rows[1]["n"]
    ):  # fmt: skip
        out.append(
            f"{at}: its rows aren't the proposal and the person's seal of this answer"
        )
    elif rows[1].get("bite_key") != ans["bite_key"]:
        out.append(f"{at}: the seal was for another question than the answer's")
    if set(map(str, ans["cites"])) - set(ans["places"]):
        out.append(f"{at}: a cite with no place")
    return out


def layers(pkg: dict) -> list[dict]:
    out = [pkg]
    while isinstance(out[-1].get("wraps"), dict) and len(out) < DEEPEST:
        out.append(out[-1]["wraps"])
    return out


def read_package(path: Path) -> tuple[dict | None, str | None]:
    try:
        if path.stat().st_size > BIGGEST:
            return None, f"{path} is bigger than a package may be"
        pkg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, f"could not read {path} as a package: {type(e).__name__}"
    if not isinstance(pkg, dict):
        return None, f"{path} is not a package"
    return pkg, None


# ── the box ─────────────────────────────────────────────────────────────────
def chain_of(box: Path) -> tuple[list[dict], str | None]:
    if not (box / "kernel.json").exists():
        return [], "not a kernel box; init first"
    rows, breaks = kernel.read(box / "record.jsonl")
    if breaks:
        return [], f"the record doesn't verify ({breaks[0]}); a person looks first"
    if not rows:
        return [], "the record is empty"
    return rows, None


def stood(rows: list[dict]) -> dict:
    return {"start": rows[0]["hash"], "rows": len(rows), "tip": rows[-1]["hash"]}


def mine(rows: list[dict], kind: str, package: str) -> dict | None:
    return next(
        (r for r in rows if r["kind"] == kind and r.get("package") == package), None
    )


def pack(seed: bytes, rows: list[dict], to_key: str, ts: str, note: str,
         replaces: str | None, answers: list[dict], wraps: dict | None,
         its_rows: list[dict]) -> dict:  # fmt: skip
    layer = {
        "share": 1, "from": ed25519.public(seed).hex(), "for": to_key,
        "chain": stood(rows), "ts": ts, "note": note, "replaces": replaces,
        "answers": answers, "wraps": wraps, "rows": its_rows,
    }  # fmt: skip
    layer["sig"] = ed25519.sign(seed, signed_part(layer)).hex()
    return layer


def out_of_box(box: Path, opts: dict) -> tuple[list[dict], bytes | None, str | None]:
    """(rows, seed, why not), for send and forward alike."""
    rows, why = chain_of(box)
    if why:
        return [], None, why
    seed, why = read_id(Path(opts["--id"]), box)
    if why:
        return [], None, why
    if not is_hex(opts["--for"], 64):
        return [], None, "--for is the public key id printed for them, 64 hex"
    rep = opts.get("--replaces")
    if rep is not None and not (is_package_id(rep) and mine(rows, "sent", rep)):
        return [], None, f"--replaces {rep} is not a package your record says you sent"
    return rows, seed, None


def written(box: Path, opts: dict, pkg: dict, ts: str, **fields) -> int:
    pid = package_id(pkg)
    why = new_file(Path(opts["--to"]), kernel.canon(pkg) + "\n", 0o644, box)
    if why:
        return refuse(why)
    row = kernel.append(box, ts, "sent", who="share", package=pid, to=pkg["for"],
                        key=pkg["from"], replaces=pkg["replaces"], **fields)  # fmt: skip
    print(f"packed {pid} for {short(pkg['for'])}, row {row['n']}")
    print(f"written to {opts['--to']}; send it any way you like")
    return kernel.ALIVE


def do_send(opts: dict, ts: str) -> int:
    box = Path(opts["--box"])
    rows, seed, why = out_of_box(box, opts)
    if why:
        return refuse(why)
    subjects = opts["--answer"].split(",")
    if len(set(subjects)) != len(subjects):
        return refuse("an answer named twice")
    good, places = kernel.sealed(box, rows), {}
    for r in rows:
        for s in r.get("served", []):
            places.setdefault(s["id"], s["where"])
    answers = []
    for subj in subjects:
        if (seal := good.get(subj)) is None:
            return refuse(f"{subj} is not an answer you sealed in this box")
        prop, asked, why = kernel.standing(box, rows, subj, seal)
        if why:
            return refuse(f"{subj}: its proposal file {why}")
        made = [r for r in rows[: seal["n"]] if r["kind"] == "proposal"
                and r.get("subject") == subj and r.get("verdict") == "pass"]  # fmt: skip
        answer = {k: prop[k] for k in ("path", "data", "cites", "claim")}
        answer.update(bite_key=asked, places={c: places.get(c, "") for c in prop["cites"]},
                      rows=[made[-1], seal])  # fmt: skip
        answers.append(answer)
    pkg = pack(seed, rows, opts["--for"], ts, opts.get("--note", ""),
               opts.get("--replaces"), answers, None, [])  # fmt: skip
    return written(box, opts, pkg, ts, subjects=subjects, wraps=None)


def do_forward(opts: dict, ts: str) -> int:
    box = Path(opts["--box"])
    rows, seed, why = out_of_box(box, opts)
    if why:
        return refuse(why)
    inner, why = read_package(Path(opts["--package"]))
    if why:
        return refuse(why)
    iid = package_id(inner)
    got = mine(rows, "received", iid)
    if got is None or got.get("verdict") != "good":
        return refuse(
            f"{iid} is not a package your record says you received and it held"
        )
    pkg = pack(seed, rows, opts["--for"], ts, opts.get("--note", ""),
               opts.get("--replaces"), [], inner, [got])  # fmt: skip
    return written(box, opts, pkg, ts, wraps=iid)


def known(rows: list[dict], key: str, start: str) -> str:
    """Whether a key has signed to you before. Only a package that held
    counts: a broken one's `from` is only what it claims."""
    seen = [
        r
        for r in rows
        if r["kind"] == "received" and r.get("from") == key and r.get("from_chain")
    ]
    if not seen:
        return "a key you haven't had a package from before"
    other = [r["n"] for r in seen if r.get("from_chain") != start]
    said = f"known since row {seen[0]['n']}"
    return said + (
        f"; but it signed for another chain at row {other[0]}" if other else ""
    )


def do_receive(opts: dict, ts: str) -> int:
    box = Path(opts["--box"])
    rows, why = chain_of(box)
    if why:
        return refuse(why)
    seed, why = read_id(Path(opts["--id"]), box)
    if why:
        return refuse(why)
    pkg, why = read_package(Path(opts["--package"]))
    if why:
        return refuse(why)
    pid = package_id(pkg)
    if (had := mine(rows, "received", pid)) is not None:
        print(f"already received at row {had['n']}: {had.get('verdict')}")
        return kernel.ALIVE if had.get("verdict") == "good" else kernel.ESCALATE
    found = problems(pkg)
    me = ed25519.public(seed).hex()
    held = not found and pkg["for"] == me
    verdict = "good" if held else "not-for-you" if not found else "broken"
    fields = {"from": pkg.get("from"), "replaces": pkg.get("replaces")}
    fields["from_chain"] = (pkg.get("chain") or {}).get("start") if not found else None
    print(f"{pid}  {verdict}")
    for p in found:
        print(f"  {p}")
    if not found:
        said(pkg, rows)
        if pkg["for"] != me:
            print(f"  it is for {short(pkg['for'])}, not you")
        follow(rows, pkg["replaces"])
    row = kernel.append(box, ts, "received", who="share", package=pid,
                        verdict=verdict, layers=len(layers(pkg)) if not found else None,
                        **fields)  # fmt: skip
    print(f"row {row['n']}: received, not sealed by you")
    return kernel.ALIVE if held else kernel.ESCALATE


def said(pkg: dict, rows: list[dict] | None) -> None:
    """Every layer, outside in, and the answer at the core."""
    for i, layer in enumerate(layers(pkg)):
        who = short(layer["from"])
        if rows is not None:
            who += f" ({known(rows, layer['from'], layer['chain']['start'])})"
        note = f' "{layer["note"]}"' if layer["note"] else ""
        print(f"  {'  ' * i}{'└ ' if i else ''}from {who}, {layer['ts']}{note}")
        for a in layer["answers"]:
            print(f"  {'  ' * i}  answer: {a['data']}")
            print(f"  {'  ' * i}    why: {a['claim']}")
            for c in a["cites"]:
                print(
                    f"  {'  ' * i}    cites {a['places'].get(c) or c[:12]}  {c[:12]}…"
                )


def follow(rows: list[dict], replaces: str | None) -> None:
    """Where a correction should go next: whoever you passed the old one to."""
    if replaces is None:
        return
    old = mine(rows, "received", replaces)
    if old is None:
        print(f"  it replaces {short(replaces)}, which your record doesn't have")
        return
    print(f"  it replaces {short(replaces)}, which you received at row {old['n']}")
    for r in rows:
        if r["kind"] == "sent" and r.get("wraps") == replaces:
            print(f"  you passed that on to {short(r['to'])} as {r['package']} (row {r['n']});"
                  f" forward this one with --replaces {r['package']}")  # fmt: skip


def do_check(opts: dict) -> int:
    pkg, why = read_package(Path(opts["--package"]))
    if why:
        return refuse(why)
    found = problems(pkg)
    print(f"{package_id(pkg)}  {'holds' if not found else 'does not hold'}")
    for p in found:
        print(f"  {p}")
    if not found:
        said(pkg, None)
    return kernel.ESCALATE if found else kernel.ALIVE


def do_log(opts: dict) -> int:
    rows, why = chain_of(Path(opts["--box"]))
    if why:
        return refuse(why)
    for r in rows:
        if r["kind"] == "sent":
            more = f" wrapping {short(r['wraps'])}" if r.get("wraps") else ""
            more += f" replacing {short(r['replaces'])}" if r.get("replaces") else ""
            print(
                f"row {r['n']}  sent      {r['package']} to {short(r['to'])}{more}  {r['ts']}"
            )
        elif r["kind"] == "received":
            print(f"row {r['n']}  received  {r['package']} from {short(str(r.get('from')))}"
                  f"  {r.get('verdict')}  {r['ts']}")  # fmt: skip
    return kernel.ALIVE


def witnessed(rows: list[dict], layer: dict) -> tuple[bool, str]:
    """(holds, the line to say) for one signed layer against a record. A
    layer signed by a key the record never sent with is said as such: either
    the record lost those rows, or someone else signed for this chain."""
    pid, chain = package_id(layer), layer["chain"]
    n, at = chain["rows"], f"{short(pid)} at row {chain['rows']}"
    if len(rows) <= n:
        line = f"cut short    {at}: signed at {n} rows; the record has {len(rows)}"
    elif rows[n - 1]["hash"] != chain["tip"]:
        line = f"rewritten    {at}: row {n - 1} is not the row it was signed after"
    elif (
        rows[n]["kind"] != "sent"
        or rows[n].get("package") != pid
        or rows[n].get("key") != layer["from"]
    ):
        line = f"rewritten    {at}: row {n} is not the record of sending it"
    else:
        return True, f"holds        {at}: sent to {short(layer['for'])}, {layer['ts']}"
    if layer["from"] not in {r.get("key") for r in rows if r["kind"] == "sent"}:
        line += (
            f"; and its key, {short(layer['from'])}, is one this record never sent with"
        )
    return False, line


def do_witness(opts: dict) -> int:
    rows, why = chain_of(Path(opts["--box"]))
    if why:
        return refuse(why)
    start, held, said = rows[0]["hash"], True, 0
    for path in opts["--package"].split(","):
        pkg, why = read_package(Path(path))
        if why:
            return refuse(why)
        if problems(pkg):
            print(f"proves nothing  {path}: the package doesn't hold (check says why)")
            held = False
            continue
        for layer in layers(pkg):
            if layer["chain"]["start"] == start:
                ok, line = witnessed(rows, layer)
                print(line)
                held, said = held and ok, said + 1
    if not said:
        print("no witness: none of these packages was signed for this record")
        return kernel.ESCALATE
    return kernel.ALIVE if held else kernel.ESCALATE


def main(argv: list[str]) -> int:
    cmd, rest = (argv[0], argv[1:]) if argv else ("", [])
    need, may = FLAGS.get(cmd, (None, set()))
    opts: dict[str, str] = {}
    ok = need is not None and len(rest) % 2 == 0
    for flag, value in zip(rest[::2], rest[1::2]):
        ok = ok and flag in need | may and flag not in opts
        opts[flag] = value
    if not ok or not need <= opts.keys():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    ts = opts.get("--now") or kernel.now()
    if cmd == "id":
        return do_id(Path(opts["--to"]))
    return {"send": lambda: do_send(opts, ts), "forward": lambda: do_forward(opts, ts),
            "receive": lambda: do_receive(opts, ts), "check": lambda: do_check(opts),
            "log": lambda: do_log(opts), "witness": lambda: do_witness(opts)}[cmd]()  # fmt: skip


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
