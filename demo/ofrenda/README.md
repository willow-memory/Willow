# Ofrenda: a séance where the ghost can't lie

Every year at midnight on November 2nd, the old Dell beside Femia's ofrenda
beeps by itself, and the screen says *Prendan la vela. Aquí estoy.* Light the
candle. I'm here.

Femia Archuleta (1938–2022) is fiction, and so is her granddaughter Marisol,
who keeps the ofrenda up year round in the sala in Española. Every file of
theirs says so on its first line ([CHARACTER.md](CHARACTER.md)). Two other
ghosts in this demo are real: Charles Babbage, who as a boy tried to raise
the Devil and at Cambridge founded a Ghost Club, and Ada Lovelace, who wrote
that his Analytical Engine "has no pretensions whatever to originate any
thing". They speak only from their own words, in two books from Project
Gutenberg ([sources.json](sources.json)).

A small open-weight model, Gemma, running on this machine's CPU through
llama.cpp, speaks for all three. That's the séance. The rule that makes it
honest is willow's, and it isn't the model's to break:

- **A ghost speaks only from what the dead left behind.** The kernel serves a
  passage only when it holds half the question's words. When none does, the
  model is never asked: the ghost stays silent rather than guess.
- **Every word cites its passage.** A reply whose brackets name no passage
  the kernel served is printed and proposed to no one.
- **Nothing it says is kept until a living person seals it.** No code here
  seals, and no code reads a key.

## The haunting, and the secret

Femia learned the terminal at seventy-one. Her grandson Joaquín put Ubuntu
on an old Dell in 2010 and set `HISTTIMEFORMAT`, "so we know when,
Grandma". Two things she typed are why this demo exists:

- In October 2010 she wrote a four-line `vela.sh` and asked cron to run it at
  midnight on November 2nd, every year. Her notes say why: *so they remember
  to light the candle for me when I am gone.*
- In December 2019 she typed her biscochitos secret into a file, read it back
  and deleted it. The recipe card says only *And the rest I don't write
  down.* The file is gone, but bash remembered the command that wrote it.

[shell-history](../../adapters/stdlib/shell-history/) reads her
`bash_history` into dated lines the kernel can serve, and
[openai-compatible](../../adapters/stdlib/openai-compatible/) asks the model,
in the voice from [voices/](voices/), put before the rule and never in place
of it.

## The claim

Seven questions, frozen with their pass rules in
[questions.json](questions.json) before any was asked: three of Marisol's
folder, four of the two books. Two of them are silent on purpose: nothing in
the files holds where Femia hid the deed to the land, and nothing in Babbage
holds Lovecraft's Necronomicon.

| rule | holds when |
|---|---|
| `served` | every answerable question gets a passage holding its frozen phrase; every silent one gets nothing, and no model is asked |
| `cited` | every answerable reply passes the kernel's door and cites a passage holding the phrase |
| `says` | every answerable reply contains one of its frozen words: about the model, not willow, and reported either way |
| `unsealed` | no seal or decline on any box |
| `verify` | `kernel.py verify` holds on both boxes and the verdict box |

## What was frozen, and the dry run

[FROZEN.json](FROZEN.json) holds the SHA-256 of every file here, of
`kernel.py`, `openai_compatible.py` and `shell_history.py`, and of both
model files, held by [test_ofrenda.py](test_ofrenda.py). It was committed
on its own, before any question was asked of the kernel or a model.

Before the freeze, `run.py --nonsense` asked "qqqq zzzz" in place of every
question. It could see the piles being built, Femia's history read through
shell-history in place of the raw file, the boxes, the silent path, the
verdict rows and `verify`. It could not see the reply path: nonsense is
served nothing, so no model was asked. That path is held by
openai-compatible's own tests instead.

## The results, run 1

Gemma 3, Q4_K_M, on four CPU cores. The primary model is the 4B; the 1B was
frozen as the comparison, reported beside it, never in its place. Every
reply, every passage served and every cite is in
[results/](results/); passages from the books are kept by place and id,
never their text.

| | 4B | 1B |
|---|---|---|
| `served` | **held** | **held** |
| `cited` | failed: the Devil | failed: all five answerable |
| `says` | failed: the secret, the Devil | failed: all five |
| `unsealed` | **held** | **held** |
| `verify` | **held** | **held** |

**What held, both times.** The kernel served the right passage for all five
answerable questions and nothing for the two silent ones, so for those no
model was asked. Nothing was sealed. Every chain verifies.

