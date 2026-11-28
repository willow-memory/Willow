# Check a translation, and seal it from your own box

A model drafted a Spanish sentence. Nothing here is true or approved until a
person who reads Spanish says so. This folder lets that person check it and say
so, on their own computer, with a key that is theirs and never leaves it.

Why a person, and why a box of your own: willow never approves anything itself.
A suggestion waits, and only the person it speaks to can **seal** it, with a key
only they hold. A seal made with someone else's key would say that person
checked the Spanish, and they did not. So the seal is made here, on your machine.

## What you have

- `suggestions.jsonl`: the draft, one line. Its `data` field is the Spanish; its
  `claim` says plainly that a model wrote it and nobody has read it.
- `pile/hurricane-maria-landfall.txt`: the one English paragraph it translates
  (see Source, below).
- `kernel.py`: willow's kernel, Python 3.9 or newer, nothing to install.

## The draft

> La tormenta tocó tierra en Puerto Rico el miércoles 20 de septiembre, cerca del
> municipio de Yabucoa, a las 10:15 UTC (6:15 a. m., hora local), como huracán de
> categoría 4 en el extremo alto de la escala, con vientos de 155 mph (249 km/h).

Please read it for whatever rings false: the choice of "tocó tierra", "extremo
alto de la escala" for "high-end", the "a. m." and "mph" formatting, anything.

## Steps

Run these in this folder.

    python kernel.py init --box box --pile pile --key my.key
    python kernel.py bite --box box "Maria made landfall on Puerto Rico on Wednesday, September 20, near the Yabucoa municipality"
    python kernel.py propose --box box --file suggestions.jsonl
    python kernel.py seal --box box proposal:d53f9c12aee372ef1548a90a996c6d0999018466d8ed7c4c0f396e0b7e65ff75

- `bite` will print `"state": "echo"` and exit 42. That is expected here: the
  question repeats the English sentence, so the kernel says it was echoed, and it
  still serves the passage the draft cites. Nothing has gone wrong.
- `init` makes `my.key`. It is yours. Do not send it to anyone, and do not put it
  in a shared folder or a repository.
- `propose` should print `pass  proposal:d53f9c12...`: the same hash as above. If
  the hash is different, stop and tell whoever sent you this.
- **To change the Spanish**, edit the `data` line in `suggestions.jsonl` before
  `propose`. The hash will differ, and that is right; seal the one you made.
- **To say no**, in place of `seal`: `python kernel.py decline --box box proposal:<hash>`.
- **To check the record**: `python kernel.py verify --box box`.

## What to send back

`box/record.jsonl`, the `box/proposals/` folder and, if you sealed, `box/written/`
(your sealed Spanish, as `translations/maria-landfall.es.md`). Never `my.key`. The
record holds your seal or your decline, and anyone can check it with `verify`;
nobody can make one for you without your key.

## Source

The English paragraph is from English Wikipedia's "Hurricane Maria"
(https://en.wikipedia.org/wiki/Hurricane_Maria), one paragraph, taken as it
reads on the page. Its text is available under the Creative Commons
Attribution-ShareAlike 4.0 license; the page's history lists its authors.
