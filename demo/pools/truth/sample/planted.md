# The pools study: what the runs said

Made by demo/pools/truth/truth.py from 200 rows: 9 steps on 20 piles, by rules 167403c1a057. Nothing here is typed by hand; each claim names the rows it stands on.

## What could not be trusted

- No step printed other than alone without a bridge to it.
- 0 step runs were refused, timed out or breached the guard; they are neither silence nor firing.
- 0 steps print differently run alone twice, so no stack is held to them.

## Pairs

26 pairs fired together on at least the rules' piles; 3 held at the false discovery rate, 3 acting on the same places, 0 sharing only files.

- `a` and `b`: acts on the same thing; both fired on 10 of 20 piles, p = 5.41e-06, places 0.6667, files 0.6667 (20 rows: 0e616750e592, 11b34afae15b, 1f06a765802d, 2a4dcbb6016e, 7e6ba4248032, a3eb76cc7f91, and 14 more, all in the result)
- `c` and `d`: acts on the same thing; both fired on 10 of 20 piles, p = 5.41e-06, places 1.0, files 1.0 (20 rows: 366e39601341, 45593c344f6d, 5b6ffef348fa, 5f97b2592f70, 69fb924fdcec, 789128abb7fb, and 14 more, all in the result)
- `r` and `t`: acts on the same thing; both fired on 10 of 20 piles, p = 5.41e-06, places 0.6, files 0.6 (20 rows: 44e40c260188, 6d0ddebbdcf5, 6f3ea81bd459, 76fd37037506, 846dadb7095a, 9c4c1a4ec2e3, and 14 more, all in the result)

## Duplicates

- `c` and `d`: the same places on all 10 piles both fired, the least 1.0 (20 rows: 366e39601341, 45593c344f6d, 5b6ffef348fa, 5f97b2592f70, 69fb924fdcec, 789128abb7fb, and 14 more, all in the result)

## Never fired, on piles it applies to

- None.

## Had no pile it applies to

- None.

## Gaps: kinds of file no add-on named

- `.zzz`, in 2 piles; ideas whose line names it: zz-reader

## Sections the runs disagree with

- None.

## The neighbours each card should list

- `a`: b
- `b`: a
- `c`: d
- `d`: c
- `r`: t
- `t`: r

No partner found for 3 steps; their cards keep what they say.
