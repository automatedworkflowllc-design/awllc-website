# -*- coding: utf-8 -*-
"""Does /check/ still put the right dollar figure on unbilled work?

WHY THIS EXISTS. /check/ is the only tool that attaches MONEY to a finding, and
the number comes from joining two files on a shared column. Measured 2026-08-17
against the shipped page: the same two files, with the invoice side spelling job
IDs in lower case, went from

    $800 of finished work nobody invoiced   ->   NO FINDING AT ALL

on data identical in substance. Worse, it still reported a successful join --
because once the ID columns stopped matching, the best-scoring overlap left was
the two AMOUNT columns, and joining work to invoices on the amount says every
job was billed whenever the numbers happen to line up. The uninvoiced job's $800
appeared on another invoice, so the gap vanished. A confident all-clear over
real unbilled revenue.

That is the /money-leak-finder/ defect (third hard lesson) reappearing on a
different page, which is why it is worth a gate and not just a fix.

WHAT IT GUARDS, in both directions. Folding spellings together is half the job:
a "fix" that always reported $800 would pass every spelling case and be far
worse than the bug. So the controls carry the weight -- a fully invoiced book
must report NOTHING, two unrelated files must not join at all, and a money
column must never become the join key even when it is the only overlap left.

Run:  python _qa/test_check_reconcile.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PAGE = os.path.join(SITE, 'check', 'index.html')

# Four completed jobs. JOB-003 was never invoiced -- and its $800 also appears on
# another invoice, so a join that keys on the AMOUNT sees no gap at all.
JOBS = '\n'.join([
    'Job ID,Client,Amount,Status',
    'JOB-001,Acme Roofing,1200,Complete',
    'JOB-002,Bell Plumbing,800,Complete',
    'JOB-003,Cole Electric,800,Complete',
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
SPACED = invoices(['JOB 001', 'JOB 002', 'JOB 004'])
MIXED = invoices(['job 001', 'JOB-002', ' Job-004'])
# Every job invoiced, spellings still messy: the honest answer is nothing owed.
ALL_BILLED = '\n'.join([
    'Invoice,Job ID,Amount,Date',
    'INV-1,JOB-001,1200,2026-03-01',
    'INV-2,job-002,800,2026-03-02',
    'INV-3,JOB 003,800,2026-03-03',
    'INV-4,Job-004,900,2026-03-04',
])
UNRELATED = '\n'.join(['Product,SKU,Price', 'Widget,W-1,10',
                       'Gadget,G-2,20', 'Doodad,D-3,30'])

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
const fns = [];
const re = /^function ([A-Za-z_$][\w$]*)\(/gm;
let m;
while ((m = re.exec(page)) !== null) {
  if (['render', 'reportHTML', 'handleFiles'].includes(m[1])) continue;
  try { fns.push(block('function ' + m[1] + '(')); } catch (e) {}
}
const alias = page.split('\n').filter(l => /^var normName = normCompany;/.test(l)).join('\n');
const M = new Function(topVars() + '\n' + fns.join('\n') + '\n' + alias + '\nreturn {runAll:runAll};')();
const a = fs.readFileSync(process.argv[3], 'utf8');
const b = fs.readFileSync(process.argv[4], 'utf8');
const res = M.runAll([{name: 'a.csv', text: a}, {name: 'b.csv', text: b}]);
const money = res.findings.filter(f => f.money);
console.log(JSON.stringify({
  joined: res.reconciled,
  atRisk: res.atRisk,
  money: money.map(f => ({sev: f.sev, amount: f.money, title: f.title, detail: f.detail}))
}));
"""


def run(runner, a_text, b_text):
    d = tempfile.mkdtemp()
    pa, pb = os.path.join(d, 'a.csv'), os.path.join(d, 'b.csv')
    io.open(pa, 'w', encoding='utf-8').write(a_text)
    io.open(pb, 'w', encoding='utf-8').write(b_text)
    out = subprocess.run(['node', runner, PAGE, pa, pb],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return {'error': (out.stderr or '').strip().splitlines()[-1:]}
    return json.loads(out.stdout.strip().splitlines()[-1])


def main():
    if not os.path.exists(PAGE):
        print('  [check] page missing: %s' % PAGE)
        return 1
    tmp = tempfile.mkdtemp()
    runner = os.path.join(tmp, 'run.js')
    io.open(runner, 'w', encoding='utf-8').write(NODE)

    fails = []

    def ok(name, cond, detail=''):
        if cond:
            print('  [check] %-48s ok' % name)
        else:
            print('  [check] %-48s FAIL  %s' % (name, detail))
            fails.append(name)

    base = run(runner, JOBS, EXACT)
    if base.get('error'):
        print('  [check] could not exercise the page: %s' % base['error'])
        return 1
    ok('exact IDs: $800 of unbilled work found',
       bool(base.get('joined')) and abs(base.get('atRisk', -1) - 800) < 0.01
       and len(base.get('money', [])) == 1,
       json.dumps(base))

    # THE DEFECT. Same truth, different spelling -- must not change the answer.
    for label, text in (('lower case', LOWER), ('padded with spaces', PADDED),
                        ('space instead of dash', SPACED), ('mixed spellings', MIXED)):
        got = run(runner, JOBS, text)
        ok('%s: same answer as exact IDs' % label,
           bool(got.get('joined')) and abs(got.get('atRisk', -1) - 800) < 0.01,
           json.dumps(got))

    ok("the unbilled job is named in the file's own spelling",
       'JOB-003' in json.dumps(base.get('money', [])), json.dumps(base.get('money')))

    # CONTROLS. A fix that always says $800 passes everything above.
    clean = run(runner, JOBS, ALL_BILLED)
    ok('every job invoiced (messy spellings): reports nothing',
       bool(clean.get('joined')) and abs(clean.get('atRisk', -1)) < 0.01
       and not clean.get('money'),
       json.dumps(clean))

    far = run(runner, JOBS, UNRELATED)
    ok('two unrelated files do not join at all',
       far.get('joined') is False, json.dumps(far))

    # A money column must never BE the key -- that is what turned "no match"
    # into a confident all-clear. With the IDs removed entirely the amounts
    # still overlap, and the tool must decline rather than reconcile on them.
    no_ids = '\n'.join(['Client,Amount,Status', 'Acme Roofing,1200,Complete',
                        'Bell Plumbing,800,Complete', 'Cole Electric,800,Complete',
                        'Dane HVAC,900,Complete'])
    amt_only = '\n'.join(['Invoice,Amount,Date', 'INV-1,1200,2026-03-01',
                          'INV-2,800,2026-03-02', 'INV-3,900,2026-03-03'])
    amt = run(runner, no_ids, amt_only)
    ok('amount columns alone are not an identity',
       amt.get('joined') is False, json.dumps(amt))

    if fails:
        print('\nCHECK RECONCILE GATE FAILED on %d check(s). This page puts a dollar '
              'figure on unbilled work; a join it gets wrong is a number someone acts on.'
              % len(fails))
        return 1
    print('  check gate: the money figure survives how the IDs are spelled')
    return 0


if __name__ == '__main__':
    sys.exit(main())
