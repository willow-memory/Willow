"""secure_sum.py: a total of everyone's counts, in which no one's own count is
ever in a package, by Shamir's secret sharing (shamirs).

    python adapters/deps/secure-sum/secure_sum.py split   --box DIR --id IDFILE --result proposal:<sha256> --among KEY,KEY,... [--threshold T] [--now TS]
    python adapters/deps/secure-sum/secure_sum.py combine --box DIR --id IDFILE --package FILE[,...] [--now TS]
    python adapters/deps/secure-sum/secure_sum.py total   --box DIR --among KEY,KEY,... --package FILE[,...] [--now TS]

Someone asks several people the same kart job. Each seals the numbers it
printed over their own folder, as kart has them do, but instead of sending
them back:

1. `split` cuts each number into one share for every person in the round,
   KEY by KEY in the order the one asking gave (`--among`, share's keys).
   One share alone, or any fewer than T of them, says nothing of the number.
   Each share is proposed as an answer of yours, waiting on your seal; you
   seal each and send it with `share send` straight to its person, never
   through the one who asked. Your own share stays in your box.
2. `combine` takes the shares the others sent you, one from each, adds them
   to your own, and proposes the sum, a share of everyone's total, waiting
   on your seal; that one goes to the one who asked.
3. `total` takes T or more of those sums and works out the total. Each sum
   must come from the person at its place in `--among`; more than T are
   checked against each other, so one changed sum is caught.

The one who asks learns the total and nothing else, unless T of the people
in the round put their shares together. A share forwarded on its way is
refused at `combine`: whoever forwarded it held it. The round is the job's
text, the keys in order, T, and the number of lines, so everyone in it
must be given the same.

Exit codes, the kernel's: 42 shares, a sum or a total proposed, waiting on
your seal; 2 refused (no shamirs, a result that isn't a sealed kart result
of yours, a key not in the round, a share or sum that doesn't belong).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

sys.path.insert(0, str(ROOT / "adapters" / "deps" / "kart"))
import kart  # noqa: E402

sys.path.insert(0, str(ROOT / "adapters" / "stdlib" / "share"))
import ed25519  # noqa: E402
import share  # noqa: E402

PRIME = 2**127 - 1  # shamirs' default field; a count and its noise fit far inside
FLAGS = {
    "split": ({"--box", "--id", "--result", "--among"}, {"--threshold", "--now"}),
    "combine": ({"--box", "--id", "--package"}, {"--now"}),
    "total": ({"--box", "--among", "--package"}, {"--now"}),
}
JOB_TEXT = re.compile(r"; job text ([0-9a-f]{64})$")
SHARE_CLAIM = re.compile(
    r"^share (\d+) of (\d+), threshold (\d+), (\d+) lines, of round ([0-9a-f]{64}), "
    r"for ([0-9a-f]{64}); job text ([0-9a-f]{64})$"
)
SUM_CLAIM = re.compile(
    r"^the sum of the (\d+) shares at (\d+), threshold (\d+), (\d+) lines, of round "
    r"([0-9a-f]{64}); job text ([0-9a-f]{64})$"
)


def refuse(why: str) -> int:
    return kart.refuse(why)


def round_of(job: str, among: list[str], threshold: int, lines: int) -> str:
    """What everyone in a round must be given alike, as one hash."""
    return kernel.h256(kernel.canon({"job": job, "among": among, "threshold": threshold,
                                     "lines": lines}))  # fmt: skip


def keys(text: str) -> tuple[list[str], str | None]:
    among = text.split(",")
    if not all(share.is_hex(k, 64) for k in among):
        return [], "--among is share keys, 64 hex each, separated by commas"
    if len(set(among)) != len(among):
        return [], "--among names a key twice"
    if len(among) < 3:
        return [], ("--among needs three people or more: with two, each works out "
                    "the other's number from the total")  # fmt: skip
    return among, None


def encode(n: int) -> int:
    return n % PRIME


def decode(n: int) -> int:
    return n - PRIME if n > PRIME // 2 else n


def numbers(text: str) -> list[int]:
    return [int(x) for x in text.strip().splitlines()]


def missing() -> str | None:
    if importlib.util.find_spec("shamirs") is None:
        return "shamirs isn't installed: pip install -r adapters/deps/secure-sum/requirements.txt"
    return None


def me_of(opts: dict, box: Path) -> tuple[str | None, str | None]:
    seed, why = share.read_id(Path(opts["--id"]), box)
    return (ed25519.public(seed).hex(), None) if seed else (None, why)


def proposal(box: Path, subj: str) -> dict | None:
    try:
        prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
    except (OSError, ValueError):
        return None
    return prop if kernel.subject_of(prop) == subj else None


def propose_all(box: Path, props: list[tuple[str, dict]], now: list[str]) -> list[str]:
    out = []
    for words, prop in props:
        subj, said = kart.propose(box, words, prop, now)
        if subj is None:
            print(said, end="")
            return []
        out.append(subj)
    return out


# ── split ───────────────────────────────────────────────────────────────────
def do_split(opts: dict, ts: str) -> int:
    import shamirs  # noqa: PLC0415

    box = Path(opts["--box"])
    rows, why = kart.box_rows(box)
    if why:
        return refuse(why)
    me, why = me_of(opts, box)
    if why:
        return refuse(why)
    among, why = keys(opts["--among"])
    if why:
        return refuse(why)
    if me not in among:
        return refuse("your key isn't in --among; a round is split by the people in it")
    try:
        t = int(opts.get("--threshold", str(len(among))))
    except ValueError:
        return refuse("--threshold is a whole number")
    if not 2 <= t <= len(among):
        return refuse(f"--threshold is from 2 to {len(among)}, the people in the round")
    subj = opts["--result"]
    if subj not in kernel.sealed(box, rows):
        return refuse(
            f"{subj} is not an answer you sealed; seal the numbers you'd stand by first"
        )
    prop = proposal(box, subj)
    job = JOB_TEXT.search((prop or {}).get("claim", ""))
    if (
        prop is None
        or not str(prop.get("path", "")).startswith("kart/results/")
        or not job
    ):
        return refuse(f"{subj} is not a kart result (kart.py run proposes those)")
    if not kart.shaped(prop["data"], "numbers"):
        return refuse(f"{subj} isn't numbers, one a line")
    values = numbers(prop["data"])
    rnd = round_of(job[1], among, t, len(values))
    for r in rows:
        if r["kind"] == "split" and (r.get("result") == subj or r.get("round") == rnd):
            return refuse(f"split already at row {r['n']}: one result, one round, once; "
                          "split again, the shares of two cuts say more than one")  # fmt: skip
    i = among.index(me) + 1
    cut = [
        shamirs.shares(encode(v), len(among), modulus=PRIME, threshold=t)
        for v in values
    ]
    at = {s.index: [] for s in cut[0]}
    for line in cut:
        for s in line:
            at[s.index].append(s.value)
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    props = []
    for j, key in enumerate(among, 1):
        props.append((f"secure sum share {j} of {rnd[:12]}", {
            "path": f"secure-sum/{rnd[:12]}/{'own' if j == i else 'share'}-{j}-of-{len(among)}.txt",
            "data": "".join(f"{v}\n" for v in at[j]), "cites": [],
            "claim": f"share {j} of {len(among)}, threshold {t}, {len(values)} lines, "
                     f"of round {rnd}, for {key}; job text {job[1]}"}))  # fmt: skip
    subjs = propose_all(box, props, now)
    if not subjs:
        return refuse("the kernel didn't take the shares as proposals")
    row = kernel.append(box, ts, "split", who="secure-sum", result=subj, round=rnd,
                        index=i, among=among, threshold=t, lines=len(values),
                        own=subjs[i - 1])  # fmt: skip
    print(
        f"split  {subj}  into {len(among)} shares, any {t} of which make it; row {row['n']}"
    )
    for j, (key, s) in enumerate(zip(among, subjs), 1):
        if j == i:
            print(f"  own    {s}  yours, kept in your box for combine")
        else:
            print(f"  share  {s}  for {share.short(key)}: seal it, then send it to them "
                  "with share.py send, yourself, never through the one who asked")  # fmt: skip
    return kernel.ESCALATE


# ── combine ─────────────────────────────────────────────────────────────────
def received(
    rows: list[dict], path: Path
) -> tuple[dict | None, dict | None, str | None]:
    """(the package, its innermost layer, why not): one that held, that your
    record received, with one answer."""
    pkg, why = share.read_package(path)
    if why:
        return None, None, why
    if share.problems(pkg):
        return None, None, f"{path} doesn't hold (share.py check says why)"
    pid = share.package_id(pkg)
    got = share.mine(rows, "received", pid)
    if got is None or got.get("verdict") != "good":
        return (
            None,
            None,
            f"{pid} is not a package your record says you received and it held",
        )
    core = share.layers(pkg)[-1]
    if len(core["answers"]) != 1:
        return None, None, f"{path} holds more than one answer"
    return pkg, core, None


def do_combine(opts: dict, ts: str) -> int:
    box = Path(opts["--box"])
    rows, why = kart.box_rows(box)
    if why:
        return refuse(why)
    me, why = me_of(opts, box)
    if why:
        return refuse(why)
    got = []
    for path in opts["--package"].split(","):
        pkg, core, why = received(rows, Path(path))
        if why:
            return refuse(why)
        if len(share.layers(pkg)) != 1:
            return refuse(f"{path} was forwarded: a share passed on was held by whoever "
                          "passed it; shares go straight to their person")  # fmt: skip
        c = SHARE_CLAIM.match(core["answers"][0]["claim"])
        if not c or not str(core["answers"][0]["path"]).startswith("secure-sum/"):
            return refuse(f"{path} isn't a secure-sum share")
        if c[6] != me:
            return refuse(f"{path} is a share for {share.short(c[6])}, not you")
        got.append(
            (
                share.package_id(pkg),
                core["from"],
                c,
                numbers(core["answers"][0]["data"]),
            )
        )
    rnds = {g[2][5] for g in got}
    if len(rnds) != 1:
        return refuse("these shares are of different rounds")
    rnd = rnds.pop()
    split = next(
        (r for r in rows if r["kind"] == "split" and r.get("round") == rnd), None
    )
    if split is None:
        return refuse("you haven't split your own result into this round; split first")
    among, i = split["among"], split["index"]
    froms = [g[1] for g in got]
    if sorted(froms) != sorted(k for k in among if k != me):
        return refuse(f"a round of {len(among)} needs one share from each of the other "
                      f"{len(among) - 1}, each from its own person; these are from "
                      f"{len(set(froms))}")  # fmt: skip
    for pid, frm, c, vals in got:
        if int(c[1]) != i or among.index(frm) + 1 == i or len(vals) != split["lines"]:
            return refuse(f"{pid} is not the share at your place {i} of this round")
    own = proposal(box, split["own"])
    if own is None:
        return refuse("your own share's proposal file is missing or changed")
    total = numbers(own["data"])
    for *_, vals in got:
        total = [(a + b) % PRIME for a, b in zip(total, vals)]
    t, lines, job = split["threshold"], split["lines"], got[0][2][7]
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    prop = {"path": f"secure-sum/{rnd[:12]}/sum-{i}.txt",
            "data": "".join(f"{v}\n" for v in total), "cites": [],
            "claim": f"the sum of the {len(among)} shares at {i}, threshold {t}, {lines} "
                     f"lines, of round {rnd}; job text {job}"}  # fmt: skip
    subj, said = kart.propose(box, f"secure sum at {i} of {rnd[:12]}", prop, now)
    if subj is None:
        print(said, end="")
        return refuse("the kernel didn't take the sum as a proposal")
    row = kernel.append(box, ts, "combined", who="secure-sum", round=rnd, index=i,
                        packages=[g[0] for g in got], sum=subj)  # fmt: skip
    print(f"sum    {subj}  of {len(among)} shares at place {i}, row {row['n']}; "
          "seal it and send it to the one who asked")  # fmt: skip
    return kernel.ESCALATE


# ── total ───────────────────────────────────────────────────────────────────
def do_total(opts: dict, ts: str) -> int:
    import shamirs  # noqa: PLC0415

    box = Path(opts["--box"])
    rows, why = kart.box_rows(box)
    if why:
        return refuse(why)
    among, why = keys(opts["--among"])
    if why:
        return refuse(why)
    got = {}
    for path in opts["--package"].split(","):
        pkg, core, why = received(rows, Path(path))
        if why:
            return refuse(why)
        c = SUM_CLAIM.match(core["answers"][0]["claim"])
        if not c or not str(core["answers"][0]["path"]).startswith("secure-sum/"):
            return refuse(f"{path} isn't a secure-sum sum (combine proposes those)")
        n, i, t, lines, rnd, job = (
            int(c[1]),
            int(c[2]),
            int(c[3]),
            int(c[4]),
            c[5],
            c[6],
        )
        if n != len(among) or round_of(job, among, t, lines) != rnd:
            return refuse(f"{path} is of a round other than these keys, in this order")
        if among[i - 1] != core["from"]:
            return refuse(f"{path} is the sum at place {i}, but {share.short(core['from'])} "
                          f"isn't the person at {i}")  # fmt: skip
        if i in got:
            return refuse(f"two sums at place {i}")
        vals = numbers(core["answers"][0]["data"])
        if len(vals) != lines:
            return refuse(f"{path} doesn't have the round's {lines} lines")
        got[i] = (share.package_id(pkg), vals)
    if len(got) < t:
        return refuse(f"{len(got)} sums of a round that needs {t}")
    places = sorted(got)

    def at(ps: list[int]) -> list[int]:
        return [decode(shamirs.interpolate([shamirs.share(p, got[p][1][k], PRIME)
                                            for p in ps])) for k in range(lines)]  # fmt: skip

    total = at(places[:t])
    if len(places) > t and at(places[-t:]) != total:
        return refuse("the sums disagree: one was changed or made wrong; ask again")
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    prop = {"path": f"secure-sum/{rnd[:12]}/total.txt",
            "data": "".join(f"{v}\n" for v in total), "cites": [],
            "claim": f"the total of {n} folders' results of job text {job}, by secure sum "
                     f"round {rnd}, from {len(places)} of its sums; no one's own number "
                     "was in any package"}  # fmt: skip
    subj, said = kart.propose(box, f"secure sum total of {rnd[:12]}", prop, now)
    if subj is None:
        print(said, end="")
        return refuse("the kernel didn't take the total as a proposal")
    row = kernel.append(box, ts, "summed", who="secure-sum", round=rnd,
                        packages=[got[p][0] for p in places], total=subj)  # fmt: skip
    print(f"  total          {' '.join(map(str, total))}  from {n} folders, "
          f"{len(places)} sums of {t} needed")  # fmt: skip
    print(f"total  {subj}  waiting on your seal; row {row['n']}")
    return kernel.ESCALATE


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
    why = missing()
    if why:
        return refuse(why)
    ts = opts.get("--now") or kernel.now()
    return {"split": do_split, "combine": do_combine, "total": do_total}[cmd](opts, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
