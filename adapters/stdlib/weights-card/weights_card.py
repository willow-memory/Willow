"""weights_card.py: a model card filled in from the weights file's own header.

    python adapters/stdlib/weights-card/weights_card.py --from FILE --to CARD

FILE is a GGUF or a safetensors file. Only its header is read: the
architecture, the model's name, its quantization, its context length, its
licence and its parameters, each as the file states it, and the whole
file's SHA-256 and size. CARD is written once, a new file:

    <!-- willow-model
    file: gemma-3-4b-it-Q4_K_M.gguf
    format: GGUF v3
    sha256: 9c1e…
    bytes: 2489757856
    architecture: gemma3
    name: Gemma 3 4b It
    quantization: Q4_K_M
    context length: 131072
    parameters: 3880263168
    licence: gemma
    -->

A value the header doesn't hold is written as `not in the header`, never
guessed and never left out. Only the file's name goes on the card, not
where it lives, so the same file gives the same bytes on any machine.

Exit codes, the kernel's: 0 a card written; 42 not a weights file it can
read (no GGUF or safetensors header, or one cut short), nothing written;
2 refused (a bad command line, FILE missing, CARD already there or its
folder missing).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

USAGE = "usage: weights_card.py --from FILE --to CARD"
MISSING = "not in the header"
MARKER = "<!-- willow-model"
FIELDS = (
    "file",
    "format",
    "sha256",
    "bytes",
    "architecture",
    "name",
    "quantization",
    "context length",
    "parameters",
    "licence",
)
#: safetensors caps its JSON header at 100 MB
SAFETENSORS_MAX = 100_000_000

#: llama.cpp's general.file_type, the quantization most of the file is in
FILE_TYPES = {
    0: "F32",
    1: "F16",
    2: "Q4_0",
    3: "Q4_1",
    7: "Q8_0",
    8: "Q5_0",
    9: "Q5_1",
    10: "Q2_K",
    11: "Q3_K_S",
    12: "Q3_K_M",
    13: "Q3_K_L",
    14: "Q4_K_S",
    15: "Q4_K_M",
    16: "Q5_K_S",
    17: "Q5_K_M",
    18: "Q6_K",
    19: "IQ2_XXS",
    20: "IQ2_XS",
    21: "Q2_K_S",
    22: "IQ3_XS",
    23: "IQ3_XXS",
    24: "IQ1_S",
    25: "IQ4_NL",
    26: "IQ3_S",
    27: "IQ3_M",
    28: "IQ2_S",
    29: "IQ2_M",
    30: "IQ4_XS",
    31: "IQ1_M",
    32: "BF16",
    36: "TQ1_0",
    37: "TQ2_0",
    38: "MXFP4_MOE",
    39: "NVFP4",
    40: "Q1_0",
}

#: GGUF value types: the struct format of each fixed-size one
SCALARS = {
    0: "<B",
    1: "<b",
    2: "<H",
    3: "<h",
    4: "<I",
    5: "<i",
    6: "<f",
    7: "<?",
    10: "<Q",
    11: "<q",
    12: "<d",
}
STRING, ARRAY = 8, 9


class Unreadable(Exception):
    """Not a header this reads, with what is wrong in a sentence."""


class Reader:
    """Reads a header forward, refusing to run past the file's end."""

    def __init__(self, f, size: int):
        self.f, self.size = f, size

    def take(self, n: int) -> bytes:
        if n < 0 or self.f.tell() + n > self.size:
            raise Unreadable("the header is cut short")
        return self.f.read(n)

    def skip(self, n: int) -> None:
        if n < 0 or self.f.tell() + n > self.size:
            raise Unreadable("the header is cut short")
        self.f.seek(n, 1)

    def unpack(self, fmt: str):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self) -> str:
        raw = self.take(self.unpack("<Q"))
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            raise Unreadable("a string in the header isn't UTF-8") from None

    def value(self, kind: int):
        """One value; an array is skipped and stands as None."""
        if kind in SCALARS:
            return self.unpack(SCALARS[kind])
        if kind == STRING:
            return self.string()
        if kind != ARRAY:
            raise Unreadable(f"the header has a value of unknown type {kind}")
        inner, count = self.unpack("<I"), self.unpack("<Q")
        if inner in SCALARS:
            self.skip(count * struct.calcsize(SCALARS[inner]))
        else:
            for _ in range(count):
                self.value(inner)
        return None


