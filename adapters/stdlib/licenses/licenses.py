"""licenses.py: the licence of every installed dependency, read from its own
metadata on this machine, and which are copyleft. Python 3.9+.

    python adapters/stdlib/licenses/licenses.py --from FOLDER
    python adapters/stdlib/licenses/licenses.py --box DIR
    python adapters/stdlib/licenses/licenses.py --site

Two kinds of installed package are read, at any depth under the folder:

- Python: every `*.dist-info/METADATA` (and `*.egg-info/PKG-INFO`), from its
  `License-Expression`, else its `License ::` classifiers, else its `License`
  line. `--site` reads the site-packages of the Python that runs this.
- npm: every package.json inside a node_modules folder, from its `license`
  (or the old `licenses` list).

Each licence is put in one class, and everything but the permissive ones is
listed, with the file and line that says so:

    strong copyleft
        somepkg 1.2   lib/site-packages/somepkg-1.2.dist-info/METADATA:9   GPL-3.0-or-later
    weak copyleft
        libthing 4.0   node_modules/libthing/package.json:5   LGPL-2.1
    undeclared
        oddity 0.1   lib/site-packages/oddity-0.1.dist-info/METADATA:3   (none)

    41 packages: 37 permissive, 1 weak copyleft, 1 strong copyleft, 2 undeclared.

An SPDX expression is read through: `MIT OR GPL-3.0` is permissive, since you
may pick MIT, and `MIT AND GPL-3.0` is strong, since both apply. Free text
(old metadata saying "GNU General Public License v3") is read by its words.
A licence this doesn't know is "undeclared", the same as none: read it. This
is a lead from what each package says about itself, never legal advice.

It only reads, and writes nothing. Exit codes, the kernel's: 0 every package
is permissive (or none installed); 42 a copyleft or undeclared licence, which
waits on you; 2 refused.
"""

from __future__ import annotations

import json
import re
import sys
import sysconfig
from pathlib import Path

STDLIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STDLIB.parents[1]))
import kernel  # noqa: E402

PERMISSIVE, WEAK, STRONG, UNDECLARED = range(4)
CLASSES = ("permissive", "weak copyleft", "strong copyleft", "undeclared")
ORDER = (STRONG, WEAK, UNDECLARED)  # the order they are listed in

STRONG_IDS = re.compile(
    r"^(?:a?gpl|eupl|osl|sspl|cpal|cc-by-sa|cc-by-nc-sa|rpl|sleepycat)"
)
WEAK_IDS = re.compile(
    r"^(?:lgpl|mpl|epl|cddl|cpl|ms-rl|eclipse|ofl|cecill-c|libpng-2|apsl)"
)
PERMISSIVE_IDS = re.compile(
    r"^(?:mit|bsd|apache|isc|zlib|psf|python|unlicense|0bsd|cc0|blueoak|bsl|hpnd|wtfpl|ncsa|x11|pil|"
    r"public-domain|artistic|unicode|openssl|curl|libtiff|ijg|boost|mulan|upl|ruby|postgresql|afl|cc-by-[\d.]+)"
)
TOKEN = re.compile(r"\(|\)|[^\s()]+")


def atom_class(atom: str) -> int:
    a = atom.lower().rstrip("+")
    a = re.sub(r"-(?:only|or-later)$", "", a)
    if STRONG_IDS.match(a):
        return STRONG
    if WEAK_IDS.match(a):
        return WEAK
    if PERMISSIVE_IDS.match(a):
        return PERMISSIVE
    return UNDECLARED


