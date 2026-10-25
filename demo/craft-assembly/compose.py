"""compose.py: one Cargo workspace assembled from the store's pieces, by rule.

    python demo/craft-assembly/compose.py --store STORE --recipe composite.json --to OUT

The recipe names the apps (sources in the store, each a Cargo workspace) and
the git address of the library they share. Everything is read from the store
(pieces.py apart wrote it), never from a checkout, and OUT is written as:

    OUT/<app>/...                every file of the app, byte for byte, but its
                                 root Cargo.toml and Cargo.lock; each member's
                                 Cargo.toml is rewritten (below)
    OUT/craft-libs/<rev>/...     each library crate an app depends on, at the
                                 commit the app pinned, with that commit's
                                 licence files; its Cargo.toml rewritten too
    OUT/Cargo.toml               the one workspace: every member, sorted
    OUT/GLUE.json                every file the rules wrote, with the piece it
                                 came from, and everything they left out, why

The rules, all of them; none looks at what a build does:

    1. inherit    a member's `x.workspace = true` (in [package], a dependency
                  table, or [lints]) is replaced by its own app's workspace
                  value: dependencies keep the member's added features and
                  `optional`; a path in a workspace value is made relative to
                  the member again. Each app keeps its own versions, so apps
                  that pin different versions of a crate need no choosing.
    2. library    a dependency on the library's git address, at a commit the
                  store holds, becomes a path dependency on that crate at that
                  commit. A crate needed at two commits stops the composite:
                  Cargo can't hold two of one name and version from paths.
    3. clash      a package name in two apps is left out in both, and so is
                  every member that depends on a member left out.
    4. profile    profiles are joined setting by setting: a setting of
                  [profile.X], or of one package's override in it, is kept when
                  every app that has [profile.X] gives it the same value, and
                  dropped (and listed) when they differ or some leave it out.
                  [patch] tables are joined; a clash stops.
    5. drop       each app's root Cargo.toml and Cargo.lock are not copied:
                  the composite has one root and resolves one lockfile.

Same store and recipe, same bytes. Exit codes: 0 composed; 2 refused, or a
rule that stops the composite (said why).
"""

from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pieces  # noqa: E402

DEP_TABLES = ("dependencies", "dev-dependencies", "build-dependencies")
PACKAGE_PATHS = {"readme", "license-file"}  # [package] keys that hold a path
LICENCE = re.compile(r"(?i)^(licen[cs]e|copying|notice|attribution)")


class Stop(Exception):
    """A rule that stops the composite."""


# ── TOML out ────────────────────────────────────────────────────────────────
BARE = re.compile(r"^[A-Za-z0-9_-]+$")


def key(k: str) -> str:
    return k if BARE.match(k) else json.dumps(k, ensure_ascii=False)


