# -*- coding: utf-8 -*-
"""Does /money-leak-finder/ still refuse to reconcile work against invoices on the MONEY?

WHY THIS EXISTS. This page tells an owner which finished jobs were never
invoiced, and puts a dollar figure on it. It picks the column to join the two
files on by scoring overlap. Measured against the shipped page on 2026-08-19,
with two files whose ID columns shared nothing and whose amounts were all
distinct, it chose Amount <-> Amount and then reported:

    $800 uninvoiced, keyed as `800`

while SILENTLY HIDING a genuinely unbilled $650 job, because an unrelated
invoice happened to also be for $650. One wrong key produced a false all-clear
over real money AND a false accusation against a job that may well be billed.

The page HAD a guard that looked like it covered this -- a column whose values
repeat too often is rejected as "not an identifier". It does not cover it. That
filter only rejected the amount column in earlier testing because that fixture
happened to contain two jobs at the same price. With all-distinct amounts, the
ordinary case, it sails straight through. **A guard that happens to fire on your
fixture is not a guard**, and this file exists so that distinction is pinned.

/check/ took the identical defect and the identical fix on 2026-08-17. This page
never got the guard, which is the argument for a test rather than a second fix:
the same mistake has now been made twice on two pages.

WHAT IT GUARDS, IN BOTH DIRECTIONS. Refusing is only half the job. A "fix" that
refused everything would pass every case above and be far worse than the bug --
the tool would simply stop working. So the ordinary paths are pinned just as
hard: exact IDs find the gap, messy spellings of the same IDs still find it, and
a fully invoiced book reports nothing at all.

Run:  python _qa/test_money_leak.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PAGE = os.path.join(SITE, 'money-leak-finder', 'index.html')

# Four completed jobs. JOB-003 is the one never invoiced.
# Two jobs share $800 on purpose -- that repetition is what made the uniqueness
# filter LOOK like a money guard, so the amount-key cases below deliberately use
# a different book with all-distinct amounts.
JOBS = '\n'.join([
    'Job ID,Client,Amount,Status',
    'JOB-001,Acme Roofing,1200,Complete',
    'JOB-002,Bell Plumbing,800,Complete',
    'JOB-003,Cole Electric,800,Complete',
    'JOB-004,Dane HVAC,900,Complete',
])

# The same book with every amount distinct -- an ordinary book, and the one the
# uniqueness filter cannot help with.
UNIQ_JOBS = '\n'.join([
    'Job ID,Client,Amount,Status',
    'JOB-001,Acme Roofing,1200,Complete',
    'JOB-002,Bell Plumbing,800,Complete',
    'JOB-003,Cole Electric,650,Complete',
    'JOB-004,Dane HVAC,900,Complete',
])


def invoices(ids, amounts=('1200', '800', '900')):
    return '\n'.join(
        ['Invoice,Job ID,Amount,Date'] +
        ['INV-%d,%s,%s,2026-03-0%d' % (i + 1, ids[i], amounts[i], i + 1)
         for i in range(len(ids))])


EXACT = invoices(['JOB-001', 'JOB-002', 'JOB-004'])
LOWER = invoices(['job-001', 'job-002', 'job-004'])
PADDED = invoices([' JOB-001 ', ' JOB-002 ', ' JOB-004 '])
ALL_BILLED = invoices(['JOB-001', 'JOB-002', 'JOB-003', 'JOB-004'],
                      ('1200', '800', '800', '900'))

# No shared reference column at all. The amounts line up exactly.
AMOUNTS_ONLY = '\n'.join(['Ref,Amount,Date',
                          'R-1,1200,2026-03-01',
                          'R-2,800,2026-03-02',
                          'R-3,900,2026-03-03'])
# The masking case: an unrelated invoice shares the unbilled job's amount.
MASKING = '\n'.join(['Ref,Amount,Date',
                     'R-1,1200,2026-03-01',
                     'R-2,650,2026-03-02',
                     'R-3,900,2026-03-03'])

NODE = r"""
const fs = require('fs');
const page = fs.readFileSync(process.argv[2], 'utf8');
function block(sig){
  const i = page.indexOf(sig);
  if (i < 0) throw new Error('page no longer defines: ' + sig);
  let d = 0, st = false, j = i;
  for (; j < page.length; j++) {
    const c = page[j];
    if (c === '{') { d++; st = true; }
    else if (c === '}') { d--; if (st && d === 0) { j++; break; } }
  }
  return page.slice(i, j);
}
function topVars(){
  const out = [];
  const re = /^var\s+[A-Z_][A-Z0-9_]*\s*=/gm;
  let m;
  while ((m = re.exec(page)) !== null) {
    let i = m.index, depth = 0, j = i;
    for (; j < page.length; j++) {
      const c = page[j];
      if (c === '(' || c === '[' || c === '{') depth++;
      else if (c === ')' || c === ']' || c === '}') depth--;
      else if (c === ';' && depth === 0) { j++; break; }
    }
    out.push(page.slice(i, j));
  }
  return out.join('\n');
}
const NEED = ['parseCSV','colValues','normKey','money','parseDate','looksSettled',
              'detectJoin','detectAmount','detectClient','detectDesc','detectPaid',
              'detectDate','reconcile'];
