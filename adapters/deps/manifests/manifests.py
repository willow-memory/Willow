"""manifests.py: Docker Compose and Kubernetes YAML, a passage for each service.

    python adapters/deps/manifests/manifests.py mirror --from FOLDER --to MIRROR

Needs PyYAML (MIT), pinned in requirements.txt beside this file:

    pip install -r adapters/deps/manifests/requirements.txt

For each .yml or .yaml under FOLDER that is a Compose file (it has
`services:`) or holds Kubernetes objects (each with `apiVersion` and `kind`),
it writes `MIRROR/<same relative path>.txt`, one passage for each Compose
service and each Kubernetes object, saying what a person asks of it: its
image, ports, volumes, what it depends on and what it selects.

    == service web
    image nginx:1.27
    ports 8080:80
    volumes ./site:/usr/share/nginx/html:ro
    depends on db
    environment names DEBUG, DB_HOST

    == Deployment shop/web
    replicas 3
    container web: image nginx:1.27
    container web: ports 80/TCP
    container web: mounts site at /usr/share/nginx/html

An environment variable, a ConfigMap or a Secret is written by its names
only, never its values: a manifest often holds a password, and a mirror is
for searching, not for copying one. YAML is read safely (no tag can build an
object), and a YAML file that is neither kind is left alone and counted.

The contract every file reader shares: FOLDER is walked in sorted order,
skipping hidden files and folders; nothing is written inside FOLDER and no
original is changed; MIRROR inside FOLDER, or FOLDER inside MIRROR, is
refused; the same file always gives the same bytes; a file that isn't YAML
is skipped and counted, never a crash.

If PyYAML isn't installed it refuses and names the install; it never skips
quietly. Exit codes, the kernel's: 0 wrote at least one file; 42 nothing
readable; 2 refused.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/manifests/requirements.txt"
KINDS = (".yml", ".yaml")
#: where each workload keeps the pod it runs
POD = {"Pod": (), "CronJob": ("jobTemplate", "spec", "template", "spec")}


def flat(v) -> str:
    """A scalar as one line: YAML's own words for true, false and nothing."""
    if v is True or v is False:
        return "true" if v else "false"
    return "" if v is None else " ".join(str(v).split())


def items(v) -> list:
    return v if isinstance(v, list) else []


def mapping(v) -> dict:
    return v if isinstance(v, dict) else {}


def names(v) -> list[str]:
    """The names of a list of `K=V` or `K`, or a mapping's keys."""
    if isinstance(v, dict):
        return [flat(k) for k in v]
    return [flat(x).split("=")[0] for x in items(v) if flat(x)]


def line(label: str, values) -> list[str]:
    values = [x for x in values if x]
    return [f"{label} {', '.join(values)}"] if values else []


def compose_port(p) -> str:
    if isinstance(p, dict):
        out = ":".join(flat(p.get(k)) for k in ("published", "target") if p.get(k))
        return out + (f"/{p['protocol']}" if p.get("protocol") else "")
    return flat(p)


def compose_volume(v) -> str:
    if isinstance(v, dict):
        out = ":".join(flat(v.get(k)) for k in ("source", "target") if v.get(k))
        return out + (":ro" if v.get("read_only") else "")
    return flat(v)


def service(name, s: dict) -> str:
    s = mapping(s)
    build = s.get("build")
    lines = [f"== service {flat(name)}"]
    lines += line("image", [flat(s.get("image"))])
    lines += line(
        "build",
        [flat(mapping(build).get("context") if isinstance(build, dict) else build)],
    )
    lines += line("ports", [compose_port(p) for p in items(s.get("ports"))])
    lines += line("expose", [flat(p) for p in items(s.get("expose"))])
    lines += line("volumes", [compose_volume(v) for v in items(s.get("volumes"))])
    lines += line("depends on", names(s.get("depends_on")))
    lines += line("networks", names(s.get("networks")))
    lines += line("environment names", names(s.get("environment")))
    env_files = s.get("env_file")
    lines += line(
        "env files",
        [flat(x) for x in (env_files if isinstance(env_files, list) else [env_files])],
    )
    lines += line("restart", [flat(s.get("restart"))])
    return "\n".join(lines)


def compose(doc: dict) -> list[str]:
    out = [service(n, s) for n, s in mapping(doc.get("services")).items()]
    for part in ("volumes", "networks", "secrets", "configs"):
        if mapping(doc.get(part)):
            out.append(f"== {part}\n" + ", ".join(names(doc[part])))
    return out


def dig(v, keys) -> dict:
    for k in keys:
        v = mapping(v).get(k)
    return mapping(v)


def pod(spec: dict) -> list[str]:
    lines = []
    for c in items(spec.get("initContainers")) + items(spec.get("containers")):
        c = mapping(c)
        who = f"container {flat(c.get('name'))}:"
        lines += line(f"{who} image", [flat(c.get("image"))])
        ports = [f"{flat(p.get('containerPort'))}/{flat(p.get('protocol') or 'TCP')}"
                 for p in map(mapping, items(c.get("ports"))) if p.get("containerPort")]  # fmt: skip
        lines += line(f"{who} ports", ports)
        lines += line(f"{who} mounts", [
            f"{flat(m.get('name'))} at {flat(m.get('mountPath'))}"
            for m in map(mapping, items(c.get("volumeMounts")))])  # fmt: skip
        env = [flat(mapping(e).get("name")) for e in items(c.get("env"))]
        lines += line(f"{who} environment names", env)
    for v in map(mapping, items(spec.get("volumes"))):
        source = next((k for k in v if k != "name"), "")
        detail = mapping(v.get(source))
        what = flat(detail.get("claimName") or detail.get("name")
                    or detail.get("secretName") or detail.get("path"))  # fmt: skip
        lines += line(f"volume {flat(v.get('name'))}:", [f"{source} {what}".strip()])
    return lines


