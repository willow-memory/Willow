"""annex_os.py: ANNEX-OS, a fictional terminal over the Annex's eight boxes.

    python demo/annex/annex_os.py build --scene DIR --to FILE.html

DIR is what scene.py wrote. FILE.html is one self-contained page, no network
and no install: open it in a browser. It reads nothing but scene.json (and
what that holds: each box's sealed answers, what it sent and received, how its
chain stood, what the witness found, and the one file an assistant was served).
It never reads a box, a key or a pile, so nothing the page shows is anything a
box did not already write to scene.json, and the rumour is in none of it.

The page is a green-screen terminal, and none of it is real:

- **Badge.** Choose who you are. A door opens only for its own badge; any other
  is "NOTHING ON RECORD FOR THIS BADGE" (the kernel's exit 42). Oversight's
  badge opens no door: it shows what each chain's witness found.
- **Doors.** Each compartment shows only its own sealed answers and its own
  chain.
- **Manifest printer.** What may leave: the sealed answers, each marked SEALED.
  Ask it to print the unsealed summary and it refuses.
- **Witness run.** The dead-man's page: when a chain stops matching what
  others kept, the screen goes dark and names the box.
- **Briefing.** An assistant that reads only the served file. A toy matcher
  (it keeps to the words of a question, nothing like the kernel's rank): what
  the file doesn't hold, it says it wasn't given.
- **The clocks.** The header shows two clocks that disagree by an hour.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ANNEX-OS</title>
<style>
:root{--bg:#050a06;--fg:#38f58a;--dim:#1f9a57;--warn:#ffb74a;--bad:#ff5a4d;--panel:#07140b;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 ui-monospace,Menlo,Consolas,monospace;
  min-height:100vh;padding:0 16px 40px;
  background-image:repeating-linear-gradient(0deg,rgba(0,0,0,.18) 0 1px,transparent 1px 3px);}
header{display:flex;flex-wrap:wrap;gap:8px 24px;align-items:baseline;border-bottom:1px solid var(--dim);padding:12px 0}
h1{font-size:16px;margin:0;letter-spacing:.15em}
.clock b{color:var(--warn)} .clock.flick b{animation:fl 3s infinite}
@keyframes fl{0%,92%,100%{opacity:1}94%{opacity:.2}97%{opacity:.8}}
.note{color:var(--dim)}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
button,select,input{background:var(--panel);color:var(--fg);border:1px solid var(--dim);padding:6px 10px;font:inherit;border-radius:0}
button{cursor:pointer} button:hover,button.on{background:var(--fg);color:var(--bg)}
button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--warn)}
section{border:1px solid var(--dim);padding:12px;margin:12px 0;background:var(--panel)}
h2{font-size:14px;margin:0 0 8px;letter-spacing:.1em;color:var(--warn)}
.doors{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
.door{border:1px solid var(--dim);padding:8px;cursor:pointer;background:transparent;text-align:left;color:var(--fg)}
.door.open{border-color:var(--fg);box-shadow:0 0 8px var(--fg) inset}
.door.shut{color:var(--dim)} .door small{display:block;color:var(--dim)}
.sealed{color:var(--fg)} .unsealed{color:var(--bad)} .bad{color:var(--bad)} .warn{color:var(--warn)}
pre{white-space:pre-wrap;margin:6px 0}
.row{display:flex;gap:12px;flex-wrap:wrap;margin:2px 0}
#dark{position:fixed;inset:0;background:#000;color:var(--bad);display:none;padding:10vh 16px;z-index:9;
  font-size:16px} #dark.on{display:block} #dark pre{max-width:70ch;margin:0 auto}
@media (prefers-reduced-motion:reduce){.clock.flick b{animation:none}}
</style></head><body>
<header>
  <h1>ANNEX-OS</h1>
  <span class="note">COMPARTMENTED RECORDS TERMINAL &middot; ONLY WHAT IS ON RECORD</span>
  <span class="clock flick">SYS <b id="c1"></b> &middot; GATE <b id="c2"></b> <span class="note">(unexplained)</span></span>
</header>
<nav>
  <label>BADGE <select id="badge"></select></label>
  <button id="bdoors" class="on">DOORS</button>
  <button id="bprint">MANIFEST PRINTER</button>
  <button id="bwit">WITNESS RUN</button>
  <button id="bbrief">BRIEFING</button>
</nav>
<main id="main"></main>
<div id="dark" role="alert"><pre id="darktext"></pre><p style="text-align:center"><button id="undark">ACKNOWLEDGE</button></p></div>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const B = D.boxes, NAMES = Object.keys(B);
const LABEL = {intake:'Intake (gate)',vask:'Vask / Helio',karst:'Karst Dynamics',lumen:'Lumen Fieldworks',
  program:'Program office',counter:'Counterintel',oversight:'Oversight',prior:'Prior (Vask)'};
const $ = id => document.getElementById(id);
const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.textContent = h; return e; };
let badge = 'vask', view = 'doors', openDoor = null;

$('c1').textContent = D.clocks.program; $('c2').textContent = D.clocks.intake;
for (const n of NAMES) { const o = el('option', '', LABEL[n]); o.value = n; $('badge').appendChild(o); }
$('badge').value = badge;

function chainLine(n) {
  const w = D.found.real[n], rew = n === 'counter' && D.found.rewritten.includes('rewritten');
  return `chain: ${B[n].rows} rows, own verify HOLDS` + (w ? `, witness ${w.toUpperCase()}` : ', no witness holds a package from it');
}
function none(m) { const p = el('pre', 'warn', m || `NOTHING ON RECORD FOR THIS BADGE (exit 42)`); return p; }

function doors(m) {
  m.appendChild(el('h2', '', 'COMPARTMENTS'));
  const g = el('div', 'doors');
  for (const n of NAMES) {
    const mine = n === badge;
    const d = el('button', 'door ' + (mine ? 'open' : 'shut'));
    d.append(el('span', '', (mine ? '[ OPEN ] ' : '[ LOCKED ] ') + LABEL[n]));
    d.append(el('small', '', mine ? 'your badge' : badge === 'oversight' ? 'witness only' : 'not on record for you'));
    d.onclick = () => { openDoor = n; render(); };
    g.appendChild(d);
  }
  m.appendChild(g);
  if (!openDoor) return;
  const s = el('section'); s.appendChild(el('h2', '', 'DOOR: ' + LABEL[openDoor].toUpperCase()));
  if (openDoor === badge) {
    const b = B[openDoor];
    s.appendChild(el('pre', 'note', chainLine(openDoor)));
    s.appendChild(el('h2', '', 'SEALED ANSWERS (' + b.said.length + ')'));
    if (!b.said.length) s.appendChild(el('pre', 'note', 'none sealed. a box can hold files and still have nothing it may hand out.'));
    for (const a of b.said) { const p = el('pre'); p.append(el('span', 'sealed', '[SEALED] '), a.data + '\n         cites ' + a.cite + ' \u2014 ' + a.claim); s.appendChild(p); }
    s.appendChild(el('h2', '', 'SENT'));
    for (const x of b.sent) s.appendChild(el('pre', '', `row ${x.n}  ${x.package}\u2026 to ${x.to}  ${x.ts}`));
    s.appendChild(el('h2', '', 'RECEIVED'));
    if (!b.received.length) s.appendChild(el('pre', 'note', 'nothing received.'));
    for (const x of b.received) s.appendChild(el('pre', x.verdict === 'good' ? '' : 'bad', `row ${x.n}  ${x.package}\u2026 from ${x.from}  ${x.verdict.toUpperCase()}`));
  } else if (badge === 'oversight') {
    s.appendChild(el('pre', 'note', 'Oversight reads nothing in this box. It holds what the box sent up, and checks it.'));
    s.appendChild(el('pre', D.found.real[openDoor] === 'holds' && !(openDoor === 'counter') ? '' : 'warn',
      `witness: ${(D.found.real[openDoor] || 'no package kept').toUpperCase()}` +
      (openDoor === 'counter' ? `\nthe copy that was rewritten: ${D.found.rewritten.join(', ').toUpperCase()}` : '')));
  } else s.appendChild(none());
  m.appendChild(s);
}

function printer(m) {
  m.appendChild(el('h2', '', 'MANIFEST PRINTER \u2014 ' + LABEL[badge]));
  const b = B[badge];
  m.appendChild(el('pre', 'note', 'Only what this box sealed may leave. Everything else is not on record.'));
  if (!b.said.length) m.appendChild(none('NOTHING SEALED. NOTHING MAY LEAVE.'));
  for (const a of b.said) { const p = el('pre'); p.append(el('span', 'sealed', '[SEALED] '), a.data); m.appendChild(p); }
  const f = el('section'); f.appendChild(el('h2', '', 'ADD A LINE'));
  const btn = el('button', '', 'ADD THE UNSEALED INTELLIGENCE SUMMARY'); const out = el('pre', 'note', '');
  btn.onclick = () => { out.className = 'bad'; out.textContent = badge === 'counter'
    ? 'REFUSED. NOT SEALED. ON RECORD IN THIS BOX, BUT NO SEAL OF YOURS IS ON IT. IT DOES NOT LEAVE.'
    : 'REFUSED. NOTHING ON RECORD FOR THIS BADGE (exit 42). YOU CANNOT PRINT WHAT YOUR BOX DOES NOT HOLD.'; };
  f.append(btn, out); m.appendChild(f);
}

function witnessRun(m) {
  m.appendChild(el('h2', '', 'WITNESS RUN \u2014 Oversight holds each chain to the packages it kept'));
  for (const n of NAMES) {
    const w = D.found.real[n];
    if (!w) { m.appendChild(el('pre', 'note', `${LABEL[n].padEnd(18)} no package kept. no witness. rows after the last one kept have none either.`)); continue; }
    m.appendChild(el('pre', w === 'holds' ? '' : 'bad', `${LABEL[n].padEnd(18)} own verify HOLDS \u00b7 witness ${w.toUpperCase()}`));
  }
  const b = el('button', '', 'RUN IT AGAINST THE COPY OF COUNTERINTEL');
  b.onclick = () => { $('darktext').textContent =
    `CHAIN: COUNTER\nITS OWN VERIFY: HOLDS\nWITNESS (oversight's package): ${D.found.rewritten.join(', ').toUpperCase()}\n\n` +
    `A seal on this chain was dated before the day began, and every row after it\nwas rewritten to match.\nIt cannot be seen from inside.\n\n` +
    `OVERSIGHT'S REPORT IS DUE AT CLOSE OF DAY.\nWHAT IT SAYS IS OUTSIDE EVERY CHAIN.`;
    $('dark').classList.add('on'); };
  m.append(el('p'), b);
}

const STOP = new Set('what when who where which does did the and for with from that this about have has not was were its are you your they them'.split(' '));
function words(t) { return t.toLowerCase().match(/[a-z0-9']{3,}/g)?.filter(w => !STOP.has(w)) || []; }
function briefing(m) {
  m.appendChild(el('h2', '', 'BRIEFING \u2014 an assistant that reads one file'));
  m.appendChild(el('pre', 'note', 'It is given only what Counterintel sealed for it. Holding the file is the permission; it never sees the box.'));
  m.appendChild(el('pre', '', D.served));
  const f = el('div', 'row'); const i = el('input'); i.placeholder = 'ask the assistant\u2026'; i.size = 44; i.setAttribute('aria-label', 'question');
  const go = el('button', '', 'ASK'); const out = el('pre');
  const ask = () => {
    const q = words(i.value), pass = new Set(words(D.served));
    const hit = q.filter(w => pass.has(w));
    out.className = hit.length * 2 >= q.length && hit.length ? 'sealed' : 'warn';
    out.textContent = hit.length * 2 >= q.length && hit.length
      ? 'FROM WHAT I WAS GIVEN: ' + D.served.split('\n').find(l => /last review|Marked/.test(l)).trim()
      : 'NOT IN WHAT I WAS GIVEN. I CANNOT TELL YOU WHETHER IT EXISTS.';
  };
  go.onclick = ask; i.onkeydown = e => { if (e.key === 'Enter') ask(); };
  f.append(i, go); m.append(f, out, el('pre', 'note', '(a toy matcher for the demo: the kernel\u2019s own rank is stricter)'));
}

function render() {
  const m = $('main'); m.textContent = '';
  for (const [id, v] of [['bdoors', 'doors'], ['bprint', 'print'], ['bwit', 'wit'], ['bbrief', 'brief']]) $(id).classList.toggle('on', view === v);
  ({ doors, print: printer, wit: witnessRun, brief: briefing })[view](m);
}
$('badge').onchange = e => { badge = e.target.value; openDoor = null; render(); };
for (const [id, v] of [['bdoors', 'doors'], ['bprint', 'print'], ['bwit', 'wit'], ['bbrief', 'brief']]) $(id).onclick = () => { view = v; render(); };
$('undark').onclick = () => $('dark').classList.remove('on');
render();
</script></body></html>
"""


def clocks(doc: dict) -> dict:
    """The two times integration day began, each read from the box that sealed it."""
    out = {}
    for who in ("program", "intake"):
        seen = re.findall(
            r"\d\d:\d\d", " ".join(a["data"] for a in doc["boxes"][who]["said"])
        )
        out[who] = seen[0] if seen else "??:??"
    return out


def build(scene: Path, to: Path) -> None:
    doc = json.loads((scene / "scene.json").read_text(encoding="utf-8"))
    keep = {
        "boxes": {
            b: {k: v[k] for k in ("rows", "said", "sent", "received")}
            for b, v in doc["boxes"].items()
        },
        "found": doc["found"],
        "served": doc["served"],
        "clocks": clocks(doc),
    }
    data = json.dumps(keep, ensure_ascii=False).replace("</", "<\\/")
    to.write_text(PAGE.replace("__DATA__", data), encoding="utf-8")
    print(f"wrote {to} ({to.stat().st_size} bytes), {len(keep['boxes'])} doors")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 5 or a[0] != "build" or a[1] != "--scene" or a[3] != "--to":
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        raise SystemExit(2)
    build(Path(a[2]), Path(a[4]))
