# -*- coding: utf-8 -*-
"""Does /demo/ still name exactly ONE invoice as the oldest?

WHY THIS EXISTS. "Oldest open -- call first" is a claim about ONE invoice. On
2026-08-13, pasting a deliberately messy book into the live page printed it
TWICE: the badge was attached to any invoice past its threshold, so a book with
two old invoices contradicted itself on screen -- and contradicted the summary
above it, which names a single account.

That is precisely the self-contradiction this product is sold to find, on the
page every outreach email points at. It was fixed the same day. Nothing has ever
guarded the fix, and the SAMPLE BOOK CANNOT: it contains exactly one sufficiently
old invoice, so the defect is invisible to it by construction. That is the third
hard lesson in one sentence -- a clean fixture cannot find a dirty-data bug --
and it is why these rows are built here rather than read from the sample.

WHAT IT GUARDS, IN BOTH DIRECTIONS. "Exactly one" has two failure modes and a
test for only the first is worse than useless:
  - more than one row claims to be oldest (the defect), and
  - NO row claims it when one genuinely is the oldest overdue invoice, which a
    naive "just remove the badge" fix would produce and which would pass every
    duplicate-check ever written.
Both are pinned, along with the tier labels the badge sits among, so a fix
cannot quietly flatten "past 90 days" and "crossed 60 days" into silence.

Run:  python _qa/test_demo_rows.py
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

# The page emits a literal em dash here, not the HTML entity -- asserting the
# entity failed 4 cases on a page that was behaving correctly. Read what it
# actually prints before deciding the tool is wrong.
BADGE = 'oldest open ' + chr(0x2014) + ' call first'   # em dash, built not typed

NODE = r"""
const fs = require('fs');
const page = fs.readFileSync(process.argv[2], 'utf8');

/* The helpers here are INDENTED inside a closure, so an anchored /^function/
   finds none of them and would silently reconstruct an empty module. Matching
   with optional leading whitespace, and throwing by name when a function is
   missing, is what keeps "the page changed shape" from looking like "the tests
   pass". */
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
function konst(name){
  const re = new RegExp('^[ \\t]*var ' + name + '\\s*=[^;]*;', 'm');
  const m = re.exec(page);
  if (!m) throw new Error('page no longer defines const: ' + name);
  return m[0];
}

const src = [konst('MON'),
             block('addDays'), block('fmtDay'), block('money'),
             block('esc'), block('rowsHTML')].join('\n');
const M = new Function(src + '\nreturn {rowsHTML: rowsHTML};')();

const items = JSON.parse(fs.readFileSync(process.argv[3], 'utf8')).map(function (r) {
  return { customer: r.customer, days: r.days, amount: r.amount,
           due: new Date('2026-01-01T00:00:00') };
});
const html = M.rowsHTML(items, false);
console.log(JSON.stringify({ html: html, rows: (html.match(/class="drow"/g) || []).length }));
"""


def rows(*specs):
    """specs are (customer, days) -- days None means the invoice carries no date."""
    return [{'customer': c, 'days': d, 'amount': 1000 + i}
            for i, (c, d) in enumerate(specs)]


def run(runner, items):
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'items.json')
    io.open(p, 'w', encoding='utf-8').write(json.dumps(items))
    out = subprocess.run(['node', runner, PAGE, p], capture_output=True, text=True, encoding='utf-8', timeout=60)
    if out.returncode != 0:
        return {'crashed': (out.stderr or '').strip().splitlines()[-1:]}
    return json.loads(out.stdout.strip().splitlines()[-1])


def main():
    if not os.path.exists(PAGE):
        print('  [demo] page missing: %s' % PAGE)
        return 1
    tmp = tempfile.mkdtemp()
    runner = os.path.join(tmp, 'run.js')
    io.open(runner, 'w', encoding='utf-8').write(NODE)

    fails = []

    def ok(name, cond, detail=''):
        if cond:
            print('  [demo] %-58s ok' % name)
        else:
            print('  [demo] %-58s FAIL  %s' % (name, str(detail)[:220]))
            fails.append(name)

    # 0. The harness must actually be rendering rows. Without this, every
    #    "the badge appears once" assertion could be passing on empty output.
    r = run(runner, rows(('Acme', 120), ('Bell', 100), ('Cole', 45)))
    ok('the page renders one row per invoice', r.get('rows') == 3, r)

    # 1. THE DEFECT. Three overdue invoices, only one may be called the oldest.
    ok('exactly ONE row is named oldest, with three overdue',
       r.get('html', '').count(BADGE) == 1, r.get('html', '')[:200])

    # 2. It must be the OLDEST one, not merely the first badge emitted. `items`
    #    arrives sorted oldest-first, so that is row 0 -- Acme.
    html = r.get('html', '')
    ok('and it is the oldest invoice that carries it',
       html.index(BADGE) < html.index('Bell') if BADGE in html and 'Bell' in html else False,
       html[:200])

    # 3. THE OTHER DIRECTION. One overdue invoice must still be named -- a "fix"
    #    that simply stopped emitting the badge would pass case 1 forever.
    r1 = run(runner, rows(('Solo', 95), ('Fresh', 5)))
    ok('a single overdue invoice IS still named oldest',
       r1.get('html', '').count(BADGE) == 1, r1.get('html', '')[:200])

    # 4. And nothing is named when nothing is overdue. A badge pinned to row 0
    #    unconditionally would satisfy every case above.
    r0 = run(runner, rows(('Fresh', 5), ('Newer', 2)))
    ok('nothing is named oldest when nothing is overdue',
       r0.get('html', '').count(BADGE) == 0, r0.get('html', '')[:200])

    # 5. The tiers the badge sits among must survive. Collapsing them into
    #    silence would "fix" the duplicate by removing the information.
    h = r.get('html', '')
    ok('the second-oldest still gets its own age tier, not the badge',
       'past 90 days' in h, h[:240])

    # 6. An undated invoice is not the oldest anything -- age is unknown, and
    #    guessing is the failure this page's own design notes are written against.
    r2 = run(runner, rows(('NoDate', None), ('Acme', 120)))
    ok('an undated invoice is reported as unknown, not aged',
       'age unknown' in r2.get('html', ''), r2.get('html', '')[:200])
    ok('and the badge still lands on the genuinely oldest dated invoice',
       r2.get('html', '').count(BADGE) == 1, r2.get('html', '')[:200])

    if fails:
        print('\nDEMO CONTROL FAILED on %d check(s). /demo/ is the page every outreach email '
              'points at. Either two rows are claiming to be the oldest again, or the claim '
              'stopped being made at all.' % len(fails))
        return 1
    print('  demo: exactly one oldest invoice, named only when one exists')
    return 0


if __name__ == '__main__':
    sys.exit(main())