const fns = NEED.map(n => block('function ' + n + '('));
const M = new Function(topVars() + '\n' + fns.join('\n') +
  '\nreturn {parseCSV:parseCSV, reconcile:reconcile, detectJoin:detectJoin};')();
function table(text){ const r = M.parseCSV(text); return {header:r[0], body:r.slice(1)}; }
const w = table(fs.readFileSync(process.argv[3], 'utf8'));
const v = table(fs.readFileSync(process.argv[4], 'utf8'));
const j = M.detectJoin(w, v);
const r = M.reconcile(w, v, new Date('2026-04-01'));
console.log(JSON.stringify({
  joinWork: j ? w.header[j.ai] : null,
  joinInv:  j ? v.header[j.bi] : null,
  error: r.error || null,
  total: r.never ? r.neverTotal : null,
  keys: r.never ? r.never.map(n => String(n.key)) : []
}));
"""


def run(runner, work, inv):
    d = tempfile.mkdtemp()
    pa, pb = os.path.join(d, 'work.csv'), os.path.join(d, 'inv.csv')
    io.open(pa, 'w', encoding='utf-8').write(work)
    io.open(pb, 'w', encoding='utf-8').write(inv)
    out = subprocess.run(['node', runner, PAGE, pa, pb],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return {'crashed': (out.stderr or '').strip().splitlines()[-1:]}
    return json.loads(out.stdout.strip().splitlines()[-1])


def main():
    if not os.path.exists(PAGE):
        print('  [money-leak] page missing: %s' % PAGE)
        return 1
    tmp = tempfile.mkdtemp()
    runner = os.path.join(tmp, 'run.js')
    io.open(runner, 'w', encoding='utf-8').write(NODE)

    fails = []

    def ok(name, cond, detail=''):
        if cond:
            print('  [money-leak] %-56s ok' % name)
        else:
            print('  [money-leak] %-56s FAIL  %s' % (name, str(detail)[:220]))
            fails.append(name)

    # 1. THE ORDINARY PATH, and the control for every refusal below. If this
    #    stops working, "it refused" cases would pass on a tool that does nothing.
    r = run(runner, JOBS, EXACT)
    ok('exact IDs: finds the one uninvoiced job',
       r.get('total') == 800 and r.get('keys') == ['JOB-003'], r)
    ok('and joins on the ID column, not the amount', r.get('joinWork') == 'Job ID', r)

    # 2. Messy spellings of the same IDs must still match. This is the defect the
    #    dirty-data probe found in 2026-08 and it must not come back.
    for label, inv in (('lower case', LOWER), ('padded with spaces', PADDED)):
        r = run(runner, JOBS, inv)
        ok('IDs %s still match: still $800, still JOB-003' % label,
           r.get('total') == 800 and r.get('keys') == ['JOB-003'], r)

    # 3. Nothing owed must report nothing. A tool that always finds a leak is
    #    worse than one that finds none -- it would be crying wolf about money.
    r = run(runner, JOBS, ALL_BILLED)
    ok('a fully invoiced book reports NO uninvoiced work',
       r.get('total') == 0 and r.get('keys') == [], r)

    # 4. THE DEFECT. All-distinct amounts, no shared ID column. Before the fix
    #    this joined Amount <-> Amount and answered confidently.
    r = run(runner, UNIQ_JOBS, AMOUNTS_ONLY)
    ok('a money column is NEVER chosen as the join key',
       r.get('joinWork') != 'Amount' and r.get('joinInv') != 'Amount', r)
    ok('and it refuses rather than reconciling on the wrong column',
       bool(r.get('error')), r)

    # 5. The direction that costs money. The unbilled job's amount also appears
    #    on an unrelated invoice, so an amount-join hides it completely.
    r = run(runner, UNIQ_JOBS, MASKING)
    ok('a real leak is not masked by an unrelated matching amount',
       bool(r.get('error')), r)
    ok('and no dollar figure is ever reported as a job reference',
       not any(k.replace('.', '').isdigit() for k in r.get('keys', [])), r)

    if fails:
        print('\nMONEY-LEAK CONTROL FAILED on %d check(s). This page states which finished '
              'work was never billed, and puts a dollar figure on it. Either it stopped '
              'finding real gaps, or it went back to reconciling on the money.' % len(fails))
        return 1
    print('  money-leak: finds the gap on IDs, refuses to invent one from amounts')
    return 0


if __name__ == '__main__':
    sys.exit(main())
