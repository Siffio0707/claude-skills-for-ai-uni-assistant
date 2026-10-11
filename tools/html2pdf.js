// html2pdf: A4 PDF from one or more HTML files, using the text engine and PDFKit built into macOS.
// Usage: osascript -l JavaScript html2pdf.js <output.pdf> <footer text> <part1.html> [<part2.html> ...]
// Each part starts on a new page. No app opens. Only simple HTML survives: headings,
// paragraphs, bold, italic, colours. Lists and tables do not, so make_digest.py
// writes those as plain paragraphs.
//
// Pages are filled here, one paragraph at a time, and each page is drawn on its own,
// so nothing is ever cut at a page edge, repeated on the next page or hidden in a margin.
// A paragraph is never split, unless it is longer than a whole page (then it is cut at a
// word). A heading is never left as the last thing on a page. To know what is a heading,
// each part may have a "<part>.kinds" file with one block kind per line (h2, h3, p, li ...).
// The printed line is "pages=<n> forced_splits=<n>" or an ERROR.
ObjC.import('AppKit');
ObjC.import('Quartz');

var W = 595, H = 842, MARGIN = 62; // A4 in points
var TEXT_W = W - 2 * MARGIN, TEXT_H = H - 2 * MARGIN;
var HEADING = {h1: 1, h2: 1, h2n: 1, h3: 1, h4: 1, h5: 1, gap: 1}; // gap: the spacer line above a band

function textView(str, height) {
    var view = $.NSTextView.alloc.initWithFrame($.NSMakeRect(0, 0, TEXT_W, height));
    view.verticallyResizable = false;
    view.horizontallyResizable = false;
    view.textContainer.lineFragmentPadding = 0;
    view.textContainer.containerSize = $.NSMakeSize(TEXT_W, 1.0e7);
    view.textStorage.setAttributedString(str);
    view.layoutManager.ensureLayoutForTextContainer(view.textContainer);
    return view;
}

function piece(str, from, to) {
    var text = ObjC.unwrap(str.string);
    while (to > from && text.charAt(to - 1) === '\n') to--; // a last line break would count as an empty line
    return str.attributedSubstringFromRange($.NSMakeRange(from, to - from));
}

function fits(str, from, to) {
    var view = textView(piece(str, from, to), TEXT_H);
    return view.layoutManager.usedRectForTextContainer(view.textContainer).size.height <= TEXT_H;
}

// Character ranges [from, to], one per page, and the number of over-long paragraphs that had to be cut.
function fill(str, kinds) {
    var text = ObjC.unwrap(str.string), n = text.length;
    var paras = [], at = 0;
    while (at < n) {
        var end = text.indexOf('\n', at);
        end = end < 0 ? n : end + 1;
        paras.push([at, end]);
        at = end;
    }
    if (kinds.length !== paras.length) kinds = []; // cannot tell headings apart: fill without that rule
    var pages = [], forced = 0, i = 0, start = paras.length ? paras[0][0] : 0;
    while (i < paras.length) {
        var j = i + 1;
        if (!fits(str, start, paras[i][1])) { // one paragraph longer than a page: cut it at a word
            var spaces = [];
            for (var c = start + 1; c < paras[i][1]; c++) if (text.charAt(c) === ' ') spaces.push(c);
            var lo = 0, hi = spaces.length - 1, best = -1;
            while (lo <= hi) {
                var mid = (lo + hi) >> 1;
                if (fits(str, start, spaces[mid])) { best = mid; lo = mid + 1; } else { hi = mid - 1; }
            }
            if (best < 0) return null;
            pages.push([start, spaces[best]]);
            start = spaces[best] + 1;
            forced++;
            continue;
        }
        while (j < paras.length && fits(str, start, paras[j][1])) j++;
        if (j < paras.length) { // more follows: do not leave a heading (or a heading and its note) at the bottom
            for (var k = i + 1; k < j; k++) { // closing notes that would run over: start them on the next page, if they fit on one
                if (kinds[k] !== 'h2n') continue;
                var notes = kinds[k - 1] === 'gap' && k - 1 > i ? k - 1 : k;
                if (fits(str, paras[notes][0], paras[paras.length - 1][1])) j = notes;
                break;
            }
            var moved = true;
            while (moved && j - 1 > i) {
                moved = false;
                var last = kinds[j - 1], before = kinds[j - 2];
                if (HEADING[last]) { j -= 1; moved = true; }
                else if ((last === 'warn' || last === 'preview') && HEADING[before] && j - 2 > i) { j -= 2; moved = true; }
            }
        }
        pages.push([start, paras[j - 1][1]]);
        i = j;
        if (i < paras.length) start = paras[i][0];
    }
    return {pages: pages, forced: forced};
}

function footer(text) {
    var safe = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    var markup = '<p style="text-align:center;font-family:\'Helvetica Neue\';font-size:8.5pt;color:#666666">' + safe + '</p>';
    return $.NSAttributedString.alloc.initWithHTMLOptionsDocumentAttributes(
        $(markup).dataUsingEncoding(4), $({CharacterEncoding: 4}), null);
}

function draw(body, foot) {
    var page = $.NSView.alloc.initWithFrame($.NSMakeRect(0, 0, W, H));
    var main = textView(body, TEXT_H);
    main.setFrameOrigin($.NSMakePoint(MARGIN, MARGIN));
    page.addSubview(main);
    var line = textView(foot, 12);
    line.setFrameOrigin($.NSMakePoint(MARGIN, 30));
    page.addSubview(line);
    return page.dataWithPDFInsideRect($.NSMakeRect(0, 0, W, H));
}

function run(argv) {
    if (argv.length < 3) return 'usage: html2pdf.js <output.pdf> <footer text> <part1.html> [<part2.html> ...]';
    var bodies = [], forced = 0;
    for (var i = 2; i < argv.length; i++) {
        var data = $.NSData.dataWithContentsOfFile(argv[i]);
        if (data.isNil()) return 'ERROR cannot read ' + argv[i];
        var str = $.NSAttributedString.alloc.initWithHTMLOptionsDocumentAttributes(data, $({CharacterEncoding: 4}), null);
        if (str.isNil()) return 'ERROR cannot read HTML in ' + argv[i];
        var listed = $.NSString.stringWithContentsOfFileEncodingError(argv[i] + '.kinds', 4, null);
        var kinds = listed.isNil() ? [] : ObjC.unwrap(listed).split('\n').filter(function (k) { return k; });
        var plan = fill(str, kinds);
        if (!plan) return 'ERROR a single word does not fit on a page in ' + argv[i];
        forced += plan.forced;
        plan.pages.forEach(function (r) { bodies.push(piece(str, r[0], r[1])); });
    }
    if (!bodies.length) return 'ERROR no pages';
    var out = $.PDFDocument.alloc.init;
    for (var p = 0; p < bodies.length; p++) {
        var one = $.PDFDocument.alloc.initWithData(draw(bodies[p], footer(argv[1] + '  ·  page ' + (p + 1) + ' of ' + bodies.length)));
        if (one.isNil()) return 'ERROR cannot draw page ' + (p + 1);
        out.insertPageAtIndex(one.pageAtIndex(0), out.pageCount);
    }
    if (!out.writeToFile(argv[0])) return 'ERROR cannot write ' + argv[0];
    return 'pages=' + bodies.length + ' forced_splits=' + forced;
}
