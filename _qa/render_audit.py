"""Open every page in a real browser and check it actually RENDERED.

Every other gate in this directory reads the HTML as text. That is the whole
blind spot: a page can parse perfectly, pass the structure/claim/palette/SEO
gates, and still arrive at a visitor as a blank screen, a collapsed layout, or
a page whose JavaScript died on load.

The precedent is already in this repo's history. On 2026-08-12 a scope bug in
the shared reader shipped to five live tools -- a ReferenceError on every file
drop -- and every gate stayed green, because not one of them opened a
spreadsheet. test_reader.py closed that half. It does NOT catch a script that
throws on PAGE LOAD, before any file is dropped, which fails the same way and is
equally invisible to a text scan.

Three checks, all deterministic. Chosen deliberately over pixel-diffing, which
is flaky, needs baselines, and cries wolf on every legitimate copy change:

  1. PAGE ERRORS ON LOAD -- any uncaught exception or failed console.error while
     the page loads. This is the load-time twin of the 8/12 reader bug.
  2. BLANK / COLLAPSED RENDER -- <body> renders under MIN_BODY_PX tall. A page
     that parses but paints nothing reads as "site is down" to a visitor.
  3. HORIZONTAL OVERFLOW AT MOBILE WIDTH -- scrollWidth exceeds a 375px viewport.
     A real defect that no HTML scan can see, on the width most visitors use.

WHAT THIS GATE CANNOT DO, stated so nobody trusts it further than it goes: it
cannot judge whether a page looks GOOD. It proves the page rendered, was not
blank, threw nothing, and does not scroll sideways. Taste is not measurable here
and this gate does not pretend otherwise.

Runs against local file:// so it needs no network and no deploy.
"""

import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_BODY_PX = 200
MOBILE_WIDTH = 375
OVERFLOW_TOLERANCE_PX = 2   # sub-pixel rounding is not a defect

# Console noise that is not a page defect: file:// has no server, so favicon and
# analytics fetches legitimately fail locally. Blocking a push on those would be
# a gate crying wolf, which is how gates get switched off.
#
# The web-font CORS entry is the one that needed proving rather than assuming.
# Root-relative hrefs (/fonts/x.woff2) resolve to C:/fonts/ under file://, so
# Chromium reports a CORS block on every page that loads a font. VERIFIED on
# 2026-08-23 that this is a local-protocol artifact and not a real defect: both
# files return HTTP 200 from https://automatedworkflowllc.com/fonts/. Scoped to
# the woff2 font fetch on purpose -- a CORS failure on anything else is still a
# defect and still blocks.
IGNORABLE = re.compile(
    r'favicon|net::ERR_FILE_NOT_FOUND|ERR_CONNECTION|googletagmanager|'
    r'google-analytics|gtag|Failed to load resource|'
    r'Access to font at .*\.woff2?.* has been blocked by CORS',
    re.I,
)


def pages():
    found = sorted(
        glob.glob(os.path.join(ROOT, '*', 'index.html'))
        + glob.glob(os.path.join(ROOT, 'index.html'))
    )
    return [p for p in found if os.sep + '_' not in p]


def audit(paths=None, verbose=True):
    from playwright.sync_api import sync_playwright

    paths = paths or pages()
    defects = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for path in paths:
            rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
            page = browser.new_page(viewport={'width': MOBILE_WIDTH, 'height': 800})
            errors = []
            page.on('pageerror', lambda e: errors.append(f'uncaught: {e}'))
            page.on('console', lambda m: errors.append(f'console.error: {m.text}')
                    if m.type == 'error' else None)
            try:
                page.goto('file:///' + path.replace(os.sep, '/'),
                          wait_until='load', timeout=20000)
                page.wait_for_timeout(400)   # let deferred scripts run

                real = [e for e in errors if not IGNORABLE.search(e)]
                for e in real:
                    defects.append((rel, 'page error on load', e[:160]))

                box = page.evaluate(
                    '({h: document.body.scrollHeight,'
                    '  sw: document.documentElement.scrollWidth,'
                    '  vw: window.innerWidth})'
                )
                if box['h'] < MIN_BODY_PX:
                    defects.append((rel, 'blank or collapsed render',
                                    f"body is {box['h']}px tall (min {MIN_BODY_PX})"))
                over = box['sw'] - box['vw']
                if over > OVERFLOW_TOLERANCE_PX:
                    defects.append((rel, 'horizontal overflow at 375px',
                                    f"scrollWidth {box['sw']} exceeds viewport {box['vw']} by {over}px"))
            except Exception as exc:                       # noqa: BLE001
                defects.append((rel, 'failed to load', str(exc)[:160]))
            finally:
                page.close()
        browser.close()

    if verbose:
        print(f'render_audit: {len(paths)} pages checked at {MOBILE_WIDTH}px')
        for rel, kind, detail in defects:
            print(f'  DEFECT  {rel}: {kind} -- {detail}')
        if not defects:
            print('  no render defects')
    return defects


if __name__ == '__main__':
    sys.exit(1 if audit() else 0)
