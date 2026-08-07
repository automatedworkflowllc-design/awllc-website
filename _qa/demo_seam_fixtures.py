#!/usr/bin/env python3
"""demo_seam_fixtures.py -- prove /demo/ can be driven by real client data.

WHY THIS EXISTS
---------------
The dashboard on /demo/ renders from one object. Sample data is the fallback,
not the only path, so the same page can drive a real client's numbers -- see the
"THE DATA SEAM" comment in _brand/build_demo_app.py for the contract.

A seam nobody exercises is a seam that quietly rots. This writes copies of the
live page with a dataset injected *before* the app script runs (deterministic --
no race against page load), so the whole thing can be re-checked in a browser
any time.

    python _qa/demo_seam_fixtures.py            # writes to _qa/_seam_out/
    python -m http.server 8878                  # from the repo root
    # then open http://localhost:8878/_qa/_seam_out/<case>.html

WHAT EACH CASE IS FOR -- every one of these caught a real bug on 2026-08-06:

  real        a normal client book. Caught a hardcoded "across 3 crews" in the
              Active Customers tile: harmless on sample data, a FABRICATION the
              moment a real book loads, because the dashboard would be asserting
              a fact about a business it knows nothing about.
  tiny        a one-week book. Caught a lookback that read weeks[-1] (undefined
              -> "$NaN" on the flagship page) and, worse, a summary that said an
              invoice was "3 days past due" when it was 3 days OLD and not due
              for another month -- the page contradicting its own list.
  allpaid     nothing outstanding. Caught a red alert badge reading "0" and two
              panels rendering blank instead of saying so.
  badvalue    a non-numeric revenue figure -> must REFUSE, naming the field.
  baddate     an unparseable week start -> must REFUSE, naming the field.
  badinvoice  a non-numeric invoice amount -> must REFUSE, naming the field.

The three "bad" cases are the important ones. Rendering "$NaN", or silently
dropping a malformed invoice and showing a confident total that is quietly
wrong, is precisely the failure this company sells against -- so the dashboard
has to refuse rather than guess, and it has to say which field was bad.
"""

import io
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'demo', 'index.html')
OUT = os.path.join(ROOT, '_qa', '_seam_out')
MARKER = '<script>\n/* aw-demo-app'

CASES = {
    'real': {
        "business": "Riverside Fleet Services",
        "weeks": [{"start": "2026-06-15", "value": 12000}, {"start": "2026-06-22", "value": 10500},
                  {"start": "2026-06-29", "value": 13000}, {"start": "2026-07-06", "value": 11500},
                  {"start": "2026-07-13", "value": 14000}, {"start": "2026-07-20", "value": 12500},
                  {"start": "2026-07-27", "value": 15000}, {"start": "2026-08-03", "value": 13800}],
        "receivables": [{"customer": "Northgate Logistics", "amount": 7200, "days": 74},
                        {"customer": "Beltline Haulage", "amount": 3150, "days": 22}],
        "spend": 1840, "activeCustomers": 7,
    },
    'tiny': {
        "business": "One Week Co",
        "weeks": [{"start": "2026-08-03", "value": 5000}],
        "receivables": [{"customer": "Solo Client", "amount": 800, "days": 3}],
        "spend": 100, "activeCustomers": 1,
    },
    'allpaid': {
        "business": "All Paid Co",
        "weeks": [{"start": "2026-07-27", "value": 9000}, {"start": "2026-08-03", "value": 9500}],
        "receivables": [], "spend": 300, "activeCustomers": 4,
    },
    'badvalue': {"business": "Bad Co",
                 "weeks": [{"start": "2026-07-06", "value": "twelve thousand"}], "receivables": []},
    'baddate': {"business": "Bad Co",
                "weeks": [{"start": "not-a-date", "value": 100}], "receivables": []},
    'badinvoice': {"business": "Bad Co", "weeks": [{"start": "2026-07-06", "value": 9000}],
                   "receivables": [{"customer": "X", "amount": "lots", "days": 10}]},
}

EXPECT = {
    'real':       'renders as "Riverside Fleet Services", AR = $10,350, sample chip GONE',
    'tiny':       'renders; "no prior month to compare against yet"; "none of it is past due yet"',
    'allpaid':    '"Nothing is outstanding"; AR $0; NO red badge; panels say so',
    'badvalue':   'REFUSES -- names weeks[0].value',
    'baddate':    'REFUSES -- names weeks[0].start',
    'badinvoice': 'REFUSES -- names receivables[0].amount',
}


def main() -> None:
    src = io.open(PAGE, encoding='utf-8').read()
    if MARKER not in src:
        raise SystemExit('app script marker not found in %s -- did the generator change?' % PAGE)

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    for name, data in CASES.items():
        inject = '<script>window.AW_DASHBOARD_DATA = %s;</script>\n' % json.dumps(data)
        # Paths are absolute (/demo/... , /favicon.ico), so serving from a
        # different directory still resolves against the repo root.
        io.open(os.path.join(OUT, name + '.html'), 'w', encoding='utf-8').write(
            src.replace(MARKER, inject + MARKER, 1))
        print('  %-11s %s' % (name, EXPECT[name]))

    print('\nwrote %d fixtures to %s' % (len(CASES), OUT))
    print('serve the repo root, then open /_qa/_seam_out/<case>.html')


if __name__ == '__main__':
    main()
