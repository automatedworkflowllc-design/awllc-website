# -*- coding: utf-8 -*-
"""Last-mile audit — codifies "find where activity dies" (gap #1).

The failure class this guards: a prospect acts, and the action goes nowhere.
A mistyped mailto, a dead form endpoint, a broken contact path — each drops a
lead silently, and a form is worse than a bad address because the visitor thinks
it sent. This is worth more to fix than more traffic.

Checks every git-tracked page:
  1. every mailto:  == the canonical address (a typo silently drops leads)   [RELIABLE]
  2. every tel:     == the canonical phone                                   [RELIABLE]
  3. every <form action="…"> host is REACHABLE (DNS/domain up)              [PARTIAL]

⚠️ HONEST LIMIT on #3: Formspree returns 405 "please POST" to GET for BOTH a live
form and a deleted one — identical. So a GET can catch a malformed/typo'd action
domain or Formspree being down, but it CANNOT confirm the form still ROUTES to the
inbox. The only real proof of routing is a POST that lands — do that periodically
(a marked test submission, then confirm it arrives; last confirmed 2026-07-11).
This check therefore never claims the form path is verified — only that its host
is up. Overclaiming here would be the "all-clear when it isn't" failure.

Baseline 2026-07-21: mailto/tel all canonical; the one form endpoint (Formspree
mgojgjwv) host is reachable and was confirmed routing to the monitored inbox by a
landed test submission on 7/11; zero real submissions since, so nothing missed.

Network check → run periodically, not on every push.
Run:  python _qa/last_mile_audit.py
Exit: 0 = every path lands somewhere · 1 = a path dead-ends
"""
import io, os, re, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# canonical NAP — the ONLY address/phone a contact path may point at
CANON_EMAIL = 'colin@automatedworkflowllc.com'
CANON_TEL   = '+17039391174'

findings = []

def tracked(pat):
    out = subprocess.run(['git', 'ls-files', pat], cwd=ROOT, capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f.strip()]

def host_reachable(url):
    """Can we reach the form endpoint's HOST at all? This catches a typo'd action
    domain (DNS fail) or the service being down — NOT a deleted-but-hosted form.
    000 = unreachable. Any HTTP response (incl. 405) = host is up."""
    try:
        code = subprocess.run(
            ['curl', '-s', '-o', os.devnull, '-w', '%{http_code}', '-m', '20',
             '-A', 'Mozilla/5.0', url],
            capture_output=True, text=True, timeout=25).stdout.strip()
    except Exception as e:
        return None, str(e)
    return (code not in ('000', '404', '410', '500', '502', '503')), code

def main():
    pages = tracked('*.html')
    mailto = tel = forms = 0
    endpoints = {}
    for rel in pages:
        s = io.open(os.path.join(ROOT, rel), encoding='utf-8', errors='replace').read()
        for addr in re.findall(r'mailto:([^"?\s>]+)', s):
            mailto += 1
            if addr.strip().lower() != CANON_EMAIL:
                findings.append((rel, 'non-canonical mailto: %s (leads to this address vanish)' % addr))
        for num in re.findall(r'tel:([^"\s>]+)', s):
            tel += 1
            if num.strip() != CANON_TEL:
                findings.append((rel, 'non-canonical tel: %s' % num))
        for act in re.findall(r'<form[^>]*action="([^"]+)"', s, re.I):
            forms += 1
            endpoints.setdefault(act, []).append(rel)

    # form endpoints: can only prove the HOST is reachable (see honest limit in docstring)
    unverifiable = []
    for url, used_on in endpoints.items():
        up, code = host_reachable(url)
        if up is None:
            findings.append(('(network)', 'form endpoint host unreachable: %s (%s)' % (url, code)))
        elif not up:
            findings.append((used_on[0], 'form endpoint host DOWN/typo: %s -> HTTP %s '
                             '(submissions on %d page(s) vanish)' % (url, code, len(used_on))))
        else:
            unverifiable.append((url, len(used_on), code))

    print('LAST-MILE AUDIT  --  %d pages, %d mailto, %d tel, %d forms -> %d endpoint(s)'
          % (len(pages), mailto, tel, forms, len(endpoints)))
    for url, n, code in unverifiable:
        print('  [host up, routing NOT GET-verifiable] %s (HTTP %s, %d page(s)) '
              '-- confirm routing with a periodic test POST' % (url, code, n))
    if not findings:
        print('  CLEAN -- mailto/tel all canonical; form hosts reachable. '
              '(Form ROUTING still needs a periodic test-submit; last confirmed 2026-07-11.)')
        return 0
    for f, msg in findings:
        print('  [DEAD-END] %-28s %s' % (f, msg))
    print('\n  %d dead-end(s). Every one silently drops the lead that hits it.' % len(findings))
    return 1

if __name__ == '__main__':
    sys.exit(main())
