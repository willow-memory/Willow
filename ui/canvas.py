"""canvas.py: willow's own UI. Put your willow together on a page, on this
machine only. Python 3.9+, stdlib only.

    python ui/canvas.py [--to DIR] [--folder PATH]... [--port N] [--no-open]

It opens a page that goes the way a person does: choose your folders; see
what the kernel alone makes of them, as counts (never a passage, never a
file's name); start from an example or pick add-ons, each with what it needs
(a card's `uses`) coming with it; save a pick as a batch to bring back;
then look it over and seal it.

    Look it over  the pick goes to the kernel as a proposal: the steps and
                  the options each runs with, every folder, where it reaches
    Seal it       your seal over those exact bytes (the kernel's own `seal`)
    Put it        only once sealed: the add-ons not yet in your stack are
    together      copied in from this willow, each one a row on its record
    Start it      your record over your folders, each add-on's own tests, the
                  flow you sealed run once, and browse opened on your record

Your stack is kept in --to, outside this repository, ~/willow-stack unless
you say: the kernel, its law and vectors, and the add-ons you put in, each
file hashed (`assemble.py`), with a record and a key of its own beside it.
The first run makes it, with stack (its examples, and the runner) and
browse (the page Start it opens).

It binds 127.0.0.1 only and answers only under a fresh random path printed
at start, with the Host it was given, so another web page can't drive it.
What it can't stop: a program running as you can read that link, or run
`kernel.py seal` itself. The seal here is the kernel's key file, as willow's
is today; `seal_step` is the one place a better one (a passkey, a key on
your phone that this machine can only verify) would go.

Exit codes, the kernel's: 0 stopped; 2 refused.
"""

from __future__ import annotations

import contextlib
import os
import io
import json
import re
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # never a __pycache__ in this repo, or in a stack
sys.path.insert(0, str(HERE))
import assemble  # noqa: E402

