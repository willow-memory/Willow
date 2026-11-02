<!-- willow-addon
section: Reading more kinds of files
line: When and where each photo was taken, as dated lines.
source: new
added: 2026-10-29
needs: Pillow; MIT-CMU
floor: Pillow 11.0.0; the 2020 rule names 8.0.1, which has no wheel for Python 3.13 and won't build there, and 11.0.0 is the first release with one
writes: to
network: none
-->
# photos

When and where each photo was taken, read from the EXIF a camera or phone
writes into it, into a mirror folder the kernel can search.

    pip install -r adapters/deps/photos/requirements.txt
    python adapters/deps/photos/photos.py mirror --from FOLDER --to MIRROR
    python kernel.py init --box BOX --pile MIRROR --key KEY

Each photo (.jpg, .jpeg, .tif, .tiff, .png, .webp) becomes
`MIRROR/<same path>.txt`, one passage:

    2024-07-14 09:32:10 holidays/eiffel.jpg
    at 48.858370 N, 2.294480 E
    camera Apple iPhone 12

The date and time come first, as the camera wrote them, so the kernel reads
the passage as dated; then where, when it has GPS; then the camera, when it
names one. "when was I in paris" needs the place's name, which a photo
doesn't hold: a folder named for it does, and the path is on the first line.

**The reader contract** (shared with every file reader): hidden files and
folders are skipped; nothing is written inside FOLDER and no original
changes; MIRROR inside FOLDER, or the other way round, is refused; the same
photo always gives the same bytes; a file Pillow can't open is skipped and
counted, never a crash, and so is a photo with neither a date nor a place.

**Can't:** guess a time zone (EXIF often has none, so the time is the
camera's clock), name a place from its coordinates (that would need a map,
or going online), or read HEIC, which Pillow doesn't open by itself.

On the 454 pictures in Pillow's own test images it wrote 32 files, from a
2003 Canon PowerShot to a 2024 Pixel 6 with its position, and skipped 16
damaged ones; the same bytes at the pins and at the floor. willow's four demo
folders hold no photo.

**Without Pillow** it refuses and names the install: exit 2, never a quiet
skip.

**Uses:** the kernel's exit codes: 0 wrote at least one file; 42 nothing
readable; 2 refused.

**Never:** writes inside your folder, changes an original, or goes online.
