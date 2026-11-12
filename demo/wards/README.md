# Held for someone else: minors, and adults who cannot decide

Test data, made 2026-11-12 on the maintainer's word, to have something to
hold the talk about health records against. Nobody here is real, and
nothing here is anyone's record. It follows from
[demo/homestead-health](../homestead-health/GUARDIANSHIP.md), where the
question was what it means to hold a record for someone else.

    python demo/wards/make_life.py
    python demo/wards/scene.py run --life demo/wards/life --to /tmp/wards

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

    python demo/wards/tense.py run --life demo/wards/life --to /tmp/tense

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

## Leo at fourteen

Four years after the first set. At ten Leo had one box, held by his
mother, and his father added to it by sending. Now he has a box of his
own beside it.

    python demo/wards/fourteen.py run --life demo/wards/life --to /tmp/fourteen

His preventer inhaler was changed at a review his mother took him to.
Nobody told his father, who still gives him the old one. Leo has counted
how often he needs his reliever: nine times in a month at his mother's,
once at his father's, and he has written down why: his mother's partner
smokes in the kitchen. He saw the asthma nurse on his own. And he wrote:
"I don't want Dad to have the count. He would use it on Mum."

What the scene plays:

1. Each parent sends his box what they know of his preventer. They do
   not agree, and neither parent's box holds the other's word.
2. The nurse sends her note to his box only. He seals the plan and sends
   it to his father; he seals the count and sends it to the box his
   mother holds.
3. He holds each parent's record to what that parent sent him.

What it found:

- **The child is the only one with all of it.** His box took in three
  packages: his mother's, his father's and the nurse's. Each parent's
  took in one, from him. Two adults who do not share a house or a
  notebook each hold half, and for four years the only whole record of
  his care is the one he keeps. That was not true at ten, when one
  parent held the box and the other fed it.
- **He sees the disagreement and they do not.** His mother's box says
  purple, one puff. His father's says brown, two. Each is sure. Only in
  his box do the two sit side by side, and a child being given two
  different doses by two careful parents is exactly the thing a shared
  record is for.
- **What he sends is his to choose, and he chooses differently for
  each.** His father gets the plan and not the count. His mother gets
  the count and not a word of what his father said. The nurse's note
  goes to neither house. This is the same wall as Sable's and Kit's,
  used by a boy who is not hiding from anyone: he is keeping a fact from
  becoming a weapon between two people he lives with.
- **He does not have to wait for eighteen to hold them to it.** Imani
  could hold her mother's record to what she was sent only at the
  handover. Leo can do it now, to both parents, because each has already
  sent him something.
- **What still does not work.** His box cannot be asked what his parents
  said: what arrives is on his record and not in his files, so to have
  it answer he has to write it down again himself, as he did with the
  nurse's plan. And it met both his parents as keys it had never seen.

## The gap that came up three times: what arrives cannot be asked

Kit's grandmother, after Kit's sentence came. Bryony, holding a court's
order. Leo, with both his parents' word. Each took a package in, and
each time the box could not answer from it. A package taken in is a row
on the record: who signed it, and that it held. Its words are not in the
box, and the kernel answers from files.

    python demo/wards/askable.py run --life demo/wards/life --to /tmp/askable

That plays Leo at fourteen and then asks his box four questions about
what he was told, with his pile made three ways.

| | his father on the brown inhaler | his mother on the review | how many puffs of the brown | the nurse's plan |
|---|---|---|---|---|
| as it is | his own count, which is about something else | nothing | his own line about the *purple* one | his own line |
| the package files dropped in his pile | his own count | nothing | the package, as raw JSON | the package, as raw JSON |
| each package written out as a page | his father's word | his mother's word | his father's word | the nurse's word |

- **As it is, it is worse than silence.** Asked how many puffs of the
  brown inhaler, his box serves his own line about the purple one. The
  words are close enough to pass the kernel's rule and the answer is the
  other inhaler. A box that holds half of what was said answers from the
  half it holds.
- **Dropping the package in is not enough.** The kernel does read it,
  and serves a line of signatures and hashes that nobody could read.
- **Written out, it works**, four of four, and each answer comes with
  where it is from: a page under `received`, headed "Received from Dad,
  not sealed by me", with the day, the key, his note, and the place in
  his own files it came from. That page is made by hand here, from the
  package. Nothing in willow makes it.

What an add-on that made such pages would have to get right, said
before anyone builds one:

- **It must not be automatic.** If taking a package in put its words in
  the pile, anyone could put words in your box by sending you
  something. Dorian could send Agnes's box "my son Dorian is to decide"
  and have it served. Keeping a package as a page has to be the owner's
  act, on the record, package by package.
