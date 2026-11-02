"""model_shelf.py: every model already on this machine, before you download another.

    python adapters/stdlib/model-shelf/model_shelf.py list [--home DIR] [--hash]

It looks where each runtime keeps its models, under your home folder (or
DIR): Ollama (`~/.ollama/models`, or OLLAMA_MODELS), LM Studio, Jan,
GPT4All, and the Hugging Face cache (`~/.cache/huggingface/hub`, or
HF_HUB_CACHE, or HF_HOME). Each GGUF or safetensors file found is one line:
its runtime, its name there, its size, its quantization (read from its own
header by weights-card) and its SHA-256.

    ollama        gemma3:4b  3338801804 bytes  Q4_K_M  sha256=aeda… (Ollama's name for it)
    lm-studio     lmstudio-community/gemma-3-4b-it-GGUF/gemma-3-4b-it-Q4_K_M.gguf  2489757856 bytes  Q4_K_M  not hashed
    jan           not on this machine

Ollama and the Hugging Face cache name each file by its SHA-256, so that
hash is theirs and nothing is read for it. The others are hashed only with
`--hash`, since a model is gigabytes; until then the line says `not hashed`.
The same weights under two names (two Ollama tags, a copy in LM Studio of
a file in the Hugging Face cache) are said, once both hashes are known; the
total counts each file once.

Paths are shown from `~` when under the home folder. It only reads.

Exit codes, the kernel's: 0 at least one model found; 42 none found;
2 refused (a bad command line, DIR not a folder).
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import kernel  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "willow_weights_card_for_shelf", HERE.parent / "weights-card" / "weights_card.py"
)
weights_card = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(weights_card)

USAGE = "usage: model_shelf.py list [--home DIR] [--hash]"
SHA = re.compile(r"[0-9a-f]{64}")
WEIGHTS = (".gguf", ".safetensors")
MODEL_LAYER = "application/vnd.ollama.image.model"
OLLAMA_HOST = "registry.ollama.ai"

#: where each runtime keeps its models, under the home folder: Linux, macOS, Windows
FOLDERS = {
    "lm-studio": [".lmstudio/models", ".cache/lm-studio/models"],
    "jan": [
        "jan/models",
        ".local/share/Jan/data",
        "Library/Application Support/Jan/data",
        "AppData/Roaming/Jan/data",
    ],
    "gpt4all": [
        ".local/share/nomic.ai/GPT4All",
        "Library/Application Support/nomic.ai/GPT4All",
        "AppData/Local/nomic.ai/GPT4All",
    ],
}


class Model:
    def __init__(self, runtime: str, name: str, path: Path, sha: str, why: str):
        self.runtime, self.name, self.path = runtime, name, path
        self.sha, self.why = sha, why  # why: whose name the hash is, or ""


def shown(path: Path, home: Path) -> str:
    try:
        return "~/" + path.relative_to(home).as_posix()
    except ValueError:
        return path.as_posix()


def weights_in(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*") if p.suffix.lower() in WEIGHTS and p.is_file()
    )


def ollama(root: Path) -> list[Model]:
    """Each tag's model layer, read from its manifest."""
    found = []
    manifests = root / "manifests"
    for m in sorted(p for p in manifests.rglob("*") if p.is_file()):
        parts = m.relative_to(manifests).parts
        if len(parts) != 4:
            continue
        host, space, model, tag = parts
        name = f"{model}:{tag}"
        if space != "library" or host != OLLAMA_HOST:
            name = f"{space}/{name}"
        if host != OLLAMA_HOST:
            name = f"{host}/{name}"
        try:
            layers = json.loads(m.read_text(encoding="utf-8")).get("layers", [])
        except (OSError, UnicodeDecodeError, ValueError, AttributeError):
            continue
        for layer in layers:
            if not isinstance(layer, dict) or layer.get("mediaType") != MODEL_LAYER:
                continue
            digest = str(layer.get("digest", "")).removeprefix("sha256:")
            if SHA.fullmatch(digest):
                blob = root / "blobs" / f"sha256-{digest}"
                found.append(
                    Model("ollama", name, blob, digest, "Ollama's name for it")
                )
    return found