KIND = "canvas"
#: kinds the kernel reads as they are: one it couldn't was too big, or saved in
#: another encoding, and a reader is no answer to either
TEXT_KINDS = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".tsv",
    ".json",
    ".html",
    ".htm",
    ".log",
    ".rst",
    ".org",
    ".yaml",
    ".yml",
    ".xml",
}
WORD = re.compile(r"[a-z0-9][a-z0-9-]*")


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def quiet(fn, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = fn(*args)
    return code, out.getvalue().strip()


class Canvas:
    def __init__(self, to: Path, willow: Path, box: Path, folders: list[str]):
        # every path whole: steps run from other folders
        self.to, self.willow, self.box = to.resolve(), willow.resolve(), box.resolve()
        self.stack = self.to / "stack"
        self.kernel = assemble.load_kernel(self.stack)
        self.folders = folders
        self.similar = self._load_similar()
        self.job = None
        self.browsers = []
        self._search = None
        self.lock = threading.Lock()
        self._pieces = None

    def _load_similar(self):
        """willow's similar add-on, from the willow this stack came from: its
        worked-out tags and nearest entries are the ones ADDONS.md shows."""
        import importlib.util

        path = self.willow / "adapters" / "stdlib" / "similar" / "similar.py"
        if not path.is_file():
            return None
        spec = importlib.util.spec_from_file_location("willow_similar", path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:  # an older willow: no tags, no search, said in the page
            return None
        return mod if hasattr(mod, "worked_out") else None

    def search(self, words: str, top: int = 12) -> dict:
        """Cards for what a person says they want, in their own words: BM25 over
        each whole card, the ranking similar's tags are made with, its name,
        line and topic tags weighed as its title."""
        if self.similar is None:
            return {
                "state": "unreachable",
                "why": "this willow's similar add-on can't search yet",
                "found": [],
            }
        words = words.strip()
        if not words:
            return {"state": "empty", "found": []}
        sim = self.similar
        if self._search is None:
            every = sim.entries()
            tags = sim.worked_out(every)
            docs = []
            for a in every:
                # name, line and tags as the passage's heading, which pile-rank weighs
                # double: what a card says it is outranks what its body mentions
                head = f"# {a['name'].replace('-', ' ')} {a['line']} {' '.join(tags[a['name']]['tags'][2:])}"
                text = head + "\n" + sim.card_text(a)
                docs.append(
                    {
                        "path": a["name"],
                        "line": 1,
                        "text": text,
                        "id": sim.kernel.h256(text),
                    }
                )
            self._search = sim.pile_rank.Ranker(docs)
        k = sim.kernel
        said = [w.lower() for w in k.words(words)]
        asked = list(said)
        asked += [a + b for a, b in zip(said, said[1:])]  # "back up" is also "backup"
        alias = self.search_words()
        means = {}  # a card's word, and the word you said it stands for
        for w in list(asked):
            for m in alias.get(w, []):
                means.setdefault(m, w)
        ranked = self._search.rank(
            " ".join(dict.fromkeys(asked + list(means))), top * 2
        )

        def named(name: str, words) -> str | None:
            plain = sim.HOW | k.FUNCTION  # "read" in "read my email" names nothing
            return next((p for p in [name, *name.split("-")]
                         if p in words and len(p) >= 3 and p not in plain), None)  # fmt: skip

        # a card you named comes first ("vim", "mail" in "my email"), then one a
        # word of yours usually means ("remind": coming-up), then the ranking
        def tier(r):
            n = r[0]["path"]
            return 0 if named(n, asked) else 1 if named(n, means) else 2

        ranked.sort(key=tier)
        found = []
        for c, _, ph in ranked[:top]:
            n = c["path"]
            if named(n, asked):
                why = "you named it"
            elif part := named(n, means):
                why = f"what “{means[part]}” usually means here"
            else:
                why = "uses " + ", ".join(ph) if ph else "close to what you said"
            found.append({"name": n, "why": why})
        return {"state": "populated" if found else "empty", "found": found}

    def search_words(self) -> dict:
        """search-words.txt beside this file: how people ask, and the words
        the cards use. The kernel's own words-list format and parser."""
        f = HERE / "search-words.txt"
        if not f.is_file():
            return {}
        alias, why = self.similar.kernel.parse_words(f.read_text(encoding="utf-8"))
        return {} if why else alias

    # ── what there is to arrange ────────────────────────────────────────────
    def pieces(self) -> dict:
        if self._pieces is not None:
            return self._pieces
        have = assemble.manifest(self.stack)["addons"]
        out = {}
        for kind in ("stdlib", "deps"):
            for d in sorted((self.willow / "adapters" / kind).iterdir()):
                c = assemble.card(d)
                if not d.is_dir() or not c:
                    continue
                hard, soft = assemble.deps(d)
                out[d.name] = {
                    "name": d.name, "kind": kind, "state": "built",
                    "section": c.get("section", ""), "line": c.get("line", ""),
                    "writes": c.get("writes", ""), "network": c.get("network", ""),
                    "needs": c.get("needs", ""), "hard": hard, "soft": soft,
                    "in_stack": d.name in have, "runs_in": c.get("runs-in", ""),
                }  # fmt: skip
        planned = json.loads((self.willow / "adapters" / "planned.json").read_text())
        for p in planned:
            if p["name"] not in out:
                out[p["name"]] = {
                    "name": p["name"], "kind": p.get("kind", ""), "state": "idea",
                    "section": p.get("section", ""), "line": p.get("line", ""),
                    "writes": p.get("writes", ""), "network": p.get("network", ""),
                    "needs": p.get("needs", ""), "hard": [], "soft": [], "in_stack": False,
                }  # fmt: skip
        if self.similar is not None:
            worked = self.similar.worked_out(self.similar.entries())
            for n, w in worked.items():
                if n in out:
                    out[n]["tags"], out[n]["near"] = w["tags"], w["near"]
        self._pieces = out
        return out

    def closure(self, names: list[str]) -> list[str]:
        """Every piece the named ones import outright, transitively, in order."""
        ps, seen, todo = self.pieces(), [], list(names)
        while todo:
            n = todo.pop(0)
            if n in seen or n not in ps:
                continue
            seen.append(n)
            todo += ps[n]["hard"]
        return [n for n in seen if n not in names]

    def folder(self, path: str) -> dict:
        typed = path.strip()
        p = Path(typed).expanduser()
        if not p.is_absolute():  # never read against wherever the server was started
            p = Path("/" + typed) if Path("/" + typed).is_dir() else Path.home() / typed
        if not p.is_dir():
            return {
                "ok": False,
                "path": typed,
                "why": "not a folder (give the whole path, starting with / or ~)",
            }
        n = 0
        for _ in p.rglob("*"):
            n += 1
            if n >= 5000:
                break
        return {"ok": True, "path": str(p.resolve()),
                "files": f"{n}+" if n >= 5000 else str(n)}  # fmt: skip

    def dirs(self, path: str, hidden: bool) -> dict:
        """One folder's subfolders, names only, for the picker. Reads no file."""
        p = Path(path).expanduser() if path else Path.home()
        try:
            p = p.resolve()
            names = sorted(
                (d.name for d in p.iterdir()
                 if d.is_dir() and (hidden or not d.name.startswith("."))),
                key=str.lower,
            )  # fmt: skip
        except OSError as e:
            return {"ok": False, "path": str(p), "why": e.strerror or "can't be read"}
        return {"ok": True, "path": str(p), "parent": str(p.parent) if p.parent != p else None,
                "dirs": names[:1000], "more": len(names) > 1000}  # fmt: skip

    # ── batches: a named set of add-ons, saved to recall, and deleted for good ─
    def _batches_file(self) -> Path:
        return self.to / "batches.json"

    def batches(self) -> dict:
        f = self._batches_file()
        try:
            got = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
        except ValueError:
            return {
                "refused": f"{f} isn't a batches file this canvas wrote; it's left as it is"
            }
        return got if isinstance(got, dict) else {}

    def save_batch(self, doc: dict) -> dict:
        name = " ".join(str(doc.get("name", "")).split())
        if not name or len(name) > 60:
            return {"refused": "a batch needs a name, up to 60 characters"}
        every = self.batches()
        if "refused" in every:
            return every
        if name in every and not doc.get("replace"):
            return {"exists": name}
        ps = self.pieces()
        stages = {}
        for stage, names in (doc.get("stages") or {}).items():
            keep = [n for n in names if isinstance(n, str) and n in ps]
            if keep:
                stages[str(stage)] = keep
        if not stages:
            return {
                "refused": "nothing is picked: a batch is the add-ons you've chosen"
            }
        with self.lock:
            every[name] = {"stages": stages, "saved": self.kernel.now(),
                           "pieces": sum(len(v) for v in stages.values())}  # fmt: skip
            self._write_batches(every)
        return {"saved": name}

    def delete_batch(self, name: str) -> dict:
        every = self.batches()
        if "refused" in every:
            return every
        if name not in every:
            return {"refused": f"no batch named {name!r}"}
        with self.lock:
            del every[name]
            self._write_batches(every)
        return {"deleted": name}

    def _write_batches(self, every: dict) -> None:
        f = self._batches_file()
        tmp = f.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(every, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        tmp.replace(f)  # whole or not at all

    # ── examples: the stack add-on's own, from the stack you put together ───
    def examples(self) -> dict:
        """The example stacks the stack add-on ships, read from this stack:
        each one's title, the paragraph about whose folder it's for, and its
        steps with the options each is run with."""
        base = self.stack / "adapters" / "stdlib" / "stack"
        if not base.is_dir():
            return {"state": "unreachable", "why": "the stack add-on isn't in your stack, and the examples come with it", "found": []}  # fmt: skip
        found = []
        for f in [base / "example.md", *sorted((base / "examples").glob("*.md"))]:
            if not f.is_file():
                continue
            title, about, steps, pool = "", [], [], None
            for block in f.read_text(encoding="utf-8").split("\n\n"):
                lines = block.splitlines()
                for ln in lines:
                    if ln.startswith("# ") and not title:
                        title = ln[2:].strip()
                    elif ln.startswith("## "):
                        pool = ln[3:].strip()
                    elif (
                        m := re.match(r"- ([a-z0-9-]+) -- (.*)$", ln)
                    ) and pool is not None:
                        steps.append(
                            {
                                "name": m.group(1),
                                "args": m.group(2).strip(),
                                "pool": pool,
                            }
                        )
                prose = [
                    ln
                    for ln in lines
                    if ln.strip() and not ln.startswith(("#", "    ", "- "))
                ]
                if prose and pool is None:
                    about.append(" ".join(x.strip() for x in prose))
            found.append(
                {
                    "file": f.name,
                    "title": title or f.stem,
                    "about": " ".join(about[:2]),
                    "steps": steps,
                }
            )
        return {"state": "populated" if found else "empty", "found": found}

    # ── the baseline: the kernel alone on a folder, as counts ───────────────
    def baseline(self, path: str) -> dict:
        """What the kernel alone makes of a folder, by its own rules, as counts
        and kinds of file only: never a passage, never a file's name, so the
        page shows nothing of what the files say or are called."""
        f = self.folder(path)
        if not f["ok"]:
            return f
        k, root = self.kernel, Path(f["path"])
        read, hidden, kinds = 0, 0, {}
        for p in root.rglob("*"):
            rel = p.relative_to(root)
            if not p.is_file():
                continue
            if any(part.startswith(".") for part in rel.parts):
                hidden += 1
                continue
            ext = p.suffix.lower() or "(no extension)"
            try:
                if p.stat().st_size > k.MAX_FILE:
                    why = f"over the kernel's {k.MAX_FILE // 1_000_000} MB a file"
                else:
                    raw = p.read_bytes()
                    if b"\0" in raw[: k.SNIFF]:
                        why = ("text in another encoding than UTF-8" if ext in TEXT_KINDS
                               else "not plain text")  # fmt: skip
                    else:
                        raw.decode("utf-8")
                        read += 1
                        continue
            except UnicodeDecodeError:
                why = "text in another encoding than UTF-8"
            except OSError:
                why = "couldn't be opened"
            kind = kinds.setdefault(ext, {"kind": ext, "files": 0, "why": {}})
            kind["files"] += 1
            kind["why"][why] = kind["why"].get(why, 0) + 1
        passages = len(k.chunks(root))
        cant = sorted(kinds.values(), key=lambda x: (-x["files"], x["kind"]))
        for c in cant:
            c["readers"] = self.readers_for(c["kind"])
            c["text"] = c["kind"] in TEXT_KINDS
        return {"ok": True, "path": f["path"], "read": read, "passages": passages,
                "hidden": hidden, "cant": cant}  # fmt: skip

    def readers_for(self, ext: str) -> list[str]:
        """Reader add-ons that could read a kind of file: box-health's own
        table, then a reader whose name or line names the kind. Words matched,
        so it's offered as could, never as will."""
        if not ext.startswith(".") or ext in TEXT_KINDS:
            return []  # text it reads anyway: too big or another encoding, no reader fixes
        word = ext[1:]
        known = {".pdf": ["pdf"], ".docx": ["office"], ".xlsx": ["office", "sheets"],
                 ".pptx": ["office"], ".odt": ["office"], ".ods": ["office"],
                 ".eml": ["mail"], ".mbox": ["mail"], ".epub": ["books"],
                 ".jpg": ["photos", "ocr"], ".jpeg": ["photos", "ocr"], ".png": ["ocr"]}  # fmt: skip
        out = [n for n in known.get(ext, []) if n in self.pieces()]
        for n, p in sorted(self.pieces().items()):
            if p["section"] != "Reading more kinds of files" or n in out:
                continue
            if n == word or re.search(
                rf"(?<![a-z0-9])\.?{re.escape(word)}(?![a-z0-9])", p["line"].lower()
            ):
                out.append(n)
        return out[:4]

    # ── the arrangement: propose, seal, assemble ────────────────────────────
    def arrangement(self, doc: dict) -> tuple[dict | None, str]:
        ps = self.pieces()
        name = str(doc.get("name", "")).strip() or "my stack"
        lanes = []
        for lane in doc.get("lanes", []):
            steps = []
            for s in lane.get("steps", []):
                n = str(s.get("name", ""))
                if n not in ps:
                    return None, f"no card named {n!r}"
                if ps[n]["state"] != "built":
                    return (
                        None,
                        f"{n} is still an idea on willow's list; it can't run yet",
                    )
                steps.append({"name": n, "args": str(s.get("args", "--box {box}"))})
            lanes.append({"title": str(lane.get("title", "")).strip() or "steps",
                          "steps": steps})  # fmt: skip
        named = [s["name"] for ln in lanes for s in ln["steps"]]
        if not named:
            return None, "the stack has no steps"
        folders = [
            f for f in (self.folder(p) for p in doc.get("folders", [])) if f["ok"]
        ]
        pulled = self.closure(named)
        every = list(dict.fromkeys(named + pulled))
        reach = sorted(
            {ps[n]["network"] for n in every if ps[n]["network"] not in ("", "none")}
        )
        writes = sorted({w.strip() for n in every for w in ps[n]["writes"].split(",")
                         if w.strip() and w.strip() != "nothing"})  # fmt: skip
        installs = sorted(n for n in every if ps[n]["kind"] == "deps")
        md = [f"# stack: {name}", ""]
        md += [f"<!-- reads: {f['path']} -->" for f in folders] + [""]
        for ln in lanes:
            md += [f"## {ln['title']}"] + [
                f"- {s['name']} -- {s['args']}" for s in ln["steps"]
            ]
            md.append("")
        return {
            "name": name, "lanes": lanes, "folders": [f["path"] for f in folders],
            "pulled_in": pulled, "pieces": every, "reach": reach, "writes": writes,
            "installs": installs, "stack_md": "\n".join(md),
        }, ""  # fmt: skip

    def propose(self, doc: dict) -> dict:
        arr, why = self.arrangement(doc)
        if arr is None:
            return {"refused": why}
        k = self.kernel
        with self.lock:
            ts = k.now()
            code, said = quiet(k.bite, self.box, f"stack {arr['name']}", ts)
            if code == k.REFUSED:
                return {"refused": f"the kernel wouldn't take the bite: {said}"}
            where = (
                "reaches " + ", ".join(arr["reach"])
                if arr["reach"]
                else "reaches no network"
            )
            prop = {
                "path": f"stacks/{re.sub(r'[^a-z0-9-]+', '-', arr['name'].lower()).strip('-') or 'stack'}.json",
                "data": k.canon(arr),
                "cites": [],
                "claim": (f"this is my stack: {plural(len(arr['folders']), 'folder')}, "
                          f"{plural(len(arr['pieces']), 'piece')}, {where}"),
            }  # fmt: skip
            code, said = quiet(k.propose, self.box, [json.dumps(prop)], ts)
            if code != k.ESCALATE:
                return {"refused": f"the kernel's door: {said}"}
            subj = k.subject_of(prop)
            k.append(self.box, ts, KIND, who="canvas", subject=subj, name=arr["name"],
                     pieces=len(arr["pieces"]), folders=len(arr["folders"]))  # fmt: skip
        return {"subject": subj, "claim": prop["claim"], "arrangement": arr}

    def seal_step(self, subject: str) -> tuple[int, str]:
        """The person's seal. Today: the kernel's own, under the key file the
        box names. The one place a passkey or a phone's key would replace."""
        return quiet(self.kernel.seal, self.box, subject, self.kernel.now())

    def seal(self, subject: str) -> dict:
        with self.lock:
            if not self.is_canvas(subject):
                return {"refused": "not a stack this canvas proposed"}
            code, said = self.seal_step(subject)
        return {"sealed": code == self.kernel.ALIVE, "said": said}

    def is_canvas(self, subject: str) -> bool:
        rows, _ = self.kernel.read(self.box / "record.jsonl")
        return any(r["kind"] == KIND and r.get("subject") == subject for r in rows)

    def state(self) -> dict:
        rows, breaks = self.kernel.read(self.box / "record.jsonl")
        sealed = self.kernel.sealed(self.box, rows)
        mine = [r for r in rows if r["kind"] == KIND]
        out = []
        for r in mine[-10:]:
            out.append({"subject": r["subject"], "name": r.get("name"), "row": r["n"],
                        "sealed": r["subject"] in sealed})  # fmt: skip
        return {"breaks": breaks, "rows": len(rows), "stacks": out,
                "in_stack": sorted(assemble.manifest(self.stack)["addons"])}  # fmt: skip

    def assemble(self, subject: str) -> dict:
        rows, _ = self.kernel.read(self.box / "record.jsonl")
        if subject not in self.kernel.sealed(self.box, rows) or not self.is_canvas(
            subject
        ):
            return {"refused": "only a sealed stack is assembled"}
        prop = json.loads((self.box / "proposals" / f"{subject[9:]}.json").read_text())
        arr = json.loads(prop["data"])
        have = assemble.manifest(self.stack)["addons"]
        want = [
            n
            for n in arr["pieces"]
            if n not in have and self.pieces()[n]["kind"] == "stdlib"
        ]
        skipped = [n for n in arr["pieces"] if self.pieces()[n]["kind"] == "deps"]
        if not want:
            return {
                "added": [],
                "skipped": skipped,
                "said": "every piece is already here",
            }
        with self.lock:
            code, said = quiet(assemble.add, want, self.to, None)
        self._pieces = None
        return {"added": want, "skipped": skipped, "exit": code, "said": said}

    # ── start it: your willow over your folders, after the seal ─────────────
    def start(self, subject: str) -> dict:
        rows, _ = self.kernel.read(self.box / "record.jsonl")
        if subject not in self.kernel.sealed(self.box, rows) or not self.is_canvas(
            subject
        ):
            return {"refused": "only a sealed stack is started"}
        with self.lock:
            if self.job and self.job["state"] == "running":
                return {"refused": "it's already starting"}
            self.job = {"state": "running", "steps": [], "browse": None, "flow": None}
        threading.Thread(target=self._start, args=(subject,), daemon=True).start()
        return {"started": True}

    def _step(self, what: str, state: str, said: str = "") -> None:
        self.job["steps"].append({"step": what, "state": state, "said": said})

    def _start(self, subject: str) -> None:
        import subprocess

        job = self.job
        try:
            arr = json.loads(
                json.loads(
                    (self.box / "proposals" / f"{subject[9:]}.json").read_text()
                )["data"]
            )
            have = assemble.manifest(self.stack)["addons"]
            k = self.kernel
            # 1. a record over each folder: the kernel's own init, the stack's key (for now)
            mine = self.to / "mine"
            key = self.to / "keys" / "stack.key"
            words = None
            if "starter-words" in have and "starter-words" in arr["pieces"]:
                words = mine / "my-words.txt"
                if not words.exists():
                    mine.mkdir(parents=True, exist_ok=True)
                    starter = (
                        self.stack
                        / "adapters"
                        / "stdlib"
                        / "starter-words"
                        / "words.txt"
                    )
                    words.write_text(
                        starter.read_text(encoding="utf-8"), encoding="utf-8"
                    )
                    words.chmod(0o600)
            boxes = []
            for folder in arr["folders"]:
                slug = (
                    re.sub(r"[^a-z0-9]+", "-", Path(folder).name.lower()).strip("-")
                    or "folder"
                )
                box = mine / slug / "box"
                if (box / "record.jsonl").exists():
                    self._step(
                        f"your record for {folder}", "ready", f"already set up at {box}"
                    )
                else:
                    argv = [
                        "init",
                        "--box",
                        str(box),
                        "--pile",
                        folder,
                        "--key",
                        str(key),
                    ]
                    if words:
                        argv += ["--words", str(words)]
                    code, said = quiet(k.main, argv)
                    self._step(
                        f"your record for {folder}",
                        "done" if code == k.ALIVE else "refused",
                        said,
                    )
                    if code != k.ALIVE:
                        continue
                boxes.append((folder, box))
            if not boxes:
                job["state"] = "stopped"
                return
            # 2. each piece's own tests, in a Python that has pytest
            import importlib.util

            py = (
                self.to / "venv" / "bin" / "python"
            )  # one beside the stack, else this one
            if not py.is_file():
                py = (
                    Path(sys.executable) if importlib.util.find_spec("pytest") else None
                )
            if py is None:
                self._step("each piece's own tests", "unreachable",
                           "no Python with pytest here: pip install pytest, or make one at venv/ beside your stack")  # fmt: skip
            else:
                passed, failed = [], []
                for name in sorted(have):
                    d = self.stack / "adapters" / "stdlib" / name
                    if not list(d.glob("test_*.py")):
                        continue
                    r = subprocess.run([str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider", str(d)],
                                       cwd=self.stack, capture_output=True, text=True, timeout=900,
                                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})  # fmt: skip
                    tail = (r.stdout.strip().splitlines() or [""])[-1]
                    (passed if r.returncode == 0 else failed).append(f"{name} ({tail})")
                    k.append(self.box, k.now(), "tested", who="assembler", piece=name,
                             state="passed" if r.returncode == 0 else "failed", tail=tail)  # fmt: skip
                self._step(
                    "each piece's own tests",
                    "failed" if failed else "done",
                    (
                        f"{len(passed)} passed"
                        + (f"; failed: {', '.join(failed)}" if failed else "")
                    ),
                )
            # 3. the flow you sealed, run once by willow's stack add-on
            runner = self.stack / "adapters" / "stdlib" / "stack" / "stack.py"
            if not runner.is_file():
                code, said = quiet(assemble.add, ["stack"], self.to, None)
                self._step(
                    "the runner for your flow (the stack add-on), put in",
                    "done" if runner.is_file() else "refused",
                    said,
                )
            folder, box = boxes[0]
            here = set(assemble.manifest(self.stack)["addons"])
            lines, skipped = [], []
            for ln in arr["stack_md"].splitlines():
                m = re.match(r"- ([a-z0-9-]+) -- ", ln)
                if m and m.group(1) not in here:
                    skipped.append(m.group(1))
                    continue
                lines.append(ln)
            flow = box.parent / "stack.md"
            flow.write_text("\n".join(lines) + "\n", encoding="utf-8")
            if runner.is_file():
                r = subprocess.run([sys.executable, str(runner), "--box", str(box), "--stack", str(flow)],
                                   cwd=self.stack, capture_output=True, text=True, timeout=900,
                                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})  # fmt: skip
                state = {0: "done", 42: "needs you"}.get(r.returncode, "refused")
                job["flow"] = (r.stdout or r.stderr)[:60000]
                note = f"over {folder}, exit {r.returncode}" + (
                    f"; not here, so left out: {', '.join(skipped)}" if skipped else ""
                )
                self._step("your flow, run once", state, note)
            # 4. browse, on your record
            b = self.stack / "adapters" / "stdlib" / "browse" / "browse.py"
            if not b.is_file():
                self._step(
                    "a page to ask your files",
                    "unreachable",
                    "browse isn't in your stack: add it under How you'll use it",
                )
            else:
                proc = subprocess.Popen([sys.executable, str(b), "--box", str(box), "--no-open"],
                                        cwd=self.stack, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)  # fmt: skip
                self.browsers.append(proc)
                link = None
                for _ in range(40):
                    line = proc.stdout.readline()
                    if not line:
                        break
                    if "http://127.0.0.1" in line:
                        link = re.search(r"http://127\.0\.0\.1:\d+/\S+", line).group(0)
                        break
                job["browse"] = link
                self._step(
                    "a page to ask your files",
                    "done" if link else "refused",
                    link or "browse didn't give a link",
                )
            job["state"] = "done"
        except Exception as e:  # said, never hidden
            self._step("starting", "refused", f"{type(e).__name__}: {e}")
            job["state"] = "stopped"


# ── the page ────────────────────────────────────────────────────────────────
PAGE = (HERE / "page.html").read_text(
    encoding="utf-8"
)  # the page, kept beside this file


def handler(cv: Canvas, token: str, host: str):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code: int, body, kind="application/json"):
            data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", kind + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; style-src 'unsafe-inline'; "
                             "script-src 'unsafe-inline'; connect-src 'self'")  # fmt: skip
            self.end_headers()
            self.wfile.write(data)

        def route(self) -> str | None:
            if self.headers.get("Host") != host:  # no DNS rebinding
                return None
            u = urlparse(self.path)
            pre = f"/{token}"
            if u.path != pre and not u.path.startswith(pre + "/"):
                return None
            return u.path[len(pre) :] or "/"

        def do_GET(self):
            r = self.route()
            if r is None:
                return self.send(404, {"refused": "not here"})
            q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
            if r == "/":
                return self.send(200, PAGE, "text/html")
            if r == "/api/search":
                return self.send(200, cv.search(q.get("q", "")))
            if r == "/api/pieces":
                return self.send(200, cv.pieces())
            if r == "/api/examples":
                return self.send(200, cv.examples())
            if r == "/api/batches":
                return self.send(200, cv.batches())
            if r == "/api/baseline":
                return self.send(200, cv.baseline(q.get("path", "")))
            if r == "/api/dirs":
                return self.send(
                    200, cv.dirs(q.get("path", ""), q.get("hidden") == "1")
                )
            if r == "/api/folder":
                return self.send(200, cv.folder(q.get("path", "")))
            if r == "/api/start":
                return self.send(200, cv.job or {"state": "none"})
            if r == "/api/state":
                return self.send(200, {**cv.state(), "folders": cv.folders})
            return self.send(404, {"refused": "no such page"})

        def do_POST(self):
            r = self.route()
            origin = self.headers.get("Origin")
            if r is None or (origin is not None and origin != f"http://{host}"):
                return self.send(403, {"refused": "not from this page"})
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self.send(415, {"refused": "JSON only"})
            n = int(self.headers.get("Content-Length") or 0)
            if n > 1_000_000:
                return self.send(413, {"refused": "too big"})
            try:
                doc = json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                return self.send(400, {"refused": "not JSON"})
            if r == "/api/propose":
                return self.send(200, cv.propose(doc))
            if r == "/api/seal":
                return self.send(200, cv.seal(str(doc.get("subject", ""))))
            if r == "/api/assemble":
                return self.send(200, cv.assemble(str(doc.get("subject", ""))))
            if r == "/api/start":
                return self.send(200, cv.start(str(doc.get("subject", ""))))
            if r == "/api/batches/save":
                return self.send(200, cv.save_batch(doc))
            if r == "/api/batches/delete":
                return self.send(200, cv.delete_batch(str(doc.get("name", ""))))
            return self.send(404, {"refused": "no such action"})

    return H


