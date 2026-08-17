# -*- coding: utf-8 -*-
"""Does any page invent a colour?

WHY THIS EXISTS. _brand/tokens.py opens by promising that "a new tool CANNOT be
off-brand, because it does not declare its own colours." Measured 2026-08-16:
nothing enforced that. 33 of 36 public pages carry a palette that predates
tokens.py, 3 are on tokens.py, and no check could tell you which -- so the
promise was aspirational, and the drift it was written to stop had already
happened twice over.

WHAT THIS ASKS, and what it deliberately does NOT. It does not ask "is this page
on tokens.py". Failing on that would demand a 33-page redesign to land a push,
which is a design decision, not a gate. It asks the one question that is
decision-neutral: **does this page use a colour that comes from no known source
at all?** A hex in neither tokens.py, nor the legacy brand, nor this page's
recorded baseline is somebody hand-picking a colour -- which is exactly how the
site ended up with two palettes. Whichever direction it eventually unifies, that
has to stop first.

BASELINE, and the watermark rule. Today's colours are recorded, so this blocks
NEW drift without demanding the existing split be fixed first. As with autoqa and
seo_audit, the baseline moves ONLY on --record and NEVER on a run that found
something -- otherwise looking at a defect twice makes it the new normal and the
second look exits 0.

Run:
    python _qa/palette_audit.py            read-only diagnostic
    python _qa/palette_audit.py --record   the push may move the baseline
"""

import io
import json
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
BASELINE = os.path.join(HERE, 'palette_baseline.json')

HEX = re.compile(r'#[0-9a-fA-F]{6}\b')

# Inline <svg> is ARTWORK, not chrome. The first run of this file flagged 697
# colours on 34 pages, which is the shape of a broken check rather than a broken
# site -- nearly all of them were gradient stops inside illustrations
# (stop-color="#3aa5ff" and friends). An illustration is allowed its own colours;
# a button is not. Strip the artwork and ask the question about the page.
SVG = re.compile(r'<svg\b.*?</svg>', re.S | re.I)

# A hex inside <code> is being TALKED ABOUT, not applied. Caught 2026-08-16: the
# /log/ entry describing this very gate quotes `.hand-picked{color:#7B2FF7}` as its
# example of a failure, and the gate then blocked the push over its own example.
# Left alone, the rule is "the build log may never describe a colour" -- which is
# not the rule anyone wanted. Paint is what a browser renders; <code> is prose.
CODE = re.compile(r'<code\b[^>]*>.*?</code>', re.S | re.I)

# Black and white are not palette decisions -- they turn up in shadows, borders
# and SVG defaults on every page and carry no brand meaning.
UNIVERSAL = set(['#000000', '#FFFFFF'])


def known_colours():
    """Every colour that has a source. There are two today, which is the problem
    this file exists to stop growing to three."""
    sys.path.insert(0, os.path.join(SITE, '_brand'))
    out = set(UNIVERSAL)
    try:
        import tokens
        for d in (tokens.LIGHT, tokens.DARK):
            for v in d.values():
                if isinstance(v, str) and v.startswith('#'):
                    out.add(v.upper())
    except Exception as e:
        print('  palette: cannot read _brand/tokens.py -- %s' % e)
        return None
    try:
        import awllc_brand as legacy
        for name in dir(legacy):
            v = getattr(legacy, name)
            if isinstance(v, str) and re.match(r'^[0-9a-fA-F]{6}$', v or ''):
                out.add('#' + v.upper())
    except Exception as e:
        print('  palette: cannot read _brand/awllc_brand.py -- %s' % e)
        return None
    return out


def pages():
    seen = []
    for pat in ('*/index.html', '*/*/index.html'):
        for p in glob.glob(os.path.join(SITE, pat)):
            rel = os.path.relpath(p, SITE).replace('\\', '/')
            if rel.startswith('_') or '/.' in rel:
                continue
            seen.append(rel)
    return sorted(set(seen))


def scan():
    known = known_colours()
    if known is None:
        return None, None
    found = {}
    for rel in pages():
        try:
            s = io.open(os.path.join(SITE, rel), encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        hx = sorted(set(h.upper() for h in HEX.findall(CODE.sub(' ', SVG.sub(' ', s)))))
        if hx:
            found[rel] = hx
    return found, known


def main():
    found, known = scan()
    if found is None:
        return 1

    prev = {}
    if os.path.exists(BASELINE):
        try:
            prev = json.load(io.open(BASELINE, encoding='utf-8'))
        except Exception:
            prev = {}

    # Unsourced = no palette knows it AND it is not already recorded for this
    # page. A brand-new page inherits nothing, so anything hand-picked on it is
    # caught the first time, which is the point.
    invented = {}
    for rel, hx in found.items():
        allowed = set(known) | set(prev.get(rel, []))
        new = [h for h in hx if h not in allowed]
        if new:
            invented[rel] = new

    total = sum(len(v) for v in invented.values())
    print('PALETTE AUDIT  --  %d page(s) with colour, %d unsourced colour(s) on %d page(s)'
          % (len(found), total, len(invented)))
    if invented:
        for rel in sorted(invented):
            print('  [invented] %-40s %s' % (rel, ' '.join(invented[rel][:8])))
        print('')
        print("  A colour in neither _brand/tokens.py nor _brand/awllc_brand.py nor this")
        print("  page's baseline was hand-picked. Use a token, or add it to the palette on")
        print('  purpose -- do not widen the baseline to hide it.')
    else:
        print('  clean -- every colour on every page traces to a source.')

    # --record NEVER moves the baseline on a run that found something: that is the
    # watermark rule, and without it running this twice turns a new colour into
    # the new normal. But with no baseline at all, every existing colour is
    # unsourced and --record can never fire -- the gate could never be armed.
    # --bootstrap is the deliberate one-time arming, and says so out loud.
    if '--bootstrap' in sys.argv:
        io.open(BASELINE, 'w', encoding='utf-8').write(
            json.dumps(found, indent=1, sort_keys=True))
        print('  BOOTSTRAP: recorded today\'s %d page(s) as the baseline.' % len(found))
        print('  This ACCEPTS the current two-palette split. It does not endorse it --')
        print('  it fixes the point from which new drift is measured.')
        return 0
    if '--record' in sys.argv and total == 0:
        io.open(BASELINE, 'w', encoding='utf-8').write(
            json.dumps(found, indent=1, sort_keys=True))
        print('  baseline recorded: %d page(s)' % len(found))

    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
