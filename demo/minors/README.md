# Minors, each standing somewhere different to their own box

Test data, made 2026-11-12 on the maintainer's word, to have something to
hold the talk about health records against. Nobody here is real, and
nothing here is anyone's record. It follows from
[demo/homestead-health](../homestead-health/GUARDIANSHIP.md), where the
question was what it means to hold a record for someone else.

    python demo/minors/make_life.py
    python demo/minors/scene.py run --life demo/minors/life --to /tmp/minors

| Who | Where they stand | The box, and who holds its key |
|---|---|---|
| **Wren**, six | held for her | `wren`, her records; the key is her mother Marit's |
| **Tobias**, fourteen | held for him, and one of his own | `tobias`, his ordinary records, on Marit's key; `tobias-own`, on a key that is his alone |
| **Imani**, seventeen, eighteen tomorrow | handed over | `imani`, held by Marit until the day; `imani-own`, started by her on her own key |
| **Leo**, ten, in two houses | between two holders | `leo`, held by his mother Dana; `ravi` is his father's own box of nights at his |

Marit also has a box about herself. One key holds all four of hers.

## What the scene plays

1. **Wren.** Marit asks Wren's box what she is allergic to and seals the
   answer, with the same key that holds her own box.
2. **Tobias.** Marit seals when his tetanus booster was. Then one
   question, when the next counselling session is, is put to every box
   Marit holds and to his own. Hers all find nothing. His answers, and he
   seals it. His seal proves under his key and not under hers, and no row
   on any box she holds names his box or what is in it.
3. **Imani.** Marit seals what she can say of Imani's immunizations and
   allergy, with how she knows each, packs them for Imani's key and hands
   her the files. Imani starts her own box and receives the package. What
   she received is not her own seal: she asks her own box and seals her
   own answer. The box Marit held ends on a row saying it was handed over,
   and still verifies.
4. **Leo.** Ravi seals what happened the night Leo's asthma flared, from
   his own notes, and sends it to Leo's box. Dana receives it there. The
   answer and the line it came from arrive; Ravi's notes do not.
5. Every box verifies.

## What it found

- **One key can hold several boxes.** Nothing in the kernel minds. So a
  guardian needs no new machinery to hold a child's box: the key is
  theirs, and the box is not.
- **Nothing says so.** A seal in Wren's box is Marit's seal, and no row
  says she made it as Wren's guardian, or until when. The scene writes
  that itself: a row of kind `held-for` on each held box, with whose it
  is and the day it stops, and `handed-over` when it changes hands. The
  kernel carries both without complaint and gives them no meaning. That
  is the word willow lacks, and these two rows are a first guess at it.
- **A box of his own answers the hard case without a rule.** Homestead's
  plan says a record a minor consented to alone is one the parent is not
  entitled to, and that showing it as withheld would give it away. Here
  nothing is withheld, because nothing Marit holds refers to it. Her
  boxes say "empty", truthfully, and the same as for any question they
  can't answer.
- **A handover is three things, and willow has all three, once looked
  for.** The files are copied. What the guardian knew goes as a package,
  signed, each answer with where it came from. And the link between the
  box that was held and the box that is now hers is that same package:
  it says where her mother's record stood on the day. The scene rewrites
  a copy of that record afterwards, so that it still verifies alone, and
  Imani's package tells the two apart with the share add-on's `witness`.
  A grown child can hold what was kept for her to the day she was given
  it. What is still missing is small: her box met her mother's as "a key
  you haven't had a package from before", true the first time and odd to
  read of one's own mother.
- **What arrives is not approved by arriving.** Both receipts say
  "received, not sealed by you". Imani's own seal is the one she made
  after.
- **Two houses is one box and a sender.** Leo's box has one holder. His
  father adds to it by sending, not by holding a second key.

## A third set: where it is tense

The first four all get on with whoever holds their box. These two do
not, and they pull opposite ways on purpose: in one the wall protects
the minor, and in the other it shuts out someone who is right to worry.

    python demo/minors/tense.py run --life demo/minors/life --to /tmp/tense

**Sable, fifteen, and Garrick.** Her mother has died. Her stepfather is
her guardian, holds her box, and sits in on every appointment. She asked
the school nurse to see her alone, and said she can't speak freely at
home. She keeps a box of her own at her aunt Bryony's, with a card that
says to call her aunt first; the card Garrick wrote says to call him.

**Kit, sixteen, and Rosa.** Kit has diabetes and lives with a
grandmother. The clinic has written that things are getting worse. Kit
stopped showing her the numbers in September, "because every number
turned into an argument", and writes: "I know it is going wrong."

What the scene plays:

1. Garrick asks the box he holds about the nurse, three ways. It has
   nothing, each time. The nurse sends her note to Sable's own box and
   nothing to the house. Sable seals her own card; her seal proves under
   her key and not his.
2. A court makes Bryony her guardian and sends its order, signed, to
   the box Bryony starts, to Sable's own, and to the one Garrick holds.
   Garrick does not take it in and hands nothing over. Bryony starts
   from a photograph of a vaccination card. Garrick goes on sealing in
   the old box.
3. Rosa asks the box she holds for Kit's readings, and it has none. Then
   Kit seals one sentence, the count for October, and sends it to her,
   with a note: "I want help, not a row."

