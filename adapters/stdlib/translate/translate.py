"""translate.py: an answer you sealed, translated by a local model, held for your seal.

    python adapters/stdlib/translate/translate.py --box DIR --into LANGUAGE
        [--url URL ...] [--model NAME] [--now TS] "your question"

The answer is the one you sealed for the question's words. A model on this
machine (the first local server answering, found as local-model finds one)
translates it into LANGUAGE, told to keep each citation, [1], where it
belongs. The translation is proposed as the answer to its own question,
"your question in LANGUAGE", so it never stands in for the original: once
you seal it, that question is answered by it.

    Lard, no mantequilla, y una cucharada de anís [1].
    pass  proposal:5e0c…  waiting on your seal

The proposal keeps the original beside the translation, cites the
original's passages that the new question's bite serves, and names the
original's proposal in its claim. A translation whose citations aren't the
original's ([1] dropped, a [3] made up) is printed and proposed to no one.

Exit codes, the kernel's: 0 a translation waits on your seal, or one is
sealed already; 42 no answer you sealed for the question, no local server
running, or a translation whose citations differ; 2 refused (a bad command
line, a URL off this machine, not a box).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


oc = _load("willow_openai_compatible_for_translate",
           HERE.parent / "openai-compatible" / "openai_compatible.py")  # fmt: skip
lm = _load(
    "willow_local_model_for_translate", HERE.parent / "local-model" / "local_model.py"
)

USAGE = (
    "usage: translate.py --box DIR --into LANGUAGE [--url URL ...] [--model NAME]"
    ' [--now TS] "your question"'
)
#: between the translation and the original it keeps beside it
SPLIT = "\n\nOriginal:\n\n"
CITE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
RULE = (
    "Translate the user's text into {into}. Keep every citation in square"
    " brackets, like [1], exactly as it is, beside the words it belongs to."
    " Reply with the translation alone."
)


def citations(text: str) -> list[int]:
    return sorted(
        {int(n) for m in CITE.finditer(text) for n in re.split(r"\s*,\s*", m.group(1))}
    )


def sealed_answer(
    box: Path, rows: list[dict], question: str
) -> tuple[str, dict] | None:
    """(subject, proposal) of the answer you sealed for the question's words."""
    want = kernel.bite_key(question)
    for subj, seal in sorted(kernel.sealed(box, rows).items(), key=lambda x: x[1]["n"]):
        prop, asked, why = kernel.standing(box, rows, subj, seal)
        if why is None and asked == want:
            return subj, prop
    return None


def main(argv: list[str]) -> int:
    opts, urls, words, it = {}, [], [], iter(argv)
    for a in it:
        if a == "--url":
            urls.append(next(it, ""))
        elif a in ("--box", "--into", "--model", "--now") and a not in opts:
            opts[a] = next(it, "")
        else:
            words.append(a)
    if (not opts.get("--box") or not opts.get("--into") or "" in urls or "" in opts.values()
            or len(words) != 1 or words[0].startswith("--") or not kernel.bite_key(words[0])):  # fmt: skip
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    question, into = words[0], opts["--into"].strip()
    off = [u for u in urls if not lm.on_this_machine(u)]
    if off:
        print(f"refused: not on this machine: {', '.join(off)}; translate asks a local model",
              file=sys.stderr)  # fmt: skip
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
    found = sealed_answer(box, rows, question)
    if found is None:
        print("no answer you sealed for that; nothing to translate")
        return kernel.ESCALATE
    subj, original = found
    asked = f"{question} in {into}"
    done = sealed_answer(box, rows, asked)
    if done is not None:
        print(f"sealed already: {done[1]['data'].split(SPLIT)[0].strip()}")
        return kernel.ALIVE
    tried = urls or [u for _, u in lm.known([])]
    url, offered = None, None
    for u in tried:
        offered = lm.models(u)
        if offered is not None:
            url = u
            break
    if url is None:
        print(f"no local model server is running (looked at {', '.join(tried)})")
        return kernel.ESCALATE
    model = opts.get("--model") or (offered[0] if offered else "")
    if not model:
        print(f"refused: {url} offers no model; name one with --model", file=sys.stderr)
        return kernel.REFUSED
    chat = [{"role": "system", "content": RULE.format(into=into)},
            {"role": "user", "content": original["data"]}]  # fmt: skip
    try:
        reply = oc.ask_model(url, model, chat).strip()
    except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
        print(f"unreachable: {url} ({e.__class__.__name__})")
        return kernel.ESCALATE
    print(reply)
    if citations(reply) != citations(original["data"]):
        print(f"its citations {citations(reply)} aren't the original's "
              f"{citations(original['data'])}; proposed to no one")  # fmt: skip
        return kernel.ESCALATE
    now = ["--now", opts["--now"]] if opts.get("--now") else []
    code, out = oc.kernel_says(["bite", "--box", str(box), *now, asked])
    try:
        doc = json.loads(out)
    except ValueError:
        print(out, end="")
        return code
    if doc.get("state") == "sealed":
        print(f"sealed already: {doc['answer'].split(SPLIT)[0].strip()}")
        return kernel.ALIVE
    served = {s["id"] for s in doc.get("served", [])}
    row = {
        "path": f"answers/{oc.slug(question)}.{oc.slug(into)}.md",
        "data": f"{reply}{SPLIT}{original['data'].strip()}\n",
        "cites": [c for c in original.get("cites", []) if c in served],
        "claim": f"{model} at {url} translated {subj} into {into}",
    }
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "translation.jsonl"
        f.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        _, out = oc.kernel_says(["propose", "--box", str(box), *now, "--file", str(f)])
    print(out, end="")
    return kernel.ALIVE if out.split()[:1] == ["pass"] else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