- **The page must say whose word it is**, in its own text, so the
  passage served carries it and not only the file's name.
- **The page must be checkable against the package.** Made from it the
  same way every time, naming it, so a page edited afterwards can be
  told from one that was not.
- **Whose key it was has to come from the owner.** "Dad" is Leo's name
  for a key. That is the same question as how a key gets known, which
  is being worked on elsewhere.
- **A later package that replaces an earlier one** has to mark the
  earlier page, or the box answers from both.

The idea is on the list of planned add-ons as `received`, with those
five things as what it has to get right; it is not built. One idea
already on that list bears on the rest of this page: `grant`, someone
else allowed to ask part of your folder, for a path and a time. That is
the other half of "a key says who approved, not who may ask".

It is the same shape the study of shared runs met from the other side:
a thing received should not be gone on from until someone has looked at
it.

## How a key gets known: a proposal from elsewhere, held to these scenes

Every scene here met someone's key "as a key you haven't had a package
from before": Imani her mother's, Bryony the court's, the hospital
Marcus's, Leo both his parents'. A proposal made on 2026-11-11 in the
maintainer's willows-grove repository (the design page "Phone keys: made
anywhere, checked at home", commit d90afb4; proposed, not ratified,
nothing built) is about exactly that, for a phone coming home. Its
thought, in the maintainer's words: the security belongs "not
necessarily where the key is produced but where it's verified".

Its shape: a box makes its own key wherever it is; its public half is
enrolled once, by the person whose door it is, over a channel they
trust; what comes back is checked at the door against the keys
enrolled; a signer the door does not know is refused, or what it sent
is held as a suggestion and not as sealed; a changed key is taken only
on that person's word.

Held to the people here:

| who meets whose key | how it would be enrolled | what changes |
|---|---|---|
| Imani, her mother's | across a table, before the handover | the package reads as her mother's and not a stranger's |
| Leo, each parent's | at each house | "Dad says" is his enrolment, not a label written by hand |
| Bryony, the court's | from the paper order, or at the court's desk | her holding rests on a key she checked, where today it rests on one she took on sight |
| Garrick, the court's | he will not | nothing. Enrolling is the owner's act, and refusing it is his |
| the hospital, Marcus's | it cannot be: they have never met | the proposal's own answer fits what a ward does. A card from a signer it does not know is held as something said, not as sealed: read, weighed, acted on with care |

So it answers every case where the two can meet first, which is most of
them, and it names the one where they cannot. The emergency card stays
the hard case: the one time a stranger has to act on a key, there was
never a door to enrol it at.

One thing it makes plain that these scenes passed over: a box's own seal
can be checked only by whoever holds that box's key. "Her seal proves
under her key and not under his" is something only she can find out.
What anyone else can check is a package, which is signed another way.
Every claim on this page that one person can check another's word is
about a package.

## The emergency card, read by a stranger

The one case the proposal above cannot reach: a ward reading a card
whose signer was never at its door. This plays what a ward can do with
one anyway.

    python demo/wards/card.py run --life demo/wards/life --to /tmp/card

Three things decide it.

**How the card stands at this door.** *Enrolled*: its signer's key is
one the ward enrolled. *Vouched*: it is not, but a signer that is has
sealed and sent whose key it is and how it knows. *Unknown*: neither;
the signature holds, and that is all that can be said. A card merely
passed on by a signer the ward knows is not vouched for.

**What each line says.** A *caution* makes the reader more careful: an
allergy named. An *all-clear* makes them less careful: "none known". A
*fact* is to be weighed: a daily medicine. A *grant* names someone to be
called and told. A *stop* is a caution that blocks: "do not operate".

**The rule.** A caution is honoured however the card stands. An
all-clear and a grant are honoured only enrolled or vouched. A fact is
shown with how it stands. A stop from an unknown signer is shown and
weighed, not obeyed. **An unknown signer can make a ward more careful,
never less, and cannot make it stop.**

What the scene plays, on the night Marcus is brought in and after:

| | how it stands | allergy to penicillin | "no known allergy" | whom to call |
|---|---|---|---|---|
| his card, handed over by Jun | unknown | honoured | | held |
| a second card, saying it is his | unknown | | held | held |
| his card, once the surgery he is registered at has said whose key it is | vouched by the surgery | honoured | | honoured: Jun is called |
| the second card, passed on by the court without a word | unknown | | held | held |
| his card again, after he shows his key at the ward's desk | enrolled | honoured | | honoured |

And when Sable is brought in with two cards:

| | how it stands | "no known allergy" | whom to call |
|---|---|---|---|
| the card Garrick wrote | unknown | held | held |
| the card she wrote | unknown | held | held |
| the court's order naming Bryony her guardian | enrolled | | honoured: Bryony is called |

