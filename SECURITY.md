# Security

Willow's whole job is to be trusted with someone's own files, so a way around
any of its promises is a security problem, and is welcome.

## What counts

- an approval accepted without the person's key, or a forged one served as
  approved;
- a past row of the record changed, removed or reordered without `verify`
  saying so;
- the key read, copied or printed by anything but the kernel's own `seal`
  and `verify`;
- an original file changed, when the pile is only ever read;
- an add-on going online, writing outside what its card says, or writing the
  record except through the kernel, without the guard catching it;
- anything that sends a person's files, questions or answers anywhere.

A wrong answer, a missed passage or a slow search is a bug, not a security
problem: open an issue for those.

## How to report one

Privately, through GitHub: the repository's **Security** tab, then **Report
a vulnerability**. Please don't open a public issue for it.

Say what you did, what happened, and what you expected, with the smallest
folder and commands that show it. Leave out anything from your own files.

You'll get a reply within a week. Once it's fixed, the fix says what it
fixed, and who found it if they'd like to be named.

## What's supported

The `main` branch. There are no releases yet, so a fix lands there.
