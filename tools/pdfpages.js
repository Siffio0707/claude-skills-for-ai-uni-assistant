// pdfpages: one PNG per page of a PDF, plus the text of each page, using PDFKit (built into macOS).
// Usage: osascript -l JavaScript pdfpages.js <input.pdf> <folder for the images>
// Writes page-01.png, page-02.png ... into the folder (replacing images with the same name)
// and prints JSON: {"pages": ["text of page 1", ...]}. Used by make_digest.py for the page check.
ObjC.import('AppKit');
ObjC.import('Quartz');

function run(argv) {
    if (argv.length !== 2) return JSON.stringify({error: 'usage: pdfpages.js <input.pdf> <folder>'});
    var doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
    if (doc.isNil()) return JSON.stringify({error: 'cannot open PDF'});
    var texts = [];
    for (var i = 0; i < Number(doc.pageCount); i++) {
        var page = doc.pageAtIndex(i);
        texts.push(ObjC.unwrap(page.string) || '');
        var box = page.boundsForBox(0);
        var image = page.thumbnailOfSizeForBox($.NSMakeSize(box.size.width * 1.5, box.size.height * 1.5), 0);
        var rep = $.NSBitmapImageRep.imageRepWithData(image.TIFFRepresentation);
        var png = rep.representationUsingTypeProperties(4, $({})); // 4 = PNG
        var name = argv[1] + '/page-' + ('0' + (i + 1)).slice(-2) + '.png';
        if (!png.writeToFileAtomically(name, true)) return JSON.stringify({error: 'cannot write ' + name});
    }
    return JSON.stringify({pages: texts});
}
