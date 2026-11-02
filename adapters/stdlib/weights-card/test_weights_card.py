"""weights-card: the card says what the weights file's header says, and
`not in the header` for what it doesn't."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "weights_card.py"
_spec = importlib.util.spec_from_file_location("weights_card", SCRIPT)
wc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wc)

U8, I8, U16, I16, U32, I32, F32, BOOL, STR, ARR, U64, I64, F64 = range(13)
FORMATS = {U8: "<B", I8: "<b", U16: "<H", I16: "<h", U32: "<I", I32: "<i",
           F32: "<f", BOOL: "<?", U64: "<Q", I64: "<q", F64: "<d"}  # fmt: skip


def s(text: str | bytes) -> bytes:
    raw = text if isinstance(text, bytes) else text.encode()
    return struct.pack("<Q", len(raw)) + raw


def val(kind: int, v) -> bytes:
    if kind == STR:
        return s(v)
    if kind == ARR:
        inner, items = v
        return struct.pack("<IQ", inner, len(items)) + b"".join(
            val(inner, x) for x in items
        )
    return struct.pack(FORMATS[kind], v)


def gguf(pairs, tensors=(), version=3) -> bytes:
    """A GGUF header, written as the spec lays it out, with no tensor data."""
    out = b"GGUF" + struct.pack("<IQQ", version, len(tensors), len(pairs))
    for key, kind, v in pairs:
        out += s(key) + struct.pack("<I", kind) + val(kind, v)
    for name, dims in tensors:
        out += s(name) + struct.pack("<I", len(dims))
        out += b"".join(struct.pack("<Q", d) for d in dims)
        out += struct.pack("<IQ", 0, 0)
    return out


def safetensors(head: dict) -> bytes:
    raw = json.dumps(head).encode()
    return struct.pack("<Q", len(raw)) + raw + b"\0" * 16


GEMMA = [
    ("general.architecture", STR, "gemma3"),
    ("general.name", STR, "Gemma 3 4b It"),
    ("tokenizer.ggml.tokens", ARR, (STR, ["<pad>", "<eos>", ""])),
    ("tokenizer.ggml.scores", ARR, (F32, [0.0, -1.5])),
    ("tokenizer.ggml.merges", ARR, (STR, [])),
    ("gemma3.context_length", U32, 131072),
    ("general.file_type", U32, 15),
    ("general.license", STR, "gemma"),
]


def run(*argv) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argv)],
                          capture_output=True, text=True, encoding="utf-8")  # fmt: skip


def write(tmp_path: Path, name: str, data: bytes) -> Path:
    p = tmp_path / name
    p.write_bytes(data)
    return p


def test_a_gguf_header_fills_in_the_card(tmp_path):
    data = gguf(GEMMA, [("token_embd.weight", [2560, 262144]), ("norm", [2560])])
    w = write(tmp_path, "gemma-3-4b-it-Q4_K_M.gguf", data)
    got = run("--from", w, "--to", tmp_path / "card.md")
    assert got.returncode == 0, got.stderr
    assert got.stdout == f"wrote {tmp_path / 'card.md'}: {w.name}\n"
    digest = hashlib.sha256(data).hexdigest()
    assert (tmp_path / "card.md").read_text(encoding="utf-8") == (
        "<!-- willow-model\n"
        "file: gemma-3-4b-it-Q4_K_M.gguf\n"
        "format: GGUF v3\n"
        f"sha256: {digest}\n"
        f"bytes: {len(data)}\n"
        "architecture: gemma3\n"
        "name: Gemma 3 4b It\n"
        "quantization: Q4_K_M\n"
        "context length: 131072\n"
        f"parameters: {2560 * 262144 + 2560}\n"
        "licence: gemma\n"
        "-->\n"
        "# Gemma 3 4b It\n"
        "\n"
        "Read from the weights file's own header by weights-card. A value the "
        'header doesn\'t hold is written as "not in the header".\n'
    )
    assert (tmp_path / "card.md").stat().st_mode & 0o111 == 0, "never executable"


def test_the_same_file_gives_the_same_card_wherever_it_lives(tmp_path):
    data = gguf(GEMMA, [("norm", [8])], version=2)
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    one = write(tmp_path / "a", "m.gguf", data)
    two = write(tmp_path / "b", "m.gguf", data)
    assert run("--from", one, "--to", tmp_path / "1.md").returncode == 0
    assert run("--from", two, "--to", tmp_path / "2.md").returncode == 0
    text = (tmp_path / "1.md").read_text(encoding="utf-8")
    assert text == (tmp_path / "2.md").read_text(encoding="utf-8")
    assert "format: GGUF v2\n" in text and str(tmp_path) not in text


def test_what_the_header_doesnt_hold_is_said(tmp_path):
    w = write(tmp_path, "bare.gguf", gguf([("general.license", STR, "")]))
    assert run("--from", w, "--to", tmp_path / "card.md").returncode == 0
    text = (tmp_path / "card.md").read_text(encoding="utf-8")
    for field in ("architecture", "name", "quantization", "context length",
                  "parameters", "licence"):  # fmt: skip
        assert f"\n{field}: not in the header\n" in text
    assert "\n# bare.gguf\n" in text, "no name: the card is titled by the file"


def test_every_kind_of_value_is_read_past(tmp_path):
    pairs = [(f"x.{k}", k, 1) for k in FORMATS]
    pairs += [(f"a.{k}", ARR, (k, [1, 0])) for k in FORMATS]
    pairs += [("a.nested", ARR, (ARR, [(U8, [1]), (STR, ["z"])]))]
    pairs += [("general.name", STR, "After All"), ("general.file_type", U32, 32)]
    fields = wc.read_header(write(tmp_path, "m.gguf", gguf(pairs)))
    assert (fields["name"], fields["quantization"]) == ("After All", "BF16")


#: llama.cpp's own names for its file types (llama.h, enum llama_ftype)
LLAMA_FTYPE = {0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 7: "Q8_0", 8: "Q5_0",
               9: "Q5_1", 10: "Q2_K", 11: "Q3_K_S", 12: "Q3_K_M", 13: "Q3_K_L",
               14: "Q4_K_S", 15: "Q4_K_M", 16: "Q5_K_S", 17: "Q5_K_M", 18: "Q6_K",
               19: "IQ2_XXS", 20: "IQ2_XS", 21: "Q2_K_S", 22: "IQ3_XS",
               23: "IQ3_XXS", 24: "IQ1_S", 25: "IQ4_NL", 26: "IQ3_S", 27: "IQ3_M",
               28: "IQ2_S", 29: "IQ2_M", 30: "IQ4_XS", 31: "IQ1_M", 32: "BF16",
               36: "TQ1_0", 37: "TQ2_0", 38: "MXFP4_MOE", 39: "NVFP4",
               40: "Q1_0"}  # fmt: skip


@pytest.mark.parametrize("code", sorted(LLAMA_FTYPE) + [4, 99])
def test_a_file_type_is_named_as_llama_cpp_names_it(code, tmp_path):
    w = write(tmp_path, "m.gguf", gguf([("general.file_type", U32, code)]))
    want = LLAMA_FTYPE.get(code, f"file type {code}, not one this card names")
    assert wc.read_header(w)["quantization"] == want


def test_a_safetensors_header_fills_in_what_it_holds(tmp_path):
    head = {
        "__metadata__": {"format": "pt", "license": "apache-2.0"},
        "lm_head.weight": {"dtype": "BF16", "shape": [4, 8], "data_offsets": [0, 64]},
        "norm.weight": {"dtype": "F32", "shape": [8], "data_offsets": [64, 96]},
        "embed.weight": {"dtype": "BF16", "shape": [2, 8], "data_offsets": [96, 128]},
        "zeros": {"dtype": "I8", "shape": [8], "data_offsets": [128, 136]},
    }
    w = write(tmp_path, "model.safetensors", safetensors(head))
    assert run("--from", w, "--to", tmp_path / "card.md").returncode == 0
    text = (tmp_path / "card.md").read_text(encoding="utf-8")
    assert "\nformat: safetensors\n" in text
    assert "\nquantization: BF16, F32, I8\n" in text, "most parameters first"
    assert "\nparameters: 64\n" in text
    assert "\nlicence: apache-2.0\n" in text
    assert "\ncontext length: not in the header\n" in text
    assert "\narchitecture: not in the header\n" in text
    empty = write(tmp_path, "empty.safetensors", safetensors({}))
    fields = wc.read_header(empty)
    assert fields["parameters"] == fields["quantization"] == wc.MISSING


@pytest.mark.parametrize(
    "data, why",
    [
        (b"Tomatoes want sun.\n", "no safetensors header"),
        (b"GGU", "cut short"),
        (gguf(GEMMA)[:-3], "cut short"),
        (gguf([], [("norm", [8])])[:-1], "cut short"),
        (gguf([("k", STR, "v")], version=1), "GGUF version 1"),
        (gguf([("k", U32, 0)]).replace(b"k\x04\0", b"k\x0d\0"), "unknown type 13"),
        (gguf([("k", STR, b"\xff")]), "isn't UTF-8"),
        (struct.pack("<Q", 100_000_001) + b"{}", "no safetensors header"),
        (struct.pack("<Q", 100_000_000) + b"{}", "cut short"),
        (struct.pack("<Q", 2) + b"[]", "no safetensors header"),
        (struct.pack("<Q", 2) + b"\xff\xfe", "no safetensors header"),
        (safetensors({"t": {"dtype": "F16"}}), "the tensor t has no shape"),
        (safetensors({"t": {"dtype": "F16", "shape": [-1]}}), "has no shape"),
        (safetensors({"t": {"dtype": "F16", "shape": ["8"]}}), "has no shape"),
        (safetensors({"t": 5}), "has no shape"),
    ],
)
def test_a_file_it_cant_read_writes_nothing(data, why, tmp_path):
    w = write(tmp_path, "notes.bin", data)
    got = run("--from", w, "--to", tmp_path / "card.md")
    assert got.returncode == 42, got.stderr
    assert got.stdout.startswith("not a weights file it can read: notes.bin: ")
    assert why in got.stdout
    assert not (tmp_path / "card.md").exists()


def test_a_bad_command_line_is_refused(tmp_path):
    w = write(tmp_path, "m.gguf", gguf(GEMMA))
    got = run()
    assert got.returncode == 2 and "weights_card.py" in got.stderr
    got = run("--from", w, "--to", tmp_path / "c.md", "stray")
    assert got.returncode == 2 and not (tmp_path / "c.md").exists()
    got = run("--from", tmp_path / "missing.gguf", "--to", tmp_path / "c.md")
    assert got.returncode == 2 and "not a file" in got.stderr
    got = run("--from", w, "--to", tmp_path / "no" / "c.md")
    assert got.returncode == 2 and "no folder" in got.stderr
    assert not (tmp_path / "no").exists(), "a missing folder is never made"
    (tmp_path / "c.md").write_text("mine\n", encoding="utf-8")
    got = run("--from", w, "--to", tmp_path / "c.md")
    assert got.returncode == 2 and "could not write" in got.stderr
    assert (tmp_path / "c.md").read_text(encoding="utf-8") == "mine\n"
