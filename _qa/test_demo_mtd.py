# -*- coding: utf-8 -*-
"""Does /demo/ report MONTHLY REVENUE as the money actually invoiced that month?

WHY THIS EXISTS. Found 2026-08-28 by a dirty-data dry run, hours before the first
real inbound mini-demo. `monthSum()` did not sum invoices -- it read the WEEKLY
series and spread each week's value evenly across its seven days
(`perDay = wk.value / wk.days`), then summed the days falling in the month. Any
week straddling a month boundary therefore split its money by day-count rather
than by invoice date.

Measured, on a two-invoice file: $900 dated 2026-08-01 and $1,200 dated
2026-08-15. True August total $2,100. The page printed $1,457. Aug 1 2026 is a
Saturday, so its Monday-week is Jul 27 - Aug 2; only 2 of those 7 days are in
August, so the $900 contributed 900*2/7 = $257 instead of $900.
2100 - 642.86 = 1457.14 -> "$1,457". Reproduced on two separate files.

WHY IT MATTERS MORE THAN THE ARITHMETIC. Directly beneath that tile the page
says, verbatim: "Every line is arithmetic on the file you loaded -- no estimates,
no industry averages". `wk.value / wk.days` IS an estimate. A client checking the
headline revenue against their own books finds it does not match, on a page that
just promised it would -- the exact failure this product is sold to catch.

The error only appears near month boundaries, which is when a month-end dashboard
gets built. The sample book cannot see it: its own weeks are synthetic, so there
is no true daily answer for it to be wrong about. A clean fixture cannot find a
dirty-data bug.

BOTH DIRECTIONS ARE PINNED. A "fix" that always trusted day totals would break
the sample dashboard, which genuinely has no day-level data and must keep the
weekly spread. So:
  - with day totals present, the month equals the exact invoiced sum, and
  - with none present, the old weekly-spread behaviour survives untouched.

Run:  python _qa/test_demo_mtd.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PAGE = os.path.join(SITE, 'demo', 'index.html')

NODE = r"""
const fs = require('fs');
const page = fs.readFileSync(process.argv[2], 'utf8');

/* Same extractor shape as test_demo_rows.py: helpers are indented inside a
   closure, so an anchored /^function/ finds none of them and would silently
   reconstruct an empty module. Throw by name instead. */
function block(name){
  const re = new RegExp('^[ \\t]*function ' + name + '\\(', 'm');
  const m = re.exec(page);
  if (!m) throw new Error('page no longer defines: ' + name);
  const i = m.index;
  let d = 0, st = false, j = i;
  for (; j < page.length; j++) {
    const c = page[j];
    if (c === '{') { d++; st = true; }
    else if (c === '}') { d--; if (st && d === 0) { j++; break; } }
  }
  return page.slice(i, j);
}

const spec = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const weeks = spec.weeks.map(w => ({ start: new Date(w.start + 'T00:00:00'),
                                     value: w.value, days: w.days }));
const dayTotals = (spec.dayTotals || []).map(d => ({ start: new Date(d.start + 'T00:00:00'),
                                                     value: d.value }));

const src = [block('addDays'), block('monthSum')].join('\n');
/* weeks/dayTotals are closure variables on the page; supply them as parameters
   so the extracted function sees exactly what it sees in the browser. */
const make = new Function('weeks', 'dayTotals', src + '\nreturn {monthSum: monthSum};');
const M = make(weeks, dayTotals);

const ref = new Date(spec.month + '-01T00:00:00');
console.log(JSON.stringify({ sum: M.monthSum(ref, spec.dayLimit) }));
"""


def run(runner, spec):
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'spec.json')
    io.open(p, 'w', encoding='utf-8').write(json.dumps(spec))
    out = subprocess.run(['node', runner, PAGE, p], capture_output=True,
                         text=True, encoding='utf-8', timeout=60)
    if out.returncode != 0:
        return {'crashed': (out.stderr or '').strip().splitlines()[-1:]}
    return json.loads(out.stdout.strip().splitlines()[-1])


# The real shape, taken from the reproduction: $900 invoiced Sat 2026-08-01 and
# $1,200 on 2026-08-15. Aug 1's Monday-week starts Jul 27 and carries only that
# $900; the Aug 10 week carries the $1,200.
STRADDLE = {
    'month': '2026-08',
    'dayLimit': 28,
    'weeks': [
        {'start': '2026-07-27', 'value': 900,  'days': 7},
        {'start': '2026-08-10', 'value': 1200, 'days': 7},
    ],
    'dayTotals': [
        {'start': '2026-08-01', 'value': 900},
        {'start': '2026-08-15', 'value': 1200},
    ],
}


def main():
    if not os.path.exists(PAGE):
        print('  [mtd] page missing: %s' % PAGE)
        return 1
    tmp = tempfile.mkdtemp()
    runner = os.path.join(tmp, 'run.js')
    io.open(runner, 'w', encoding='utf-8').write(NODE)

    fails = []

    def ok(name, cond, detail=''):
        if cond:
            print('  [mtd] %-58s ok' % name)
        else:
            print('  [mtd] %-58s FAIL  %s' % (name, str(detail)[:200]))
            fails.append(name)

    # 0. Control: the harness must actually be computing something. Without this
    #    every "equals N" assertion below could be passing on a crash.
    r0 = run(runner, dict(STRADDLE, dayTotals=[], weeks=[{'start': '2026-08-10',
                                                          'value': 1200, 'days': 7}]))
    ok('harness computes a month from weeks at all', r0.get('sum') == 1200, r0)

    # 1. THE DEFECT. A week straddling the month boundary must not split its
    #    money by day-count. All $900 was invoiced on Aug 1.
    r1 = run(runner, STRADDLE)
    ok('a month-boundary week counts by invoice date, not per-day spread',
       r1.get('sum') == 2100, r1)

    # 2. THE OTHER DIRECTION. With no day-level data -- the sample book, whose
    #    weeks are synthetic -- the weekly spread must survive exactly as before,
    #    or the sample dashboard changes for no reason.
    r2 = run(runner, dict(STRADDLE, dayTotals=[]))
    ok('with no day data the weekly spread is unchanged (1457)',
       r2.get('sum') == 1457, r2)

    # 3. A month with no straddling week is unaffected either way, so the fix
    #    cannot be "always return the day sum and hope".
    clean = {'month': '2026-08', 'dayLimit': 28,
             'weeks': [{'start': '2026-08-10', 'value': 1200, 'days': 7}],
             'dayTotals': [{'start': '2026-08-15', 'value': 1200}]}
    ok('a fully-inside-the-month week is the same by either route',
       run(runner, clean).get('sum') == 1200, clean)

    # 4. The day-limit cut-off still applies -- MTD is "so far this month", and a
    #    later invoice must not be pulled into a to-date figure.
    late = {'month': '2026-08', 'dayLimit': 10,
            'weeks': [{'start': '2026-08-10', 'value': 1200, 'days': 7}],
            'dayTotals': [{'start': '2026-08-15', 'value': 1200}]}
    r4 = run(runner, late)
    ok('an invoice after the day cut-off is excluded', r4.get('sum') == 0, r4)

    print('\n  [mtd] %s' % ('ALL PASS' if not fails else 'FAILED: ' + ', '.join(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
