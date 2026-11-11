//! Two counts over /pile, every file under it: lines naming Johnson (any
//! case), and lines dated March or April 2026. What
//! `grep -rhi johnson; grep -rh '2026-0[34]'` counts, the same everywhere.
use std::fs;
use std::path::Path;

fn walk(dir: &Path, johnson: &mut u64, spring: &mut u64) {
    let mut names: Vec<_> = match fs::read_dir(dir) {
        Ok(it) => it.filter_map(|e| e.ok()).map(|e| e.path()).collect(),
        Err(_) => return,
    };
    names.sort();
    for p in names {
        if p.is_dir() {
            walk(&p, johnson, spring);
        } else if let Ok(bytes) = fs::read(&p) {
            for line in bytes.split(|b| *b == b'\n') {
                let low = line.to_ascii_lowercase();
                if low.windows(7).any(|w| w == b"johnson") {
                    *johnson += 1;
                }
                if line.windows(7).any(|w| w == b"2026-03" || w == b"2026-04") {
                    *spring += 1;
                }
            }
        }
    }
}

fn main() {
    let (mut johnson, mut spring) = (0, 0);
    walk(Path::new("/pile"), &mut johnson, &mut spring);
    println!("{johnson}\n{spring}");
}
