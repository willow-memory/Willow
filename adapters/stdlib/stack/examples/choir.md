# a community choir's secretary

The committee's minutes, the weekly register, the score library and the
volunteers' hours, kept as plain notes in one folder. Run it the night before
rehearsal:

    python adapters/stdlib/stack/stack.py --box DIR --stack adapters/stdlib/stack/examples/choir.md

## before Thursday
- minutes -- --box {box} --open
- coming-up -- --box {box} --days 30

## the register and the library
- attendance -- --box {box}
- lending -- --box {box}

## who gave their time
- hours -- --box {box}