What it found:

- **Most of a card is safe to honour from a stranger, and the part that
  matters most is.** Penicillin was withheld from the first minute, on a
  card whose signer the ward had never met. Believing a false caution
  costs a little care. That is why a bracelet works.
- **A caution that blocks is another thing.** The second card also says
  "do not operate". Withholding one drug on a stranger's word costs
  little; stopping an operation on a stranger's word could cost him the
  leg. So it is shown to the team, who weigh it, and the surgery is not
  stopped by it. Had the card stood enrolled or vouched it would have
  been honoured. This was the line this page first set aside; the
  proposal took it up, and the scene follows.
- **The dangerous lie is the all-clear.** The second card says he has no
  allergy. Had it been believed, it would have undone the first. Under
  the rule it changes nothing: an unknown signer cannot lower the care
  taken. Both cards arrived with good signatures; a signature was never
  the question.
- **One hop of vouching is enough, and it is something people already
  do.** Marcus showed his key at his surgery's desk a year before. The
  ward knows the surgery. So the surgery seals and sends one sentence,
  "the key … is Marcus Bell's: he showed it at our desk", and that is
  what turns "call Jun" from held to honoured. The surgery never has to
  hold the card: it speaks for the key, and the card Jun handed over the
  night before is the one read again. No stranger has to be trusted,
  only a desk he once stood at.
- **Passing a card on is not speaking for it.** The second card is sent
  to the court, which the ward knows, and the court passes it on
  without a word. It stands unknown, as it did. A wrap is not a
  statement, and the ward's record keeps each statement it does hear as
  a row of its own: whose key, said by whom.
- **Two cards that disagree are settled by neither.** Sable's cards name
  two people. Neither is called on a card alone. The court's order,
  from a key the ward has, names her guardian, and that is who is
  called. It is the person her own card names, and it is not because
  her card says so.
- **How strict, settled 2026-11-12 by the maintainer: the middle is
  fine.** The rule as played sits between telling whoever is at the
  bedside and telling no one a card names: cautions at once, grants
  when someone the ward knows has spoken for the key.
- **The cost falls on Jun, for a night.** Under the rule the person
  Marcus chose is not told until morning. The adults' scene had the
  ward tell Jun at once, as a ward might; this one is stricter, and the
  difference is a choice about harm that the scene does not make for
  anyone.
- **Every reading is on the ward's record**: which card, what kind of
  line, how it stood, what was done. When Marcus wakes that is what he
  is shown.
- **Enrolling after is cheap.** He shows his key at the desk, and the
  same card read again stands enrolled. The second card still stands
  unknown.

The rule went back the way it came: the proposal in willows-grove now
carries it, in a section called "A signer who can never be enrolled"
(commit 55afe2d), for a phone that comes home unenrolled. Its rows can
add caution on sight, and grant or relax nothing until it is enrolled
or vouched for.

Held on 2026-11-12 to the section the proposal now carries, three
things came out that neither page had said:

- **A wrap is not a word.** As first played, and in the proposal's
  wording, a card was vouched when a signer the door knows had wrapped
  it. The surgery checked the key inside before passing the card on,
  but nothing made it check and nothing read its note: a known signer
  passing on a stranger's card without looking would have vouched for
  it. The scene is changed. Vouching is now a thing said and signed,
  "this key is his, and here is how I know", and a card merely passed
  on stays unknown. That is this scene's choice; the proposal's own
  wording is the maintainer's to settle.
- **A caution is cheap in a ward and may not be at a door.** Every
  caution first played here withheld one drug. The proposal let an
  unenrolled device "flag something, refuse something, hold something
  back", and a refusal is a larger thing: anyone who can reach the door
  could make it refuse. On the maintainer's word the proposal now splits
  them (commit cc4c876): a caution that is cheap is honoured on sight,
  and one that blocks is shown and weighed until its signer is enrolled
  or vouched. The scene plays that too, as the line "do not operate".
- **A card whose signature does not hold.** The scene's code honoured a
  caution even then, and nobody had decided that; it was never played,
  only asserted in a test. The rule is about cards that hold. One that
  does not is now left unread by the rule, as a note of no known hand,
  for the ward to treat as it would any unsigned note. The proposal's
  door refuses what fails, which is the same thing said more firmly.

What it rests on that nothing here builds:

- **A ring at each door.** The scene holds the ward's enrolled keys in a
  table of its own. That is the ring the proposal above asks for.
- **Someone to read each line.** Which lines are cautions and which are
  grants is a table in the scene, standing in for a nurse. A card cannot
  be let to say what kind of thing it says: a grant marked as a caution
  would walk through.
