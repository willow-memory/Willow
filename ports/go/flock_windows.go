//go:build windows
// +build windows

package main

import "os"

// posix says a file's mode is not read, as kernel.py reads none on Windows.
const posix = false

// lockFile takes no lock: there is no flock, and kernel.py's Windows lock is
// its own (msvcrt), which this port doesn't share.
func lockFile(f *os.File) error { return nil }