def value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(value(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{key(k)} = {value(x)}" for k, x in v.items()) + " }"
    return v.isoformat()  # a TOML date or time


def is_tables(v) -> bool:
    return isinstance(v, list) and bool(v) and all(isinstance(x, dict) for x in v)


def toml(doc: dict) -> str:
    """`doc` as TOML: scalars first, then each table and array of tables, in
    the order they came; a dependency spec stays one inline table."""
    out: list[str] = []

    def emit(table: dict, path: list[str], header: str) -> None:
        plain = {
            k: v
            for k, v in table.items()
            if not (isinstance(v, dict) and not inline(path, k)) and not is_tables(v)
        }
        if header and (plain or not table):
            out.append(f"\n{header}")
        for k, v in plain.items():
            out.append(f"{key(k)} = {value(v)}")
        for k, v in table.items():
            sub = path + [k]
            if isinstance(v, dict) and not inline(path, k):
                emit(v, sub, "[" + ".".join(map(key, sub)) + "]")
            elif is_tables(v):
                for item in v:
                    out.append("\n[[" + ".".join(map(key, sub)) + "]]")
                    emit(item, sub, "")

    emit(doc, [], "")
    return "\n".join(out).lstrip("\n") + "\n"


def inline(path: list[str], k: str) -> bool:
    """A dependency's spec is written inline: `name = { version = "1" }`."""
    return bool(path) and path[-1] in DEP_TABLES


# ── reading the store ───────────────────────────────────────────────────────
def rows_of(store: Path, name: str) -> dict[str, tuple[str, str]]:
    return {p: (m, s) for p, m, s in pieces.recipe(store, name)["files"]}


def manifest(store: Path, rows: dict, path: str) -> dict:
    return tomllib.loads(pieces.get(store, rows[path][1]).decode("utf-8"))


def members(ws: dict, rows: dict) -> list[str]:
    """The member folders a workspace's globs name, that hold a Cargo.toml."""
    dirs = sorted(
        {posixpath.dirname(p) for p in rows if posixpath.basename(p) == "Cargo.toml"}
        - {""}
    )

    def pick(globs: list[str]) -> set[str]:
        return {d for d in dirs for g in globs if matches(d, g.rstrip("/"))}

    return sorted(pick(ws.get("members", [])) - pick(ws.get("exclude", [])))


def matches(path: str, glob: str) -> bool:
    """A workspace glob as Cargo reads it: `*` stays inside one folder name,
    so `crates/*` names crates/core but never crates/core/tests/fixture."""
    parts, pats = path.split("/"), glob.split("/")
    return len(parts) == len(pats) and all(
        fnmatch.fnmatchcase(p, g) for p, g in zip(parts, pats)
    )


def rel(target: str, member: str) -> str:
    return posixpath.relpath(posixpath.normpath(target), member) if target else "."


# ── the rules ───────────────────────────────────────────────────────────────
class App:
    def __init__(self, store: Path, name: str):
        self.name, self.rows = name, rows_of(store, name)
        if "Cargo.toml" not in self.rows:
            raise Stop(f"{name} has no root Cargo.toml")
        self.root = manifest(store, self.rows, "Cargo.toml")
        self.ws = self.root.get("workspace", {})
        if "package" in self.root:
            raise Stop(f"{name}'s root is a package as well as a workspace")
        self.members = members(self.ws, self.rows)


def inherit(doc: dict, ws: dict, member: str, libs, where: str) -> dict:
    """Rule 1 and rule 2 on one manifest; `member` is its folder in its own
    source, `where` that folder in the composite."""
    out = dict(doc)
    pkg = dict(doc.get("package", {}))
    for k, v in doc.get("package", {}).items():
        if isinstance(v, dict) and v.get("workspace") is True:
            got = ws.get("package", {})[k]
            pkg[k] = (
                rel(got, member) if k in PACKAGE_PATHS and isinstance(got, str) else got
            )
    if pkg:
        out["package"] = pkg
    if isinstance(doc.get("lints"), dict) and doc["lints"].get("workspace") is True:
        out["lints"] = ws.get("lints", {})

    def deps(table: dict) -> dict:
        new = {}
        for name, spec in table.items():
            if isinstance(spec, dict) and spec.get("workspace") is True:
                base = ws.get("dependencies", {})[name]
                base = {"version": base} if isinstance(base, str) else dict(base)
                if "path" in base:
                    base["path"] = rel(base["path"], member)
                feats = base.get("features", []) + [
                    f
                    for f in spec.get("features", [])
                    if f not in base.get("features", [])
                ]
                if feats:
                    base["features"] = feats
                for k, v in spec.items():
                    if k not in ("workspace", "features"):
                        base[k] = v
                spec = base
            new[name] = libs(name, spec, where) if isinstance(spec, dict) else spec
        return new

    for t in DEP_TABLES:
        if t in doc:
            out[t] = deps(doc[t])
    if "target" in doc:
        out["target"] = {cfg: {k: (deps(v) if k in DEP_TABLES else v) for k, v in tables.items()}
                         for cfg, tables in doc["target"].items()}  # fmt: skip
    return out


def compose(store: Path, recipe: dict, to: Path) -> dict:
    apps = [App(store, n) for n in recipe["apps"]]
    url = recipe["library"].rstrip("/")
    revs = {
        r["source"]: r
        for r in (
            pieces.recipe(store, p.stem)
            for p in (store / "recipes").glob("craft-libs@*.json")
        )
    }
    lib_rows = {n.split("@", 1)[1]: rows_of(store, n) for n in revs}
    glue = {
        "rewritten": [],
        "left_out": [],
        "profiles_dropped": [],
        "library": {},
        "local_cargo_config": [],
    }
    needed: dict[
        str, tuple[str, str]
    ] = {}  # package -> (rev, its folder in that commit)
    used_by: dict[str, set[str]] = {}

    def libs(name: str, spec: dict, where: str) -> dict:
        if spec.get("git", "").rstrip("/").removesuffix(".git") != url:
            return spec
        rev = spec.get("rev", "")
        short = next((r for r in lib_rows if rev.startswith(r)), None)
        if short is None:
            raise Stop(
                f"{name} wants the library at {rev or 'no rev'}, which the store doesn't hold"
            )
        pkg = spec.get("package", name)
        folder = lib_folder(store, lib_rows[short], pkg)
        if needed.setdefault(pkg, (short, folder)) != (short, folder):
            raise Stop(f"{pkg} is wanted at two commits, {needed[pkg][0]} and {short}")
        if not where.startswith("craft-libs/"):
            used_by.setdefault(pkg, set()).add(where.split("/")[0])
        out = {
            k: v for k, v in spec.items() if k not in ("git", "rev", "branch", "tag")
        }
        out["path"] = rel(f"craft-libs/{short}/{folder}", where)
        return out

    # rule 3: names in two apps
    names: dict[str, list[tuple[str, str]]] = {}
    docs: dict[tuple[str, str], dict] = {}
    for app in apps:
        for m in app.members:
            doc = manifest(store, app.rows, f"{m}/Cargo.toml")
            docs[(app.name, m)] = doc
            names.setdefault(doc.get("package", {}).get("name", m), []).append(
                (app.name, m)
            )
    out_of = {am for n, where in names.items() if len(where) > 1 for am in where}
    for n, where in sorted(names.items()):
        if len(where) > 1:
            glue["left_out"] += [
                {"member": f"{a}/{m}", "why": f"the name {n} is in {len(where)} apps"}
                for a, m in where
            ]
    changed = True
    while changed:  # and whatever depends on a member left out
        changed = False
        for (a, m), doc in sorted(docs.items()):
            if (a, m) in out_of:
                continue
            app = next(x for x in apps if x.name == a)
            for dep in path_deps(doc, app.ws, m):
                if (a, dep) in out_of:
                    out_of.add((a, m))
                    glue["left_out"].append(
                        {
                            "member": f"{a}/{m}",
                            "why": f"it depends on {a}/{dep}, left out",
                        }
                    )
                    changed = True
                    break

    # copy the apps, rewriting each member's manifest
    kept = []
    for app in apps:
        manifests = {f"{m}/Cargo.toml" for m in app.members}
        for path, (mode, sha) in sorted(app.rows.items()):
            if path in ("Cargo.toml", "Cargo.lock"):
                continue
            if path.startswith(".cargo/") or "/.cargo/" in path:
                glue["local_cargo_config"].append(f"{app.name}/{path}")
            target = f"{app.name}/{path}"
            if path in manifests and (app.name, posixpath.dirname(path)) not in out_of:
                m = posixpath.dirname(path)
                text = toml(
                    inherit(docs[(app.name, m)], app.ws, m, libs, f"{app.name}/{m}")
                )
                write_text(to / target, text)
                glue["rewritten"].append(
                    {"file": target, "from": sha, "rule": "inherit, library"}
                )
                kept.append(f"{app.name}/{m}")
            else:
                pieces.write(store, [[path, mode, sha]], to / app.name)

    # the library crates, each at its commit, with that commit's licence files
    for pkg, (short, folder) in sorted(needed.items()):
        rows = lib_rows[short]
        root = tomllib.loads(
            pieces.get(store, rows["Cargo.toml"][1]).decode("utf-8")
        ).get("workspace", {})
        base = f"craft-libs/{short}"
        for path, (mode, sha) in sorted(rows.items()):
            top_licence = "/" not in path and LICENCE.match(path)
            if not (top_licence or path.startswith(folder + "/")):
                continue
            if path == f"{folder}/Cargo.toml":
                doc = tomllib.loads(pieces.get(store, sha).decode("utf-8"))
                write_text(
                    to / base / path,
                    toml(inherit(doc, root, folder, libs, f"{base}/{folder}")),
                )
                glue["rewritten"].append(
                    {"file": f"{base}/{path}", "from": sha, "rule": "inherit, library"}
                )
            elif not (to / base / path).exists():
                pieces.write(store, [[path, mode, sha]], to / base)
        glue["library"][pkg] = {"commit": short, "folder": f"{base}/{folder}",
                                "used_by": sorted(used_by.get(pkg, ()))}  # fmt: skip

    # rule 4 and the root
    profiles, patch = (
        join_profiles(
            [a.root.get("profile", {}) for a in apps], glue["profiles_dropped"]
        ),
        {},
    )
    for a in apps:
        for src, table in a.root.get("patch", {}).items():
            for k, v in table.items():
                if patch.setdefault(src, {}).setdefault(k, v) != v:
                    raise Stop(f"[patch.{src}] {k} differs between apps")
    resolver = max((a.ws.get("resolver", "1") for a in apps), key=lambda r: int(r))
    root = {"workspace": {"resolver": resolver, "members": sorted(kept),
                          "exclude": sorted(f"{a}/{m}" for a, m in out_of)}}  # fmt: skip
    if profiles:
        root["profile"] = profiles
    if patch:
        root["patch"] = patch
    write_text(to / "Cargo.toml", toml(root))
    glue["members"] = len(kept)
    glue["left_out"].sort(key=lambda g: g["member"])
    glue["rewritten"].sort(key=lambda g: g["file"])
    write_text(to / "GLUE.json", pieces.dump(glue))
    return glue


def join_profiles(all_profiles: list[dict], dropped: list[str]) -> dict:
    """Rule 4: each profile's settings, and each package override's, kept
    where every app with that profile agrees; `dropped` gets the rest."""
    out = {}
    for name in sorted({n for p in all_profiles for n in p}):
        having = [p[name] for p in all_profiles if name in p]
        kept = {}
        for k in sorted({k for h in having for k in h}):
            if k == "package":
                over = {}
                for pkg in sorted({q for h in having for q in h.get("package", {})}):
                    sets = [
                        h["package"][pkg] for h in having if pkg in h.get("package", {})
                    ]
                    if pkg == "*" and len(sets) < len(having):
                        dropped.append(f"{name}.package.*")
                        continue
                    joined = {s: sets[0][s] for s in sorted({s for x in sets for s in x})
                              if all(x.get(s, object()) == sets[0].get(s, object()) for x in sets)}  # fmt: skip
                    dropped += [
                        f"{name}.package.{pkg}.{s}"
                        for s in sorted({s for x in sets for s in x} - set(joined))
                    ]
                    if joined:
                        over[pkg] = joined
                if over:
                    kept["package"] = over
            elif all(k in h and h[k] == having[0].get(k) for h in having):
                kept[k] = having[0][k]
            else:
                dropped.append(f"{name}.{k}")
        if kept:
            out[name] = kept
    return out


def path_deps(doc: dict, ws: dict, member: str) -> list[str]:
    """The member folders (in its own source) `doc` depends on by path."""
    out = []
    tables = [doc.get(t, {}) for t in DEP_TABLES]
    tables += [v.get(t, {}) for v in doc.get("target", {}).values() for t in DEP_TABLES]
    for table in tables:
        for name, spec in table.items():
            if isinstance(spec, dict) and spec.get("workspace") is True:
                base = ws.get("dependencies", {}).get(name)
                if isinstance(base, dict) and "path" in base:
                    out.append(posixpath.normpath(base["path"]))
            elif isinstance(spec, dict) and "path" in spec:
                out.append(posixpath.normpath(posixpath.join(member, spec["path"])))
    return out


def lib_folder(store: Path, rows: dict, pkg: str) -> str:
    """The folder of package `pkg` in one commit of the library."""
    for path in sorted(rows):
        if posixpath.basename(path) == "Cargo.toml" and "/" in path:
            doc = tomllib.loads(pieces.get(store, rows[path][1]).decode("utf-8"))
            if doc.get("package", {}).get("name") == pkg:
                return posixpath.dirname(path)
    raise Stop(f"the library has no package {pkg}")


def write_text(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    os.chmod(p, 0o644)


def main(argv: list[str]) -> int:
    opts, it = {}, iter(argv)
    for a in it:
        v = next(it, "")
        if a not in ("--store", "--recipe", "--to") or not v or a in opts:
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return 2
        opts[a] = v
    if len(opts) != 3:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    store, to = Path(opts["--store"]), Path(opts["--to"])
    if to.exists() and any(to.iterdir()):
        print(f"refused: {to} isn't empty; compose into a new folder", file=sys.stderr)
        return 2
    try:
        glue = compose(
            store, json.loads(Path(opts["--recipe"]).read_text(encoding="utf-8")), to
        )
    except Stop as e:
        print(f"stopped: {e}", file=sys.stderr)
        return 2
    print(f"composed {glue['members']} members, {len(glue['library'])} library crates, "
          f"{len(glue['left_out'])} left out, {len(glue['rewritten'])} manifests rewritten")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