#: what a new stack starts with, beside the kernel: the runner and its examples,
#: and the page Start it opens
BASE = ("stack", "browse")
WILLOW = HERE.parent


def ready(to: Path) -> int:
    """A stack at `to`, made from this willow on first run."""
    if (to / "stack" / "STACK.json").is_file():
        return assemble.ALIVE
    if to.resolve().is_relative_to(WILLOW.resolve()):
        print(f"refused: keep your stack outside this repository, not in {to}",
              file=sys.stderr)  # fmt: skip
        return assemble.REFUSED
    print(f"making your stack at {to}, from this willow")
    code = assemble.init(WILLOW, to, None)
    if code != assemble.ALIVE:
        return code
    code = assemble.add(list(BASE), to, None)
    return assemble.ALIVE if code in (assemble.ALIVE, assemble.ESCALATE) else code


def main(argv: list[str]) -> int:
    opts: dict[str, str] = {}
    folders: list[str] = []
    it = iter(argv)
    for a in it:
        if a in ("--to", "--port"):
            opts[a] = next(it, "")
        elif a == "--folder":
            folders.append(next(it, ""))
        elif a == "--no-open":
            opts[a] = "1"
        else:
            print(__doc__.split("\n\n")[1], file=sys.stderr)
            return assemble.REFUSED
    port = opts.get("--port") or "0"
    if not port.isdigit() or "--to" in opts and not opts["--to"]:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return assemble.REFUSED
    to = Path(opts.get("--to") or Path.home() / "willow-stack").expanduser()
    code = ready(to)
    if code != assemble.ALIVE:
        return code
    cv = Canvas(to, WILLOW, to / "box", folders)
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", int(port)), None)
    except OSError as e:
        print(f"refused: port {port}: {e.strerror}", file=sys.stderr)
        return assemble.REFUSED
    host = f"127.0.0.1:{srv.server_address[1]}"
    token = secrets.token_urlsafe(18)
    srv.RequestHandlerClass = handler(cv, token, host)
    url = f"http://{host}/{token}/"
    print(f"your willow, on this machine only: {url}\n(Ctrl-C stops it)", flush=True)
    if not opts.get("--no-open"):
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in cv.browsers:  # the pages it opened stop with it
            proc.terminate()
    return assemble.ALIVE


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
