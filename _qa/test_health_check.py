# -*- coding: utf-8 -*-
"""Does /spreadsheet-health-check/ still find a duplicate row -- and only a real one?

WHY THIS EXISTS. This is the last of the nine live file-dropping tools to get a
test of what it actually reports. It was probed by hand in August and came back
CLEAN, which is the unusual outcome and exactly why it needs pinning: a
hand-check is one person looking once.

THE NON-FINDING WORTH PRESERVING. Its duplicate key is `r.join('')` -- no
separator. That reads like a collision waiting to happen, because ["ab","c"] and
["a","bc"] both become "abc", and predicting that wrongly is the useful part: it
does NOT reproduce on the live page, and the case below proves it. Anyone
reading that line in future will suspect it again; this is the answer, executable
rather than remembered.

Read the direction of each failure. A missed duplicate inflates every total built
on the sheet and says nothing. A FALSE duplicate accuses someone of pasting twice
when they did not. Both are pinned, because a detector that fires on everything
is not a detector -- and the "clean" cases here are what proved the checker was
actually running during the original clean result.

Run:  python _qa/test_health_check.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PAGE = os.path.join(SITE, 'spreadsheet-health-check', 'index.html')

NODE = r"""
const fs = require('fs');
const page = fs.readFileSync(process.argv[2], 'utf8');
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
/* analyze() reaches top-level constants; without them it throws on the first
   row. Balanced-bracket scan because DATE_SHAPES spans many lines. A missing
   one is a HARD ERROR -- a quietly empty module would make every "no finding"
   assertion in this file pass on nothing at all. */
function konst(name){
  const re = new RegExp('^var ' + name + ' *=', 'm');
  const m = re.exec(page);
  if (!m) throw new Error('page no longer defines const: ' + name);
  let i = m.index, depth = 0, j = i;
  for (; j < page.length; j++) {
    const c = page[j];
    if (c === '(' || c === '[' || c === '{') depth++;
    else if (c === ')' || c === ']' || c === '}') depth--;
    else if (c === ';' && depth === 0) { j++; break; }
  }
  return page.slice(i, j);
}
const CONSTS = ['DECISION', 'IDISH', 'DATE_SHAPES', 'MONTHS'];
const NEED = ['pad2', 'toISO', 'dateShape', 'numberShape', 'normalize', 'analyze'];
const src = CONSTS.map(konst).concat(NEED.map(block)).join('\n');
const M = new Function(src + '\nreturn {analyze: analyze, normalize: normalize};')();

const rows = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const res = M.analyze(rows);
/* normalize() is the FIX for what analyze() REPORTS, and each keeps its own
   copy of the duplicate key. Returning both lets one test hold them together. */
