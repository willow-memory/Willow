<!-- willow-addon
section: Assistants
line: Suggestions through the llm command, so any model its plugins reach (local or hosted) can hand one in, with llm's own log naming the model.
source: new
added: 2026-11-05
version: 0.1.0
needs: llm and the plugin for your model; Apache-2.0
floor: llm 0.28; the rule names 0.1, its first release (2023), but llm up to 0.27.1 has a known advisory (PYSEC-2026-400, code run by --functions, which willow never passes), so 0.28 is the first safe one
writes: record
network: the model its plugin reaches, to ask for suggestions
hands: your question and the passages served, to the llm command and the model it runs
role: suggests
uses: openai-compatible
-->
# llm-cli

A model reached through Simon Willison's `llm` command suggests an answer
from your folder, and the suggestion waits for your seal. Any plugin llm
loads (OpenAI, local models, …) can hand one in; llm's own log names which.

```
pip install -r adapters/deps/llm-cli/requirements.txt
python adapters/deps/llm-cli/llm_cli.py ask --box DIR [--model NAME] \
    "what goes in biscochitos"

Lard, not butter, and a spoonful of anise seed [1].
pass  proposal:cdd2…  waiting on your seal
```

**The kernel asks first.** The question is a bite, on the record like any
other, and only the passages it served go to `llm`, numbered, under one
rule: answer only from them, and cite each one used as [1], [2]. When the
kernel serves nothing, llm is never run. A model with no passage under it
has nothing to say, and is not given the chance.

**A reply is a suggestion, never an answer.** It goes to `kernel.py
propose`, citing the passages its brackets name, and waits there for your
seal. A reply whose brackets name no served passage is printed and
proposed to no one. `--model` is `llm -m`; without it, llm's default.
`--system FILE` puts a voice before the rule, never in place of it.

Keys for the model stay with llm (and its plugins); this add-on never
reads your willow key.

Exit codes, the kernel's: 0 a suggestion is waiting on your seal; 42
nothing served, llm unreachable, or a reply citing nothing; 2 refused.

**Uses:** the kernel's `bite` and `propose`;
[openai-compatible](../../stdlib/openai-compatible/)'s passage framing and
cite parse.

**Never:** seals, declines or reads your willow key; sends the model a
passage the bite didn't serve; proposes a reply that cites nothing; asks a
model when your folder holds nothing.
