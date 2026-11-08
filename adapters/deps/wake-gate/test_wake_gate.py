"""wake-gate holds its card: nothing said before the wake word is
transcribed, a step is said without its words, a false wake and a long
sentence end untranscribed or cut, the wake word pipeline reads what
openWakeWord's models take, and a bad command line, a missing model or
audio of another kind is refused before anything loads.

The machine is tested with engines of the tests' own, frame by frame; the
pipeline with sessions that record what they were given. No model is
needed, and nothing goes online.
"""

from __future__ import annotations

import array
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "wake_gate.py"
spec = importlib.util.spec_from_file_location("wake_gate", SCRIPT)
wg = importlib.util.module_from_spec(spec)
sys.modules["wake_gate"] = wg  # dataclasses read their module's annotations from here
spec.loader.exec_module(wg)


def frame(mark: int, loud: bool) -> bytes:
    """A frame whose first sample says which it is, loud or quiet."""
    a = array.array("h", [3000 if loud else 0] * wg.FRAME)
    a[0] = mark
    return a.tobytes()


class Wake:
    """Arms on the frames it's told to; counts its resets."""

    def __init__(self, on: set[int]):
        self.on, self.seen, self.resets = on, [], 0

    def score(self, pcm: bytes) -> float:
        mark = array.array("h", pcm[:2])[0]
        self.seen.append(mark)
        return 0.9 if mark in self.on else 0.1

    def reset(self) -> None:
        self.resets += 1


class Ears:
    def __init__(self, says: str = "when is the boiler due"):
        self.calls: list[list[int]] = []
        self.says = says

    def __call__(self, frames: list[bytes]) -> str:
        self.calls.append([array.array("h", f[:2])[0] for f in frames])
        return self.says


def machine(on={20}, says="when is the boiler due", **cfg):
    wake, ears, asked = Wake(set(on)), Ears(says), []
    c = wg.Controller(wake, wg.loud(500), ears, asked.append, wg.Config(**cfg))
    return c, wake, ears, asked


def test_nothing_said_before_the_wake_word_is_transcribed():
    c, wake, ears, asked = machine(on={20})
    for i in range(1, 20):  # someone talking before the wake word
        c.step(frame(i, loud=True))
    c.step(frame(20, loud=True))  # the wake word
    for i in range(21, 30):
        c.step(frame(i, loud=True))  # the question
    for i in range(30, 45):
        c.step(frame(i, loud=False))  # quiet: the sentence is over
    assert asked == ["when is the boiler due"]
    assert len(ears.calls) == 1
    heard = ears.calls[0]
    assert min(heard) == 21, "the transcriber got audio from before the wake word"
    assert heard == list(range(21, 21 + len(heard)))
    assert wake.seen[:20] == list(range(1, 21)), "the wake word saw what came before"
    assert c.state is wg.State.IDLE and c._kept == []


def test_a_step_is_said_without_its_words():
    c, *_ = machine(on={1})
    c.step(frame(1, loud=False))
    for i in range(2, 6):
        c.step(frame(i, loud=True))
    for i in range(6, 20):
        c.step(frame(i, loud=False))
    events = [r.event for r in c.receipts]
    assert events == ["armed", "endpoint", "transcribed", "disarm"]
    for r in c.receipts:
        assert not wg.FORBIDDEN & r.meta.keys()
        assert "boiler" not in json.dumps(r.meta)
    assert c.receipts[2].meta == {"chars": len("when is the boiler due")}
    with pytest.raises(AssertionError, match="would hold"):
        c._receipt("transcribed", text="when is the boiler due")


def test_a_wake_with_no_speech_is_dropped_untranscribed():
    c, wake, ears, asked = machine(on={1})
    for i in range(1, 40):
        c.step(frame(i, loud=False))
    assert ears.calls == [] and asked == []
    assert [r.event for r in c.receipts] == ["armed", "false_wake"]
    assert c.receipts[1].tick - c.receipts[0].tick == wg.Config().false_wake_frames


