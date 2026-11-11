"""chain.py: a stack built by a chain of agents, each handed only what the
last one's run left: no person leads, a script carries the baton.

    python demo/shared-runs/chain.py start PROJECT
    python demo/shared-runs/chain.py handoff PROJECT LINK
    python demo/shared-runs/chain.py apply PROJECT LINK MODEL REPLY

`start` makes PROJECT, a folder outside the repository: the pile (this
repository cloned at demo/kept's pinned commit), a fresh box over it, and a
short stack, the first seven steps of demo/kept's, run once.

`handoff` prints what link LINK is handed, and nothing else is: the brief,
the line the hook-handoff add-on gives a new session about the one before,
what the handover add-on says of the project, the stack as it stands, and
the add-ons it may choose from, each with its card's one line.

`apply` takes a link's reply (`want:`, `step:`, `why:`, a line each). A
step that names no built add-on, repeats one that is there, reaches for a
key or a seal, or names a path of its own is refused and the stack is left
as it was. One that passes is added under its want and the stack is run
again, going on from what was kept. Either way the link's turn is over:
hook-handoff writes its Stop row on the record, and the outcome is one
line added to PROJECT/chain.jsonl.

Nothing is sealed, and the key `init` makes is never read. Exit codes, the
kernel's: 0 done (apply: the step was added and ran); 42 apply: the step
was refused, or ran and ended other than 0; 2 a bad command line.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = __doc__.split("\n\n")[1]
KEPT = ROOT / "demo" / "kept"
BRIEF = HERE / "trial-2" / "brief.txt"
ROLES = ("reads", "tools", "page", "makes")  # what a step of a stack can be
START_STEPS = 7  # demo/kept's stack through glance
PY = sys.executable


def stack_module():
    spec = importlib.util.spec_from_file_location(
        "stack", ROOT / "adapters/stdlib/stack/stack.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def catalog() -> dict[str, str]:
    """{add-on: its card's line}, for each built add-on a stack can run."""
    out = {}
    for card in sorted(ROOT.glob("adapters/*/*/README.md")):
        text = card.read_text(encoding="utf-8")
        if not text.startswith("<!-- willow-addon"):
            continue
        head = text.split("-->", 1)[0]
        role = re.search(r"^role: (.+)$", head, flags=re.M)
        line = re.search(r"^line: (.+)$", head, flags=re.M)
        if role and line and role.group(1) in ROLES:
            out[card.parent.name] = line.group(1)
    return out


def steps_of(text: str) -> list[tuple[str, str]]:
    """(add-on, its arguments as written) for each step line of a stack file."""
    return [tuple(m) for m in re.findall(r"^- ([a-z0-9-]+) -- (.*)$", text, flags=re.M)]


def placed(text: str, project: Path) -> str:
    return (
        text.replace("<scratch>", str(project))
        .replace("<pile>", str(project / "pile"))
        .replace("<repo>", str(ROOT))
    )


def scrub(text: str, project: Path) -> str:
    return (
        text.replace(str(project / "pile"), "<pile>")
        .replace(str(project), "<scratch>")
        .replace(str(ROOT), "<repo>")
    )


def run_stack(project: Path) -> int:
    (project / "stack.md").write_text(
        placed((project / "stack.txt").read_text(), project)
    )
    got = subprocess.run(
        [PY, str(ROOT / "adapters/stdlib/stack/stack.py"), "--box", str(project / "box"),
         "--stack", str(project / "stack.md"), "--to", str(project / "run"), "--resume"],
        capture_output=True, text=True, cwd=ROOT)  # fmt: skip
    (project / "page.txt").write_text(got.stdout)
    return got.returncode


def hook(project: Path, event: str, session: str) -> str:
    """What hook-handoff prints for this event: a Stop writes a row, a
    SessionStart gives the line about the session before."""
    call = {"hook_event_name": event, "session_id": session, "cwd": "<scratch>"}
    got = subprocess.run(
        [PY, str(ROOT / "adapters/stdlib/hook-handoff/hook_handoff.py"), "run", "--box", str(project / "box")],
        input=json.dumps(call), capture_output=True, text=True)  # fmt: skip
    try:
        return json.loads(got.stdout).get("additionalContext", "")
    except ValueError:
        return ""


def start(project: Path) -> int:
    pinned = re.search(r"^PINNED=([0-9a-f]{40})$", (KEPT / "rebuild.sh").read_text(), flags=re.M).group(1)  # fmt: skip
    if any(project.iterdir()) if project.exists() else False:
        print(f"refused: {project} is not empty", file=sys.stderr)
        return kernel.REFUSED
    for sub in ("run", "kept", "out"):
        (project / sub).mkdir(parents=True)
    subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(project / "pile")], check=True)  # fmt: skip
    subprocess.run(["git", "-C", str(project / "pile"), "checkout", "-q", "--detach", pinned], check=True)  # fmt: skip
    for name in ("questions.txt", "words.txt"):
        (project / name).write_text((KEPT / name).read_text())
    (project / "words.txt").chmod(0o600)
    lines, seen = [], 0
    for line in (KEPT / "stack.md").read_text().splitlines():
        lines.append(line)
        seen += line.startswith("- ")
        if seen == START_STEPS:
            break
    (project / "stack.txt").write_text("\n".join(lines) + "\n")
    subprocess.run(
        [PY, str(ROOT / "kernel.py"), "init", "--box", str(project / "box"), "--pile", str(project / "pile"),
         "--key", str(project / "scratch.key"), "--words", str(project / "words.txt")],
        check=True, capture_output=True)  # fmt: skip
    code = run_stack(project)
    print(f"started: {START_STEPS} steps, the stack's exit {code}")
    return kernel.ALIVE


