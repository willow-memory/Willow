"""versions.py: each add-on and idea a pull request changes steps its version,
once. Python 3.9+.

    python adapters/stdlib/ci/versions.py check --base REF
    python adapters/stdlib/ci/versions.py write --base REF

Everything willow keeps is versioned the same way (CONTRIBUTING.md, Releases),
MAJOR.MINOR.PATCH, by the pull request that changes it: an idea starts at
0.0.1 and steps a patch each time its entry in adapters/planned.json
changes; its first build is 0.1.0; a built add-on steps by the size of its
change, a patch for a fix, a minor step for something added, a major one
when something that relied on it no longer can. Below 1.0 a breaking change
is a minor step, as the standard says, and 1.0 comes when its author judges
it has settled. One pull request is one step, however many commits it has:
REF...HEAD, the pull request's own commits, is what is compared.

`check` refuses:

  * an add-on whose folder changed (any file but its tests) whose version
    didn't step, or stepped by more than one step (0.1.0 to 0.3.0, or to
    0.2.1); its card is one of its files, so a change to its words steps it;
  * a change to what its card promises, `writes`, `network` or `hands`,
    taken as a patch: a promise changed is at least a minor step (whether
    it is a major one is its author's call);
  * an add-on new here that isn't 0.1.0, whether built from an idea or not;
  * an idea new here that isn't 0.0.1, a changed one that isn't the next
    patch, and an unchanged one whose version moved.

`write` gives each add-on and idea that owes a step and hasn't taken one
the smallest it owes: a patch, or a minor step for a changed promise, and
0.1.0 or 0.0.1 for a new one. It never changes a step already taken, so a
bigger one stays the author's.

Exit codes, the kernel's: 0 every version is where it should be (`write`:
and none is left owing); 42 git couldn't compare with REF; 2 a version is
wrong, or a bad command line.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import kernel  # noqa: E402

USAGE = "usage: versions.py check|write --base REF"
KINDS = ("stdlib", "deps")
PLANNED = "adapters/planned.json"
HEADER = re.compile(r"\A<!-- willow-addon\n(.*?)\n-->\n", re.S)
VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
#: what a card promises: a change to one is never a patch
PROMISES = ("writes", "network", "hands")
FIRST_BUILD, FIRST_IDEA = "0.1.0", "0.0.1"


class Unreachable(Exception):
    pass


def git(*args: str, root: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def header(text: str) -> dict[str, str]:
    """A card's header fields, or {} when it has none."""
    m = HEADER.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            out[key.strip()] = value.strip()
    return out


def parts(version: str) -> tuple[int, int, int] | None:
    m = VERSION.fullmatch(version or "")
    return tuple(int(x) for x in m.groups()) if m else None


def step(old: str, new: str) -> str | None:
    """How far `old` to `new` moves: "same", "patch", "minor", "major", or
    None when it isn't one of those (skipped, backwards, or not a version)."""
    o, n = parts(old), parts(new)
    if o is None or n is None:
        return None
    if n == o:
        return "same"
    for kind, want in (
        ("major", (o[0] + 1, 0, 0)),
        ("minor", (o[0], o[1] + 1, 0)),
        ("patch", (o[0], o[1], o[2] + 1)),
    ):
        if n == want:
            return kind
    return None


def bumped(version: str, kind: str) -> str:
    a, b, c = parts(version)
    return {"major": f"{a + 1}.0.0", "minor": f"{a}.{b + 1}.0"}.get(
        kind, f"{a}.{b}.{c + 1}"
    )


def cards_at(ref: str, root: Path = ROOT) -> dict[str, dict]:
    """{name: {"kind", "path", "head"}} for every built add-on at `ref`."""
    got = git("ls-tree", "-r", "--name-only", ref, "adapters/", root=root)
    if got.returncode != 0:
        raise Unreachable(got.stderr.strip())
    out = {}
    for path in got.stdout.split("\n"):
        bits = path.split("/")
        if len(bits) == 4 and bits[1] in KINDS and bits[3] == "README.md":
            shown = git("show", f"{ref}:{path}", root=root)
            out[bits[2]] = {"kind": bits[1], "path": path, "head": header(shown.stdout)}
    return out


def ideas_at(ref: str, root: Path = ROOT) -> dict[str, dict]:
    got = git("show", f"{ref}:{PLANNED}", root=root)
    if got.returncode != 0:
        return {}
    try:
        return {e["name"]: e for e in json.loads(got.stdout)}
    except (ValueError, KeyError, TypeError):
        return {}


