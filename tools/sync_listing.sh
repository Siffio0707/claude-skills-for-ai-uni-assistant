#!/bin/bash
# Read-only listing for the canvas-sync skill's download checks. No arguments.
# Prints every file in _inbox with its size in bytes and its `file -b` type,
# Writes nothing.
cd "$(dirname "$0")/../.." || exit 1

section() { printf '\n=== %s ===\n' "$1"; }

section "_inbox (path, bytes, type)"
find _inbox -type f ! -name '.DS_Store' -print0 2>/dev/null | sort -z | while IFS= read -r -d '' f; do
  printf '%s\t%s bytes\t%s\n' "$f" "$(stat -f %z "$f")" "$(file -b "$f")"
done