def handoff(project: Path, link: str) -> str:
    before = (
        hook(project, "SessionStart", link)
        or "hook-handoff: no session before this one."
    )
    hand = subprocess.run(
        [PY, str(ROOT / "adapters/stdlib/handover/handover.py"), "--project", str(project)],
        capture_output=True, text=True).stdout  # fmt: skip
    cards = "\n".join(f"{name}: {line}" for name, line in catalog().items())
    parts = [
        BRIEF.read_text().rstrip(),
        "--- what the session before left (the hook-handoff add-on) ---\n" + before,
        "--- where the project stands (the handover add-on) ---\n"
        + scrub(hand, project).rstrip(),
        "--- the stack as it stands ---\n"
        + (project / "stack.txt").read_text().rstrip(),
        "--- the add-ons you may choose from, each with its card's line ---\n" + cards,
    ]
    return "\n\n".join(parts) + "\n"


def refusal(name: str, args: str, stack_text: str) -> str | None:
    """Why this step can't go on the stack, or None when it can."""
    if name not in catalog():
        return f"{name} is not a built add-on a stack can run"
    if (name, args) in steps_of(stack_text):
        return "that step is already on the stack"
    low = (
        f"{name} {args}".lower()
    )  # the add-on's own name counts: session-seal is a seal
    for word in ("seal", "decline", ".key", "--key", "propose"):
        if word in low:
            return f"a step may not name {word}"
    if ".." in args or re.search(r"(^|[\s=\"'])[/~]", args):
        return "a step names no path of its own: use {box}, <pile> or <scratch>"
    if re.search(r"<(?!pile>|scratch>)[a-z]+>", args):
        return "the only folders are {box}, <pile> and <scratch>"
    have = len(steps_of(stack_text))
    for taken in re.findall(r"\{(\d\d)(?:\.json)?\}", args):
        if not 1 <= int(taken) <= have:
            return f"step {taken} is not an earlier step"
    _, err = stack_module().parse_stack(stack_text + f"- {name} -- {args}\n")
    return f"the stack would not read: {err}" if err else None


def read_reply(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"want": [], "step": [], "why": []}
    for line in text.splitlines():
        key, sep, rest = line.partition(":")
        if sep and key.strip().lower() in out:
            out[key.strip().lower()].append(rest.strip())
    return out


def apply(project: Path, link: str, model: str, reply: str) -> dict:
    stack_text = (project / "stack.txt").read_text()
    said = read_reply(reply)
    done: dict = {"link": link, "model": model, "want": " ".join(said["want"]), "why": " ".join(said["why"])}  # fmt: skip
    m = (
        re.fullmatch(r"- ([a-z0-9-]+) -- (.*)", said["step"][0])
        if len(said["step"]) == 1
        else None
    )
    if not (m and len(said["want"]) == 1 and len(said["why"]) == 1):
        done["refused"] = "the reply is not one want, one step and one why"
    else:
        done["step"] = said["step"][0]
        done["refused"] = refusal(m.group(1), m.group(2), stack_text)
    if not done["refused"]:
        place = len(steps_of(stack_text)) + 1
        want = re.sub(r"\s+", " ", done["want"])
        (project / "stack.txt").write_text(
            f"{stack_text}# want ({link}, {model}): {want}\n{done['step']}\n"
        )
        done["stack_exit"] = run_stack(project)
        log = (project / "run" / "00-stack.txt").read_text()
        ended = re.findall(
            rf"^{place:02d} [a-z0-9-]+: (exit \d+|not run)", log, flags=re.M
        )
        done["ended"] = ended[-1] if ended else "no line in the log"
        files = sorted((project / "run").glob(f"{place:02d}-*.txt"))
        lines = files[0].read_text(errors="replace").splitlines() if files else []
        done["first_line"] = scrub(lines[0], project)[:200] if lines else ""
        done["place"] = place
    hook(project, "Stop", link)
    with (project / "chain.jsonl").open("a") as f:
        f.write(json.dumps(done, ensure_ascii=False) + "\n")
    return done


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "start":
        return start(Path(argv[1]).resolve())
    if len(argv) == 3 and argv[0] == "handoff" and Path(argv[1]).is_dir():
        sys.stdout.write(handoff(Path(argv[1]).resolve(), argv[2]))
        return kernel.ALIVE
    if (
        len(argv) == 5
        and argv[0] == "apply"
        and Path(argv[1]).is_dir()
        and Path(argv[4]).is_file()
    ):
        done = apply(
            Path(argv[1]).resolve(), argv[2], argv[3], Path(argv[4]).read_text()
        )
        print(json.dumps(done, ensure_ascii=False))
        ok = not done["refused"] and done.get("ended") == "exit 0"
        return kernel.ALIVE if ok else kernel.ESCALATE
    print(USAGE, file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
