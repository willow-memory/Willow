"""quantized.py: the smallest local model that still gets your own questions right.

    python adapters/stdlib/quantized/quantized.py --box DIR --questions FILE
        [--url URL ...] [--model NAME ...]

Each model the local server offers (or each `--model` named) sits
model-exam's exam: every question in FILE that you sealed an answer for is
asked, with the passages your folder serves for it, and passes when the
reply cites a passage your answer cites and says what it says. The models
are then listed smallest first, by the size the server gives (Ollama's own
list gives each model's size and quantization; others give none), and the
smallest that passes every marked question is named.

    gemma3:1b    815319791 bytes  Q4_K_M  passed 3 of 4
    gemma3:4b   3338801804 bytes  Q4_K_M  passed 4 of 4
    smallest passing all 4: gemma3:4b, 3338801804 bytes

A model whose size the server doesn't give is listed after those it does,
and named only when none with a size passes.

Exit codes, the kernel's: 0 a model passed every marked question; 42 none
did, no question had a sealed answer, or no local server ran; 2 refused (a
bad command line, not a box, a record that doesn't verify, a URL off this
machine, a questions file that can't be read).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


exam = _load(
    "willow_model_exam_for_quantized", HERE.parent / "model-exam" / "model_exam.py"
)
lm = _load(
    "willow_local_model_for_quantized", HERE.parent / "local-model" / "local_model.py"
)

USAGE = (
    "usage: quantized.py --box DIR --questions FILE [--url URL ...] [--model NAME ...]"
)


def ollama_sizes(url: str) -> dict[str, tuple[int, str]]:
    """{model: (bytes, quantization)} from Ollama's /api/tags, where it answers."""
    base = url.rstrip("/")
    base = base[: -len("/v1")] if base.endswith("/v1") else base
    try:
        with urllib.request.urlopen(base + "/api/tags", timeout=5) as r:
            doc = json.loads(r.read().decode("utf-8"))
    except (OSError, ValueError):
        return {}
    out = {}
    for m in doc.get("models", []) if isinstance(doc, dict) else []:
        if (
            isinstance(m, dict)
            and isinstance(m.get("name"), str)
            and isinstance(m.get("size"), int)
        ):
            details = m.get("details") if isinstance(m.get("details"), dict) else {}
            out[m["name"]] = (
                m["size"],
                str(details.get("quantization_level") or "quantization not said"),
            )
    return out


def passes(
    box: Path, url: str, model: str, marked: list[tuple[str, dict, list[dict]]]
) -> int:
    """How many marked questions the model's replies pass, as model-exam marks them."""
    n = 0
    for q, prop, served in marked:
        reply = exam.oc.ask_model(url, model, exam.oc.messages(q, served))
        held, counted = exam.said(reply, prop.get("data", ""))
        cites_ok = bool(set(exam.oc.cited(reply, served)) & set(prop.get("cites", [])))
        n += cites_ok and counted > 0 and held >= kernel.HOLD * counted
    return n


def main(argv: list[str]) -> int:
    opts, urls, names, rest, it = {}, [], [], [], iter(argv)
    for a in it:
        if a == "--url":
            urls.append(next(it, ""))
        elif a == "--model":
            names.append(next(it, ""))
        elif a in ("--box", "--questions") and a not in opts:
            opts[a] = next(it, "")
        else:
            rest.append(a)
    if (
        rest
        or not opts.get("--box")
        or not opts.get("--questions")
        or "" in urls + names
    ):
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    off = [u for u in urls if not lm.on_this_machine(u)]
    if off:
        print(f"refused: not on this machine: {', '.join(off)}", file=sys.stderr)
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
    try:
        text = Path(opts["--questions"]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"refused: can't read the questions: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    sealed = exam.answers(box, rows)
    marked = []
    try:
        for q in dict.fromkeys(q.strip() for q in text.splitlines() if q.strip()):
            prop = sealed.get(kernel.bite_key(q) or "")
            served = exam.served_for(box, q) if prop else []
            if prop and served:
                marked.append((q, prop, served))
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return kernel.REFUSED
    if not marked:
        print(
            "nothing to mark: no question has an answer you sealed that your folder still serves"
        )
        return kernel.ESCALATE
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
    models = names or offered
    if not models:
        print(
            f"refused: {url} offers no model; name some with --model", file=sys.stderr
        )
        return kernel.REFUSED
    sizes = ollama_sizes(url)
    scored = []
    for m in dict.fromkeys(models):
        try:
            got = passes(box, url, m, marked)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
            print(f"unreachable: {url} ({e.__class__.__name__}), asking {m}")
            return kernel.ESCALATE
        scored.append((m, sizes.get(m), got))
    scored.sort(key=lambda s: (s[1] is None, s[1][0] if s[1] else 0, s[0]))
    width = max(len(m) for m, _, _ in scored)
    for m, size, got in scored:
        said = f"{size[0]} bytes  {size[1]}" if size else "size not said by the server"
        print(f"{m:<{width}}  {said}  passed {got} of {len(marked)}")
    best = next((s for s in scored if s[2] == len(marked)), None)
    if best is None:
        print(f"none passed all {len(marked)}")
        return kernel.ESCALATE
    size = f"{best[1][0]} bytes" if best[1] else "its size not said"
    print(f"smallest passing all {len(marked)}: {best[0]}, {size}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
