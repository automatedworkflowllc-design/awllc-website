# -*- coding: utf-8 -*-
"""Negative control for the palette gate. Proves it still fires, and still doesn't.

WHY THIS EXISTS. The palette gate was wrong twice on the day it shipped, and both
mistakes were the same kind: it flagged things that were never paint.

  - 697 "unsourced colours" on 34 pages, nearly all gradient stops inside inline
    <svg> illustrations. Artwork is allowed its own colours; a button is not.
  - then it blocked a push over a hex quoted inside <code> in the build-log entry
    describing the gate itself. Left alone, the effective rule was "the log may
    never mention a colour".

Both fixes NARROW the gate, and a narrowed gate is exactly the kind that quietly
stops catching what it was built for. So the duty here is symmetric, and the
second half matters as much as the first:

  1. a hand-picked colour in real paint is still caught, and NAMED
  2. the same hex as artwork or as quoted prose is still ignored
  3. --record cannot launder a failing run into the baseline

The proof for all of this lived only in a transcript until 2026-08-18. A gate
nobody has seen go red is not evidence, and a gate whose only red was watched
once by one person is barely better.

Run: python _qa/test_palette_audit.py
"""

import io
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
AUDIT = HERE / 'palette_audit.py'

# A colour from no palette at all. Distinctive enough to grep for in the output.
INVENTED = '#7B2FF7'


def site(pages):
    """Build a synthetic site whose _qa/ holds the real palette_audit.py."""
    root = pathlib.Path(tempfile.mkdtemp())
    (root / '_qa').mkdir()
    (root / '_brand').mkdir()
    shutil.copy(str(AUDIT), str(root / '_qa' / 'palette_audit.py'))
    for mod in ('tokens.py', 'awllc_brand.py'):
        shutil.copy(str(SITE / '_brand' / mod), str(root / '_brand' / mod))
    for name, body in pages.items():
        d = root / name
        d.mkdir()
        io.open(d / 'index.html', 'w', encoding='utf-8').write(body)
    return root


def run(root, *args):
    p = subprocess.run([sys.executable, str(root / '_qa' / 'palette_audit.py')] + list(args),
                       cwd=str(root), capture_output=True, text=True, timeout=120)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


TOKEN_PAGE = '<style>body{color:#191713;background:#F5F3ED}</style><p>hello</p>'
PAINTED = '<style>.x{color:%s}</style><p>hello</p>' % INVENTED
AS_ARTWORK = ('<svg viewBox="0 0 2 2"><stop stop-color="%s"/></svg>'
              '<style>body{color:#191713}</style>' % INVENTED)
AS_PROSE = ('<p>we screen for <code>.x{color:%s}</code></p>'
            '<style>body{color:#191713}</style>' % INVENTED)
UNIVERSAL = '<style>body{color:#000000;background:#FFFFFF}</style>'


def main():
    fails = []

    def ok(name, cond, detail=''):
        if cond:
            print('  [palette-control] %-50s ok' % name)
        else:
            print('  [palette-control] %-50s FAIL  %s' % (name, detail[:200]))
            fails.append(name)

    # 1. Tokens only -- must pass. A gate that cannot pass gets disabled.
    code, out = run(site({'clean': TOKEN_PAGE}))
    ok('a page using only real tokens passes', code == 0, 'exit %s | %s' % (code, out))

    # 2. Black and white are not palette decisions -- shadows, borders, SVG
    #    defaults. Flagging them would make every page red forever.
    code, out = run(site({'bw': UNIVERSAL}))
    ok('black and white alone do not trip it', code == 0, 'exit %s' % code)

    # 3. THE POINT. Real paint from no palette must fail, and be named.
    code, out = run(site({'painted': PAINTED}))
    ok('a hand-picked colour in real paint fails the gate', code == 1, 'exit %s' % code)
    ok('the offending page is named', 'painted' in out, out)
    ok('the offending colour is named', INVENTED in out, out)

    # 4. The two narrowings, each still holding. Same hex, not paint.
    code, out = run(site({'art': AS_ARTWORK}))
    ok('the same hex inside <svg> is ignored (the 697 false positives)',
       code == 0, 'exit %s | %s' % (code, out))
    code, out = run(site({'prose': AS_PROSE}))
    ok('the same hex inside <code> is ignored (the gate blocking its own docs)',
       code == 0, 'exit %s | %s' % (code, out))

    # 5. The watermark rule: looking twice must not make a defect the new normal.
    root = site({'painted': PAINTED})
    code, out = run(root, '--record')
    ok('--record still fails on a painted page', code == 1, 'exit %s' % code)
    base = root / '_qa' / 'palette_baseline.json'
    laundered = base.exists() and INVENTED in json.dumps(
        json.load(io.open(base, encoding='utf-8')))
    ok('--record does NOT launder the colour into the baseline', not laundered,
       'baseline exists=%s' % base.exists())

    # 6. Bootstrap arms it deliberately, and says so.
    root = site({'painted': PAINTED})
    code, out = run(root, '--bootstrap')
    ok('--bootstrap arms the baseline and exits 0', code == 0, 'exit %s' % code)
    ok('and says out loud that it is accepting the current state',
       'ACCEPTS' in out or 'BOOTSTRAP' in out, out)
    code, out = run(root)
    ok('after bootstrap the same page is clean (baseline honoured)',
       code == 0, 'exit %s | %s' % (code, out))

    if fails:
        print('\nPALETTE CONTROL FAILED on %d check(s). Either the gate stopped catching a '
              'hand-picked colour, or it started flagging artwork and prose again.' % len(fails))
        return 1
    print('  palette control: still catches real paint, still ignores artwork and prose')
    return 0


if __name__ == '__main__':
    sys.exit(main())
