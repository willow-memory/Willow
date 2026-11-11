"""dp.py: noise on a count before it leaves, by OpenDP, so one person's number
doesn't give away what their folder holds.

    python adapters/deps/dp/dp.py noise --box DIR --result proposal:<sha256> --epsilon E [--per-item N] [--now TS]
    python adapters/deps/dp/dp.py spent --box DIR

`noise` takes a kart result of yours, whole numbers that a job printed over
your folder, and proposes the same numbers with OpenDP's discrete Laplace
noise added to each, as a new answer of yours waiting on your seal. Seal that
one, not the first, and send it with share: the true numbers stay in your
box. The claim keeps the result's tools and job text, so kart's `gather`
adds noisy results as it adds any others.

`--epsilon` is how much privacy the numbers spend: smaller is noisier and
safer. `--per-item` is how far one item of your folder (a line, a file, as
the job counts) can move each number: 1 for a count of lines. OpenDP works
out the noise for both and checks the spend, not this file. A result is
noised once: noised again, the copies average back to the truth, so a
second `noise` of the same result is refused. Each spend is a `noised` row
on your record, never the numbers; `spent` adds them up, by job.

Exit codes, the kernel's: 0 what was spent printed; 42 the noisy numbers
proposed, waiting on your seal; 2 refused (no OpenDP, not a kart result of
yours, not numbers, noised already, a bad epsilon).
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

sys.path.insert(0, str(ROOT / "adapters" / "deps" / "kart"))
import kart  # noqa: E402

FLAGS = {
    "noise": ({"--box", "--result", "--epsilon"}, {"--per-item", "--now"}),
    "spent": ({"--box"}, set()),
}
ALPHA = 0.05  # the accuracy said: each number is within it 95 times in 100
TAIL = re.compile(r"(; tools [0-9a-f]{64})?; job text [0-9a-f]{64}$")


def refuse(why: str) -> int:
    return kart.refuse(why)


def noisy(numbers: list[int], epsilon: float, per_item: int) -> tuple[list[int], dict]:
    """(the numbers with noise, how): OpenDP's discrete Laplace over the
    vector, its scale set so one item moving every number by `per_item`
    spends `epsilon`, and that spend checked by OpenDP's own map."""
    import opendp.prelude as dp  # noqa: PLC0415

    dp.enable_features("contrib")
    d_in = per_item * len(numbers)  # one item, every number: the l1 bound
    scale = d_in / epsilon
    m = dp.m.make_laplace(
        dp.vector_domain(dp.atom_domain(T=int)), dp.l1_distance(T=int), scale=scale
    )
    spent = m.map(d_in)
    if spent > epsilon * (1 + 1e-9):
        raise ValueError(f"OpenDP says this spends {spent}, more than {epsilon}")
    out = [int(x) for x in m(numbers)]
    import opendp  # noqa: PLC0415

    how = {"mechanism": "discrete laplace", "scale": scale, "spent": spent,
           "within": dp.discrete_laplacian_scale_to_accuracy(scale, ALPHA),
           "opendp": getattr(opendp, "__version__", "")}  # fmt: skip
    return out, how


def mine(box: Path, rows: list[dict], subj: str) -> tuple[dict | None, str | None]:
    """(the result's proposal, why not): a kart result proposed in this box,
    not declined, of numbers, not itself noised, and never noised before."""
    if not re.fullmatch(r"proposal:[0-9a-f]{64}", subj):
        return None, "--result is proposal:<sha256>"
    if not any(r["kind"] == "proposal" and r.get("subject") == subj
               and r.get("verdict") == "pass" for r in rows):  # fmt: skip
        return None, f"{subj} is not a proposal of yours in this box"
    if subj in kernel.declined(box, rows):
        return None, f"{subj} is one you declined"
    try:
        prop = json.loads((box / "proposals" / f"{subj[9:]}.json").read_text())
    except (OSError, ValueError):
        return None, f"{subj}'s proposal file is missing or can't be read"
    if kernel.subject_of(prop) != subj:
        return None, f"{subj}'s proposal file is not the bytes that were proposed"
    path = str(prop.get("path", ""))
    if not path.startswith("kart/results/") or not TAIL.search(prop.get("claim", "")):
        return None, f"{subj} is not a kart result (kart.py run proposes those)"
    if path.startswith("kart/results/dp-"):
        return None, f"{subj} is noised already; noise the result it came from"
    if not kart.shaped(prop["data"], "numbers"):
        return None, f"{subj} isn't numbers, one a line; only counts are noised"
    had = next(
        (r for r in rows if r["kind"] == "noised" and r.get("result") == subj), None
    )
    if had is not None:
        return None, (f"{subj} was noised at row {had['n']}; noised twice, the "
                      "copies average back to the truth")  # fmt: skip
    return prop, None