def gguf(f, size: int) -> dict[str, str]:
    r = Reader(f, size)
    if r.take(4) != b"GGUF":
        raise Unreadable("no GGUF header")
    version = r.unpack("<I")
    if version not in (2, 3):
        raise Unreadable(f"GGUF version {version}, which this doesn't read")
    tensors, pairs = r.unpack("<Q"), r.unpack("<Q")
    meta = {}
    for _ in range(pairs):
        key = r.string()
        meta[key] = r.value(r.unpack("<I"))
    params = 0
    for _ in range(tensors):
        r.string()
        dims = r.unpack("<I")
        count = 1
        for _ in range(dims):
            count *= r.unpack("<Q")
        r.skip(12)  # its type (u32) and offset (u64)
        params += count
    arch = meta.get("general.architecture")
    ftype = meta.get("general.file_type")
    if ftype is None:
        quant = MISSING
    else:
        quant = FILE_TYPES.get(ftype, f"file type {ftype}, not one this card names")
    return {
        "format": f"GGUF v{version}",
        "architecture": arch,
        "name": meta.get("general.name"),
        "quantization": quant,
        "context length": meta.get(f"{arch}.context_length") if arch else None,
        "parameters": params if tensors else None,
        "licence": meta.get("general.license"),
    }


def safetensors(f, size: int) -> dict[str, str]:
    r = Reader(f, size)
    n = r.unpack("<Q")
    if n > SAFETENSORS_MAX:
        raise Unreadable("no safetensors header")
    try:
        head = json.loads(r.take(n).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise Unreadable("no safetensors header") from None
    if not isinstance(head, dict):
        raise Unreadable("no safetensors header")
    meta = head.pop("__metadata__", None)
    meta = meta if isinstance(meta, dict) else {}
    by_dtype: dict[str, int] = {}
    for name, t in sorted(head.items()):
        if not isinstance(t, dict) or not isinstance(t.get("shape"), list):
            raise Unreadable(f"the tensor {name} has no shape")
        count = 1
        for d in t["shape"]:
            if not isinstance(d, int) or d < 0:
                raise Unreadable(f"the tensor {name} has no shape")
            count *= d
        dtype = str(t.get("dtype"))
        by_dtype[dtype] = by_dtype.get(dtype, 0) + count
    order = sorted(by_dtype, key=lambda d: (-by_dtype[d], d))
    return {
        "format": "safetensors",
        "architecture": meta.get("architecture"),
        "name": meta.get("name"),
        "quantization": ", ".join(order) if order else None,
        "context length": None,
        "parameters": sum(by_dtype.values()) if head else None,
        "licence": meta.get("license"),
    }


def read_header(path: Path) -> dict[str, str]:
    """The card's fields from the file's header, or Unreadable."""
    size = path.stat().st_size
    with path.open("rb") as f:
        magic = f.read(4)
        f.seek(0)
        got = gguf(f, size) if magic == b"GGUF" else safetensors(f, size)
    return {k: MISSING if v in (None, "") else str(v) for k, v in got.items()}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(io.DEFAULT_BUFFER_SIZE), b""):
            h.update(block)
    return h.hexdigest()


def card(path: Path) -> str:
    fields = read_header(path)
    fields.update(
        file=path.name, sha256=sha256_file(path), bytes=str(path.stat().st_size)
    )
    title = fields["name"] if fields["name"] != MISSING else path.name
    lines = [MARKER, *(f"{k}: {fields[k]}" for k in FIELDS), "-->", f"# {title}", ""]
    lines.append(
        "Read from the weights file's own header by weights-card. A value "
        f'the header doesn\'t hold is written as "{MISSING}".'
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a in ("--from", "--to"):
            opts[a] = next(it, "")
        else:
            args.append(a)
    if not opts.get("--from") or not opts.get("--to") or args:
        print(USAGE, file=sys.stderr)
        return kernel.REFUSED
    src, to = Path(opts["--from"]), Path(opts["--to"])
    if not src.is_file():
        print(f"refused: not a file: {src}", file=sys.stderr)
        return kernel.REFUSED
    if not to.parent.is_dir():
        print(f"refused: no folder to write {to} in", file=sys.stderr)
        return kernel.REFUSED
    try:
        text = card(src)
    except Unreadable as e:
        print(f"not a weights file it can read: {src.name}: {e}")
        return kernel.ESCALATE
    try:
        fd = os.open(to, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except OSError as e:
        print(f"refused: could not write {to}: {type(e).__name__}", file=sys.stderr)
        return kernel.REFUSED
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as out:
        out.write(text)
    print(f"wrote {to}: {src.name}")
    return kernel.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
