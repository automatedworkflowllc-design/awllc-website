# -*- coding: utf-8 -*-
"""Does /shift-coverage-check/ still treat a person as an IDENTITY?

WHY THIS EXISTS. Measured 2026-08-17 against the shipped page: one nurse covering
all six shifts of a week, spelled five ways ("Dave Smith", "dave smith",
"Dave  Smith", "DAVE SMITH", a trailing space), turned

    Nurse -- only Dave Smith covers it, 6 shifts        -> NOTHING REPORTED
    Dave Smith, 54h in one week                         -> NOTHING REPORTED

on a schedule that is identical in substance. Both of the page's headline
findings vanished, and vanished toward SILENCE -- the tool said there is no
single point of failure and nobody near overtime, about a roster where one
person is both. A wrong number invites a second look; a wrong all-clear closes
the question. That is the /almanac/ failure, and this page had no test suite of
any kind, which is why it survived.

WHAT IT GUARDS, in both directions. Folding spellings together is only half the
job -- a "fix" that merged everyone would also pass the first assertions and be
worse than the bug. So the controls matter more: two genuinely different people
must still read as two, and the page must print the spelling the user actually
typed rather than a normalised key.

Run:  python _qa/test_shift_coverage.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PAGE = os.path.join(SITE, 'shift-coverage-check', 'index.html')

DAYS = ['2026-03-02', '2026-03-03', '2026-03-04',
        '2026-03-05', '2026-03-06', '2026-03-07']
HEADER = 'Date,Start,End,Employee,Role'


def csv(rows):
    return '\n'.join([HEADER] + rows)


def shift(day, person, role='Nurse'):
    return '%s,08:00,17:00,%s,%s' % (day, person, role)


# Every case below is ONE nurse working six 9h shifts (54h) unless it says
# otherwise, so the correct answer never changes with the spelling.
ONE_SPELLING = csv([shift(d, 'Dave Smith') for d in DAYS])
FIVE_SPELLINGS = csv([
    shift(DAYS[0], 'Dave Smith'), shift(DAYS[1], 'dave smith'),
    shift(DAYS[2], 'Dave  Smith'), shift(DAYS[3], 'DAVE SMITH'),
    shift(DAYS[4], 'Dave Smith '), shift(DAYS[5], 'Dave.Smith'),
])
ROLE_SPELLINGS = csv([
    shift(DAYS[i], 'Dave Smith', r) for i, r in
    enumerate(['Nurse', 'nurse', 'NURSE', 'Nurse ', 'Nurse', 'nurse'])
])
TWO_PEOPLE = csv([
    shift(d, 'Dave Smith' if i % 2 else 'Dana Smythe')
    for i, d in enumerate(DAYS)
])

NODE = r"""
const fs = require('fs');
const page = fs.readFileSync(process.argv[2], 'utf8');
function block(sig){
  const i = page.indexOf(sig);
  if (i < 0) throw new Error('page no longer defines: ' + sig);
  let d = 0, started = false, j = i;
  for (; j < page.length; j++) {
    const c = page[j];
    if (c === '{') { d++; started = true; }
    else if (c === '}') { d--; if (started && d === 0) { j++; break; } }
  }
  return page.slice(i, j);
}
const lines = (re) => page.split('\n').filter(l => re.test(l)).join('\n');
const src = [
  lines(/^\s*var\s+(OT_HOURS|SHORT_TURNAROUND|MAX_STREAK|ID_NOISE|LEGAL_SUFFIX)\s*=/),
  block('var NAMED = {') + ';',
  // The identity rule lives in _brand/toolkit.py now, injected as normPerson
  // with `var normId = normPerson;` aliasing it. Pull both plus the alias:
  // extracting `function normId(` alone stopped working the moment it stopped
  // being a local function, and this gate said so instead of quietly passing.
  block('function normPerson('), block('function normCompany('),
  lines(/^var normId = normPerson;/),
  block('function noteLabel('),
  block('function labelFor('), block('function spellingCount('),
  block('function parseCSV('), block('function parseDate('),
  block('function parseTime('), block('function distinctCount('),
  block('function scoreCol('), block('function detect('),
  block('function iso('), block('function weekKey('),
  block('function fmtH('), block('function analyze(')
].join('\n');
const M = new Function(src + '\nreturn {parseCSV:parseCSV,detect:detect,analyze:analyze};')();
const rows = M.parseCSV(fs.readFileSync(process.argv[3], 'utf8'));
const header = rows[0];
const body = rows.slice(1).filter(r => r.join('').trim() !== '');
const res = M.analyze(header, body, M.detect(header, body));
console.log(JSON.stringify({
  solo: (res.solo || []).map(s => ({role: s.role, person: s.person, shifts: s.shifts})),
  ot: (res.ot || []).map(o => ({person: o.person, hours: Math.round(o.hours)}))
}));
"""


def run(runner, text):
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    io.open(path, 'w', encoding='utf-8').write(text)
    try:
        out = subprocess.run(['node', runner, PAGE, path],
                             capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            return {'error': (out.stderr or '').strip().splitlines()[-1:]}
        return json.loads(out.stdout.strip().splitlines()[-1])
    finally:
        os.remove(path)


def main():
    if not os.path.exists(PAGE):
        print('  [shift] page missing: %s' % PAGE)
        return 1
    tmp = tempfile.mkdtemp()
    runner = os.path.join(tmp, 'run.js')
    io.open(runner, 'w', encoding='utf-8').write(NODE)

    fails = []

    def check(name, cond, detail=''):
        if cond:
            print('  [shift] %-46s ok' % name)
        else:
            print('  [shift] %-46s FAIL  %s' % (name, detail))
            fails.append(name)

    base = run(runner, ONE_SPELLING)
    if base.get('error'):
        print('  [shift] could not exercise the page: %s' % base['error'])
        return 1
    check('one spelling: solo role found',
          len(base['solo']) == 1 and base['solo'][0]['shifts'] == 6,
          json.dumps(base['solo']))
    check('one spelling: overtime found',
          len(base['ot']) == 1 and base['ot'][0]['hours'] == 54,
          json.dumps(base['ot']))

    # The defect. Same roster, five spellings -- must match the clean answer.
    dirty = run(runner, FIVE_SPELLINGS)
    check('five spellings of one nurse: same solo role',
          dirty['solo'] == base['solo'], json.dumps(dirty['solo']))
    check('five spellings of one nurse: same overtime',
          dirty['ot'] == base['ot'], json.dumps(dirty['ot']))
    check('reports the spelling the user typed',
          bool(dirty['solo']) and dirty['solo'][0]['person'] == 'Dave Smith',
          json.dumps(dirty['solo']))

    roles = run(runner, ROLE_SPELLINGS)
    check('role spelled six ways is still one role',
          roles['solo'] == base['solo'], json.dumps(roles['solo']))

    # CONTROL. A fix that merged everyone would pass everything above. Two real
    # people covering alternate days are NOT a single point of failure and NOT
    # overtime, and must stay that way.
    two = run(runner, TWO_PEOPLE)
    check('two different people are NOT merged (no solo)',
          two['solo'] == [], json.dumps(two['solo']))
    check('two different people are NOT merged (no overtime)',
          two['ot'] == [], json.dumps(two['ot']))

    if fails:
        print('\nSHIFT COVERAGE GATE FAILED on %d check(s). A roster tool that loses a '
              'person to a spelling reports an all-clear over a real risk.' % len(fails))
        return 1
    print('  shift-coverage gate: identity holds, and distinct people stay distinct')
    return 0


if __name__ == '__main__':
    sys.exit(main())
