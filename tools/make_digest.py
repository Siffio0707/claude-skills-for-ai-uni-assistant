"""Build the Word and PDF versions of the morning digest, and check the PDF's pages.

Usage: _system/tools/make_digest.sh   (no arguments)

For every "morning-digest/YYYY-MM-DD Morning Digest.md" whose .docx or .pdf is
missing or older than the .md, writes both next to it. The .md is the only source;
the .docx (python-docx) and the .pdf (html2pdf.js, built into macOS) are derived
from it and are replaced when the .md changes.

Page check: after the PDF is written, every page is rendered as an image into
morning-digest/_check/page-NN.png (replacing the images of the previous build) and
the text of the pages is compared with the .md: every block must be on exactly one
page, whole. The result is the "page check:" line; anything else than
"repeated=0 split=0 missing=0 orphan=0" is a failure.

The .md uses a small subset of Markdown, one block per line:
  # Title                 once, first line
  ## Class heading        one per class; the second and later classes start on a new page
  ## Notes                the closing notes; follows the last class without a page break
  Preview: one sentence   right under a class heading (the morning brief reads it)
  ### Section heading     #### Reading title     ##### Part of a reading
  - bullet                1. numbered point      > warning
  anything else           a paragraph (one line each)
Inline: **bold**, *italic*, [src: file, p. 4] (shown as a grey citation) and
(verify: OCR) (shown in orange).
"""
import html
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "_system" / "tools"
FOLDER = ROOT / "morning-digest"
NAME = re.compile(r"^\d{4}-\d{2}-\d{2} Morning Digest\.md$")
FONT = "Helvetica Neue"
NAVY, GREY, ORANGE, PALE, SLATE = "1F3A5F", "666666", "9A3B00", "FBEFE3", "555555"
INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*\*|\[src: [^\]]+\]|\(verify: OCR\))")
BLOCKS = (("##### ", "h5"), ("#### ", "h4"), ("### ", "h3"), ("## ", "h2"), ("# ", "h1"), ("- ", "li"),
          ("> ", "warn"), ("Preview: ", "preview"))


def parse(text: str) -> list:
    """[(kind, text)] for every non-blank line. "## Notes" is kind h2n."""
    blocks = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for prefix, kind in BLOCKS:
            if line.startswith(prefix):
                rest = line[len(prefix):].strip()
                blocks.append(("h2n" if kind == "h2" and rest.lower() == "notes" else kind, rest))
                break
        else:
            m = re.match(r"^(\d+)\. (.+)$", line)
            blocks.append(("num", f"{m.group(1)}.\t{m.group(2)}") if m else ("p", line))
    return blocks


def spans(text: str) -> list:
    """[(style, text)] with style one of '', 'b', 'i', 'cite', 'ocr'."""
    out = []
    for piece in INLINE.split(text):
        if not piece:
            continue
        if piece.startswith("**"):
            out.append(("b", piece[2:-2]))
        elif piece.startswith("[src: "):
            out.append(("cite", "(" + piece[6:-1] + ")"))
        elif piece == "(verify: OCR)":
            out.append(("ocr", piece))
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            out.append(("i", piece[1:-1]))
        else:
            out.append(("", piece))
    return out


def new_page(blocks: list, i: int) -> bool:
    """A class heading starts a new page, except the first one."""
    return blocks[i][0] == "h2" and any(kind == "h2" for kind, _ in blocks[:i])


# ---------- Word ----------

def shade(par, colour: str) -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), colour)
    par._p.get_or_add_pPr().append(shd)


def write(par, text: str, size=10.5, bold=False, italic=False, colour=None, caps=False) -> None:
    for style, piece in spans(text):
        run = par.add_run(piece)
        run.font.name, run.font.size = FONT, Pt(size)
        run.font.bold = bold or style == "b"
        run.font.italic = italic or style in ("i", "cite")
        run.font.all_caps = caps
        tint = {"cite": GREY, "ocr": ORANGE}.get(style, colour)
        if tint:
            run.font.color.rgb = RGBColor.from_string(tint)


