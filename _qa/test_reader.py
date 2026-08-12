# -*- coding: utf-8 -*-
"""Gate: the shipped xlsx reader must actually READ A SPREADSHEET.

WHY THIS EXISTS. On 2026-08-12 a scope bug in the shared reader shipped to five
live tools -- a ReferenceError on every file drop -- and every gate stayed green,
because not one of them opens a spreadsheet. They check structure, links,
metadata and copy. Five tools whose entire job is reading files could be wholly
broken while the suite reported clean.

  question:   does the reader in the SHIPPED page still read a real workbook?
  blind spot: it proves the reader parses; it does not prove any tool's analysis
              of what it read is correct.

The fixture is built here, in memory, with a known number of formulas -- no
committed binary, nothing to go stale, and it works on a fresh clone. The count
is the point: a reader that silently returns nothing is the exact failure that
got through, and "0 formulas" and "a workbook with no formulas" must never look
the same to this gate.
"""
import io, os, json, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
PAGES = ['check/index.html', 'demo/index.html', 'money-leak-finder/index.html',
         'spreadsheet-health-check/index.html', 'duplicate-customer-finder/index.html']
EXPECT_FORMULAS = 12
EXPECT_CELLS = 36


def fixture_sheet_xml():
    """12 rows x 3 cells; the third cell of each row is a formula."""
    rows = []
    for r in range(1, 13):
        rows.append(
            '<row r="%d">'
            '<c r="A%d"><v>%d</v></c>'
            '<c r="B%d"><v>%d</v></c>'
            '<c r="C%d"><f>A%d*B%d</f><v>%d</v></c>'
            '</row>' % (r, r, r, r, r * 2, r, r, r, r * r * 2))
    return '<worksheet><sheetData>%s</sheetData></worksheet>' % ''.join(rows)


NODE = r"""
const fs = require('fs');
const page = fs.readFileSync(process.argv[2], 'utf8');
const i = page.indexOf('function parseWS(ws){');
if (i < 0) { console.log(JSON.stringify({error: 'parseWS not found in page'})); process.exit(0); }
let d = 0, started = false, j = i;
for (; j < page.length; j++) {
  const c = page[j];
  if (c === '{') { d++; started = true; }
  else if (c === '}') { d--; if (started && d === 0) { j++; break; } }
}
const stubs = 'var sst=[],dateStyle=[];function unesc(s){return String(s);}'
            + 'function texts(){return "";}function serialToISO(){return null;}';
let parseWS;
try { parseWS = new Function(stubs + page.slice(i, j) + ' return parseWS;')(); }
catch (e) { console.log(JSON.stringify({error: 'reader will not compile: ' + e.message})); process.exit(0); }
let cells = 0, formulas = 0;
try {
  const rows = parseWS(fs.readFileSync(process.argv[3], 'utf8'));
  for (const row of rows) cells += row.length;
  for (const row of (rows.formulaRows || [])) for (const c of (row || [])) if (c) formulas++;
} catch (e) { console.log(JSON.stringify({error: 'reader THREW on a real sheet: ' + e.message})); process.exit(0); }
console.log(JSON.stringify({cells: cells, formulas: formulas}));
"""


def main():
    tmp = tempfile.mkdtemp()
    sheet = os.path.join(tmp, 'sheet1.xml')
    io.open(sheet, 'w', encoding='utf-8').write(fixture_sheet_xml())
    runner = os.path.join(tmp, 'run.js')
    io.open(runner, 'w', encoding='utf-8').write(NODE)

    bad = 0
    for rel in PAGES:
        path = os.path.join(SITE, rel)
        if not os.path.exists(path):
            print('  [reader] %s missing' % rel); bad += 1; continue
        try:
            out = subprocess.run(['node', runner, path, sheet],
                                 capture_output=True, text=True, timeout=60).stdout.strip()
            res = json.loads(out.splitlines()[-1])
        except Exception as e:
            print('  [reader] %s could not be exercised: %s' % (rel, e)); bad += 1; continue
        if res.get('error'):
            print('  [reader] %s -- %s' % (rel, res['error'])); bad += 1; continue
        if res['formulas'] != EXPECT_FORMULAS or res['cells'] != EXPECT_CELLS:
            print('  [reader] %s read %s cells / %s formulas, expected %s / %s'
                  % (rel, res['cells'], res['formulas'], EXPECT_CELLS, EXPECT_FORMULAS))
            bad += 1
        else:
            print('  [reader] %-42s %s cells, %s formulas  ok' % (rel, res['cells'], res['formulas']))
    if bad:
        print('\nREADER GATE FAILED on %d page(s) -- a tool that cannot read a file is broken '
              'no matter how clean the rest of the site looks.' % bad)
        return 1
    print('  reader gate: all %d page(s) read a real sheet correctly' % len(PAGES))
    return 0


if __name__ == '__main__':
    sys.exit(main())
