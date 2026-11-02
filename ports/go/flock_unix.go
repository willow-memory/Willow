//go:build !windows
// +build !windows

package main

import (
	"os"
	"syscall"
)

// posix says a file's mode is read, as kernel.py reads it where os.name is "posix".
const posix = true

// lockFile takes the lock kernel.py takes: a blocking exclusive flock on the
// record, so this port and kernel.py keep out of each other's way on one box.
func lockFile(f *os.File) error { return syscall.Flock(int(f.Fd()), syscall.LOCK_EX) }
