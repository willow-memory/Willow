"""sort_ask.py: a local model suggests a category for each file sort left
unsorted or in more than one, and the kernel holds each for your seal.
Python 3.9+, stdlib only.

    python adapters/stdlib/sort-ask/sort_ask.py --box DIR --categories FILE \\
        --model NAME [--url URL] [--reasoning EFFORT] [--limit N] [--now TS] [--json]

sort places what your own phrases reach; this is the rung after it. For each
file sort left unsorted, or in more than one category, and with no
suggestion standing for it yet:

1. the kernel bites on the file's own opening words, so the question is on
   your record and the passages that hold it are served; a file none of whose
   passages are served is skipped and said, never guessed at;
2. the model at URL (Ollama's http://127.0.0.1:11434/v1 unless you say)
   is sent labelled facts and one return line: your categories with their
   phrases, the file's place, and its served passages numbered, then "Return
   one line: CATEGORY [n], or NONE". A URL off this machine (anything but a
   loopback address or localhost) is refused before anything is sent: the
   model on this machine, nothing else;
3. an answer naming one of your categories and citing a served passage goes
   to the kernel's door as a suggestion: this file, that category, from that
   passage. Anything else is said and proposed to no one.

Nothing is placed here: a suggestion waits for your seal, and a seal is the
correction your record keeps. Asked through openai-compatible's ask, at
temperature 0 with its own fixed seed; `--reasoning none|low|medium|high`
asks a thinking model to think that much, and its claim says so.
`--limit N` asks about the first N such files (in sort's order), since a
small model on a laptop takes seconds a file.

It prints a report (adapters/stdlib/ci/README.md, the report contract): the
suggestions made, the files skipped and why. Exit codes, the kernel's: 0
nothing left to ask about (empty); 42 suggestions wait on your seal, or files
were asked and none fitted (populated), or the model wasn't reachable
(unreachable); 2 refused.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import ipaddress
import json
import re
import sys
import tempfile
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

sys.path.insert(0, str(HERE.parent / "sort"))
import sort  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_openai_compatible_for_sort_ask",
    HERE.parent / "openai-compatible" / "openai_compatible.py",
)
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)  # its ask and its claim, the suggestions contract's

NAME = "sort-ask"
URL = "http://127.0.0.1:11434/v1"
SEED, PASSAGES, CUT, OPENING = 7, 4, 600, 30
RULE = (
    "You sort one file into one of a person's categories, from its passages "
    "only. Answer with exactly one line: the category's name as written, then "
    "the number of the passage that shows it, as `money [2]`. If no category "
    "fits, answer NONE."
)


def on_this_machine(url: str) -> bool:
    host = urllib.parse.urlsplit(url).hostname or ""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def kernel_says(argv: list[str]) -> tuple[int, str]:
    got = io.StringIO()
    with contextlib.redirect_stdout(got), contextlib.redirect_stderr(got):
        code = kernel.main(argv)
    return code, got.getvalue()


def messages(cats: dict, path: str, served: list[dict]) -> list[dict]:
    """Labelled facts and one return line: what a small model reads right."""
    listed = "\n".join(
        f"- {n}: {', '.join(s for s, _ in ps)}" for n, ps in cats.items()
    )
    passages = "\n\n".join(f"[{i}] ({s['where']})\n{s['text'][:CUT]}"
                            for i, s in enumerate(served, 1))  # fmt: skip
    # an example that is none of the person's names: one of theirs would
    # be copied (a 3B model answered the example's name for an allotment)
    example = next(
        w
        for w in ("fruit", "weather", "music", "sport")
        if w not in {n.lower() for n in cats}
    )
    user = (f"Categories, each with words that mean it:\n{listed}\n\nFile: {path}\n\n"
            f"Passages:\n\n{passages}\n\nWhich one category is this file about? "
            f"Answer with one line: a name from the list and the passage that shows it, "
            f"for example `{example} [1]` if the list had {example}. If none fits, answer NONE.")  # fmt: skip
    return [{"role": "system", "content": RULE}, {"role": "user", "content": user}]


def answer(reply: str, cats: dict, served: list[dict]) -> tuple[str, str] | None:
    """(category, the served passage's id) from the reply's first line, or
    None: a category of yours, as written but for case, and a passage served."""
    first = (reply.strip().splitlines() or [""])[0]
    first = re.sub(r"(?i)^\s*(?:category\s*:?\s*|answer\s*:\s*)", "", first)
    m = re.match(r"\s*`?([^\[`]+?)`?\s*\[(\d+)\]", first)
    if not m:
        return None
    by = {n.lower(): n for n in cats}
    name, i = by.get(m.group(1).strip().lower()), int(m.group(2))
    if name is None or not 1 <= i <= len(served):
        return None
    return name, served[i - 1]["id"]


def asked(box: Path) -> set[str]:
    """The paths a suggestion already stands under, sealed or waiting."""
    out = set()
    for p in (box / "proposals").glob("*.json"):
        try:
            out.add(json.loads(p.read_text(encoding="utf-8"))["path"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return out


def where_for(path: str) -> str:
    """The box path a file's suggestion goes under: sort/<the file>.txt."""
    return "sort/" + path + ".txt"


# ── the report: the shape every report add-on prints (ci/README.md) ─────────
def report(addon: str, state: str, said: str, groups: list) -> dict:
    """A report: its state, one line said, and each group's rows (where,
    what); a group named None comes first and has no heading."""
    return {"addon": addon, "state": state, "said": said,
            "groups": [{"name": g, "rows": [{"where": w, "what": x} for w, x in rows]}
                       for g, rows in groups if rows]}  # fmt: skip


def report_text(doc: dict) -> str:
    """A report as every report add-on prints it: the same twenty lines each
    keeps, held to this one by test_contract.py."""
    rows = [r for g in doc["groups"] for r in g["rows"]]
    w = min(max((len(r["where"]) for r in rows), default=0), 60)
    out = [f"{doc['addon']}: {doc['state']}, {doc['said']}"]
    for g in doc["groups"]:
        if g["name"] is not None:
            out.append(f"## {g['name']}")
        out += [f"  {r['where']:<{w}}  {r['what']}".rstrip() for r in g["rows"]]
    return "\n".join(out)


def say(doc: dict, as_json: bool) -> None:
    print(json.dumps(doc, ensure_ascii=False) if as_json else report_text(doc))


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    opts = dict(zip(argv[::2], argv[1::2]))
    known = {
        "--box",
        "--categories",
        "--model",
        "--url",
        "--reasoning",
        "--limit",
        "--now",
    }
    if (len(argv) % 2 or set(opts) - known or not {"--box", "--categories", "--model"} <= set(opts)
            or "" in opts.values() or opts.get("--reasoning", "none") not in oc.REASONING):  # fmt: skip
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    url, now = (
        opts.get("--url", URL),
        (["--now", opts["--now"]] if opts.get("--now") else []),
    )
    if not on_this_machine(url):
        print(
            f"refused: {url} isn't on this machine; only a model here is asked",
            file=sys.stderr,
        )
        return kernel.REFUSED
    try:
        limit = int(opts.get("--limit", "0")) or None
    except ValueError:
        print("refused: --limit is a whole number", file=sys.stderr)
        return kernel.REFUSED
    box = Path(opts["--box"])
    if not (box / "kernel.json").exists():
        print("refused: not a kernel box; init first", file=sys.stderr)
        return kernel.REFUSED
    try:
        cats = sort.categories(Path(opts["--categories"]).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        print(f"refused: can't read {opts['--categories']}", file=sys.stderr)
        return kernel.REFUSED
    if not cats:
        print(
            "refused: no category in it: a line is `name: phrase, phrase`",
            file=sys.stderr,
        )
        return kernel.REFUSED
    pile = kernel.chunks(Path(kernel.config(box)["pile"]))
    _, more, none = sort.placed(sort.sort(pile, cats), list(cats))
    standing = asked(box)
    todo = [p for p, _ in more + none if where_for(p) not in standing]
    if limit:
        todo = todo[:limit]
    if not todo:
        say(
            report(
                NAME,
                "empty",
                "no file left to ask about: every one is sorted or has a suggestion",
                [],
            ),
            as_json,
        )
        return kernel.ALIVE
    first = {}
    for c in pile:
        first.setdefault(c["path"], c["text"])
    made, skipped = [], []
    for path in todo:
        question = " ".join(kernel.words(first.get(path, ""))[:OPENING])
        if not question:
            skipped.append((path, "no words to ask with"))
            continue
        code, out = kernel_says(["bite", "--box", str(box), *now, question])
        try:
            doc = json.loads(out)
        except ValueError:
            skipped.append((path, "the kernel refused the bite"))
            continue
        # the file's own passages, an echo of its opening words among them: for
        # sorting, the passage itself is what the model should read
        served = [s for s in doc.get("served", [])
                  if s.get("where", "").startswith(path + ":")][:PASSAGES]  # fmt: skip
        if not served:
            skipped.append((path, "none of its passages was served"))
            continue
        try:
            reply = oc.ask_model(url, opts["--model"], messages(cats, path, served),
                                 opts.get("--reasoning", ""), seed=SEED)  # fmt: skip
        except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
            say(report(NAME, "unreachable", f"{url} didn't answer ({e.__class__.__name__}); "
                       f"{len(made)} suggested before it stopped", [("suggested", made)]), as_json)  # fmt: skip
            return kernel.ESCALATE
        got = answer(reply, cats, served)
        if got is None:
            line = (reply.strip().splitlines() or ["(nothing)"])[0][:80]
            skipped.append((path, f"no category of yours, cited: {line}"))
            continue
        name, cite = got
        row = {"path": where_for(path), "data": name + "\n", "cites": [cite],
               "claim": oc.claim(opts["--model"], f"at {url}", oc.settings(SEED, opts.get("--reasoning", "")),
                                 f"read {path} as {name}, from the passage it cited")}  # fmt: skip
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "suggestion.jsonl"
            f.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
            _, out = kernel_says(["propose", "--box", str(box), *now, "--file", str(f)])
        if out.split()[:1] == ["pass"]:
            made.append((path, f"{name}  (waits on your seal)"))
        else:
            skipped.append((path, f"the door refused it: {out.strip()[:60]}"))
    said = f"{len(made)} suggestion{'s' if len(made) != 1 else ''} of {len(todo)} file{'s' if len(todo) != 1 else ''} asked about, by {opts['--model']}"
    if not made:
        say(
            report(
                NAME,
                "populated" if skipped else "empty",
                said,
                [("not suggested", skipped)],
            ),
            as_json,
        )
        return kernel.ESCALATE if skipped else kernel.ALIVE
    say(
        report(
            NAME, "populated", said, [("suggested", made), ("not suggested", skipped)]
        ),
        as_json,
    )
    return kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
