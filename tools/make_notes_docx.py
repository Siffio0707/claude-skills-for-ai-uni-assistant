"""Build a Word (.docx) study-notes document from a Markdown source.

Usage: _system/venv/bin/python _system/tools/make_notes_docx.py "<in.md>" "<out.docx>" "<footer title>"

The .md is the only source; the
.docx (python-docx 1.2.0, already installed in _system/venv) is derived from it and is
replaced when the .md changes. Reads the .md, writes the .docx, touches nothing else.

Markdown subset (one block per line):
  # Title (once)            ## Part or session heading (new page)   ### Section   #### Sub-section
  - bullet  (two spaces of indent per level)    1. numbered point    > callout box
  | a | b | table rows, with a |---| separator after the header row      ---  separator (ignored)
  anything else: a paragraph
Inline: **bold**  *italic*  [src: file, p. 4] (grey)  (verify: OCR) (orange)  (web: URL) (blue)
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Helvetica Neue"
NAVY, GREY, ORANGE, BLUE, PALE, HEADFILL = "1F3A5F", "666666", "9A3B00", "1F5FA8", "FBEFE3", "DCE6F2"
INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|\[src: [^\]]+\]|\(verify: OCR\)|\(web: [^)\s]+\))")


def spans(text):
    out = []
    for piece in INLINE.split(text):
        if not piece:
            continue
        if piece.startswith("**") and piece.endswith("**") and len(piece) > 4:
            out.append(("b", piece[2:-2]))
        elif piece.startswith("[src: "):
            out.append(("cite", "(" + piece[6:-1] + ")"))
        elif piece == "(verify: OCR)":
            out.append(("ocr", piece))
        elif piece.startswith("(web: "):
            out.append(("web", piece))
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            out.append(("i", piece[1:-1]))
        else:
            out.append(("", piece))
    return out


def write(par, text, size=10.5, bold=False, italic=False, colour=None):
    for style, piece in spans(text):
        # bold and italic can be nested one level: **...*x*...** is not supported; keep it simple
        run = par.add_run(piece)
        run.font.name, run.font.size = FONT, Pt(size)
        run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        run.font.bold = bold or style == "b"
        run.font.italic = italic or style in ("i", "cite")
        tint = {"cite": GREY, "ocr": ORANGE, "web": BLUE}.get(style, colour)
        if tint:
            run.font.color.rgb = RGBColor.from_string(tint)


def shade(el, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    el.append(shd)


def cell_margins(table, top=40, bottom=40, left=70, right=70):
    pr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for k, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{k}")
        e.set(qn("w:w"), str(v))
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    pr.append(mar)


def add_table(doc, rows):
    header, body = rows[0], rows[1:]
    ncol = len(header)
    t = doc.add_table(rows=1, cols=ncol)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    tblPr = t._tbl.tblPr
    for old in tblPr.findall(qn("w:tblW")):
        tblPr.remove(old)
    w = OxmlElement("w:tblW")
    w.set(qn("w:w"), "5000")
    w.set(qn("w:type"), "pct")
    tblPr.append(w)
    cell_margins(t)
    total = 9638  # 17 cm text width in twentieths of a point
    weights = []
    for i in range(ncol):
        lens = [len(re.sub(r"[*\[\]]", "", (r[i] if i < len(r) else ""))) for r in rows]
        avg = sum(lens) / len(lens)
        weights.append(min(max(avg, 8), 70) ** 0.8)
    wsum = sum(weights)
    widths = [max(int(total * w / wsum), 700) for w in weights]
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    grid = t._tbl.tblGrid
    for gc, wd in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(wd))
    size = 8.5 if ncol >= 5 else 9
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.width = Cm(widths[i] / 567)
        shade(c._tc.get_or_add_tcPr(), HEADFILL)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        write(p, h, size=size, bold=True, colour=NAVY)
    # repeat header row on every page
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    for r in body:
        cells = t.add_row().cells
        trPr = t.rows[-1]._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit")
        cs.set(qn("w:val"), "true")
        trPr.append(cs)
        for i in range(ncol):
            cells[i].width = Cm(widths[i] / 567)
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            write(p, r[i] if i < len(r) else "", size=size)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def parse(lines):
    blocks, i = [], 0
    while i < len(lines):
        s = lines[i].rstrip()
        if not s.strip() or s.strip() == "---":
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            blocks.append(("table", rows))
            continue
        for prefix, kind in (("#### ", "h4"), ("### ", "h3"), ("## ", "h2"), ("# ", "h1"), ("> ", "callout")):
            if s.startswith(prefix):
                blocks.append((kind, s[len(prefix):].strip()))
                break
        else:
            m = re.match(r"^(\s*)- (.*)$", s)
            n = re.match(r"^(\d+)\. (.*)$", s)
            if m:
                blocks.append(("li", (len(m.group(1)) // 2, m.group(2))))
            elif n:
                blocks.append(("num", (n.group(1), n.group(2))))
            else:
                blocks.append(("p", s.strip()))
        i += 1
    return blocks


def build(src, dst, title):
    blocks = parse(src.read_text(encoding="utf-8").splitlines())
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = FONT, Pt(10.5)
    for name, size, colour in (("Heading 1", 18, NAVY), ("Heading 2", 15, "FFFFFF"), ("Heading 3", 12, NAVY), ("Heading 4", 11, "222222")):
        st = doc.styles[name]
        st.font.name, st.font.size, st.font.bold = FONT, Pt(size), True
        st.font.color.rgb = RGBColor.from_string(colour)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        st.element.rPr.rFonts.set(qn("w:ascii"), FONT)
        st.element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
    foot = sec.footer.paragraphs[0]
    foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    write(foot, title + "  ·  page ", size=8.5, colour=GREY)
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    foot._p.append(field)

    first_h2 = True
    for kind, val in blocks:
        if kind == "table":
            add_table(doc, val)
            continue
        if kind == "h1":
            p = doc.add_paragraph(style="Heading 1")
            p.paragraph_format.space_after = Pt(8)
            write(p, val, size=18, bold=True, colour=NAVY)
        elif kind == "h2":
            p = doc.add_paragraph(style="Heading 2")
            pf = p.paragraph_format
            pf.page_break_before = not first_h2
            first_h2 = False
            pf.space_before, pf.space_after, pf.keep_with_next = Pt(0), Pt(8), True
            shade(p._p.get_or_add_pPr(), NAVY)
            write(p, " " + val, size=15, bold=True, colour="FFFFFF")
        elif kind == "h3":
            p = doc.add_paragraph(style="Heading 3")
            pf = p.paragraph_format
            pf.space_before, pf.space_after, pf.keep_with_next = Pt(14), Pt(4), True
            write(p, val, size=12, bold=True, colour=NAVY)
        elif kind == "h4":
            p = doc.add_paragraph(style="Heading 4")
            pf = p.paragraph_format
            pf.space_before, pf.space_after, pf.keep_with_next = Pt(10), Pt(3), True
            write(p, val, size=11, bold=True, colour="222222")
        elif kind == "callout":
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.space_before, pf.space_after, pf.left_indent, pf.right_indent = Pt(4), Pt(6), Cm(0.2), Cm(0.2)
            shade(p._p.get_or_add_pPr(), PALE)
            write(p, val, size=10, colour="3A2A1A")
        elif kind == "li":
            level, text = val
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent = Cm(0.9 + 0.8 * level)
            pf.first_line_indent = Cm(-0.45)
            pf.space_after = Pt(3)
            write(p, ("•" if level == 0 else "–") + "\u00a0\u00a0" + text)
        elif kind == "num":
            n, text = val
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent, pf.first_line_indent, pf.space_after = Cm(0.9), Cm(-0.6), Pt(3)
            write(p, f"{n}.\u00a0\u00a0{text}")
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            write(p, val)
    doc.save(dst)
    return len(blocks)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    n = build(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
    print(f"blocks={n} -> {sys.argv[2]}")
