<!-- willow-addon
section: Assistants
line: Suggestions from a model on this machine only, such as Ollama, llama.cpp's server, llamafile, KoboldCpp or Jan.
source: new
added: 2026-11-02
version: 0.1.0
writes: record
network: loopback
role: suggests
uses: openai-compatible
output: suggestions
-->
# local-model

A model on this machine suggests an answer from your folder, and the
suggestion waits for your seal. Nothing is sent anywhere else: a URL off
this machine is refused before a word goes out.

```
python adapters/stdlib/local-model/local_model.py servers

ollama         http://127.0.0.1:11434/v1  gemma3:4b, qwen3:8b
lm-studio      http://127.0.0.1:1234/v1  not running
llama.cpp      http://127.0.0.1:8080/v1  not running
…

python adapters/stdlib/local-model/local_model.py ask --box DIR "what goes in biscochitos"

Lard, not butter, and a spoonful of anise seed [1].
pass  proposal:cdd2…  waiting on your seal
```

**`servers`** asks each local runtime's model list (`GET /v1/models`) on the port it listens
on unless told otherwise, in this order: Ollama (11434), LM Studio (1234),
llama.cpp's server, llamafile and LocalAI (8080), vLLM (8000), KoboldCpp
(5001), Jan (1337), GPT4All (4891). `--url` names others instead, as many
as you like, each on this machine.

**`ask`** is [openai-compatible](../openai-compatible/)'s ask, held to this
machine: the kernel bites first, only the passages it served go to the
model, under the rule to answer only from them, and a reply is proposed
through `kernel.py propose` citing the passages its brackets name, to wait
for your seal. It asks the first server answering among those `--url`
names (as many as you like, tried in turn), or else in the order above;
without `--model`, the first model that server lists. A server whose list
doesn't answer is asked only when it is the one `--url` and you name the
model too.

`--system FILE` (a voice before the rule) and `--reasoning
none|low|medium|high` (how much a thinking model thinks first) go to
openai-compatible's ask as they are, and mean what its card says. The
second is `reasoning_effort` in the request, a setting a server may
ignore; on Ollama 0.40.14, `none` stopped qwen3:8b's thinking, where
"/no_think" in a system file and `think: false` didn't.

**Built in stdlib.** The idea was filed as needing an install: a local
model server. That server is a program you run, not a package this
imports, and it is reached over HTTP with Python's own library, as
openai-compatible reaches any endpoint, so the add-on needs nothing
installed beside it. Run Ollama, LM Studio, llama.cpp's `llama-server` or
any of the others yourself; the model's licence is the model's.

Exit codes, the kernel's: for `servers`, 0 one is running, 42 none; for
`ask`, openai-compatible's: 0 a suggestion waits on your seal, 42 nothing
served, no server running or a reply citing nothing; 2 refused (a bad
command line, a URL off this machine, a server offering no model).

**Uses:** the kernel's `bite` and `propose`, through
[openai-compatible](../openai-compatible/)'s ask.

**Never:** sends anything off this machine, seals, declines, or reads your
key.
