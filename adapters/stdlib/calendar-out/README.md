<!-- willow-addon
section: Ways to use it
line: Dates coming up as an .ics file your calendar app can subscribe to.
source: new
added: 2026-10-29
writes: to
network: none
tags: no-install, offline, writes-output, interface
-->
# calendar-out

The dates in your files, in your calendar.

[coming-up](../coming-up/) finds the dates your files hold in the next few
days: a renewal, a deadline, an appointment, a birthday. This writes them as an
iCalendar file that any calendar app can import or subscribe to.

    python adapters/stdlib/calendar-out/calendar_out.py --box DIR --to FILE [--days N]
    wrote FILE: 7 events, 2026-10-24 to 2026-11-23

Each date is an all-day event. Its title is the line it was found on and its
description says where (a file and line), so you can go back to it.

    BEGIN:VEVENT
    UID:4f2a0c1e9b7d...@willow
    DTSTAMP:20261024T000000Z
    DTSTART;VALUE=DATE:20261030
    DTEND;VALUE=DATE:20261031
    SUMMARY:Your cover ends on 31/10/2026 unless renewed
    DESCRIPTION:From work/insurance.txt:4
    END:VEVENT

The window is the next 30 days unless `--days` says. A date that repeats (a
birthday, a yearly renewal) is one event on each repeat in the window. The UID
is made from the date, the place and the line, so importing the file again
updates an event and doesn't double it, and the stamp is the day it was run, so
the same folder on the same day gives the same bytes. Lines are folded at 75
bytes, never inside a character, and text is escaped as the standard asks.

A date found in a calendar file (an .ics, or a mirror of one) is not written
again, since it is already in a calendar. A title is the line as it was found,
so a date inside a web page or a chat export can carry some of its markup; the
description points at the file so you can see.

To subscribe, put FILE where your calendar app can fetch it. Nothing here
serves it or sends it anywhere. A folder with nothing dated in the window
writes nothing. FILE is written once, readable only by you, never over a file
that exists, and your folder is only read.

Exit codes, the kernel's: 0 written; 42 nothing dated in the window, nothing
written; 2 refused.

**Uses:** the coming-up add-on's dates.

**Never:** sends or serves anything, changes your files, or writes anywhere but FILE.