def expression_class(text: str) -> int:
    """An SPDX expression's class: OR takes the most permissive side, AND and
    WITH the most restrictive."""
    tokens = TOKEN.findall(text)
    pos = 0

    def parse_or() -> int:
        nonlocal pos
        best = parse_and()
        while pos < len(tokens) and tokens[pos].upper() == "OR":
            pos += 1
            best = min(best, parse_and())
        return best

    def parse_and() -> int:
        nonlocal pos
        worst = parse_atom()
        while pos < len(tokens) and tokens[pos].upper() in ("AND", "WITH"):
            with_ = tokens[pos].upper() == "WITH"
            pos += 1
            other = parse_atom()
            if not with_:
                worst = max(worst, other)
        return worst

    def parse_atom() -> int:
        nonlocal pos
        if pos >= len(tokens):
            return UNDECLARED
        t = tokens[pos]
        pos += 1
        if t == "(":
            inner = parse_or()
            if pos < len(tokens) and tokens[pos] == ")":
                pos += 1
            return inner
        return atom_class(t)

    return parse_or() if tokens else UNDECLARED


def text_class(text: str) -> int:
    """Free text ('GNU Lesser General Public License v3') read by its words."""
    t = text.lower()
    if re.search(r"affero|\bagpl|\bsspl", t):
        return STRONG
    if re.search(
        r"lesser general|library general|\blgpl|mozilla public|\bmpl\b|eclipse public|common development|\bcddl",
        t,
    ):
        return WEAK
    if re.search(r"general public licen[cs]e|\bgpl", t):
        return STRONG
    if re.search(
        r"\bmit\b|\bbsd|apache|\bisc\b|python software|\bpsf|public domain|unlicense|\bzlib|\bcc0",
        t,
    ):
        return PERMISSIVE
    return (
        expression_class(text)
        if len(text) < 80 and " " not in text.strip()
        else UNDECLARED
    )


def line_of(text: str, pattern: str) -> int:
    m = re.search(pattern, text, re.M)
    return text.count("\n", 0, m.start()) + 1 if m else 1


def python_license(raw: str):
    """(name, version, line, shown, class) from a METADATA or PKG-INFO."""
    head = raw.split("\n\n", 1)[0]
    fields: dict[str, list[str]] = {}
    for m in re.finditer(r"^([A-Za-z-]+):[ \t]*(.*)$", head, re.M):
        fields.setdefault(m.group(1).lower(), []).append(m.group(2).strip())
    name = (fields.get("name") or ["?"])[0]
    version = (fields.get("version") or [""])[0]
    expr = (fields.get("license-expression") or [""])[0]
    classifiers = [
        c.split("::", 1)[1].strip()
        for c in fields.get("classifier", [])
        if c.startswith("License ::")
    ]
    classifiers = [c.removeprefix("OSI Approved ::").strip() for c in classifiers]
    classifiers = [c for c in classifiers if c and c != "OSI Approved"]
    lic = (fields.get("license") or [""])[0]
    if expr:
        return (
            name,
            version,
            line_of(head, r"^License-Expression:"),
            expr,
            expression_class(expr),
        )
    if classifiers:
        shown = "; ".join(classifiers)
        return (
            name,
            version,
            line_of(head, r"^Classifier:[ \t]*License ::"),
            shown,
            min(text_class(c) for c in classifiers),
        )
    if lic and lic.upper() not in ("UNKNOWN", "NONE", "") and len(lic) < 300:
        return name, version, line_of(head, r"^License:"), lic, text_class(lic)
    return name, version, 1, "(none)", UNDECLARED


def npm_license(raw: str, data: dict, folder_name: str):
    name = data.get("name") if isinstance(data.get("name"), str) else folder_name
    version = data.get("version") if isinstance(data.get("version"), str) else ""
    lic = data.get("license")
    if isinstance(lic, dict):
        lic = lic.get("type")
    if not isinstance(lic, str):
        old = data.get("licenses")
        types = (
            [x.get("type") if isinstance(x, dict) else x for x in old]
            if isinstance(old, list)
            else []
        )
        types = [t for t in types if isinstance(t, str)]
        lic = " OR ".join(types) if types else None
        line = line_of(raw, r'"licenses"\s*:')
    else:
        line = line_of(raw, r'"license"\s*:')
    if not lic or lic.upper().startswith(("SEE LICEN", "UNLICENSED")):
        return name, version, line if lic else 1, lic or "(none)", UNDECLARED
    return (
        name,
        version,
        line,
        lic,
        expression_class(lic),
    )


