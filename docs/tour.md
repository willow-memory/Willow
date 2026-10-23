# Your first five minutes

Everything below runs from a fresh clone with nothing installed beyond Python.
The output shown is real.

## 1. Check it works on your machine

```
$ git clone https://github.com/willow-memory/Willow && cd Willow
$ python kernel.py test
kernel: the eight beats held
```

`test` sets up a throwaway folder, runs every command, and checks eight
properties, among them that an unapproved suggestion is never given as an
answer, a forged approval is rejected, and an edited log is refused.

## 2. Ask questions of someone else's files

The repo includes made-up people to try it on. Odile is a piano tuner and
beekeeper with six years of notes, logs, texts, letters and receipts.

```
$ python demo/odile/make_life.py           # writes her 254 files into demo/odile/life/
$ python kernel.py init --box odile-record --pile demo/odile/life --key odile.key
ready: record started, row 0 6ecb8f01be3521d6

$ python kernel.py bite --box odile-record "how are the bees"
```

`init` made two things: `odile-record/`, the folder where the log is kept,
and `odile.key`, the private key that approves answers. Odile's own folder is
only read.

The answer is JSON: up to three passages, each with its file, line and text.
Here they are the three most recent hive inspections from `hives/2026.txt`,
newest first, because her log has a date over every entry.

## 3. Ask something her files don't say

```
$ python kernel.py bite --box odile-record "when is the county deadline"
```

```json
{
  "state": "populated",
  "served": [
    { "where": "mail/2026-03-20-county.txt:12",
      "text": "... You may file a response or an\nobjection within 180 days of the date of this notice. ..." },
    { "where": "mail/2026-03-20-county.txt:10", "text": "NOTICE OF PROPOSED DETERMINATION OF WATER RIGHT" },
    { "where": "mail/2026-03-20-county.txt:8",  "text": "RE: Case No. WR-2026-0117" }
  ],
  "look": [
    { "why": "no file in your folder has deadline",
      "where": "it may be called something else there",
      "next": "add it to your words list, or use a search that matches by meaning" }
  ]
}
```

(Trimmed: each passage also carries an `id` and an `echo` flag.) Her files
never say "deadline", and the output says so rather than pretending. The
county's letter is still found from the other words. When no passage holds
enough of the question, the exit code is 42 and nothing is served.

## 4. Teach it her words

"Who still owes me money" brings back a text message about money, because her
files never say "owes": her invoices do. A words list connects the two:

```
$ printf 'owes = invoice, outstanding\n' > words.txt && chmod 600 words.txt
$ python kernel.py init --box odile-record-2 --pile demo/odile/life --key odile.key --words words.txt
$ python kernel.py bite --box odile-record-2 "who still owes me money"
```

Now two of the three passages are her unpaid school-district invoices, and
the output says why: `"read owes as invoice, from your words list"`.

## 5. Approve an answer

Suppose an assistant read the county letter and suggests an answer. It hands
it in, citing the passage it relied on (the passage's `id` from step 3):

```
$ cat rows.jsonl                           # one suggestion per line; wrapped here
{"path": "county.md", "data": "Reply by 2026-09-16: 180 days from the 2026-03-20 notice.",
 "cites": ["0e4ba2df…"], "claim": "the notice gives 180 days to file"}

$ python kernel.py propose --box odile-record --file rows.jsonl
pass  proposal:0a6fde95…  waiting on your seal          (exit 42: waiting on you)

$ python kernel.py out --box odile-record
waiting on your seal: proposal:0a6fde95…
5 rows; 0 sealed; 1 waiting

$ python kernel.py seal --box odile-record proposal:0a6fde95…
sealed proposal:0a6fde95…; written to written/county.md

$ python kernel.py bite --box odile-record "When is the county deadline?"
{"state": "sealed", "answer": "Reply by 2026-09-16: 180 days from the 2026-03-20 notice.", "by": "proposal:0a6fde95…"}

$ python kernel.py verify --box odile-record
the chain holds: 7 rows, 1 sealed
```

The same question, typed with different case and punctuation, now returns the
approved answer. Until `seal` ran it was only a suggestion, and it was never
given as an answer.

Then point it at a folder of your own:

```
$ python kernel.py init --box my-record --pile path/to/your/folder --key my.key
$ python kernel.py bite --box my-record "your own question"
```

Keep the key somewhere other than the record folder; `init` refuses a key
inside it.

Back to the [README](../README.md).