def test_every_return_to_idle_starts_the_wake_word_clean():
    c, wake, ears, asked = machine(on={1, 40})
    for i in range(1, 30):  # a false wake
        c.step(frame(i, loud=False))
    assert wake.resets == 1
    c.step(frame(40, loud=False))
    for i in range(41, 45):
        c.step(frame(i, loud=True))
    for i in range(45, 60):
        c.step(frame(i, loud=False))
    assert wake.resets == 2 and asked == ["when is the boiler due"]
    assert 40 not in wake.seen[wake.seen.index(40) + 1 :], (
        "scored again while capturing"
    )


def test_a_long_sentence_is_cut_and_still_heard():
    c, wake, ears, asked = machine(on={1}, max_frames=12)
    c.step(frame(1, loud=False))
    for i in range(2, 30):
        c.step(frame(i, loud=True))
    assert ears.calls[0] == list(range(2, 14))
    endpoint = next(r for r in c.receipts if r.event == "endpoint")
    assert endpoint.meta == {"frames": 12, "cut": True}


def test_audio_that_ends_mid_sentence_ends_the_sentence():
    c, wake, ears, asked = machine(on={1})
    c.step(frame(1, loud=False))
    for i in range(2, 6):
        c.step(frame(i, loud=True))
    assert asked == []
    c.finish()
    assert asked == ["when is the boiler due"] and ears.calls == [[2, 3, 4, 5]]
    c2, _, ears2, asked2 = machine(on={1})
    c2.step(frame(1, loud=False))
    c2.finish()  # armed, then the audio ended before a word
    assert ears2.calls == [] and c2.receipts[-1].event == "false_wake"


def test_nothing_heard_is_nothing_asked():
    c, wake, ears, asked = machine(on={1}, says="   ")
    c.step(frame(1, loud=False))
    c.step(frame(2, loud=True))
    c.finish()
    assert len(ears.calls) == 1 and asked == [] and c.asked == 0


def test_speech_is_loudness():
    speech = wg.loud(500)
    assert not speech(frame(0, loud=False))
    assert speech(frame(0, loud=True))
    assert not speech(b"")
    assert wg.loud(5000)(frame(0, loud=True)) is False


def test_audio_comes_in_80_ms_frames_and_a_short_last_one_is_padded():
    raw = b"\x01\x00" * (wg.FRAME * 2 + 10) + b"\x07"  # an odd byte at the end
    got = list(wg.frames_of(io.BytesIO(raw)))
    assert [len(f) for f in got] == [wg.FRAME_BYTES] * 3
    assert got[2][:20] == b"\x01\x00" * 10 and set(got[2][20:]) == {0}


def wav(path: Path, rate=16000, channels=1, width=2, seconds=0.5) -> Path:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(b"\0" * int(rate * seconds) * channels * width)
    return path


def test_a_wav_is_read_only_as_16k_mono_16_bit():
    with tempfile.TemporaryDirectory() as d:
        good = wav(Path(d) / "good.wav")
        assert (
            len(list(wg.wav_frames(good))) == 7
        )  # 8000 samples: six whole, one padded
        with pytest.raises(ValueError, match="8000 Hz, 1 channel"):
            wg.wav_frames(wav(Path(d) / "phone.wav", rate=8000))
        with pytest.raises(ValueError, match="2 channel"):
            wg.wav_frames(wav(Path(d) / "stereo.wav", channels=2))


class Session:
    """An onnxruntime-like session: the shapes it's run with, and its answer."""

    def __init__(self, path: str, np, log: list):
        self.name, self.np, self.log = Path(path).name, np, log

    class _In:
        name = "input"

    def get_inputs(self):
        return [self._In()]

    def run(self, _, feeds):
        x = next(iter(feeds.values()))
        self.log.append((self.name, x.shape, x.dtype.name))
        np = self.np
        if self.name == "melspectrogram.onnx":
            frames = x.shape[1] // 160 - 3  # what the real one gives: 12880 → 78
            return [np.zeros((1, 1, frames, 32), np.float32)]
        if self.name == "embedding_model.onnx":
            return [np.ones((x.shape[0], 1, 1, 96), np.float32)]
        return [np.array([[0.75]], np.float32)]


