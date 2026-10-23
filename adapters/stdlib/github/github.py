"""github.py: what willow's repo needs from GitHub, and only from GitHub.

    python adapters/stdlib/github/github.py report < ISSUE_BODY
    python adapters/stdlib/github/github.py check

`report` reads a security report's body, the issue form's "Where it is"
section, one place per line, and prints the comment the security workflow
posts on it: each pull request that wrote those lines, found by
adapters/stdlib/ci/whose.py with this folder's host.json, and its author,
asked of GitHub with `gh`. None of the report's own text reaches the
comment, so a report can't make it tag anyone.

`check` holds `.github/` to the repo: the CI matrix starts at the Python
the kernel names, and the README (its words and its badges) and FILES.md
quote the matrix as it is; the CI badge names a workflow that exists;
the idea form offers the add-on list's own sections and `writes` values;
the changelog job skips Dependabot's pull requests and no one else's;
the security form asks under the heading `report` reads.

Delete this folder and `.github/`, and willow runs and tests the same on
your own machine; a host of another kind gets a folder of its own beside
this one, with its own host.json.

Exit codes, the kernel's: 0 the comment printed, or `.github/` holds; 2 it
doesn't, or a bad command line.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: github.py report < ISSUE_BODY | github.py check"
SECTION = "Where it is"
WHOSE = ROOT / "adapters" / "stdlib" / "ci" / "whose.py"
DOT = ROOT / ".github"
#: the changelog job runs on every pull request but Dependabot's, which can't
#: write an entry and isn't listed; no other author is skipped
CHANGELOG_IF = ("github.event_name == 'pull_request' && "
                "github.event.pull_request.user.login != 'dependabot[bot]'")  # fmt: skip


def places(body: str) -> list[str]:
    """The lines of the form's "Where it is" section, blanks and fences out."""
    m = re.search(
        rf"^### {re.escape(SECTION)}\s*\n(.*?)(?=^### |\Z)", body, re.M | re.S
    )
    lines = m.group(1).splitlines() if m else []
    return [ln for ln in (x.strip() for x in lines)
            if ln and ln != "_No response_" and not ln.startswith("```")]  # fmt: skip


def author(label: str) -> str | None:
    got = subprocess.run(["gh", "pr", "view", label.lstrip("#"), "--json", "author",
                          "--jq", ".author.login"], capture_output=True, text=True)  # fmt: skip
    login = got.stdout.strip()
    return login if got.returncode == 0 and re.fullmatch(r"[\w-]+(\[bot\])?", login) else None  # fmt: skip


def report(body: str) -> str:
    """The comment for one security report."""
    named = places(body)
    if not named:
        return ("No lines were named under \"Where it is\", so no pull request was "
                "looked up.\n")  # fmt: skip
    got = subprocess.run([sys.executable, str(WHOSE), "--host", str(HERE), "-"],
                         input="\n".join(named), capture_output=True, text=True)  # fmt: skip
    if got.returncode == kernel.REFUSED:
        return ("The places under \"Where it is\" couldn't be looked up. Each should "
                "be PATH:FIRST-LAST, a line range in a file in the repo.\n")  # fmt: skip
    if got.returncode != kernel.ALIVE:
        return "No pull request wrote the lines this report names: they landed before pull requests.\n"  # fmt: skip
    rows = []
    for line in got.stdout.splitlines():
        label, where = line.split(" ", 1)
        who = author(label)
        rows.append(f"- {label} ({where})" + (f", by @{who}" if who else ""))
    return ("The lines this report names were written by:\n\n" + "\n".join(rows)
            + "\n\nTagged so you hear about it from the start. Nothing here says who "
            "is at fault: the lines are a place to begin.\n")  # fmt: skip


# ── check: .github/ held to the repo ─────────────────────────────────────────
def matrix(ci: str) -> list[str]:
    return re.findall(
        r'"(3\.\d+)"', re.search(r"python-version: \[(.*?)\]", ci).group(1)
    )


def problems() -> list[str]:
    out = []
    versions = matrix((DOT / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    first, last = versions[0], versions[-1]
    head = (ROOT / "kernel.py").read_text(encoding="utf-8").splitlines()[0]
    if f"Python {first}+" not in head:
        out.append(
            f"ci.yml's matrix starts at {first}, not at the Python kernel.py names"
        )
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    if f"Python {first} through {last}" not in readme:
        out.append(
            f"README.md doesn't say the tests run on Python {first} through {last}"
        )
    files = " ".join((ROOT / "FILES.md").read_text(encoding="utf-8").split())
    if f"tests on Python {first} to {last}" not in files:
        out.append(f"FILES.md's ci.yml line doesn't say Python {first} to {last}")

    spec = importlib.util.spec_from_file_location(
        "willow_readme_for_github",
        ROOT / "adapters" / "stdlib" / "readme" / "readme.py",
    )
    rd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rd)
    form = (DOT / "ISSUE_TEMPLATE" / "idea.yml").read_text(encoding="utf-8")

    def options(field: str) -> list[str]:
        block = form.split(f"id: {field}\n", 1)[1].split("validations:", 1)[0]
        return re.findall(r"^        - (.+)$", block, re.M)

    if options("section") != rd.NAMES:
        out.append("idea.yml's sections aren't the add-on list's")
    if sorted(o.split()[0] for o in options("writes")) != sorted(rd.WRITES):
        out.append("idea.yml's writes values aren't the ones readme.py takes")

    badge = re.search(
        r"img\.shields\.io/badge/python-([\d.]+)%20to%20([\d.]+)-", readme
    )
    if not badge or badge.groups() != (first, last):
        out.append(f"README.md's Python badge doesn't say {first} to {last}")
    for flow in re.findall(r"github\.com/willow-memory/Willow/actions/workflows/([\w.-]+)/badge\.svg", readme):  # fmt: skip
        if not (DOT / "workflows" / flow).is_file():
            out.append(
                f"README.md's CI badge names {flow}, which .github/workflows/ doesn't hold"
            )
    ci = (DOT / "workflows" / "ci.yml").read_text(encoding="utf-8")
    job = re.search(r"^  changelog:\n(.*?)(?=^  \S|\Z)", ci, re.M | re.S)
    if not job or f"    if: {CHANGELOG_IF}\n" not in job.group(1):
        out.append(
            "ci.yml's changelog job doesn't run on every pull request but Dependabot's"
        )
    security = (DOT / "ISSUE_TEMPLATE" / "security.yml").read_text(encoding="utf-8")
    if f"label: {SECTION}\n" not in security:
        out.append(f'security.yml has no "{SECTION}" field for report to read')
    return out


def main(argv: list[str]) -> int:
    if argv == ["report"]:
        print(report(sys.stdin.read()), end="")
        return kernel.ALIVE
    if argv == ["check"]:
        bad = problems()
        for p in bad:
            print(f"refused: {p}", file=sys.stderr)
        if not bad:
            print(".github/ holds to the repo")
        return kernel.REFUSED if bad else kernel.ALIVE
    print(USAGE, file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
