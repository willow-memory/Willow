<!-- willow-addon
section: Ways to use it
line: Ask out loud after a wake word you chose: audio before it is never transcribed, kept or sent.
source: new
added: 2026-11-08
version: 0.1.0
needs: onnxruntime, numpy and faster-whisper; MIT, BSD-3-Clause, MIT. A wake word model you give it, trained the openWakeWord way; openWakeWord's own are CC BY-NC-SA 4.0
floor: faster-whisper 1.2.1, numpy 2.1.0, onnxruntime 1.20.0; the 2020 rule names numpy 1.19.4 and onnxruntime 1.6.0, which have no wheel for Python 3.13, and faster-whisper's first, 0.2.0; every faster-whisper before 1.2.1 pins av below 13, the first av with one, or imports requests without declaring it, which today's huggingface-hub no longer brings
writes: nothing
network: none
role: ways
from: code, https://github.com/willow-memory/willow-mcp, Apache-2.0; code, https://github.com/dscripka/openWakeWord, Apache-2.0
-->
# wake-gate

Your question, spoken after a wake word you chose and turned to text on this
machine; nothing you say before the wake word is transcribed, kept or sent.

    pip install -r adapters/deps/wake-gate/requirements.txt
    arecord -q -f S16_LE -r 16000 -c 1 -t raw | python adapters/deps/wake-gate/wake_gate.py \
        listen --wake <your-wake-word>.onnx --features <FEATURES> --whisper <WHISPER> \
        | while read -r q; do python kernel.py bite --box <BOX> "$q"; done

**The wake word is the consent boundary.** While it listens, each 80 ms of
audio goes to the wake word model and nowhere else, and is then dropped.
Only when the wake word scores past `--threshold` (0.5) does it keep what
follows, and only that goes to the transcriber, once, at the end of the
sentence. Then it forgets it and listens again.

    {"tick": 88, "event": "armed", "score": 0.957}
    {"tick": 124, "event": "endpoint", "frames": 36, "cut": false}
    {"tick": 124, "event": "transcribed", "chars": 31}
    When is the boiler service too?
    {"tick": 124, "event": "disarm"}

That is a recording made with a speech synthesizer: a sentence, a second's
pause, "Hey Jarvis", then the question. The sentence before the wake word
was never transcribed. Each step of the machine is a line on stderr, saying
the fact (armed, its score; how many frames; how many characters) and never
the audio or the words; what it heard goes to stdout, one question a line.
Whisper heard "due" as "too", which is why what it heard is printed for you
to ask, not asked for you.

**Its models are files you give it.** It fetches nothing:

- `--wake`: a wake word model trained the openWakeWord way, as an `.onnx`
  file. openWakeWord's own pre-trained ones (hey jarvis, alexa) are CC
  BY-NC-SA 4.0, non-commercial; train your own with openWakeWord's training
  notebook, as willow-mcp's hey willow is.
- `--features`: a folder holding openWakeWord's two feature models,
  `melspectrogram.onnx` and `embedding_model.onnx`, from its releases.
  The embedding is Google's speech embedding, Apache-2.0.
- `--whisper`: a folder holding a faster-whisper model (CTranslate2), such as
  Systran's faster-whisper-base.en, saved with `hf download`; MIT.

**Its audio** is 16 kHz, 16-bit, mono: raw samples on stdin (`--from -`, the
default), as `arecord` gives them, or a `.wav` file of that kind. A file of
another kind is refused, never converted.

**When a sentence ends.** After 0.8 s under `--speech-level` (500: the
loudness, as RMS of the 16-bit samples, that counts as speech). A wake word
with no speech within 2 s is a false wake, dropped untranscribed; a sentence
is cut at 15 s. The audio ending mid-sentence ends the sentence.

**Taken from.** The machine is willow-mcp's voice ingress membrane, kept to
its listening and capturing states. The wake word pipeline is
openWakeWord's: a melspectrogram of the last audio, Google's speech
embedding of its last 76 frames, the wake word model over the last 16
embeddings. It runs through onnxruntime directly, since the openwakeword
package needs tflite-runtime on Linux, which has no wheel for Python 3.13.
Both are Apache-2.0; their licences and what changed are in NOTICE beside
this card.

Exit codes, the kernel's: 0 a question heard; 42 none; 2 refused (a model
missing, audio of another kind, an install missing, which it names).

**Never:** writes anything, goes online, keeps audio, or asks for you: what
it heard is yours to read before it reaches the kernel.
