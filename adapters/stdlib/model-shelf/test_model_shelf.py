"""model-shelf: every model on the machine, from each runtime's own folder,
with what's absent said."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "model_shelf.py"
ENV_KEYS = ("OLLAMA_MODELS", "HF_HUB_CACHE", "HF_HOME")


def gguf(file_type: int, name: str = "m") -> bytes:
    """A GGUF header holding general.file_type and general.name."""

    def s(b: bytes) -> bytes:
        return struct.pack("<Q", len(b)) + b

    return (b"GGUF" + struct.pack("<IQQ", 3, 0, 2)
            + s(b"general.file_type") + struct.pack("<II", 4, file_type)
            + s(b"general.name") + struct.pack("<I", 8) + s(name.encode()))  # fmt: skip


def run(*argv, env: dict | None = None) -> subprocess.CompletedProcess:
    clean = {k: v for k, v in os.environ.items() if k not in ENV_KEYS}
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8",
                          env={**clean, **(env or {})})  # fmt: skip


def put(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def ollama_tag(models: Path, host_space_model: str, tag: str, data: bytes) -> str:
    digest = hashlib.sha256(data).hexdigest()
    put(models / "blobs" / f"sha256-{digest}", data)
    manifest = {"layers": [
        {"mediaType": "application/vnd.ollama.image.template", "digest": "sha256:" + "1" * 64},
        {"mediaType": "application/vnd.ollama.image.model", "digest": f"sha256:{digest}"},
    ]}  # fmt: skip
    put(models / "manifests" / host_space_model / tag, json.dumps(manifest).encode())
    return digest


def test_each_runtime_is_read_from_its_own_folder(tmp_path):
    home = tmp_path / "home"
    q4 = gguf(15)
    d = ollama_tag(
        home / ".ollama/models", "registry.ollama.ai/library/gemma3", "4b", q4
    )
    lm = put(home / ".lmstudio/models/lmstudio-community/g-GGUF/g-Q8_0.gguf", gguf(7))
    put(home / ".lmstudio/models/notes.txt", b"not a model")
    put(home / ".local/share/nomic.ai/GPT4All/orca.gguf", gguf(2))
    hub = home / ".cache/huggingface/hub/models--google--gemma"
    st = b"\x02\0\0\0\0\0\0\0{}"
    sha_st = hashlib.sha256(st).hexdigest()
    put(hub / "blobs" / sha_st, st)
    (hub / "snapshots/abc123").mkdir(parents=True)
    (hub / "snapshots/abc123/model.safetensors").symlink_to(hub / "blobs" / sha_st)
    got = run("list", "--home", home)
    assert got.returncode == 0, got.stderr
    assert got.stdout.splitlines() == [
        f"ollama        gemma3:4b  {len(q4)} bytes  Q4_K_M  sha256={d} (Ollama's name for it)",
        f"lm-studio     lmstudio-community/g-GGUF/g-Q8_0.gguf  {lm.stat().st_size} bytes  Q8_0  not hashed",
        f"gpt4all       orca.gguf  {len(gguf(2))} bytes  Q4_0  not hashed",
        f"hugging-face  google/gemma/model.safetensors  {len(st)} bytes  not in the header  "
        f"sha256={sha_st} (the cache's name for it)",
        "jan           not on this machine (looked in ~/jan/models, ~/.local/share/Jan/data, "
        "~/Library/Application Support/Jan/data, ~/AppData/Roaming/Jan/data)",
        f"4 models in 4 files, {len(q4) + lm.stat().st_size + len(gguf(2)) + len(st)} bytes",
    ]


def test_hash_hashes_the_rest_and_finds_the_same_weights_twice(tmp_path):
    home = tmp_path / "home"
    data = gguf(15, "gemma")
    d = ollama_tag(
        home / ".ollama/models", "registry.ollama.ai/library/gemma3", "4b", data
    )
    ollama_tag(
        home / ".ollama/models", "registry.ollama.ai/library/gemma3", "latest", data
    )
    put(home / "jan/models/gemma/g.gguf", data)
    got = run("list", "--home", home)
    assert "jan           gemma/g.gguf" in got.stdout and "not hashed" in got.stdout
    assert (
        "the same weights under 2 names: ollama gemma3:4b, ollama gemma3:latest"
        in got.stdout
    )
    got = run("list", "--home", home, "--hash")
    assert got.returncode == 0
    assert (
        f"jan           gemma/g.gguf  {len(data)} bytes  Q4_K_M  sha256={d} (hashed now)"
        in got.stdout
    )
    assert ("the same weights under 3 names: ollama gemma3:4b, ollama gemma3:latest, "
            f"jan gemma/g.gguf (sha256={d})") in got.stdout  # fmt: skip
    assert got.stdout.endswith(f"3 models in 2 files, {2 * len(data)} bytes\n")


def test_names_off_ollamas_own_library_keep_their_place(tmp_path):
    models = tmp_path / "models"
    ollama_tag(models, "registry.ollama.ai/ana/tiny", "q4", gguf(2))
    ollama_tag(models, "hf.co/bartowski/qwen-GGUF", "Q6_K", gguf(18))
    put(models / "manifests/registry.ollama.ai/library/bad/x", b"not json")
    put(models / "manifests/registry.ollama.ai/stray", b"{}")
    put(models / "manifests/registry.ollama.ai/library/list/x", b"[]")
    put(models / "manifests/registry.ollama.ai/library/odd/x",
        json.dumps({"layers": ["x", {"mediaType": "application/vnd.ollama.image.model",
                                     "digest": "sha256:short"}]}).encode())  # fmt: skip
    got = run("list", "--home", tmp_path, env={"OLLAMA_MODELS": str(models)})
    assert got.returncode == 0, got.stderr
    lines = [line for line in got.stdout.splitlines() if line.startswith("ollama ")]
    assert len(lines) == 2
    assert lines[0].startswith("ollama        hf.co/bartowski/qwen-GGUF:Q6_K  ")
    assert lines[1].startswith("ollama        ana/tiny:q4  ")
    assert "Q6_K" in lines[0] and "Q4_0" in lines[1]


def test_a_missing_blob_and_an_unreadable_header_are_said(tmp_path):
    home = tmp_path / "home"
    models = home / ".ollama/models"
    d = ollama_tag(models, "registry.ollama.ai/library/gone", "1b", gguf(2))
    (models / "blobs" / f"sha256-{d}").unlink()
    put(home / ".lmstudio/models/broken.gguf", b"GGUF\x03\0")
    got = run("list", "--home", home)
    assert got.returncode == 0
    assert (
        "ollama        gone:1b  its file is missing (~/.ollama/models/blobs/sha256-"
        in got.stdout
    )
    assert (
        "lm-studio     broken.gguf  6 bytes  header unreadable: the header is cut short  not hashed"
        in got.stdout
    )
    assert got.stdout.endswith("1 models in 1 files, 6 bytes\n")


def test_hugging_face_cache_from_the_environment_and_a_blob_not_named_by_hash(tmp_path):
    cache = tmp_path / "hf"
    repo = cache / "hub/models--org--tiny"
    put(repo / "blobs/etag-not-a-hash", gguf(1))
    snap = repo / "snapshots/r1/sub"
    snap.mkdir(parents=True)
    (snap / "t.gguf").symlink_to(repo / "blobs/etag-not-a-hash")
    (repo / "snapshots/r2").mkdir(parents=True)
    put(repo / "snapshots/r2/config.json", b"{}")  # not weights: not a model
    (repo / "snapshots/r2/dir.gguf").mkdir()  # a folder, whatever its name
    (repo / "snapshots/r2/t.gguf").symlink_to(repo / "blobs/etag-not-a-hash")
    got = run("list", "--home", tmp_path, env={"HF_HOME": str(cache)})
    lines = [
        line for line in got.stdout.splitlines() if line.startswith("hugging-face ")
    ]
    assert lines == [
        f"hugging-face  org/tiny/sub/t.gguf  {len(gguf(1))} bytes  F16  not hashed"
    ]
    got = run(
        "list",
        "--home",
        tmp_path,
        env={"HF_HOME": "/nowhere", "HF_HUB_CACHE": str(cache / "hub")},
    )
    assert "org/tiny/sub/t.gguf" in got.stdout


def test_an_empty_shelf_is_42_and_says_where_it_looked(tmp_path):
    home = tmp_path / "home"
    (home / ".lmstudio/models").mkdir(parents=True)
    got = run("list", "--home", home)
    assert got.returncode == 42
    assert "lm-studio     nothing there (~/.lmstudio/models)\n" in got.stdout
    assert (
        "ollama        not on this machine (looked in ~/.ollama/models)\n" in got.stdout
    )
    assert got.stdout.endswith("0 models in 0 files, 0 bytes\n")
    elsewhere = run("list", "--home", home, env={"OLLAMA_MODELS": str(tmp_path / "o")})
    assert f"(looked in {(tmp_path / 'o').as_posix()})" in elsewhere.stdout


def test_a_bad_command_line_is_refused(tmp_path):
    got = run()
    assert got.returncode == 2 and "model_shelf.py" in got.stderr
    got = run("list", "stray")
    assert got.returncode == 2 and "model_shelf.py" in got.stderr
    got = run("list", "--home")
    assert got.returncode == 2 and "model_shelf.py" in got.stderr
    got = run("list", "--home", tmp_path / "missing")
    assert got.returncode == 2 and "not a folder" in got.stderr
