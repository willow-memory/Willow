`ci`: a deps gate is held, not reinstalled, on a pull request whose change
didn't touch what it rests on: each deps verdict carries a key, the SHA-256
of the add-on's folder, kernel.py, ci.py, the guard, its pins and the
Python, and the deps job fetches main's last record, holding a gate whose
key has a satisfied verdict there. A push to main holds nothing