def hugging_face(root: Path) -> list[Model]:
    """Each weights file in a snapshot, named by the blob it points to."""
    found, seen = [], set()
    for repo in sorted(root.glob("models--*")):
        org_name = repo.name[len("models--") :].replace("--", "/")
        for p in sorted((repo / "snapshots").glob("*/**/*")):
            if p.suffix.lower() not in WEIGHTS or not p.is_file():
                continue
            blob = p.resolve()
            if blob in seen:
                continue
            seen.add(blob)
            rel = p.relative_to(repo / "snapshots").parts[1:]
            name = f"{org_name}/{'/'.join(rel)}"
            if SHA.fullmatch(blob.name):
                found.append(
                    Model(
                        "hugging-face", name, blob, blob.name, "the cache's name for it"
                    )
                )
            else:
                found.append(Model("hugging-face", name, blob, "", ""))
    return found


def plain(runtime: str, root: Path) -> list[Model]:
    return [
        Model(runtime, p.relative_to(root).as_posix(), p, "", "")
        for p in weights_in(root)
    ]


def places(home: Path, env: dict[str, str]) -> list[tuple[str, list[Path]]]:
    hf = env.get("HF_HUB_CACHE") or (
        str(Path(env["HF_HOME"]) / "hub") if env.get("HF_HOME") else ""
    )
    return [
        ("ollama", [Path(env["OLLAMA_MODELS"])] if env.get("OLLAMA_MODELS") else [home / ".ollama/models"]),
        *((rt, [home / f for f in fs]) for rt, fs in FOLDERS.items()),
        ("hugging-face", [Path(hf)] if hf else [home / ".cache/huggingface/hub"]),
    ]  # fmt: skip


def quantization(path: Path) -> str:
    try:
        return weights_card.read_header(path)["quantization"]
    except weights_card.Unreadable as e:
        return f"header unreadable: {e}"
    except OSError as e:
        return f"unreadable: {type(e).__name__}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(io.DEFAULT_BUFFER_SIZE), b""):
            h.update(block)
    return h.hexdigest()


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a == "--home":
            opts[a] = next(it, "")
        elif a == "--hash":
            opts[a] = "yes"
        else:
            args.append(a)
    if args != ["list"] or opts.get("--home") == "":
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    home = Path(opts["--home"]) if "--home" in opts else Path.home()
    if not home.is_dir():
        print(f"refused: not a folder: {home}", file=sys.stderr)
        return kernel.REFUSED
    models, absent = [], []
    for runtime, roots in places(home, dict(os.environ)):
        there = [r for r in roots if r.is_dir()]
        if not there:
            absent.append(f"{runtime:<13} not on this machine "
                          f"(looked in {', '.join(shown(r, home) for r in roots)})")  # fmt: skip
            continue
        got = []
        for root in there:
            if runtime == "ollama":
                got += ollama(root)
            elif runtime == "hugging-face":
                got += hugging_face(root)
            else:
                got += plain(runtime, root)
        if not got:
            absent.append(f"{runtime:<13} nothing there "
                          f"({', '.join(shown(r, home) for r in there)})")  # fmt: skip
        models += got
    for m in models:
        if not m.path.is_file():
            print(
                f"{m.runtime:<13} {m.name}  its file is missing ({shown(m.path, home)})"
            )
            continue
        if not m.sha and "--hash" in opts:
            m.sha, m.why = sha256_file(m.path), "hashed now"
        sha = f"sha256={m.sha} ({m.why})" if m.sha else "not hashed"
        size = m.path.stat().st_size
        print(f"{m.runtime:<13} {m.name}  {size} bytes  {quantization(m.path)}  {sha}")
    for line in absent:
        print(line)
    by_sha: dict[str, list[Model]] = {}
    for m in models:
        if m.sha and m.path.is_file():
            by_sha.setdefault(m.sha, []).append(m)
    for sha, same in sorted(by_sha.items()):
        if len(same) > 1:
            names = ", ".join(f"{m.runtime} {m.name}" for m in same)
            print(f"the same weights under {len(same)} names: {names} (sha256={sha})")
    held = [m for m in models if m.path.is_file()]
    files = {m.path.resolve() for m in held}
    total = sum(p.stat().st_size for p in files)
    print(f"{len(held)} models in {len(files)} files, {total} bytes")
    return kernel.ALIVE if held else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
