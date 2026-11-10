"""wake_gate.py: ask out loud only after a wake word you chose.

    python adapters/deps/wake-gate/wake_gate.py listen --wake MODEL.onnx --features DIR --whisper DIR
        [--from FILE.wav | --from -] [--threshold 0.5] [--speech-level 500]

Audio before the wake word is never transcribed, kept or sent. A state
machine holds that: while it listens, each 80 ms of audio goes to the wake
word model and nowhere else, then is dropped; only once the wake word
scores past --threshold does it start keeping what follows, and only that,
up to the end of the sentence, goes to the transcriber, once. What it
heard is printed, one question a line, for you to ask:

    arecord -q -f S16_LE -r 16000 -c 1 -t raw | python adapters/deps/wake-gate/wake_gate.py \\
        listen --wake hey_willow.onnx --features FEATURES --whisper WHISPER --from - \\
        | while read -r q; do python kernel.py bite --box BOX "$q"; done

Audio is 16 kHz, 16-bit, mono: a .wav file of that kind, or raw samples on
stdin (--from -, the default). MODEL.onnx is a wake word model trained the
openWakeWord way; FEATURES is a folder holding openWakeWord's two feature
models, melspectrogram.onnx and embedding_model.onnx; WHISPER is a folder
holding a faster-whisper (CTranslate2) model. Nothing is fetched: every
model is a file you give it.

Each step of the machine is said on stderr as one JSON line (armed, its
score; endpoint, how many frames; transcribed, how many characters), never
the audio and never the words. A sentence is over after 0.8 s under
--speech-level (the loudness, as RMS of the 16-bit samples, that counts as
speech); a wake word with no speech within 2 s is a false wake, dropped
untranscribed; a sentence is cut at 15 s.

Needs onnxruntime, numpy and faster-whisper:

    pip install -r adapters/deps/wake-gate/requirements.txt

Without them it refuses and names the install; it never skips quietly.
Exit codes, the kernel's: 0 a question heard; 42 none; 2 refused.

The controller is ported from willow-mcp's voice ingress membrane, and the
wake word pipeline from openWakeWord, both Apache-2.0: their licences and
notices are beside this file.
"""

from __future__ import annotations

import array
import json
import math
import sys
import wave
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Iterable, Iterator, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import kernel  # noqa: E402

INSTALL = "pip install -r adapters/deps/wake-gate/requirements.txt"
RATE = 16000
#: one frame: 80 ms, the step openWakeWord scores at
FRAME = 1280
FRAME_BYTES = FRAME * 2


# ── the machine: ported from willow-mcp's voice_controller.py ───────────────
class State(Enum):
    IDLE = auto()
    CAPTURE = auto()


#: keys that would turn a receipt into a recording; refused at write time
FORBIDDEN = frozenset(
    {"audio", "samples", "pcm", "transcript", "text", "utterance", "words"}
)


@dataclass
class Receipt:
    tick: int
    event: str
    meta: dict = field(default_factory=dict)


class WakeGate(Protocol):
    """A streaming wake word scorer. score() is called only while idle, a
    frame at a time; reset() on every return to idle, so no part of one
    wake survives into the next."""

    def score(self, pcm: bytes) -> float: ...

    def reset(self) -> None: ...


@dataclass
class Config:
    threshold: float = 0.5  # a wake word score this high arms it
    silence_frames: int = 10  # 0.8 s under speech level ends a sentence
    false_wake_frames: int = 25  # 2 s armed with no speech is a false wake
    max_frames: int = 188  # 15 s: a sentence is cut there


