# -*- coding: utf-8 -*-
"""Does /duplicate-customer-finder/ still tell a FACT from a GUESS?

WHY THIS EXISTS. This page is the reference implementation of the house identity
rule -- "the only one that got it right, because it was the only one written
while thinking about names". Three other tools were fixed by copying what it
does. Nothing has ever tested it.

It groups in two passes and they are NOT the same kind of claim:

  1. EXACT match after normalising case, punctuation, & / and, and legal
     suffixes. Two spellings of one company. Stated as fact.
  2. EDIT DISTANCE -- a typo pass, threshold scaling with length. Stated as a
     SUGGESTION: the group renders with a `soft` class and says "worth a human
     glance", never "these are the same client".

That separation is the load-bearing part. The workspace rule is exact-match
grouping and NEVER its edit-distance half on a page that states findings as fact
about a named client -- so if a future edit let pass 2 render like pass 1, this
page would assert that two differently-named businesses are one, in public, on
the strength of a spelling distance. That is the third hard lesson's worst case:
a wrong VERDICT closes the question, where a wrong number invites a second look.

BOTH DIRECTIONS. A normaliser that merged everything would pass every "these
group" case and be far worse than none, so genuinely different companies must
stay apart -- and short names must not be fuzzy-merged just because they are
short.

Run:  python _qa/test_duplicate_finder.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PAGE = os.path.join(SITE, 'duplicate-customer-finder', 'index.html')

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
const alias = (/^var normName = \w+;/m.exec(page) || [null])[0];
if (!alias) throw new Error('page no longer binds normName to a normaliser');

/* The identity block declares its regexes as top-level consts; without them
   normCompany throws ReferenceError on the first name. Pulled in by name, and
   MISSING ONE IS A HARD ERROR rather than a quietly empty module. */
function konst(name){
  const re = new RegExp('^var ' + name + ' *=[^;]*;', 'm');
  const m = re.exec(page);
  if (!m) throw new Error('page no longer defines const: ' + name);
  return m[0];
}

const src = [konst('ID_NOISE'), konst('LEGAL_SUFFIX'),
             block('normCompany'), block('normPerson'), alias,
             block('withinEdits'), block('findGroups')].join('\n');
const M = new Function(src +
  '\nreturn {findGroups: findGroups, normName: normName, normCompany: normCompany,' +
  ' normPerson: normPerson};')();

const names = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const groups = M.findGroups(names);
console.log(JSON.stringify({
  alias: alias,
  groups: groups.map(g => ({ canonical: g.canonical, forms: g.forms,
                             rows: g.rows, fuzzy: !!g.fuzzy })),
  emptyKeyCompany: M.normCompany('Sons'),
  emptyKeyPerson: M.normPerson('Sons')
}));
"""


def run(runner, names):
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'names.json')
    io.open(p, 'w', encoding='utf-8').write(json.dumps(names))
    out = subprocess.run(['node', runner, PAGE, p],
                         capture_output=True, text=True, encoding='utf-8', timeout=60)
    if out.returncode != 0:
        return {'crashed': (out.stderr or '').strip().splitlines()[-1:]}
    return json.loads(out.stdout.strip().splitlines()[-1])


def main():
    if not os.path.exists(PAGE):
        print('  [dupfinder] page missing: %s' % PAGE)
        return 1
    tmp = tempfile.mkdtemp()
    runner = os.path.join(tmp, 'run.js')
    io.open(runner, 'w', encoding='utf-8').write(NODE)

    fails = []

    def ok(name, cond, detail=''):
        if cond:
            print('  [dupfinder] %-56s ok' % name)
        else:
            print('  [dupfinder] %-56s FAIL  %s' % (name, str(detail)[:240]))
            fails.append(name)

    # 1. EXACT: three spellings of one company, differing only by case,
    #    punctuation and legal suffix. One group, and NOT a guess.
    r = run(runner, ['Acme Roofing', 'ACME ROOFING LLC', 'Acme Roofing, Inc.'])
    g = (r.get('groups') or [{}])[0]
    ok('three spellings of one company make one group',
       len(r.get('groups', [])) == 1 and len(g.get('forms', [])) == 3, r)
    ok('and it is reported as a FACT, not a fuzzy guess', g.get('fuzzy') is False, r)
    ok('the count is the rows, not the spellings', g.get('rows') == 3, r)

    # 2. THE CONTROL for all of the above. A normaliser that folded everything
    #    together would satisfy every case in this file except this one.
    r = run(runner, ['Acme Roofing', 'Beta Plumbing', 'Cole Electric'])
    ok('genuinely different companies are NOT grouped', r.get('groups') == [], r)

    # 3. EDIT DISTANCE is allowed to group -- but must mark itself as a guess.
    r = run(runner, ['Acme Roofing', 'Acme Roofng', 'Acme Roofing'])
    g = (r.get('groups') or [{}])[0]
    ok('a typo is still caught', len(g.get('forms', [])) == 2, r)
    ok('but a typo group is flagged FUZZY, so the page can soften it',
       g.get('fuzzy') is True, r)

    # 4. Short unrelated names must not be swept together by the typo pass --
    #    the threshold scales with length precisely so this cannot happen.
    r = run(runner, ['Ash Ltd', 'Oak Ltd'])
    ok('two short unrelated names stay apart', r.get('groups') == [], r)

    # 5. THE NORMALISER BINDING. This is a company tool and must use the company
    #    rule; normPerson deliberately does NOT strip legal suffixes, so binding
    #    it here would stop "Inc"/"LLC" spellings folding together at all.
    r = run(runner, ['Acme Roofing'])
    ok('the page binds normName to the COMPANY rule',
       r.get('alias') == 'var normName = normCompany;', r.get('alias'))

    # 6. And the reason the two rules must stay distinct, pinned here because
    #    this page owns the rule: under the COMPANY rule the surname "Sons"
    #    normalises to the empty string. A person called Sons would key to
    #    nothing and merge with every other empty-keyed person, which is why
    #    normPerson must never strip suffixes.
    ok('normCompany empties a bare legal-suffix word', r.get('emptyKeyCompany') == '', r)
    ok('normPerson does NOT, so surnames survive', r.get('emptyKeyPerson') == 'sons', r)

    # 7. Presentation. SOURCE-LEVEL and therefore weaker than everything above --
    #    said plainly rather than dressed up as behavioural. The render reads the
    #    DOM, so driving it headlessly is not worth the harness; what this pins is
    #    that the two kinds of group still get DIFFERENT wording keyed off `fuzzy`.
    src = io.open(PAGE, encoding='utf-8').read()
    ok('a fuzzy group still renders softened and hedged',
       "g.fuzzy ? ' soft'" in src and 'worth a human glance' in src,
       'the soft class or the hedge wording is gone')
    ok('and an exact group still states it plainly',
       'identical once case, punctuation and legal suffixes are ignored' in src,
       'the exact-match wording is gone')

    if fails:
        print('\nDUPLICATE-FINDER CONTROL FAILED on %d check(s). This page is the reference '
              'implementation of the identity rule three other tools were fixed against. '
              'Either it stopped folding real spelling variants, or it started asserting a '
              'typo match as fact about a named business.' % len(fails))
        return 1
    print('  dupfinder: exact matches stated as fact, typo matches marked as guesses')
    return 0


if __name__ == '__main__':
    sys.exit(main())
