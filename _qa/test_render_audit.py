"""Negative controls for render_audit -- prove it can still go RED.

The rule this file exists for is written across this repo: a gate nobody has
seen fail is not evidence. The security sweep learned it the hard way (its key
pattern could not match `sk-ant-...`, so a real key was invisible), and autoqa's
own controls sat unexecuted by any gate until 2026-08-18.

So this plants each of render_audit's three defect classes in a throwaway page
and asserts the gate CATCHES it -- and plants a clean page and asserts the gate
IGNORES it. Both directions, because a gate that flags everything is as useless
as one that flags nothing.
"""

import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_audit  # noqa: E402

CLEAN = """<!doctype html><html><head><meta charset=utf8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>ok</title></head>
<body style="margin:0"><div style="height:900px">real content</div></body></html>"""

THROWS = """<!doctype html><html><head><meta charset=utf8><title>boom</title></head>
<body><div style="height:900px">content</div>
<script>window.nope.deeper = 1;</script></body></html>"""

BLANK = """<!doctype html><html><head><meta charset=utf8><title>blank</title></head>
<body></body></html>"""

OVERFLOW = """<!doctype html><html><head><meta charset=utf8><title>wide</title></head>
<body style="margin:0"><div style="width:1400px;height:900px">too wide</div></body></html>"""


def run(name, html):
    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, 'index.html')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(html)
        return render_audit.audit([p], verbose=False)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    failures = []

    clean = run('clean', CLEAN)
    if clean:
        failures.append(f'FALSE POSITIVE: clean page flagged {clean}')
    else:
        print('  ok  clean page passes (no false positive)')

    cases = [
        ('page error on load', THROWS, 'uncaught JS on load'),
        ('blank or collapsed render', BLANK, 'blank body'),
        ('horizontal overflow', OVERFLOW, '1400px content at 375px viewport'),
    ]
    for kind, html, label in cases:
        got = run(kind, html)
        if not any(kind.split()[0] in k for _, k, _ in got):
            failures.append(f'MISSED: {label} was not caught (got {got})')
        else:
            print(f'  ok  catches {label}')

    if failures:
        print('\nrender_audit controls FAILED:')
        for f in failures:
            print('  ' + f)
        return 1
    print('\nrender_audit controls pass: 3 planted defects caught, clean page ignored.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
