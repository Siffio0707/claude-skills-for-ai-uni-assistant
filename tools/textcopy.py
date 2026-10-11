"""Read-only reader for a course's text copies in _text/ and its saved Markdown pages.

Used by the morning-digest skill, which runs unattended and cannot count on a
search tool. Files are addressed by the number that `list` prints, so no command
ever needs a file name. Numbers are only valid until files are added: run `list`
first in every session. Writes nothing.

Usage:
  python3 -u _system/tools/textcopy.py list  "<Course folder>"
  python3 -u _system/tools/textcopy.py info  "<Course folder>" <file no>
  python3 -u _system/tools/textcopy.py pages "<Course folder>" <file no> <from> <to>
  python3 -u _system/tools/textcopy.py find  "<Course folder>" "<phrase>" [file no]

list   every text copy under _text/<Course> and every saved Markdown page under
       <Course>/ (announcements, page text), with page counts and which pages are
       empty, OCR only or OCR added.
info   the same line for one file, plus the pages with under 20 letters.
pages  the text of pages (or slides) <from> to <to>, under their markers. Stops at
       about 24,000 characters and says from which page to continue.
find   pages whose text contains the phrase (case and spacing ignored), with an
       excerpt. At most 80 hits.
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COURSES = ("Law Course 2", "Law Course 1", "Course A", "Course C", "Course B", "Law Course 3")
PUBLISHER = re.compile(r"mylab|pearson|mastering", re.I)  # never read (CLAUDE.md)
MARKER = re.compile(r"^=== (Page|Slide) (\d+) ===$", re.M)
LIMIT = 24000


def letters(s: str) -> int:
    return sum(1 for c in s if c.isalnum())


def files(course: str) -> list:
    if course not in COURSES:
        sys.exit(f"unknown course folder: {course!r}. One of: " + ", ".join(COURSES))
    found = sorted(p for p in (ROOT / "_text" / course).rglob("*") if p.is_file() and p.name != ".DS_Store")
    found += sorted(p for p in (ROOT / course).rglob("*.md")
                    if "_summaries" not in p.parts and p.name != "course-index.md")
    return [p for p in found if not PUBLISHER.search(p.name)]


def units(path: Path) -> tuple:
    """(kind, [(number, text)]). A file without page markers is one unit."""
    text = path.read_text(encoding="utf-8", errors="replace")
    marks = list(MARKER.finditer(text))
    if not marks:
        return "file", [(1, text)]
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((int(m.group(2)), text[m.end():end].strip("\n")))
    return m.group(1).lower(), out


def describe(path: Path) -> tuple:
    kind, us = units(path)
    empty, ocr_only, ocr_added, short = [], [], [], []
    for n, body in us:
        before, sep, _ = body.partition("\n[OCR]\n") if not body.startswith("[OCR]\n") else ("", "[OCR]", body)
        if letters(body) == 0:
            empty.append(n)
        elif sep and letters(before) < 20:
            ocr_only.append(n)
        elif sep:
            ocr_added.append(n)
        elif letters(body) < 20:
            short.append(n)
    lst = lambda a: ",".join(map(str, a)) if a else "-"
    line = (f"{kind}s={len(us)} empty={lst(empty)} ocr_only={lst(ocr_only)} ocr_added={lst(ocr_added)}"
            if kind != "file" else f"no page markers, {letters(us[0][1])} letters")
    return line, lst(short)


def pick(course: str, number: str) -> Path:
    fs = files(course)
    if not number.isdigit() or not 1 <= int(number) <= len(fs):
        sys.exit(f"file no must be 1 to {len(fs)} (see: list \"{course}\")")
    return fs[int(number) - 1]


def squash(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip().lower()


def main() -> None:
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "list":
        for i, p in enumerate(files(a[1]), 1):
            print(f"[{i}] {p.relative_to(ROOT)} | {describe(p)[0]}", flush=True)
    elif len(a) == 3 and a[0] == "info":
        p = pick(a[1], a[2])
        line, short = describe(p)
        print(f"[{a[2]}] {p.relative_to(ROOT)} | {line} | under 20 letters: {short}", flush=True)
    elif len(a) == 5 and a[0] == "pages" and a[3].isdigit() and a[4].isdigit():
        p = pick(a[1], a[2])
        kind, us = units(p)
        print(f"[{a[2]}] {p.relative_to(ROOT)}", flush=True)
        used = 0
        for n, body in us:
            if not int(a[3]) <= n <= int(a[4]):
                continue
            if used and used + len(body) > LIMIT:
                print(f"--- STOPPED before {kind} {n} (output limit): run again from {n} ---", flush=True)
                break
            print(f"=== {kind.capitalize()} {n} ===\n{body}\n", flush=True)
            used += len(body)
    elif len(a) in (3, 4) and a[0] == "find":
        want = squash(a[2])
        fs = files(a[1])
        chosen = [(int(a[3]), pick(a[1], a[3]))] if len(a) == 4 else list(enumerate(fs, 1))
        hits = 0
        for i, p in chosen:
            kind, us = units(p)
            for n, body in us:
                flat = squash(body)
                at = flat.find(want)
                if at < 0:
                    continue
                hits += 1
                if hits > 80:
                    sys.exit("--- more than 80 hits: use a longer phrase or give a file no ---")
                print(f"[{i}] {p.relative_to(ROOT)} | {kind} {n} | x{flat.count(want)} | "
                      f"...{flat[max(0, at - 70):at + len(want) + 90]}...", flush=True)
        print(f"{hits} page(s) with a hit", flush=True)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
