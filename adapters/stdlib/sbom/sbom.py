r"""sbom.py: Software bills of materials in SPDX or CycloneDX JSON. Python 3.9+.

    python adapters/stdlib/sbom/sbom.py mirror --from FOLDER --to MIRROR

Walks FOLDER for .json files that are an SBOM (CycloneDX: `bomFormat` and
`components`; SPDX: `spdxVersion` and `packages`; hidden folders and files
skipped; other JSON skipped and counted) and writes the bill, then one line for
each component:

    sbom: garden-app 1.0 (CycloneDX 1.5)
    requests 2.31.0: Apache-2.0 (pkg:pypi/requests@2.31.0)
    urllib3 2.0.7: MIT OR Apache-2.0 (pkg:pypi/urllib3@2.0.7)
    legacy-lib: no licence stated

Components come in name order. A CycloneDX licence is its id, its name or its
expression; an SPDX package's is the concluded licence, else the declared one,
and NOASSERTION or NONE counts as none stated. The package URL is kept when the
component gives one (an SPDX package's `purl` external reference). Hashes,
dependency graphs and vulnerabilities are not copied.

Each file is written to MIRROR at the same relative path with `.txt` added.
FOLDER is only read.

Exit codes, the kernel's: 0 wrote some; 42 nothing readable; 2 refused (FOLDER
is not a folder, or MIRROR and FOLDER are inside one another).
"""

from __future__ import annotations

import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402


def text(v: object) -> str:
    return " ".join(v.split()) if isinstance(v, str) else ""


def cdx_licence(lic: object) -> str:
    out = []
    for item in lic if isinstance(lic, list) else []:
        if not isinstance(item, dict):
            continue
        inner = item.get("license") if isinstance(item.get("license"), dict) else {}
        out.append(
            text(inner.get("id"))
            or text(inner.get("name"))
            or text(item.get("expression"))
        )
    return ", ".join(x for x in out if x)


def spdx_licence(pkg: dict) -> str:
    for key in ("licenseConcluded", "licenseDeclared"):
        v = text(pkg.get(key))
        if v and v not in ("NOASSERTION", "NONE"):
            return v
    return ""


def spdx_purl(pkg: dict) -> str:
    for ref in (
        pkg.get("externalRefs") if isinstance(pkg.get("externalRefs"), list) else []
    ):
        if isinstance(ref, dict) and text(ref.get("referenceType")) == "purl":
            return text(ref.get("referenceLocator"))
    return ""


def line(name: str, version: str, licence: str, purl: str) -> str:
    head = f"{name} {version}".strip()
    if not licence:
        return f"{head}: no licence stated" + (f" ({purl})" if purl else "")
    return f"{head}: {licence}" + (f" ({purl})" if purl else "")


def convert(data: bytes) -> str | None:
    doc = json.loads(data.decode("utf-8-sig"))
    if not isinstance(doc, dict):
        return None
    rows = []
    if doc.get("bomFormat") == "CycloneDX" and isinstance(doc.get("components"), list):
        meta = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
        top = meta.get("component") if isinstance(meta.get("component"), dict) else {}
        head = (
            f"sbom: {text(top.get('name')) or '(unnamed)'} {text(top.get('version'))}".rstrip()
            + f" (CycloneDX {text(doc.get('specVersion'))})".replace(" )", ")")
        )
        for c in doc["components"]:
            if isinstance(c, dict) and text(c.get("name")):
                name = text(c["name"])
                group = text(c.get("group"))
                rows.append(
                    (
                        name.lower(),
                        line(
                            f"{group}/{name}" if group else name,
                            text(c.get("version")),
                            cdx_licence(c.get("licenses")),
                            text(c.get("purl")),
                        ),
                    )
                )
    elif isinstance(doc.get("spdxVersion"), str) and isinstance(
        doc.get("packages"), list
    ):
        head = (
            f"sbom: {text(doc.get('name')) or '(unnamed)'} ({text(doc['spdxVersion'])})"
        )
        for p in doc["packages"]:
            if isinstance(p, dict) and text(p.get("name")):
                rows.append(
                    (
                        text(p["name"]).lower(),
                        line(
                            text(p["name"]),
                            text(p.get("versionInfo")),
                            spdx_licence(p),
                            spdx_purl(p),
                        ),
                    )
                )
    else:
        return None
    return head + "\n" + "\n".join(t for _k, t in sorted(rows)) + "\n" if rows else None


EXTS = (".json",)
ERRORS = (OSError, UnicodeDecodeError, ValueError)

USAGE = "usage: sbom.py mirror --from FOLDER --to MIRROR"


def _sources(folder: Path) -> list[Path]:
    """Files under `folder` this reads, sorted by relative path. Hidden folders
    and files are skipped; symlinked folders are not followed."""
    found = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            p = Path(dirpath) / name
            if not name.startswith(".") and name.lower().endswith(EXTS) and p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(folder).as_posix())


def _within(inner: Path, outer: Path) -> bool:
    return inner == outer or outer in inner.parents


def mirror(src: Path, dst: Path) -> tuple[int, int]:
    """Write the mirror of `src` into `dst`. Returns (written, skipped)."""
    wrote = skipped = 0
    for path in _sources(src):
        rel = path.relative_to(src)
        try:
            text = convert(path.read_bytes())
            if text is None:
                skipped += 1
                continue
            target = dst.joinpath(rel.parent, rel.name + ".txt")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        except ERRORS:
            skipped += 1
            continue
        wrote += 1
    return wrote, skipped


def main(argv: list[str]) -> int:
    opts = dict(zip(argv[1::2], argv[2::2])) if argv[:1] == ["mirror"] else {}
    if len(argv) != 5 or sorted(opts) != ["--from", "--to"]:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    if not Path(opts["--from"]).is_dir():
        print(f"refused: not a folder: {opts['--from']}", file=sys.stderr)
        return kernel.REFUSED
    src = Path(opts["--from"]).resolve()
    dst = Path(opts["--to"]).resolve()
    if _within(dst, src) or _within(src, dst):
        print(
            "refused: MIRROR and FOLDER must not be inside one another", file=sys.stderr
        )
        return kernel.REFUSED
    wrote, skipped = mirror(src, dst)
    print(f"wrote {wrote} files to {opts['--to']}; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