def owed(ref: str, root: Path = ROOT) -> list[dict]:
    """What each add-on and idea REF...HEAD changed owes, one dict each:
    name, kind ("addon" or "idea"), was, now, want (the step it needs:
    "first" for a new one, else "patch" or "minor", the least it owes),
    and why when it doesn't hold."""
    base = git("merge-base", ref, "HEAD", root=root)
    if base.returncode != 0:
        raise Unreachable(base.stderr.strip())
    base = base.stdout.strip()
    diff = git("diff", "--name-only", f"{base}...HEAD", root=root)
    if diff.returncode != 0:
        raise Unreachable(diff.stderr.strip())
    touched = set()
    for path in diff.stdout.split("\n"):
        bits = path.split("/")
        if len(bits) >= 4 and bits[0] == "adapters" and bits[1] in KINDS:
            if not bits[-1].startswith("test_") and "__pycache__" not in bits:
                touched.add(bits[2])
    then, now = cards_at(base, root), cards_at("HEAD", root)
    ideas_then, ideas_now = ideas_at(base, root), ideas_at("HEAD", root)
    out = []
    for name, c in sorted(now.items()):
        ver = c["head"].get("version", "")
        item = {"name": name, "kind": "addon", "path": c["path"], "now": ver}
        if name not in then:
            item.update(was=None, want="first")
            if ver != FIRST_BUILD:
                item["why"] = f"is new here, so its first build is {FIRST_BUILD}, not {ver or 'none'}"  # fmt: skip
            out.append(item)
            continue
        was = then[name]["head"].get("version", "")
        item["was"] = was
        moved = step(was, ver)
        promised = any(then[name]["head"].get(p) != c["head"].get(p) for p in PROMISES)
        if name not in touched:  # its version lives in its card: moving it touches it
            continue
        item["want"] = "minor" if promised else "patch"
        if not was:  # a card from before versions: its first is 0.1.0
            item.update(was=None, want="first")
            if ver != FIRST_BUILD:
                item["why"] = f"has no version at the base, so starts at {FIRST_BUILD}, not {ver or 'none'}"  # fmt: skip
        elif moved == "same":
            item["why"] = f"changed here, so its version steps from {was}"
        elif moved is None:
            item["why"] = f"steps from {was} to {ver}, which is more than one step"
        elif moved == "patch" and promised:
            item["why"] = f"changed what its card promises ({', '.join(p for p in PROMISES if then[name]['head'].get(p) != c['head'].get(p))}), which is at least a minor step, not {was} to {ver}"  # fmt: skip
        out.append(item)
    for name, e in sorted(ideas_now.items()):
        ver = str(e.get("version", ""))
        item = {"name": name, "kind": "idea", "now": ver}
        if name not in ideas_then:
            item.update(was=None, want="first")
            if ver != FIRST_IDEA:
                item["why"] = f"is a new idea, so it starts at {FIRST_IDEA}, not {ver or 'none'}"  # fmt: skip
            out.append(item)
            continue
        old = ideas_then[name]
        was = str(old.get("version", ""))
        item["was"] = was
        same = {k: v for k, v in old.items() if k != "version"} == {
            k: v for k, v in e.items() if k != "version"
        }
        moved = step(was, ver)
        if not was:
            if ver != FIRST_IDEA:
                item.update(was=None, want="first", why=f"has no version at the base, so starts at {FIRST_IDEA}, not {ver or 'none'}")  # fmt: skip
                out.append(item)
            continue
        if same:
            if moved != "same":
                item.update(
                    want=None, why=f"didn't change here, so stays {was}, not {ver}"
                )
                out.append(item)
            continue
        item["want"] = "patch"
        if moved != "patch":
            item["why"] = f"changed here, so steps a patch from {was} (an idea is 0.0.N), not to {ver}"  # fmt: skip
        out.append(item)
    return out


def write(items: list[dict], root: Path = ROOT) -> list[str]:
    """The smallest step each item still owes, written; what was written."""
    done = []
    ideas_path = root / PLANNED
    ideas = json.loads(ideas_path.read_text(encoding="utf-8")) if ideas_path.is_file() else []  # fmt: skip
    ideas_changed = False
    for it in items:
        if "why" not in it or it.get("want") is None:
            continue
        if it["want"] == "first":
            to = FIRST_BUILD if it["kind"] == "addon" else FIRST_IDEA
        elif it.get("was") and step(it["was"], it["now"]) == "same":
            to = bumped(it["was"], it["want"])
        elif (
            it.get("was")
            and it["want"] == "minor"
            and step(it["was"], it["now"]) == "patch"
        ):
            to = bumped(it["was"], "minor")
        else:
            continue  # a step taken that doesn't hold is the author's to fix
        if it["kind"] == "addon":
            card = root / it["path"]
            text = card.read_text(encoding="utf-8")
            m = HEADER.match(text)
            head = m.group(1)
            if re.search(r"^version: .*$", head, re.M):
                new = re.sub(
                    r"^version: .*$", f"version: {to}", head, count=1, flags=re.M
                )
            elif re.search(r"^added: .*$", head, re.M):
                new = re.sub(r"^(added: .*)$", rf"\1\nversion: {to}", head, count=1, flags=re.M)  # fmt: skip
            else:
                new = head + f"\nversion: {to}"
            card.write_text(text.replace(head, new, 1), encoding="utf-8")
        else:
            for e in ideas:
                if e.get("name") == it["name"]:
                    e["version"] = to
                    ideas_changed = True
        done.append(f"{it['name']}: {it.get('was') or 'new'} to {to}")
    if ideas_changed:
        ideas_path.write_text(json.dumps(ideas, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")  # fmt: skip
    return done


def main(argv: list[str], root: Path = ROOT) -> int:
    if len(argv) != 3 or argv[0] not in ("check", "write") or argv[1] != "--base":
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    verb, ref = argv[0], argv[2]
    try:
        items = owed(ref, root)
    except Unreachable as why:
        print(f"unreachable: git can't compare with {ref}: {why}")
        return kernel.ESCALATE
    if verb == "write":
        for line in write(items, root):
            print(f"wrote {line}")
        print("written into the working tree; check reads what is committed, so commit it")  # fmt: skip
        return kernel.ALIVE
    wrong = [it for it in items if "why" in it]
    for it in wrong:
        print(f"refused: {it['kind']} {it['name']} {it['why']}")
    stepped = [it for it in items if "why" not in it and it.get("want")]
    if not wrong:
        print(f"every version holds: {len(stepped)} stepped here, as each change owes")
    return kernel.REFUSED if wrong else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