let removed = null;
try { removed = M.normalize(rows).removed; } catch (e) { removed = 'threw: ' + e.message; }
console.log(JSON.stringify({
  n: res.n,
  removed: removed,
  findings: res.findings.map(f => ({ sev: f.sev, title: f.title, where: f.where }))
}));
"""


def run(runner, rows):
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'rows.json')
    io.open(p, 'w', encoding='utf-8').write(json.dumps(rows))
    out = subprocess.run(['node', runner, PAGE, p],
                         capture_output=True, text=True, encoding='utf-8', timeout=60)
    if out.returncode != 0:
        return {'crashed': (out.stderr or '').strip()[-400:]}
    return json.loads(out.stdout.strip().splitlines()[-1])


def dup_titles(r):
    """Duplicate findings -- or a sentinel if the run produced no result at all.

    Returning [] for a CRASHED run is not harmless: while building this file the
    analyzer was throwing on every row, and two "reports NO duplicates"
    assertions cheerfully said ok because an absent result and a clean result
    looked identical. Only the row-count control caught it. An absence is
    evidence exactly when the tool actually ran, and not before.
    """
    if 'findings' not in r:
        return ['<<no result -- the run did not complete: %s>>' % str(r)[:120]]
    return [f['title'] for f in r['findings'] if 'duplicate' in f['title']]


HEAD = ['Client', 'City', 'Amount']


def main():
    if not os.path.exists(PAGE):
        print('  [health] page missing: %s' % PAGE)
        return 1
    tmp = tempfile.mkdtemp()
    runner = os.path.join(tmp, 'run.js')
    io.open(runner, 'w', encoding='utf-8').write(NODE)

    fails = []

    def ok(name, cond, detail=''):
        if cond:
            print('  [health] %-58s ok' % name)
        else:
            print('  [health] %-58s FAIL  %s' % (name, str(detail)[:240]))
            fails.append(name)

    # 0. The harness must be analysing rows at all, or every "no finding"
    #    assertion below is passing on an empty result.
    clean = [HEAD, ['Acme', 'Gainesville', '100'], ['Bell', 'Ocala', '200'],
             ['Cole', 'Tampa', '300'], ['Dane', 'Miami', '400']]
    r = run(runner, clean)
    ok('the analyzer reads every data row', r.get('n') == 4, r)

    # 1. A tidy sheet must not be accused of anything. THIS IS THE CONTROL for
    #    every detection case: a detector that fires on everything is not one.
    ok('a clean sheet reports NO duplicate rows', dup_titles(r) == [], r)

    # 2. A real repeated row is found, and counted once rather than twice.
    dupd = clean + [['Bell', 'Ocala', '200']]
    r = run(runner, dupd)
    ok('an exact repeated row IS reported', len(dup_titles(r)) == 1, r)
    ok('and exactly one duplicate is counted',
       dup_titles(r) and dup_titles(r)[0].startswith('1 exact duplicate row'), dup_titles(r))

    # 3. THE NON-FINDING. The key is a bare join with no separator, so
    #    ["ab","c"] and ["a","bc"] would collide if the concern were real.
    #    Constructed so the concatenations are identical and the rows are not.
    collide = [HEAD, ['ab', 'c', 'X'], ['a', 'bc', 'X'],
               ['Cole', 'Tampa', '300'], ['Dane', 'Miami', '400']]
    r = run(runner, collide)
    ok('rows that CONCATENATE alike are not called duplicates', dup_titles(r) == [], r)

    # 4. ...and the detector was genuinely running during case 3. Without this,
    #    a checker that had silently stopped would produce the same clean result
    #    and read as a passing non-finding.
    r = run(runner, collide + [['ab', 'c', 'X']])
    ok('the same sheet with a REAL repeat still reports one',
       len(dup_titles(r)) == 1, r)

    # 5. Severity is a judgement the page states out loud, and it is
    #    PROPORTIONAL, not a count. I guessed the opposite first and the tool was
    #    right: one repeat in a five-row sheet is a fifth of the sheet, and
    #    calling that merely "medium" would understate it. Measured before
    #    asserting -- 1 in 61 rows comes back medium, 1 in 4 comes back high.
    def sev_of(res):
        d = [f for f in res.get('findings', []) if 'duplicate' in f['title']]
        return d[0]['sev'] if d else None

    small = run(runner, [HEAD, ['a', 'b', '1'], ['c', 'd', '2'],
                         ['e', 'f', '3'], ['a', 'b', '1']])
    ok('one repeat in a tiny sheet is HIGH -- it is a fifth of the rows',
       sev_of(small) == 'high', small.get('findings'))

    big_rows = [HEAD] + [['C%d' % i, 'City%d' % i, str(i)] for i in range(60)]
    big = run(runner, big_rows + [['C5', 'City5', '5']])
    ok('the same single repeat in a big sheet is only MEDIUM',
       sev_of(big) == 'med', big.get('findings'))

    # 6. THE DRIFT GUARD, and the reason it exists is visible in the source: the
    #    duplicate key is written TWICE -- once in analyze(), which REPORTS "N
    #    exact duplicate rows", and once in normalize(), which REMOVES them. Two
    #    copies of one identity rule, agreeing only by having been written
    #    together, which is the shape that produced the three-parser problem.
    #    If they drift, the page tells an owner it found N and then hands back a
    #    cleaned sheet with a different number gone, and neither number is
    #    obviously the wrong one.
    three_dups = [HEAD, ['a', 'b', '1'], ['c', 'd', '2'], ['e', 'f', '3'],
                  ['a', 'b', '1'], ['c', 'd', '2'], ['a', 'b', '1']]
    r = run(runner, three_dups)
    reported = dup_titles(r)
    ok('the count it REPORTS is the count the fix REMOVES',
       reported and reported[0].startswith('3 exact duplicate rows') and r.get('removed') == 3,
       {'reported': reported, 'removed': r.get('removed')})

    # 7. Too little data must refuse rather than guess -- the same refusal
    #    discipline the other tools use when they cannot judge.
    r = run(runner, [HEAD, ['Acme', 'Gainesville', '100'], ['Bell', 'Ocala', '200']])
    ok('fewer than three rows refuses to judge',
       any('Not enough rows' in f['title'] for f in r.get('findings', [])), r)

    if fails:
        print('\nHEALTH-CHECK CONTROL FAILED on %d check(s). Either it stopped finding real '
              'repeated rows -- which inflates every total built on the sheet -- or it '
              'started accusing someone of pasting twice when they did not.' % len(fails))
        return 1
    print('  health-check: finds real repeats, and does not invent them from concatenation')
    return 0


if __name__ == '__main__':
    sys.exit(main())