def find(folder: Path):
    """[(name, version, file, line, shown, class)] and the files that couldn't be read."""
    out, bad = [], []
    base = folder.resolve().name
    for p in sorted(folder.rglob("*")):
        rel = p.relative_to(folder)
        if not p.is_file() or ".git" in rel.parts:
            continue
        try:
            if p.name in ("METADATA", "PKG-INFO") and p.parent.name.endswith(
                (".dist-info", ".egg-info")
            ):
                raw = p.read_text(encoding="utf-8", errors="replace")
                name, version, line, shown, cls = python_license(raw)
                out.append((name, version, rel.as_posix(), line, shown, cls))
            elif p.name == "package.json" and "node_modules" in (base, *rel.parts[:-1]):
                raw = p.read_text(encoding="utf-8", errors="replace")
                data = json.loads(raw)
                if isinstance(data, dict):
                    name, version, line, shown, cls = npm_license(
                        raw, data, p.parent.name
                    )
                    out.append((name, version, rel.as_posix(), line, shown, cls))
        except (OSError, ValueError):
            bad.append(rel.as_posix())
    return out, bad


def main(argv: list[str]) -> int:
    site = "--site" in argv
    argv = [a for a in argv if a != "--site"]
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--box", "--from"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    given = [v for v in opts.values() if v]
    if args or len(given) + site != 1 or len(opts) + site != 1:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return kernel.REFUSED
    if site:
        folders = sorted(
            {Path(sysconfig.get_paths()[k]) for k in ("purelib", "platlib")}
        )
    elif "--box" in opts:
        box = Path(opts["--box"])
        if not (box / "kernel.json").exists():
            print("refused: not a kernel box; init first", file=sys.stderr)
            return kernel.REFUSED
        folders = [Path(kernel.config(box)["pile"])]
    else:
        folders = [Path(opts["--from"])]
        if not folders[0].is_dir():
            print(f"refused: {folders[0]} isn't a folder", file=sys.stderr)
            return kernel.REFUSED
    rows, bad = [], []
    for f in folders:
        r, b = find(f)
        rows += [
            (n, v, (f.name + "/" if site else "") + file, line, shown, cls)
            for n, v, file, line, shown, cls in r
        ]
        bad += b
    for path in bad:
        print(
            f"note: {path} couldn't be read, so its licence was not checked",
            file=sys.stderr,
        )
    if not rows:
        print(
            "No installed packages found here (no .dist-info, .egg-info or node_modules)."
        )
        return kernel.ALIVE
    rows.sort(key=lambda r: (r[0].lower(), r[1]))
    counts = [sum(1 for r in rows if r[5] == c) for c in range(4)]
    for cls in ORDER:
        group = [r for r in rows if r[5] == cls]
        if not group:
            continue
        print(CLASSES[cls])
        label = [f"{n} {v}".strip() for n, v, *_ in group]
        w1 = max(len(x) for x in label)
        w2 = max(len(f"{file}:{line}") for _, _, file, line, _, _ in group)
        for lbl, (_, _, file, line, shown, _) in zip(label, group):
            print(f"    {lbl:<{w1}}   {f'{file}:{line}':<{w2}}   {shown}")
    parts = [f"{counts[PERMISSIVE]} permissive"] + [
        f"{counts[c]} {CLASSES[c]}" for c in (WEAK, STRONG, UNDECLARED) if counts[c]
    ]
    print(f"\n{len(rows)} package{'s' if len(rows) != 1 else ''}: {', '.join(parts)}.")
    return kernel.ESCALATE if len(rows) != counts[PERMISSIVE] else kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