def k8s(doc: dict) -> str:
    kind, meta, spec = (
        flat(doc.get("kind")),
        mapping(doc.get("metadata")),
        mapping(doc.get("spec")),
    )
    ns = flat(meta.get("namespace"))
    lines = [f"== {kind} {ns + '/' if ns else ''}{flat(meta.get('name'))}"]
    lines += line(
        "labels",
        [f"{flat(k)}={flat(v)}" for k, v in mapping(meta.get("labels")).items()],
    )
    if kind in ("ConfigMap", "Secret"):  # names only: a value may be a password
        lines += line("keys", names(doc.get("data")) + names(doc.get("stringData")))
    elif kind == "Service":
        lines += line("type", [flat(spec.get("type"))])
        lines += line("ports", [
            f"{flat(p.get('port'))} to {flat(p.get('targetPort') or p.get('port'))}"
            f"/{flat(p.get('protocol') or 'TCP')}"
            + (f" node {flat(p['nodePort'])}" if p.get("nodePort") else "")
            for p in map(mapping, items(spec.get("ports")))])  # fmt: skip
        lines += line(
            "selects",
            [f"{flat(k)}={flat(v)}" for k, v in mapping(spec.get("selector")).items()],
        )
    elif kind == "Ingress":
        for r in map(mapping, items(spec.get("rules"))):
            for p in map(mapping, items(dig(r, ("http",)).get("paths"))):
                back = dig(p, ("backend", "service"))
                port = mapping(back.get("port"))
                lines.append(f"route {flat(r.get('host')) or '*'}{flat(p.get('path')) or '/'} "
                             f"to {flat(back.get('name'))}:{flat(port.get('number') or port.get('name'))}")  # fmt: skip
    elif kind == "PersistentVolumeClaim":
        size = dig(spec, ("resources", "requests")).get("storage")
        lines += line("size", [flat(size)])
        lines += line("access", [flat(m) for m in items(spec.get("accessModes"))])
    else:
        lines += line("replicas", [flat(spec.get("replicas"))])
        lines += line("schedule", [flat(spec.get("schedule"))])
        lines += pod(dig(doc, ("spec", *POD.get(kind, ("template", "spec")))))
        for t in map(mapping, items(spec.get("volumeClaimTemplates"))):
            size = dig(t, ("spec", "resources", "requests")).get("storage")
            name = flat(mapping(t.get("metadata")).get("name"))
            lines += line(f"claim {name}:", [flat(size)])
    return "\n".join(lines)


def is_object(doc) -> bool:
    return isinstance(doc, dict) and "apiVersion" in doc and "kind" in doc


def passages(docs: list) -> list[str]:
    out = []
    for doc in docs:
        if isinstance(doc, dict) and isinstance(doc.get("services"), dict):
            out += compose(doc)
        elif is_object(doc) and doc["kind"] == "List":
            out += [k8s(x) for x in items(doc.get("items")) if is_object(x)]
        elif is_object(doc):
            out.append(k8s(doc))
    return out


def as_text(path: Path) -> str:
    """The file's passages, "" for YAML that is neither kind; raises for a
    file that isn't YAML."""
    import yaml

    with open(path, encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))
    found = passages(docs)
    return "\n\n".join(found) + "\n" if found else ""


def inside(a: Path, b: Path) -> bool:
    return a == b or b in a.parents


def mirror(src: Path, dst: Path) -> int:
    try:
        import yaml  # noqa: F401
    except ImportError:
        print(f"refused: manifests needs PyYAML: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    src, dst = src.resolve(), dst.resolve()
    if not src.is_dir():
        print(f"refused: {src} is not a folder", file=sys.stderr)
        return kernel.REFUSED
    if inside(dst, src) or inside(src, dst):
        print(
            "refused: the mirror and the folder can't be inside each other",
            file=sys.stderr,
        )
        return kernel.REFUSED
    wrote = other = skipped = 0
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if not p.is_file() or p.suffix.lower() not in KINDS:
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            text = as_text(p)
        except Exception:  # PyYAML raises many kinds for a broken file
            skipped += 1
            continue
        if not text:
            other += 1
            continue
        out = dst / (str(rel) + ".txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        wrote += 1
    print(f"wrote {wrote} files to {dst}; {other} other YAML; skipped {skipped}")
    return kernel.ALIVE if wrote else kernel.ESCALATE


def main(argv: list[str]) -> int:
    if (
        len(argv) == 5
        and argv[0] == "mirror"
        and argv[1] == "--from"
        and argv[3] == "--to"
    ):
        return mirror(Path(argv[2]), Path(argv[4]))
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


if __name__ == "__main__":
    os.environ.setdefault("PYTHONHASHSEED", "0")
    raise SystemExit(main(sys.argv[1:]))
