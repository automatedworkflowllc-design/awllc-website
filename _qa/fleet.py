#!/usr/bin/env python3
"""One definition of "how many scheduled jobs, and how many are guarded".

WHY THIS FILE EXISTS -- the mistake it fixes is worth stating plainly.

The /proof/ page claimed "seven of our nine scheduled jobs" run under attest,
and the claim audit verified it and passed. Both were wrong. Both counted
DIRECTORIES under Scheduled\\, and two of those directories (daily-morning-
briefing, gex-desk-assistant) hold only a SKILL.md -- no launcher, no registered
task, not jobs at all. The real numbers are seven registered tasks and seven
guarded: full coverage, understated on a page whose whole subject is not
misstating things.

The audit did not catch it because the audit and the page shared the same wrong
definition of "job", so they agreed. That is precisely the rule written at the
top of claims.toml -- two things agreeing with each other is not evidence, it is
a rumour with a citation -- and I broke it the same day I wrote it.

So: the source of truth is the WINDOWS TASK SCHEDULER, which is the thing that
actually decides whether a job exists. It lives here once, imported by both the
page builder and the audit. A folder is not a job. A job is a registered task,
and it is guarded when the launcher it actually runs goes through attest.
"""
from __future__ import annotations

import json
import pathlib
import subprocess

SCHEDULED_ROOT = pathlib.Path(r'C:\Users\hisbo\claude\Scheduled')

_PS = (
    "Get-ScheduledTask | ForEach-Object { $t=$_; $t.Actions | ForEach-Object { "
    "[PSCustomObject]@{ TaskName=$t.TaskName; Execute=$_.Execute } } } | ConvertTo-Json -Compress"
)


def _registered_actions() -> list[dict]:
    """Every scheduled task action on this machine, as {TaskName, Execute}."""
    r = subprocess.run(['powershell', '-NoProfile', '-Command', _PS],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not r.stdout.strip():
        # Fail loudly. A count that silently returns 0 would let a page claim
        # coverage over a fleet nobody could see -- the exact class of quiet
        # wrongness this whole system exists to catch.
        raise RuntimeError('could not read the Windows task scheduler: '
                           + (r.stderr.strip() or 'no output')[:200])
    data = json.loads(r.stdout)
    return data if isinstance(data, list) else [data]


def fleet() -> dict:
    """Return {'total', 'guarded', 'jobs': [{name, launcher, guarded}]}.

    A job counts only if its action points inside Scheduled\\. It counts as
    guarded only if the launcher it actually runs mentions attest -- read from
    the file on disk, not assumed from the folder it sits in.
    """
    jobs = []
    seen = set()
    for a in _registered_actions():
        exe = (a.get('Execute') or '').strip('"')
        if not exe:
            continue
        p = pathlib.Path(exe)
        try:
            inside = SCHEDULED_ROOT in p.parents
        except (OSError, ValueError):
            inside = False
        if not inside or exe.lower() in seen:
            continue
        seen.add(exe.lower())
        guarded = False
        if p.exists():
            guarded = 'attest' in p.read_text(encoding='utf-8', errors='replace')
        jobs.append({'name': a.get('TaskName', '?'), 'launcher': p.name, 'guarded': guarded})
    jobs.sort(key=lambda j: j['name'])
    return {'total': len(jobs), 'guarded': sum(1 for j in jobs if j['guarded']), 'jobs': jobs}


_WORDS = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six',
          7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve'}


def coverage_phrase(style: str = 'words') -> str:
    """The phrase a page may print, built from the count rather than typed.

    Says "all seven" when coverage is complete, because "seven of our seven"
    reads like an evasion, and understating coverage on a page about honesty is
    its own kind of wrong.
    """
    f = fleet()
    g, t = f['guarded'], f['total']
    if style != 'words':
        return f'{g} of {t}'
    if g not in _WORDS or t not in _WORDS:
        return f'{g} of {t}'
    return f'all {_WORDS[t]} of our' if g == t else f'{_WORDS[g]} of our {_WORDS[t]}'


if __name__ == '__main__':
    f = fleet()
    print(f'{f["guarded"]} of {f["total"]} registered scheduled jobs run under attest')
    for j in f['jobs']:
        print(f'  [{"guarded" if j["guarded"] else "UNGUARDED"}] {j["name"]}  ({j["launcher"]})')
    print('phrase:', coverage_phrase())