def make_docx(blocks: list, dst: Path, title: str) -> None:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(2.2)
    doc.styles["Normal"].font.name, doc.styles["Normal"].font.size = FONT, Pt(10.5)
    foot = sec.footer.paragraphs[0]
    foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    write(foot, title + "  ·  page ", size=8.5, colour=GREY)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    foot._p.append(field)

    for i, (kind, text) in enumerate(blocks):
        par = doc.add_paragraph()
        fmt = par.paragraph_format
        fmt.space_before, fmt.space_after = Pt(0), Pt(5)
        fmt.keep_together = True  # Word, too, never splits a paragraph across pages
        if kind == "h1":
            fmt.space_after = Pt(8)
            write(par, text, size=17, bold=True, colour=NAVY)
        elif kind in ("h2", "h2n"):
            fmt.page_break_before, fmt.space_after, fmt.keep_with_next = new_page(blocks, i), Pt(8), True
            fmt.space_before = Pt(0) if fmt.page_break_before else Pt(16)
            shade(par, NAVY if kind == "h2" else SLATE)
            write(par, text, size=14 if kind == "h2" else 12, bold=True, colour="FFFFFF")
        elif kind == "h3":
            fmt.space_before, fmt.space_after, fmt.keep_with_next = Pt(10), Pt(3), True
            write(par, text, size=11, bold=True, colour=NAVY, caps=True)
        elif kind == "h4":
            fmt.space_before, fmt.space_after, fmt.keep_with_next = Pt(8), Pt(2), True
            write(par, text, size=11.5, bold=True)
        elif kind == "h5":
            fmt.space_before, fmt.space_after, fmt.keep_with_next = Pt(6), Pt(2), True
            write(par, text, size=10.5, bold=True, colour=NAVY)
        elif kind == "preview":
            write(par, text, size=11, italic=True, colour=NAVY)
        elif kind == "warn":
            fmt.keep_with_next = True
            shade(par, PALE)
            write(par, text, colour=ORANGE)
        elif kind in ("li", "num"):
            fmt.left_indent, fmt.first_line_indent, fmt.space_after = Cm(0.9), Cm(-0.6), Pt(3)
            fmt.tab_stops.add_tab_stop(Cm(0.9))
            write(par, ("•\t" + text) if kind == "li" else text)
        else:
            write(par, text)
    doc.save(dst)


# ---------- PDF ----------

CSS = f"""
body{{font-family:"{FONT}";font-size:10.5pt;color:#222;line-height:1.35}}
p{{margin:0 0 5pt 0}}
h1{{font-size:17pt;color:#{NAVY};margin:0 0 8pt 0}}
h2{{font-size:14pt;color:#fff;background:#{NAVY};margin:0 0 8pt 0}}
p.gap{{font-size:5pt;margin:0}}
h2.notes{{font-size:12pt;background:#{SLATE}}}
h3{{font-size:11pt;color:#{NAVY};margin:10pt 0 3pt 0;text-transform:uppercase}}
h4{{font-size:11.5pt;color:#222;margin:8pt 0 2pt 0}}
h5{{font-size:10.5pt;color:#{NAVY};margin:6pt 0 2pt 0}}
p.preview{{font-size:11pt;font-style:italic;color:#{NAVY}}}
p.warn{{color:#{ORANGE};background:#{PALE}}}
p.li{{margin:0 0 3pt 14pt}}
.cite{{color:#{GREY};font-style:italic}}
.ocr{{color:#{ORANGE}}}
"""


def to_html(text: str) -> str:
    wrap = {"b": "<b>{}</b>", "i": "<i>{}</i>", "cite": '<span class="cite">{}</span>',
            "ocr": '<span class="ocr">{}</span>', "": "{}"}
    return "".join(wrap[style].format(html.escape(piece).replace("\t", "&nbsp; ")) for style, piece in spans(text))


def block_html(kind: str, text: str, first: bool) -> str:
    body = to_html(text)
    if kind == "h2":
        gap = '<p class="gap">&nbsp;</p>' if first else ""  # the text engine ignores a top margin on the band
        return f"{gap}<h2>&nbsp;{body}&nbsp;</h2>"
    if kind == "h2n":
        return f'<p class="gap">&nbsp;</p><h2 class="notes">&nbsp;{body}&nbsp;</h2>'
    if kind in ("h1", "h3", "h4", "h5"):
        return f"<{kind}>{body}</{kind}>"
    if kind == "li":
        return f'<p class="li">•&nbsp; {body}</p>'
    if kind == "num":
        return f'<p class="li">{body}</p>'
    return f"<p>{body}</p>" if kind == "p" else f'<p class="{kind}">{body}</p>'


def make_pdf(blocks: list, dst: Path, title: str) -> str:
    parts = [[]]
    for i, (kind, text) in enumerate(blocks):
        if new_page(blocks, i):
            parts.append([])
        parts[-1].append((kind, block_html(kind, text, first=kind == "h2" and not new_page(blocks, i))))
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for n, part in enumerate(parts):
            f = Path(tmp) / f"part-{n:02d}.html"
            f.write_text(f'<html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
                         + "\n".join(markup for _, markup in part) + "</body></html>", encoding="utf-8")
            Path(str(f) + ".kinds").write_text(  # one kind per paragraph, so the spacer line counts too
                "\n".join("gap\n" + kind if markup.startswith('<p class="gap">') else kind for kind, markup in part),
                encoding="utf-8")
            files.append(str(f))
        made = Path(tmp) / "digest.pdf"
        r = subprocess.run(["/usr/bin/osascript", "-l", "JavaScript", str(TOOLS / "html2pdf.js"), str(made), title]
                           + files, capture_output=True, text=True, timeout=600)
        result = (r.stdout.strip() or r.stderr.strip() or "ERROR no output").splitlines()[-1]
        if result.startswith("pages="):
            dst.write_bytes(made.read_bytes())
        return result