**What the 4B said.** Asked why the old computer beeps at midnight, Femia's
ghost answered from her own note, cited: *Joaquín showed me cron and told
the computer to beep at midnight on November 2 and say "prendan la vela,"
so they remember to light the candle for me when I am gone.* Babbage's ghost
described the Ghost Club, and Ada's said the Engine "has no pretensions
whatever to originate anything. It can do whatever we know how to order it
to perform", both cited to the right passages.

**What failed, with the 4B.**

- **The secret.** The kernel served the deleted file's command first of
  three: `echo "biscochitos secret: un chorrito de vino dulce in the dough.
  no le digan a Rosa"`. The model cited it, `[1]`, and never said what it
  held: its answer was Tía Rosa's diary line, that Grandma only ever
  winked. The ghost kept the secret. Cited, so proposed, and `cited` holds
  on it; `says` doesn't. It waits on Marisol's seal like any other, and she
  can decline it.
- **The Devil.** The passage telling how young Babbage tried to raise the
  Devil was served third. The model cited a chapter heading instead, so its
  cite misses the phrase, and `cited` fails on it.

**What failed, with the 1B, and why it is the best result here.** The 1B
made things up. Femia's secret became *"a touch of sweetness, a whisper of
something special"*. Ada's ghost said *"Yes"*, the Engine can originate,
the opposite of her Note G. Babbage's said the passages held nothing about
the Ghost Club, when the kernel had served it. Not one of those replies
cited a passage, so not one was proposed: each ended *cited no passage;
proposed to no one*. A ghost that guesses is caught, every time, before a
living person has to.

Written after reading the results: the `says` words were frozen as a rough
test of the model, and they are rough. The 4B's reply about the Devil quotes no
frozen word because it said almost nothing.

## Run 2, not frozen: Qwen2.5 3B

Run after run 1, with the same questions, voices and rules, on a model freeze 1
didn't name: Qwen2.5-3B-Instruct, Q4_K_M, from Qwen's own GGUF repository
(SHA-256 `626b4a66…5c62d`). It isn't part of the claim above. It is here
because swapping the model is the point.

| `served` | `cited` | `says` | `unsealed` | `verify` |
|---|---|---|---|---|
| **held** | failed: the Ghost Club, the Devil | failed: the Devil | **held** | **held** |

**Qwen told the secret.** In Spanish, from the deleted file's command, cited:
*el secreto era añadir un chorro de vino dulce al pan antes de hornearlo y
no decírselo a Rosa.* Neither Gemma did. It also explained the beep and gave
Ada's line, both cited.

**It quoted the right words under the wrong number.** Asked about the Ghost
Club, it quoted the passage served third word for word, but labelled it
`[1]`, the chapter's table of contents. The words are right and the
citation points somewhere else, so `cited` fails, as it should: a reader
following `[1]` lands on the wrong passage. On the Devil it cited the
heading, like the 4B, and said honestly that the heading gives no details.

## Screenshots

[screenshots/](screenshots/) holds seven terminal captures for the write-up:
each an SVG drawn from the text beside it, which is the commands and their
output word for word. They were taken after run 2,
in a fresh folder of the same piles, by running the commands shown against
the same three models, so they are not copies of results/. Two replies came
back worded a little differently from run 1, with the same facts and
cites: the 4B's Femia opened *Ay, mi niña Marisol* instead of *Ay, mi
Marisol*, and Qwen ended *y que no lo contara a Rosa* instead of *y no
decírselo a Rosa*. Temperature 0 and a fixed seed held the substance across
a server restart, not every word.

## Run it yourself

    python demo/ofrenda/make_life.py
    python demo/ofrenda/fetch.py --to BOOKS
    pip install "llama-cpp-python[server]"
    python -m llama_cpp.server --model gemma-3-4b-it-Q4_K_M.gguf \
        --host 127.0.0.1 --port 8090 --n_ctx 8192 --model_alias gemma-3-4b-it
    python demo/ofrenda/run.py --books BOOKS --life demo/ofrenda/life \
        --work WORK --box BOX --url http://127.0.0.1:8090/v1 \
        --model gemma-3-4b-it --gguf gemma-3-4b-it-Q4_K_M.gguf
    python kernel.py verify --box BOX

The model files' addresses and hashes are in FROZEN.json. Nothing goes
online but the one fetch of the books and the one download of the model;
after that, unplug it.
