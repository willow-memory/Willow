"""askable.py: what Leo was sent, and three ways of having his box answer
from it.

    python demo/wards/askable.py run --life DIR --to DIR

A package taken in is a row on the record: who signed it, and that it
held. Its words are not in the box, so the kernel, which answers from
files, cannot answer from it. That came up three times in these scenes.
This plays fourteen.py, then asks Leo's box four questions about what his
parents told him, with his pile made three ways:

    as it is          his own files only, as the scenes leave it
    packages dropped  the three package files copied into his pile
    written out       each package written out as a page of its own: who
                      said it, when, under which key, that it was received
                      and not sealed by him, and where in their files it
                      came from

It prints what each serves first. Nothing here is an add-on; the third
way is done by hand, to see what one would have to do. Exit 0 when run,
2 a bad command.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fourteen  # noqa: E402
from scene import KERNEL  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
ASKED = (
    "what did Dad say about the brown inhaler",
    "what did Mum say changed at the review",
    "how many puffs of the brown inhaler",
    "what did the nurse say the plan is at both homes",
)
SENT = (
    ("dana-to-leo", "Mum"),
    ("ravi-to-leo", "Dad"),
    ("nurse-to-leo", "the asthma nurse"),
)


def page(package: dict, who: str) -> str:
    """One package as a page a person could read, and the kernel can serve."""
    out = [
        f"# Received from {who}, not sealed by me",
        "",
        f'Sent {package["ts"]}, signed by the key {package["from"][:12]}. Their note: "{package["note"]}"',
        "",
    ]  # fmt: skip
    for a in package["answers"]:
        out += [
            f"{who} says: {a['data']}",
            f"Their reason: {a['claim']}. It is from {', '.join(a['places'].values())} in their own files, which I do not have.",
            "",
        ]  # fmt: skip
    return "\n".join(out)


def ways(life: Path, played: Path) -> dict:
    def none(pile: Path) -> None:
        pass

    def dropped(pile: Path) -> None:
        for name, _ in SENT:
            shutil.copy(played / f"{name}.pkg", pile / "received" / f"{name}.pkg")

    def written(pile: Path) -> None:
        for name, who in SENT:
            package = json.loads((played / f"{name}.pkg").read_text(encoding="utf-8"))
            (pile / "received" / f"{name}.md").write_text(
                page(package, who), encoding="utf-8"
            )

    return {"as it is": none, "packages dropped": dropped, "written out": written}


def run(life: Path, to: Path) -> dict:
    played = to / "played"
    doc = fourteen.Fourteen(life, played).play()
    if doc["wrong"]:
        raise ValueError("fourteen.py did not play as told")
    out: dict = {}
    for n, (name, fill) in enumerate(ways(life, played).items()):
        pile, box = to / f"way-{n}" / "pile", to / f"way-{n}" / "box"
        shutil.copytree(life / "leo-own", pile)
        (pile / "received").mkdir()
        fill(pile)
        subprocess.run([sys.executable, str(KERNEL), "init", "--box", str(box), "--pile", str(pile),
                        "--key", str(to / f"way-{n}" / "key")], capture_output=True)  # fmt: skip
        out[name] = {}
        for q in ASKED:
            got = subprocess.run([sys.executable, str(KERNEL), "bite", "--box", str(box), q],
                                 capture_output=True, text=True).stdout  # fmt: skip
            first = (json.loads(got).get("served") or [{}])[0]
            out[name][q] = {"where": first.get("where", ""), "readable": first.get("text", "x")[:1] != "{",
                            "says_whose": "not sealed by me" in first.get("text", "") or " says: " in first.get("text", "")}  # fmt: skip
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[0] != "run" or {argv[1], argv[3]} != {"--life", "--to"}:
        print(USAGE, file=sys.stderr)
        return 2
    opts = {argv[1]: argv[2], argv[3]: argv[4]}
    life, to = Path(opts["--life"]), Path(opts["--to"]).resolve()
    if (
        not (life / "leo-own").is_dir()
        or to.exists()
        or to.is_relative_to(HERE.parents[1])
    ):
        print("refused: --life is what make_life.py wrote; --to is new and outside the repository", file=sys.stderr)  # fmt: skip
        return 2
    to.mkdir()
    out = run(life, to)
    print()
    for name, asked in out.items():
        print(f"── {name}")
        for q, got in asked.items():
            said = got["where"] or "nothing"
            if got["where"] and not got["readable"]:
                said += ", as raw JSON"
            print(f"  {q}: {said}")
    (to / "askable.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