- **What a refusal of treatment needs beyond this.** The scene honours
  a stop from a signer the ward knows or has had spoken for. Whether a
  refusal binds is a matter of law and of the person's state when they
  wrote it, and a signature settles neither.
- **A ward that knows no one who knows him.** Vouching needs one desk in
  common. A traveller far from home has none.

## Two adults who cannot decide

A child has a guardian from the start and a day the holding ends. An
adult has neither. The two stories differ in the one thing that turns
out to matter: whether they said beforehand.

    python demo/wards/adults.py run --life demo/wards/life --to /tmp/adults

**Agnes, seventy-eight.** In March 2025, well, she wrote: "If two
doctors say I can no longer decide about my care, my daughter Petra
Thorne is to hold my papers and decide for me. Not my son: we do not see
it the same way. I want to stay in my own house as long as it is safe."
She sealed it and sent it to Petra. In November 2026 a memory clinic
finds that she cannot, for now, weigh a decision about her treatment, to
be looked at again in three months. Her son Dorian wants her moved near
him and the house sold.

**Marcus, forty-one.** Knocked off his bike on the second of November,
unconscious for nine days. He had named no one. In January he had
written an emergency card (allergic to penicillin; call his partner Jun
first) and sent it to Jun, "in case". His mother Elaine arrives too, and
writes: "Nobody at the hospital would tell me anything until the
afternoon."

What the scene plays:

1. Petra and Dorian each start a box held for Agnes. Petra's rests on
   two packages: Agnes's own word, signed by Agnes's key in 2025, and
   the clinic's finding, signed by the clinic's. Dorian's rests on
   nothing.
2. After the finding, on a clear day, Agnes seals that she wants to stay
   in her house. The next evening Dorian, at her computer, seals with
   her key that he is to decide for her.
3. Jun passes Marcus's card to the hospital, Marcus's signature inside
   Jun's. Nobody holds a box for Marcus and nobody touches his. The
   hospital keeps its own record. When he wakes it sends him what was
   done; he takes it in, holds the hospital's record to it, and seals
   that he has read it.

What it found:

- **Said beforehand, an adult's own key is the authority.** No court is
  needed to tell Agnes's children apart. Her word is a package signed by
  her, sent while she could send it, and it names Petra. That is the
  strongest holding in any of these scenes: the minors' guardians hold
  by law, and Bryony by a court; Petra holds because Agnes said so.
- **It takes two signatures, and that is the right number.** Her word
  says who, and on what condition. The clinic's finding says the
  condition is met. Either alone starts nothing.
- **The key outlives the deciding.** Three seals on Agnes's record prove
  under her key: her word of 2025, her wish on a clear day, and Dorian's
  at her keyboard. Her record has no way to tell her hand from his. A
  key says a key was used. With a child that never came up, because a
  child's key was never the authority.
- **The record's order is what is left.** Agnes's box took the clinic's
  finding in. So her record itself puts one seal before the finding and
  two after it, whatever any clock says. It cannot say which of the two
  is hers; it can say both were made when two doctors had found she
  could not decide. And her word of 2025 still holds against what Petra
  was sent: a later seal does not unsay an earlier one.
- **A seal can cite a page that says the opposite.** Dorian's "my son
  Dorian is to decide for me" cites the line of her own page that says
  "not my son". The kernel checks that what is cited was served, not
  that the answer agrees with it.
- **For a short while, the right amount of holding is none.** Nobody
  needed Marcus's key or his box. Jun had something he signed; the
  hospital acted and wrote down what it did; and when he woke it was
  handed to him as a thing received, for him to read and hold them to.
  His own record then has, in its own order, what was done while he
  could not say.
- **Who is believed turns on who was sent something.** Jun is not his
  wife and Elaine is his mother. Jun has his card, signed by his key;
  Elaine has nothing he signed. The scene does not say that is fair. It
  is what the papers show.

What it leaves open:

- **Whose key it is.** The hospital met Marcus's key, and Jun's, as keys
  it had never seen. Whether the card is his rests on that; see "How a
  key gets known", above.
- **Getting better.** The finding says "looked at again in three
  months". If Agnes can decide again, something has to say so with the
  same weight as the finding, and Petra's holding has to stop. The scene
  writes the review date on the `held-for` row and nothing reads it.
- **A clear day.** Capacity comes and goes, and is judged decision by
  decision. Her record has one line drawn across it.
- **Taking the finding in.** It reached Agnes's box because someone at
  her computer took it in. Had Dorian been that someone, he need not
  have.

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
- **An adult with no one at all.** Agnes has a daughter and Marcus a
  partner. Someone with neither, and nothing said beforehand, is the
  case a court's deputy or a public guardian is for, and is not here.
- **Anything real.** The names, dates and care are invented, and the
  rules about what a minor may consent to differ by place.
