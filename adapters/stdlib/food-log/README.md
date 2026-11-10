<!-- willow-addon
section: Keeping track
line: What you ate, from your notes, by day.
source: new
added: 2026-11-06
version: 0.1.0
writes: nothing
network: none
role: page
uses: habits, log-kit
-->
# food-log

What you ate, from your notes, by day.

    python adapters/stdlib/food-log/food_log.py --box DIR [--by day|week|month]

Every line of your files that names a meal, or says you ate, under its day,
with the meal it names and where it is:

    2026-03-02
      breakfast  diary/march.md:2  Breakfast: porridge and honey.
      lunch      diary/march.md:3  Lunch was leek soup at Ana's.
    2026-03-03
      dinner     diary/march.md:7  Supper: the rest of the soup.
                 diary/march.md:8  Ate an apple on the bus.
    2 days, 4 lines

**A meal** is breakfast, brunch, lunch, dinner (or supper) or a snack, the
first the line names, its plural too; a line that says only "ate", "eaten" or
"eating" is listed with no meal. **A line's day** is the latest date it says,
else the nearest date written above it in its file, else the date its file is
named for; a line no day reaches is not listed.

**Nothing is counted, scored or judged**: these are lines that name a meal,
put in order. A school newsletter's "breakfast club" names one too, so a
folder holding mail lists it.

**It is a spec**, not a program: the meals and the words above, given to
[log-kit](../log-kit/), the engine the logs share, which reads the lines and
puts them in order.

**Exit codes:** 0 lines found; 42 none; 2 refused (a bad command line, not a
box).

**Never:** writes anything, or goes online.
