# -*- coding: utf-8 -*-
"""Lift base64 webfonts out of page <head>s into cacheable /fonts/ files.

THE PROBLEM THIS SOLVES, measured 2026-08-17.

The homepage embedded eight woff2 fonts as data: URIs -- 368 KB of base64 inside
a 552 KB document, all of it in the <head>. `</head>` sat 85% of the way through
the file, so a browser had to download 85% of the page before reaching a single
visible element. Lighthouse mobile: FCP 3.6s, LCP 6.9s, performance 52.

`font-display: swap` was already set on every face and could not help. Swap
governs what happens while a font is FETCHING; these fonts were not being
fetched, they were bytes in the middle of the HTML the parser had to chew
through first. The only fix is to stop shipping them inside the document.

Across the site the waste compounds: 33 pages carried 3,612 KB of embedded
fonts, but there are only EIGHT DISTINCT FONTS -- 3,244 KB (90%) was the same
handful of files re-encoded into page after page. The two logo faces alone were
embedded on all 33.

HOW IT WORKS. Files are content-addressed: the name carries a hash of the font
bytes, so the same face referenced from thirty-three pages resolves to one URL
and is fetched once and cached for every subsequent page. Dedup is a property of
the naming scheme rather than something a human has to maintain.

SAFETY. Idempotent -- a page with no data: fonts is left byte-identical. Every
@font-face keeps its existing descriptors; only the url() changes. A face
without font-display gets `swap` added, because an external font WITHOUT it
blocks text for up to 3s, which would trade one paint problem for another.

Usage:
  python _brand/extract_fonts.py --check          report, change nothing
  python _brand/extract_fonts.py <page> [...]     rewrite the named pages
  python _brand/extract_fonts.py --all            rewrite every page that has them
"""
import base64
import glob
import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
FONT_DIR = os.path.join(SITE, "fonts")

# url(data:font/woff2;base64,....) inside an @font-face src.
DATA_URL = re.compile(
    r"url\(\s*(['\"]?)data:(font/woff2|application/font-woff2|font/woff)"
    r";base64,([A-Za-z0-9+/=\s]+?)\1\s*\)",
    re.I,
)
FACE = re.compile(r"@font-face\s*\{(.*?)\}", re.S)


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-") or "font"


def face_name(block, digest):
    """A readable, stable filename: family-weight-style-hash.woff2."""
    fam = re.search(r"font-family\s*:\s*[\"']?([^;\"'}]+)", block)
    wt = re.search(r"font-weight\s*:\s*([^;}]+)", block)
    st = re.search(r"font-style\s*:\s*([^;}]+)", block)
    parts = [slug(fam.group(1)) if fam else "font"]
    if wt:
        parts.append(slug(wt.group(1)))
    if st and "italic" in st.group(1).lower():
        parts.append("italic")
    parts.append(digest)
    return "-".join(parts) + ".woff2"


def process(path, check=False):
    """Returns (fonts_written, bytes_removed_from_html, [filenames])."""
    src = io.open(path, encoding="utf-8", errors="replace").read()
    if "base64," not in src:
        return 0, 0, []

    written = []
    saved = [0]

    def rewrite_face(match):
        block = match.group(0)

        def rewrite_url(m):
            raw = re.sub(r"\s+", "", m.group(3))
            try:
                data = base64.b64decode(raw)
            except Exception:
                return m.group(0)  # leave anything we cannot decode alone
            digest = hashlib.sha256(data).hexdigest()[:10]
            name = face_name(block, digest)
            if not check:
                if not os.path.isdir(FONT_DIR):
                    os.makedirs(FONT_DIR)
                out = os.path.join(FONT_DIR, name)
                if not os.path.exists(out):
                    with open(out, "wb") as fh:
                        fh.write(data)
            written.append(name)
            saved[0] += len(m.group(0)) - len(name) - 12
            return "url('/fonts/%s')" % name

        new = DATA_URL.sub(rewrite_url, block)
        # An external font with no font-display blocks text for up to 3s. Never
        # introduce that while fixing a paint problem.
        if "font-display" not in new.lower():
            new = new.replace("{", "{font-display:swap;", 1)
        return new

    out_html = FACE.sub(rewrite_face, src)
    if not check and out_html != src:
        io.open(path, "w", encoding="utf-8", newline="").write(out_html)
    return len(written), saved[0], written


def pages():
    seen = []
    for pat in ("index.html", "*/index.html", "*/*/index.html"):
        seen += glob.glob(os.path.join(SITE, pat))
    return sorted(set(seen))


def main(argv):
    check = "--check" in argv
    targets = [a for a in argv if not a.startswith("--")]
    if "--all" in argv or (check and not targets):
        targets = pages()
    if not targets:
        print(__doc__.strip().splitlines()[-4])
        return 2

    total_fonts, total_saved, uniq = 0, 0, set()
    for t in targets:
        path = t if os.path.isabs(t) else os.path.join(SITE, t)
        if not os.path.exists(path):
            print("  missing: %s" % t)
            continue
        n, saved, names = process(path, check=check)
        if n:
            rel = os.path.relpath(path, SITE)
            print("  %-46s %2d font(s)  -%6.0f KB" % (rel, n, saved / 1024.0))
            total_fonts += n
            total_saved += saved
            uniq.update(names)

    print("\n%s  --  %d font reference(s) across the pages above, "
          "%d DISTINCT file(s), %.0f KB removed from HTML"
          % ("WOULD EXTRACT" if check else "EXTRACTED",
             total_fonts, len(uniq), total_saved / 1024.0))
    if check:
        print("  (dry run -- nothing written)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