# ---------- page check ----------

def flat(s: str) -> str:
    """Text reduced to what survives PDF extraction: no spacing, hyphens or case."""
    s = unicodedata.normalize("NFKC", s).lower()
    return re.sub(r"[\s\-­‐‑•·]", "", s)


def check_pages(blocks: list, pdf: Path, forced: int, title: str) -> tuple:
    """(ok, lines to print). Renders the pages as images and compares their text with the blocks."""
    shots = pdf.parent / "_check"
    shots.mkdir(exist_ok=True)
    r = subprocess.run(["/usr/bin/osascript", "-l", "JavaScript", str(TOOLS / "pdfpages.js"), str(pdf), str(shots)],
                       capture_output=True, text=True, timeout=600)
    try:
        pages = json.loads(r.stdout)["pages"]
    except (ValueError, KeyError):
        return False, [f"PAGE CHECK FAILED: cannot read the pages ({(r.stdout or r.stderr).strip()[:200]})"]
    foot = flat(title)
    texts = [flat(p).replace(foot + f"page{n}of{len(pages)}", "") for n, p in enumerate(pages, 1)]
    wanted = [flat("".join(piece for _, piece in spans(text))) for _, text in blocks]
    joined = "".join(texts)
    repeated, split, missing = [], [], []
    for (kind, text), want in zip(blocks, wanted):
        if len(want) < 40:  # short lines also occur inside sentences; only check that they are there
            if want and want not in joined:
                missing.append(text)
            continue
        expected = sum(other.count(want) for other in wanted)
        found = sum(t.count(want) for t in texts)
        if found > expected:
            repeated.append(text)
        elif found < expected:
            (split if joined.count(want) >= expected else missing).append(text)
    # A heading must never be the last thing on a page: it stays with its first item.
    orphan = []
    heads = {flat(text): text for kind, text in blocks if kind in ("h2", "h3", "h4", "h5") and flat(text)}
    for n, t in enumerate(texts[:-1], 1):
        for key, text in heads.items():
            if t.endswith(key):
                orphan.append(f"page {n}: {text}")
    split_extra = max(0, len(split) - forced)
    ok = not repeated and not missing and not orphan and not split_extra and len(set(split)) <= forced
    lines = [f"page check: pages={len(pages)} | repeated={len(repeated)} split={len(split)} missing={len(missing)} orphan={len(orphan)}"
             + (f" | {forced} paragraph(s) longer than a page were cut at a word" if forced else "")]
    for label, items in (("REPEATED", repeated), ("SPLIT", split), ("MISSING", missing), ("HEADING ENDS PAGE", orphan)):
        lines += [f"  {label}: {item[:90]}" for item in items[:10]]
    lines.append(f"check images: {shots.relative_to(pdf.parent.parent)}/page-01.png to page-{len(pages):02d}.png")
    if not ok:
        lines.insert(0, "PAGE CHECK FAILED")
    return ok, lines


def main() -> int:
    folder = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else FOLDER  # a folder argument is for testing only
    sources = sorted(p for p in folder.glob("*.md") if NAME.match(p.name))
    failed = built = 0
    for src in sources:
        docx, pdf = src.with_suffix(".docx"), src.with_suffix(".pdf")
        if all(f.exists() and f.stat().st_mtime >= src.stat().st_mtime for f in (docx, pdf)):
            continue
        blocks = parse(src.read_text(encoding="utf-8"))
        classes = sum(1 for kind, _ in blocks if kind == "h2")
        title = next((text for kind, text in blocks if kind == "h1"), src.stem)
        ok = False
        try:
            make_docx(blocks, docx, title)
            print(f"built: {docx.name} | {docx.stat().st_size} bytes | classes={classes}", flush=True)
            result = make_pdf(blocks, pdf, title)
            if result.startswith("pages="):
                print(f"built: {pdf.name} | {pdf.stat().st_size} bytes | {result}", flush=True)
                forced = int(result.rsplit("=", 1)[1])
                ok, lines = check_pages(blocks, pdf, forced, title)
                print("\n".join(lines), flush=True)
        except Exception as exc:  # report and continue with the next digest
            result = f"ERROR {type(exc).__name__}: {exc}"
        if ok:
            built += 1
        else:
            print(f"FAILED: {src.name} | {result}", flush=True)
            failed += 1
    print(f"done: {built} built, {failed} failed, {len(sources) - built - failed} already up to date", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