def test_the_wake_word_reads_76_spectrogram_frames_and_16_embeddings():
    np = pytest.importorskip("numpy", reason="wake-gate's deps job installs numpy")
    log: list = []
    gate = wg.OnnxWake(
        Path("wake.onnx"), Path("features"), lambda p: Session(p, np, log), np
    )
    quiet = b"\0" * wg.FRAME_BYTES
    scores = [gate.score(quiet) for _ in range(30)]
    first = next(i for i, s in enumerate(scores) if s)
    assert scores[first] == pytest.approx(0.75)
    # 10 frames to fill 12,880 samples of audio, then 16 embeddings
    assert first == 10 + 15
    mels = [s for n, s, _ in log if n == "melspectrogram.onnx"]
    assert mels[0] == (1, wg.OnnxWake.AUDIO) and len(set(mels)) == 1
    assert {s for n, s, _ in log if n == "embedding_model.onnx"} == {(1, 76, 32, 1)}
    assert {s for n, s, _ in log if n == "wake.onnx"} == {(1, 16, 96)}
    assert {d for *_, d in log} == {"float32"}
    gate.reset()
    log.clear()
    assert gate.score(quiet) == 0.0 and log == [], "reset kept audio from before"


def run(*args: str, stdin: bytes = b"") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin,
                          capture_output=True)  # fmt: skip


def models(d: Path) -> list[str]:
    (d / "features").mkdir()
    for f in (
        "wake.onnx",
        "features/melspectrogram.onnx",
        "features/embedding_model.onnx",
    ):
        (d / f).write_bytes(b"not a model")
    (d / "whisper").mkdir()
    return ["--wake", str(d / "wake.onnx"), "--features", str(d / "features"),
            "--whisper", str(d / "whisper")]  # fmt: skip


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["speak"],
        ["listen"],
        ["listen", "--wake", "w.onnx", "--features", "f"],
        [
            "listen",
            "--wake",
            "w",
            "--features",
            "f",
            "--whisper",
            "m",
            "--threshold",
            "2",
        ],
        ["listen", "--wake", "w", "--features", "f", "--whisper", "m", "--stray", "x"],
        ["listen", "--wake", "w", "--wake", "v", "--features", "f", "--whisper", "m"],
    ],
)
def test_a_bad_command_line_is_refused_and_says_how(argv):
    got = run(*argv)
    assert got.returncode == 2 and b"wake_gate.py listen" in got.stderr


def test_a_missing_model_is_refused_by_name():
    with tempfile.TemporaryDirectory() as d:
        argv = models(Path(d))
        (Path(d) / "features" / "embedding_model.onnx").unlink()
        got = run("listen", *argv)
        assert got.returncode == 2
        assert b"embedding_model.onnx" in got.stderr and b"wake.onnx" not in got.stderr


def test_audio_of_another_kind_is_refused_before_a_model_loads():
    with tempfile.TemporaryDirectory() as d:
        argv = models(Path(d))
        got = run("listen", *argv, "--from", str(wav(Path(d) / "phone.wav", rate=8000)))
        assert got.returncode == 2 and b"8000 Hz" in got.stderr
        got = run("listen", *argv, "--from", str(Path(d) / "none.wav"))
        assert got.returncode == 2 and b"none.wav" in got.stderr


def test_a_model_that_wont_load_is_refused_and_says_so():
    pytest.importorskip("onnxruntime", reason="wake-gate's deps job installs it")
    with tempfile.TemporaryDirectory() as d:
        got = run("listen", *models(Path(d)), "--from", str(wav(Path(d) / "a.wav")))
        assert got.returncode == 2 and b"wouldn't load" in got.stderr


def test_listen_prints_the_question_alone_and_each_step_as_a_fact(capsys):
    wake = Wake({1})
    frames = [frame(1, False)] + [frame(i, True) for i in range(2, 6)]
    frames += [frame(i, False) for i in range(6, 20)]
    code = wg.listen(iter(frames), wake, wg.loud(500), Ears("when is  the boiler\ndue"),
                     wg.Config())  # fmt: skip
    out, err = capsys.readouterr()
    assert code == 0 and out == "when is the boiler due\n"
    steps = [json.loads(line) for line in err.splitlines()]
    assert [s["event"] for s in steps] == ["armed", "endpoint", "transcribed", "disarm"]
    assert "boiler" not in err
    code = wg.listen(iter([frame(i, True) for i in range(5)]), Wake(set()), wg.loud(500),
                     Ears(), wg.Config())  # fmt: skip
    out, err = capsys.readouterr()
    assert code == 42 and out == "" and err == ""