class Controller:
    """Feed it frames with step(); finish() at the end of the audio."""

    def __init__(
        self,
        wake: WakeGate,
        speech: Callable[[bytes], bool],
        transcribe: Callable[[list[bytes]], str],
        ask: Callable[[str], None],
        config: Config | None = None,
        said: Callable[[Receipt], None] | None = None,
    ):
        self.wake, self.speech, self.transcribe, self.ask = (
            wake,
            speech,
            transcribe,
            ask,
        )
        self.cfg = config or Config()
        self.said = said or (lambda r: None)
        self.state = State.IDLE
        self.tick = 0
        self.receipts: list[Receipt] = []
        self.asked = 0
        self._kept: list[bytes] = []  # only ever filled while capturing
        self._armed_at = 0
        self._heard_speech = False
        self._quiet = 0

    def _receipt(self, event: str, **meta) -> None:
        leaked = FORBIDDEN & meta.keys()
        if leaked:
            raise AssertionError(f"receipt {event!r} would hold {sorted(leaked)}")
        r = Receipt(self.tick, event, meta)
        self.receipts.append(r)
        self.said(r)

    def _to_idle(self, event: str, **meta) -> None:
        self._kept = []  # what was kept goes on every return to idle
        self._heard_speech = False
        self._quiet = 0
        self.state = State.IDLE
        self.wake.reset()
        self._receipt(event, **meta)

    def step(self, pcm: bytes) -> None:
        self.tick += 1
        if self.state is State.IDLE:
            score = self.wake.score(pcm)
            if score >= self.cfg.threshold:
                self._kept = []
                self._armed_at = self.tick
                self.state = State.CAPTURE
                self._receipt("armed", score=round(score, 3))
            return  # a frame below the wake word is dropped here, unkept
        self._kept.append(pcm)
        if self.speech(pcm):
            self._heard_speech = True
            self._quiet = 0
        elif self._heard_speech:
            self._quiet += 1
        elif self.tick - self._armed_at >= self.cfg.false_wake_frames:
            self._to_idle("false_wake")
            return
        ended = self._heard_speech and self._quiet >= self.cfg.silence_frames
        if ended or len(self._kept) >= self.cfg.max_frames:
            self._endpoint(cut=not ended)

    def finish(self) -> None:
        """The audio ended: a sentence being kept is heard as it stands."""
        if self.state is State.CAPTURE and self._heard_speech:
            self._endpoint(cut=True)
        elif self.state is State.CAPTURE:
            self._to_idle("false_wake")

    def _endpoint(self, cut: bool) -> None:
        self._receipt("endpoint", frames=len(self._kept), cut=cut)
        heard = self.transcribe(list(self._kept)).strip()
        self._receipt("transcribed", chars=len(heard))
        if heard:
            self.ask(heard)
            self.asked += 1
        self._to_idle("disarm")


def loud(level: float) -> Callable[[bytes], bool]:
    """Speech is a frame whose RMS, over its 16-bit samples, reaches level."""

    def speech(pcm: bytes) -> bool:
        a = array.array("h", pcm)
        if not a:
            return False
        return math.sqrt(sum(s * s for s in a) / len(a)) >= level

    return speech


# ── the wake word: openWakeWord's pipeline, run through onnxruntime ─────────
class OnnxWake:
    """openWakeWord's three models in turn: the melspectrogram of the last
    audio, Google's speech embedding of the last 76 of its frames, and the
    wake word model over the last 16 embeddings. `session` makes an
    onnxruntime-like session from a path (tests give their own)."""

    MEL_WINDOW = 76  # melspectrogram frames an embedding reads
    EMBEDDINGS = 16  # embeddings the wake model reads
    #: audio the melspectrogram needs for 76 frames: 160-sample hops, 400-wide
    AUDIO = 160 * (MEL_WINDOW - 1) + 400 + 480

    def __init__(self, model: Path, features: Path, session: Callable, np):
        self.np = np
        self.mel = session(str(features / "melspectrogram.onnx"))
        self.embed = session(str(features / "embedding_model.onnx"))
        self.model = session(str(model))
        self.reset()

    def reset(self) -> None:
        self.audio = self.np.zeros(0, dtype=self.np.int16)
        self.embeddings: deque = deque(maxlen=self.EMBEDDINGS)

    def score(self, pcm: bytes) -> float:
        np = self.np
        new = np.frombuffer(pcm, dtype=np.int16)
        self.audio = np.concatenate([self.audio, new])[-self.AUDIO :]
        if len(self.audio) < self.AUDIO:
            return 0.0
        x = self.audio.astype(np.float32)[None, :]
        spec = self.mel.run(None, {self.mel.get_inputs()[0].name: x})[0]
        spec = np.squeeze(spec) / 10 + 2  # openWakeWord's own scaling
        if spec.ndim != 2 or spec.shape[0] < self.MEL_WINDOW:
            return 0.0
        window = spec[-self.MEL_WINDOW :][None, :, :, None].astype(np.float32)
        e = self.embed.run(None, {self.embed.get_inputs()[0].name: window})[0]
        self.embeddings.append(np.squeeze(e).astype(np.float32))
        if len(self.embeddings) < self.EMBEDDINGS:
            return 0.0
        feats = np.stack(list(self.embeddings))[None, :, :]
        out = self.model.run(None, {self.model.get_inputs()[0].name: feats})[0]
        return float(np.ravel(out)[0])


