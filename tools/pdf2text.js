// pdf2text: text copy of a PDF using PDFKit (text layer) and Vision (OCR), both built into macOS.
// Usage: osascript -l JavaScript pdf2text.js <input.pdf> <output.txt>
// Every page is written under a "=== Page N ===" marker. Each page is also OCR'd;
// if OCR finds clearly more text than the text layer (scans, screenshots inside
// slides), the OCR text is added under "[OCR]". The printed line is a summary:
// pages=<n> textlayer=<n> ocr_only=<list> ocr_added=<list> empty=<list>
// (pdf2text.swift is the same logic in Swift; it is unused because the Swift
// toolchain on this Mac does not compile.)
ObjC.import('Quartz');
ObjC.import('Vision');

function ocr(page) {
    var box = page.boundsForBox(1);
    var img = page.thumbnailOfSizeForBox($.NSMakeSize(box.size.width * 2, box.size.height * 2), 1);
    var req = $.VNRecognizeTextRequest.alloc.init;
    req.recognitionLevel = 0; // accurate
    req.usesLanguageCorrection = true;
    req.recognitionLanguages = $(['en-US', 'es-ES']);
    var handler = $.VNImageRequestHandler.alloc.initWithDataOptions(img.TIFFRepresentation, $.NSDictionary.dictionary);
    if (!handler.performRequestsError($.NSArray.arrayWithObject(req), null)) return '';
    var res = req.results;
    var lines = [];
    for (var i = 0; i < res.count; i++) {
        var cands = res.objectAtIndex(i).topCandidates(1);
        if (cands.count > 0) lines.push(ObjC.unwrap(cands.objectAtIndex(0).string));
    }
    return lines.join('\n');
}

function letters(s) {
    var m = s.match(/[\p{L}\p{N}]/gu);
    return m ? m.length : 0;
}

function list(a) { return a.length ? a.join(',') : '-'; }

function run(argv) {
    if (argv.length !== 2) return 'usage: pdf2text.js <input.pdf> <output.txt>';
    var doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
    if (doc.isNil()) return 'ERROR cannot open PDF';
    var n = Number(doc.pageCount);
    var out = [];
    var textLayer = 0, ocrOnly = [], ocrAdded = [], empty = [];
    for (var i = 0; i < n; i++) {
        var page = doc.pageAtIndex(i);
        var layer = (ObjC.unwrap(page.string) || '').trim();
        var seen = ocr(page).trim();
        var nLayer = letters(layer), nSeen = letters(seen);
        out.push('=== Page ' + (i + 1) + ' ===');
        if (nLayer >= 20) {
            textLayer++;
            out.push(layer);
            if (nSeen > nLayer * 1.5 + 100) {
                ocrAdded.push(i + 1);
                out.push('', '[OCR]', seen);
            }
        } else if (nSeen > 0) {
            ocrOnly.push(i + 1);
            if (nLayer > 0) out.push(layer);
            out.push('[OCR]', seen);
        } else if (nLayer > 0) {
            out.push(layer);
        } else {
            empty.push(i + 1);
        }
        out.push('');
    }
    var ok = $(out.join('\n')).writeToFileAtomicallyEncodingError(argv[1], true, $.NSUTF8StringEncoding, null);
    if (!ok) return 'ERROR cannot write output';
    return 'pages=' + n + ' textlayer=' + textLayer + ' ocr_only=' + list(ocrOnly) +
        ' ocr_added=' + list(ocrAdded) + ' empty=' + list(empty);
}
