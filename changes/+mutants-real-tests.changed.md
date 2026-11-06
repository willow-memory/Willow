`advisories`, `lesson-time`: two tests of behaviour a person sees, kept from
#291 without its rewrites: a lockfile sitting directly in node_modules/ is
skipped (parts[:-2] would let it through), and --period 1000 is refused at
the range's top edge. advisories' accepted maxsplit break is now killed, so
its entry leaves accepted.json; lesson-time's still survives, harmless, and
stays
