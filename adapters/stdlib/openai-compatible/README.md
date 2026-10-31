<!-- willow-addon
section: Assistants
line: Suggestions from any OpenAI-compatible endpoint you choose (LM Studio, vLLM, LocalAI, SGLang, Docker Model Runner, OpenRouter, Groq, Mistral), citing your passages.
source: new
added: 2026-10-31
writes: record
network: the endpoint you configure, to ask for suggestions
tags: no-install, online, records, assistant
-->
# openai-compatible

A model suggests an answer from your folder, through any endpoint that
speaks OpenAI's chat JSON, and the suggestion waits for your seal. Point it
at a model on this machine (llama.cpp's server, Ollama, LM Studio, vLLM)
and nothing leaves it.

```
python adapters/stdlib/openai-compatible/openai_compatible.py ask --box DIR \
    --url http://127.0.0.1:8080/v1 --model gemma-3-4b-it "what goes in biscochitos"

Lard, not butter, and a spoonful of anise seed [1].
pass  proposal:cdd2…  waiting on your seal
```

**The kernel asks first.** The question is a bite, on the record like any
other, and only the passages it served go to the model, numbered, under
one rule: answer only from them, and cite each one used as [1], [2]. When
the kernel serves nothing, the model is never asked. A model with no
passage under it has nothing to say, and is not given the chance.

**A reply is a suggestion, never an answer.** It goes to `kernel.py
propose`, citing the passages its brackets name, and waits there for your
seal. A reply whose brackets name no served passage is printed and
proposed to no one. Asked at temperature 0 with a fixed seed, so a server
that honours them says the same thing twice. It waits up to fifteen
minutes for a reply, since a model on a laptop's CPU can be slow.

`--system FILE` puts a voice before the rule (a persona, a tone), never in
place of it. An API key, when the endpoint wants one, comes from
`OPENAI_API_KEY`; on your own machine it needs none.

Exit codes, the kernel's: 0 a suggestion is waiting on your seal; 42
nothing served, the endpoint unreachable, or a reply citing nothing; 2
refused (a bad command line, a `--system` file that can't be read).

**Uses:** the kernel's `bite` and `propose`, as the kernel's own commands.

**Never:** seals, declines or reads your key; sends the model a passage
the bite didn't serve; proposes a reply that cites nothing; asks a model
when your folder holds nothing.