def do_noise(opts: dict, ts: str) -> int:
    box = Path(opts["--box"])
    rows, why = kart.box_rows(box)
    if why:
        return refuse(why)
    try:
        epsilon = float(opts["--epsilon"])
        per_item = int(opts.get("--per-item", "1"))
    except ValueError:
        return refuse("--epsilon is a number and --per-item a whole one")
    if not (math.isfinite(epsilon) and 0 < epsilon <= 10) or per_item < 1:
        return refuse("--epsilon is above 0 and at most 10, --per-item at least 1")
    if importlib.util.find_spec("opendp") is None:
        return refuse(
            "OpenDP isn't installed: pip install -r adapters/deps/dp/requirements.txt"
        )
    subj = opts["--result"]
    prop, why = mine(box, rows, subj)
    if why:
        return refuse(why)
    numbers = [int(x) for x in prop["data"].strip().splitlines()]
    try:
        out, how = noisy(numbers, epsilon, per_item)
    except Exception as e:  # noqa: BLE001  OpenDP's refusal, said in its words
        return refuse(f"OpenDP refused: {str(e).strip().splitlines()[0][:200]}")
    tail = TAIL.search(prop["claim"])[0]
    job = tail.rpartition("job text ")[2]
    row = kernel.append(box, ts, "noised", who="dp", result=subj, job=job,
                        epsilon=epsilon, per_item=per_item, lines=len(numbers), **how)  # fmt: skip
    within = how["within"]
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    res = {"path": f"kart/results/dp-{subj[9:21]}.txt",
           "data": "".join(f"{x}\n" for x in out), "cites": [],
           "claim": f"result {subj} with OpenDP's discrete Laplace noise, epsilon "
                    f"{epsilon:g} for {per_item} an item, each number within {within:g} "
                    f"of the truth 95 times in 100, noised at row {row['n']}{tail}"}  # fmt: skip
    nsubj, said = kart.propose(box, f"dp noise {subj}", res, now)
    if nsubj is None:
        print(said, end="")
        return refuse("the kernel didn't take the noisy numbers as a proposal")
    print(f"noised {subj}  epsilon {epsilon:g}, each number within {within:g} "
          f"95 times in 100, row {row['n']}")  # fmt: skip
    print(
        f"noisy  {nsubj}  waiting on your seal; seal this one, not {subj[:21]}…, to send"
    )
    return kernel.ESCALATE


def do_spent(opts: dict) -> int:
    box = Path(opts["--box"])
    rows, why = kart.box_rows(box)
    if why:
        return refuse(why)
    by_job: dict[str, float] = {}
    for r in rows:
        if r["kind"] == "noised":
            by_job[r["job"]] = by_job.get(r["job"], 0.0) + float(r["epsilon"])
    for job, eps in sorted(by_job.items(), key=lambda x: -x[1]):
        print(f"  job text {job[:12]}…  epsilon {eps:g}")
    print(f"spent  epsilon {sum(by_job.values()):g} over {len(by_job)} jobs")
    return kernel.ALIVE


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
    if cmd == "spent":
        return do_spent(opts)
    ts = opts.get("--now") or kernel.now()
    return do_noise(opts, ts)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
