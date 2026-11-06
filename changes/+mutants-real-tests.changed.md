`advisories`, `lesson-time`: two tests of behaviour a person sees, kept from
#291 without its rewrites: a lockfile sitting directly in node_modules/ is
skipped (parts[:-2] would let it through), and --period 1000 is refused at
the range's top edge. accepted.json stays as it was: its entries for these
two are still harmless, and still survive