class Whisper:
    """faster-whisper over a model folder on this machine; never fetches."""

    def __init__(self, folder: Path, WhisperModel, np):
        self.np = np
        self.model = WhisperModel(
            str(folder), device="cpu", compute_type="int8", local_files_only=True
        )

    def __call__(self, frames: list[bytes]) -> str:
        np = self.np
        audio = np.frombuffer(b"".join(frames), dtype=np.int16).astype(np.float32)
        segments, _ = self.model.transcribe(audio / 32768.0, language=None)
        return " ".join(s.text.strip() for s in segments)


# ── the audio ───────────────────────────────────────────────────────────────
def frames_of(stream) -> Iterator[bytes]:
    """80 ms frames of raw 16-bit samples; a short last one is padded with silence."""
    while True:
        b = stream.read(FRAME_BYTES)
        if not b:
            return
        if len(b) % 2:
            b = b[:-1]
        yield b + b"\0" * (FRAME_BYTES - len(b))


def wav_frames(path: Path) -> Iterable[bytes]:
    """A .wav file's frames; its kind is checked before the first one is read."""
    w = wave.open(str(path), "rb")
    got = (w.getframerate(), w.getnchannels(), w.getsampwidth())
    if got != (RATE, 1, 2):
        w.close()
        raise ValueError(
            f"{path.name} is {got[0]} Hz, {got[1]} channel(s), {8 * got[2]}-bit;"
            " it reads 16000 Hz, 1 channel, 16-bit"
        )
    return _closing(w)


def _closing(w) -> Iterator[bytes]:
    class Samples:
        def read(self, n: int) -> bytes:
            return w.readframes(n // 2)

    try:
        yield from frames_of(Samples())
    finally:
        w.close()


# ── the command line ────────────────────────────────────────────────────────
TAKES = ("--wake", "--features", "--whisper", "--from", "--threshold", "--speech-level")


def usage() -> int:
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return kernel.REFUSED


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "listen":
        return usage()
    opts: dict[str, str] = {}
    it = iter(argv[1:])
    for a in it:
        if a not in TAKES or a in opts:
            return usage()
        opts[a] = next(it, "")
    if not all(opts.get(k) for k in ("--wake", "--features", "--whisper")):
        return usage()
    try:
        cfg = Config(threshold=float(opts.get("--threshold", "0.5")))
        level = float(opts.get("--speech-level", "500"))
    except ValueError:
        return usage()
    if not 0 < cfg.threshold <= 1 or level <= 0:
        return usage()
    wake, features, folder = (
        Path(opts[k]) for k in ("--wake", "--features", "--whisper")
    )
    missing = [
        str(p)
        for p in (
            wake,
            features / "melspectrogram.onnx",
            features / "embedding_model.onnx",
        )
        if not p.is_file()
    ] + ([str(folder)] if not folder.is_dir() else [])
    if missing:
        print(f"refused: no model at {', '.join(missing)}", file=sys.stderr)
        return kernel.REFUSED
    source = opts.get("--from", "-")
    try:
        frames = (
            frames_of(sys.stdin.buffer) if source == "-" else wav_frames(Path(source))
        )
    except (OSError, EOFError, wave.Error, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return kernel.REFUSED
    try:
        import numpy as np
        import onnxruntime
        from faster_whisper import WhisperModel
    except ImportError as exc:
        print(f"refused: wake-gate needs {exc.name}: {INSTALL}", file=sys.stderr)
        return kernel.REFUSED
    try:
        gate = OnnxWake(
            wake,
            features,
            lambda p: onnxruntime.InferenceSession(
                p, providers=["CPUExecutionProvider"]
            ),
            np,
        )
        transcribe = Whisper(folder, WhisperModel, np)
    except Exception as exc:  # noqa: BLE001  a model that won't load: say which, and why
        print(f"refused: a model wouldn't load: {str(exc)[:300]}", file=sys.stderr)
        return kernel.REFUSED
    return listen(frames, gate, loud(level), transcribe, cfg)


def listen(frames, gate: WakeGate, speech, transcribe, cfg: Config) -> int:
    """Run the machine over the frames: each question heard to stdout, each
    step to stderr. 0 a question heard, 42 none."""

    def ask(heard: str) -> None:
        print(" ".join(heard.split()), flush=True)

    def said(r: Receipt) -> None:
        print(json.dumps({"tick": r.tick, "event": r.event, **r.meta}), file=sys.stderr)

    c = Controller(gate, speech, transcribe, ask, cfg, said)
    for f in frames:
        c.step(f)
    c.finish()
    return kernel.ALIVE if c.asked else kernel.ESCALATE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
