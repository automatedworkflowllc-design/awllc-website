#!/usr/bin/env python3
"""Claim audit -- re-derive every factual claim the public site makes.

The other gates check STRUCTURE: titles, links, tag balance, no secrets. None of
them check whether what a page SAYS is still true. That is the exact failure we
sell against -- a report that arrives on time carrying last week's numbers -- and
we were running it on ourselves: 72 distinct numeric claims on the public site,
zero of them verified after the day they were written. Twice in two days a claim
went stale and a human caught it late (a log saying "live" over unpushed commits;
a page claiming a pipeline "runs" weeks after the trial lapsed).

So every claim worth checking gets an entry in claims.toml naming its SOURCE OF
TRUTH, and this re-derives the value from that source and asserts the page still
says it.

DESIGN RULES, each one load-bearing:

  * Derivers are a WHITELIST of Python functions, never shell from the config.
    A claim file that can run arbitrary commands is a remote-code-execution hole
    dressed as a gate.
  * UNCHECKABLE is a first-class, reported outcome. Some claims are about the
    outside world (a partner's record count) and cannot be re-derived here.
    Saying so is honest; quietly passing them is the lie this tool exists to
    catch, and a gate that hides its blind spots is worse than no gate.
  * A claim whose page no longer contains the derived value FAILS, and a claim
    whose deriver errors FAILS too -- a check that cannot run must never read as
    a check that passed.

Exit: 0 all good, 1 any claim DISAGREES or its deriver broke.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLAIMS = pathlib.Path(__file__).resolve().parent / 'claims.toml'
HISTORY = pathlib.Path(__file__).resolve().parent / 'claims_history.json'

SUPPORTED, DISAGREES, UNCHECKABLE = 'SUPPORTED', 'DISAGREES', 'UNCHECKABLE'


# --- derivers ------------------------------------------------------------
# Each returns a string that must appear in the page, or raises. Adding one is
# a deliberate act: it is the only way a new kind of claim becomes checkable.

def d_pytest_count(path: str, **_) -> str:
    """Number of tests actually collected by the suite at `path`."""
    p = pathlib.Path(path)
    if not p.is_absolute():
        p = (ROOT / path).resolve()
    r = subprocess.run([sys.executable, '-m', 'pytest', '--collect-only', '-q'],
                       cwd=str(p), capture_output=True, text=True, timeout=180)
    m = re.search(r'(\d+) tests? collected', r.stdout + r.stderr)
    if not m:
        raise RuntimeError(f'could not read a test count from pytest in {p}')
    return m.group(1)


_WORDS = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six',
          7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve'}


def d_wrapped_jobs(scheduled_dir: str, style: str = 'digits', **_) -> str:
    """How many scheduled jobs actually run under attest.

    `style` exists because prose spells small numbers out ("six of our eight")
    while a stat block uses digits. The check must match the page as written,
    not force the page to match the checker.
    """
    root = pathlib.Path(scheduled_dir)
    if not root.is_dir():
        raise RuntimeError(f'{root} is not a directory')
    # Dotted entries are not jobs. `.git` is a directory and iterdir() returns
    # it, which made the very first run of this audit report a false failure
    # against a page that was correct -- the checker was wrong, not the claim.
    jobs = [d for d in sorted(root.iterdir()) if d.is_dir() and not d.name.startswith('.')]
    wrapped = [d for d in jobs
               if any('attest' in f.read_text(encoding='utf-8', errors='replace')
                      for f in d.glob('*.cmd'))]
    if style == 'words':
        if len(wrapped) not in _WORDS or len(jobs) not in _WORDS:
            raise RuntimeError('counts outside the spelled-out range; use digits')
        return f'{_WORDS[len(wrapped)]} of our {_WORDS[len(jobs)]}'
    return f'{len(wrapped)} of {len(jobs)}'


def d_anchor_receipts(**_) -> str:
    """Receipt count in the newest PUBLISHED anchor line."""
    txt = (ROOT / 'proof' / 'attest-anchors.txt').read_text(encoding='utf-8')
    lines = [l for l in txt.splitlines() if l.strip() and not l.startswith('#')]
    if not lines:
        raise RuntimeError('no anchor lines published')
    m = re.search(r'receipts=(\d+)', lines[-1])
    if not m:
        raise RuntimeError('newest anchor line carries no receipt count')
    return m.group(1)


def d_anchor_head(chars: int = 8, **_) -> str:
    """Leading hex of the newest published chain head."""
    txt = (ROOT / 'proof' / 'attest-anchors.txt').read_text(encoding='utf-8')
    lines = [l for l in txt.splitlines() if l.strip() and not l.startswith('#')]
    m = re.search(r'head=sha256:([0-9a-f]{64})', lines[-1])
    if not m:
        raise RuntimeError('newest anchor line carries no head')
    return m.group(1)[:int(chars)]


def d_sitemap_urls(**_) -> str:
    return str((ROOT / 'sitemap.xml').read_text(encoding='utf-8').count('<loc>'))


def d_from_source(source: str, pattern: str, **_) -> str:
    """Pull a value out of the file that is its source of truth.

    `pattern` must capture exactly one group. This is how a figure printed on a
    page gets tied back to the code that computes it: the money figures on three
    pages and in every outreach email all trace to one builder, and if that
    number moves the copy has to move with it or this fails.
    """
    p = pathlib.Path(source)
    if not p.is_absolute():
        p = ROOT / source
    if not p.exists():
        raise RuntimeError(f'{p} does not exist')
    m = re.search(pattern, p.read_text(encoding='utf-8', errors='replace'))
    if not m or not m.groups():
        raise RuntimeError(f'pattern {pattern!r} captured nothing in {p.name}')
    return m.group(1)


def d_sum_rows(source: str, ids: list, **_) -> str:
    """Sum named rows out of a builder's sample data and format as money.

    The headline "$1,240 of work never invoiced" is not stored anywhere -- it is
    410 + 520 + 310 from three rows of sample data. So the honest check is to do
    the arithmetic again rather than grep for a copy of the answer: edit the
    sample and the page's figure has to move with it or this fails.
    """
    p = pathlib.Path(source)
    if not p.is_absolute():
        p = ROOT / source
    src = p.read_text(encoding='utf-8', errors='replace')
    total = 0
    for row_id in ids:
        m = re.search(rf'{re.escape(row_id)},[^\n\']*?\$?([0-9][0-9,]*)\.[0-9]{{2}}', src)
        if not m:
            raise RuntimeError(f'row {row_id} not found in {p.name}')
        total += int(m.group(1).replace(',', ''))
    return '$' + format(total, ',')


DERIVERS = {
    'sum_rows': d_sum_rows,
    'pytest_count': d_pytest_count,
    'wrapped_jobs': d_wrapped_jobs,
    'anchor_receipts': d_anchor_receipts,
    'anchor_head': d_anchor_head,
    'sitemap_urls': d_sitemap_urls,
    'from_source': d_from_source,
}


def audit() -> int:
    spec = tomllib.loads(CLAIMS.read_text(encoding='utf-8'))
    rows, failed, unchecked = [], 0, 0

    for c in spec.get('claim', []):
        cid = c.get('id', '(unnamed)')
        page = c.get('page')
        note = c.get('note', '')

        if c.get('derive') == 'external':
            unchecked += 1
            rows.append((UNCHECKABLE, cid, note or 'depends on a system outside this repo'))
            continue

        fn = DERIVERS.get(c.get('derive', ''))
        if fn is None:
            failed += 1
            rows.append((DISAGREES, cid, f'no deriver named {c.get("derive")!r}'))
            continue

        try:
            value = fn(**c.get('args', {}))
        except Exception as e:                      # a check that cannot run has failed
            failed += 1
            rows.append((DISAGREES, cid, f'deriver raised: {e}'))
            continue

        target = ROOT / page
        if not target.exists():
            failed += 1
            rows.append((DISAGREES, cid, f'page missing: {page}'))
            continue

        text = target.read_text(encoding='utf-8', errors='replace')
        says = c.get('says', '{}').replace('{}', value)
        if says in text:
            rows.append((SUPPORTED, cid, f'{page} still says "{says}"'))
        else:
            failed += 1
            rows.append((DISAGREES, cid,
                         f'derived "{value}" -> expected "{says}" in {page}, not found'))

    print(f'CLAIM AUDIT  --  {len(rows)} claim(s): '
          f'{sum(1 for r in rows if r[0] == SUPPORTED)} supported, '
          f'{failed} disagree, {unchecked} uncheckable')
    for status, cid, detail in rows:
        if status != SUPPORTED:
            print(f'  [{status:11}] {cid}: {detail}')
    if not failed:
        print('  clean -- every checkable claim still matches its source of truth')

    HISTORY.write_text(json.dumps(
        {'claims': len(rows), 'failed': failed, 'uncheckable': unchecked,
         'rows': [{'status': s, 'id': i, 'detail': d} for s, i, d in rows]},
        indent=1), encoding='utf-8')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(audit())
