#!/bin/bash
# Builds the Word and PDF versions of the morning digest. No arguments.
# For every "morning-digest/YYYY-MM-DD Morning Digest.md" whose .docx or .pdf is
# missing or older than the .md, writes both next to it. Touches nothing else.
cd "$(dirname "$0")/../.." || exit 1
exec _system/venv/bin/python -u _system/tools/make_digest.py