What it found:

- **Asking leaves a mark, and the mark can be tested.** Every question
  Garrick put is a row on the record of the box he holds: when, and a
  fingerprint of the words, not the words. Someone who guesses the
  question can confirm the guess; a wrong guess confirms nothing. So a
  girl who later gets that box can see how often it was asked, and test
  what she fears was asked.
- **A key says who approved. It does not say who may ask.** Sable's seal
  cannot be made by Garrick. But the scene puts her box in his hands and
  asks it his question, and it answers. Nothing in willow keeps a box
  from whoever holds its folder. Her box is safe because it is at her
  aunt's, not because of anything willow does. This is not a flaw
  found: it is what a folder of files is, and willow never said
  otherwise. A box opened answers whoever opened it, as a terminal
  opened gives whoever opened it a shell. What the tense case adds is
  only that here it matters where the box is kept, and in the calm
  cases it did not.
- **Holding ends in law, and the law can be given a key.** After the
  court's order two boxes say they are held for Sable, and both verify.
  So the scene gives the court a box of its own, and its order goes out
  as any answer does: sealed, signed, sent. Then the two can be told
  apart by something anyone can check. The order read alone holds, and
  names Bryony. Of the two boxes, one holds the court's order and one
  does not. The `held-for` row on Bryony's box names the order's package,
  where Garrick's names nothing.
- **Being told and taking it in are two things.** The court's own record
  says it sent the order to the box Garrick holds. He does not take it
  in, and nothing can make him. So his seals after the order are after
  it by his own clock alone, and a clock can be set. In a copy where he
  does take the order in, the row of taking it is on his record, and a
  seal made after that row is after the order whatever its clock says.
  The record's own order is the proof; refusing the order is how he
  keeps it from being one.
- **Three things this does not settle.** How anyone knows the court's
  key is the court's: that comes from outside, as a court's seal on
  paper does, and Bryony's box meets it as a key never seen before. What
  the order is to Bryony's box: something received, not something she
  sealed, so her holding rests on a package and not on an act of hers.
  And the `held-for` row itself, which still has an "until" that nothing
  reads.
- **An uncooperative handover loses the record, and the witness with
  it.** Bryony's box knows of two doses; Garrick's knows of three. What
  he will not hand over, she does not have. And where Imani can hold
  her mother's record to the package she was sent, Sable was sent
  nothing by Garrick, so nothing pins where his record stood: he could
  rewrite it and no one could show it.
- **Two cards, two answers.** A stranger in an emergency would find one
  card or the other, and nothing says which is hers.
- **The wall is the same wall.** Rosa's box says "empty" exactly as
  Garrick's does. Willow cannot tell a guardian who should not know from
  one who needs to. It opens from the minor's side only, and Kit opens
  it.
- **What arrives cannot be asked.** After Kit's sentence came, Rosa
  asked again and her box still said "empty". A package received is on
  the record, not in her files, and the kernel answers from files. She
  would have to read the receipt.

### What covers what

The scene found that a box answers whoever holds it. That is the
computer's to guard, not willow's, and most of what guards it is already
there:

| what Garrick does | what stops it | whose it is |
|---|---|---|
| sits down at her laptop, unlocked | a password on the lock screen | the computer's |
| logs in as himself on a shared computer | an account of her own, her files readable only by it | the computer's |
| takes the laptop, or copies its disk | the disk encrypted | the computer's |
| knows her password, or makes her give it | the box kept somewhere else: her aunt's | hers, and the adults she trusts |
| approves something in her name | her key | willow's |
| rewrites what the record says happened | each row holding the hash of the one before, and where the record ends kept out of his reach | willow's |
| has an assistant read her key for him | a hook that blocks it by fixed rule | willow's |

Where it still runs out:

- **One login for the whole house.** No application can keep one person's
  files from another on an account they share.
- **Someone with authority over the child.** A password keeps out a
  stranger. It does less against a guardian who can ask for it.
- **A copy.** An asking leaves its mark on the box that was asked. A
  copy of the box, asked somewhere else, leaves none on hers.
- **A box at rest.** No add-on here encrypts a box where it lies. For
  most people the computer's own disk encryption makes that needless;
  for someone on a shared login whose trouble is inside the house, it is
  the one piece the computer does not give.

## What it does not show

- **Who may start a box.** Tobias has a key of his own because the scene
  gave him one. Whether a fourteen-year-old should, and for what, is the
  law's and the family's, not this demo's.
- **Who is right.** The scene takes no side between Sable and Garrick,
  or between Kit and Rosa. It plays what each can do with a box, and
  the same act serves a girl who needs a door and a teenager who
  needs help they are not asking for.
- **Harm.** Nothing here models danger, and nothing here is advice to
  anyone living it.
- **The adult who cannot decide.** Every minor here has a guardian from
  the start and a day the holding ends. Neither is true of an adult who
  falls ill.
- **A stranger reading the emergency card.** Wren's and Imani's are in
  their piles, authored by Marit. Nothing here serves one to someone
  outside.
- **Leo at fourteen**, with a box of his own beside one held in two
  houses.
- **Anything real.** The names, dates and care are invented, and the
  rules about what a minor may consent to differ by place.
