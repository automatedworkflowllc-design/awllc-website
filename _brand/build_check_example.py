#!/usr/bin/env python3
"""Build /check/example/ -- a real report, visible without uploading anything.

The conversion problem this solves: every free tool is gated behind "drop a
file." A prospect who is curious but not yet willing to hand over their books
cannot see a single line of output, so they leave having seen nothing. That is
the wrong order -- proof should come before the ask.

The important property is that this page is NOT a mockup. It is produced by
executing the analyzer that ships inside /check/ against the same two sample
files the tool offers, and rendering the result through the tool's own
reportHTML(). If the analyzer changes, this page changes with it; if the
analyzer breaks, this build fails rather than serving a stale screenshot of a
result the tool no longer produces.

That matters more than it sounds. A hand-written "example report" is a claim
about what the software does. This is the software doing it.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
TOOL = ROOT / 'check' / 'index.html'
OUT_DIR = ROOT / 'check' / 'example'

TITLE = 'Example Report — See What The Free File Check Finds'
DESC = ('A real report from our free business file check, run on two sample files. '
        'See exactly what it finds before you upload anything of your own.')
CANON = 'https://automatedworkflowllc.com/check/example/'

# Node harness: load the tool's own script, run it, hand back the report.
# The DOM stub is deliberately complete enough that the page's wiring code runs
# untouched -- stubbing too little produced a false "this page is broken" once
# already, and the fix was the harness, not the page.
HARNESS = r"""
const fs=require('fs'), vm=require('vm');
const s=fs.readFileSync(process.argv[2],'utf8');
let js=s.substring(s.indexOf('<script>', s.indexOf('</footer>'))+8);
js=js.substring(0, js.lastIndexOf('</script>'));
js=js.replace(/\(function\(\)\{/,'').replace(/\}\)\(\);\s*$/,'');
const el=()=>{const e={style:{},dataset:{},files:[],value:'0',textContent:'',innerHTML:'',
  addEventListener(){},removeEventListener(){},classList:{add(){},remove(){},toggle(){},contains:()=>false},
  scrollIntoView(){},click(){},setAttribute(){},getAttribute:()=>null,appendChild(){},removeChild(){},
  querySelector:()=>el(),querySelectorAll:()=>[],closest:()=>el(),focus(){}};return e;};
const doc={getElementById:()=>el(),querySelector:()=>el(),querySelectorAll:()=>[],
  createElement:()=>el(),body:el(),documentElement:el(),addEventListener(){}};
const ctx=vm.createContext({document:doc,FileReader:function(){this.readAsText=()=>{}},
  alert:()=>{},Blob:function(){},URL:{createObjectURL:()=>'',revokeObjectURL:()=>{}},console,setTimeout,window:{}});
vm.runInContext(js, ctx);
const res=ctx.runAll([{name:'sample-jobs.csv',text:ctx.SAMPLE_A},
                      {name:'sample-invoices.csv',text:ctx.SAMPLE_B}]);
process.stdout.write(JSON.stringify({
  report: ctx.reportHTML(res),
  atRisk: res.atRisk,
  findings: res.findings.length,
  high: res.findings.filter(f=>f.sev==='high').length,
  meta: res.meta
}));
"""

PAGE_CSS = """
/* ---- example report ---- */
.ex-lede{max-width:40rem;color:var(--ink-soft)}
.ex-strip{display:flex;gap:.6rem;flex-wrap:wrap;margin:1.4rem 0}
.ex-kpi{border:1px solid var(--line);border-radius:.7rem;padding:.7rem 1rem;background:var(--card)}
.ex-kpi b{display:block;font-family:var(--mono);font-size:1.5rem;line-height:1.1}
.ex-kpi.k-bad b{color:#B4452C}
.ex-kpi span{font-size:.72rem;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.06em}
.ex-frame{border:1px solid var(--line-strong);border-radius:12px;background:var(--card);
padding:1.4rem 1.6rem;margin:1.4rem 0}
.ex-frame .f{background:var(--bg-soft);border:1px solid var(--line);border-left:4px solid var(--line-strong);
border-radius:.5rem;padding:.8rem 1rem;margin:0 0 .5rem}
.ex-frame .f.high{border-left-color:#B4452C}
.ex-frame .f.med{border-left-color:#A8842B}
.ex-frame .f h3{margin:0 0 .2rem;font-size:1rem}
.ex-frame .f p{margin:.2rem 0 0;color:var(--ink-soft);font-size:.9rem}
.ex-frame .s{font-family:var(--mono);font-size:.78rem;color:var(--ink-soft)}
.ex-frame .file{border:1px solid var(--line);border-radius:.5rem;padding:.5rem .8rem;
margin:0 0 .4rem;background:var(--bg-soft);font-size:.85rem}
.ex-frame .risk{border:1px solid var(--line-strong);border-left:4px solid #B4452C;background:var(--bg-soft);
border-radius:.5rem;padding:.8rem 1rem;margin:0 0 1rem}
.ex-frame .risk strong{font-size:1.3rem;font-family:var(--mono)}
.ex-frame .sub{color:var(--ink-soft);font-size:.85rem;margin:0 0 1.2rem}
.ex-note{border-left:4px solid var(--accent);background:var(--card);border-radius:.6rem;
padding:1rem 1.2rem;color:var(--ink-soft);font-size:.92rem;margin:1.4rem 0}
.ex-cta{margin-top:1.8rem;padding:1.4rem;border:1px solid var(--line);border-radius:12px;background:var(--bg-soft)}
.ex-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
"""


def main() -> None:
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as fh:
        fh.write(HARNESS)
        harness = fh.name
    try:
        out = subprocess.run(['node', harness, str(TOOL)],
                             capture_output=True, text=True, encoding='utf-8')
    finally:
        pathlib.Path(harness).unlink(missing_ok=True)
    if out.returncode != 0:
        raise SystemExit('analyzer harness failed -- refusing to ship a stale example:\n' + out.stderr)
    data = json.loads(out.stdout)

    # A page claiming to show findings must actually contain some. If the
    # analyzer ever returns nothing, fail loudly rather than publishing an
    # empty "example" that quietly says we find nothing.
    if data['findings'] < 5 or data['atRisk'] <= 0:
        raise SystemExit('analyzer returned %d findings / $%s at risk -- too thin to publish'
                         % (data['findings'], data['atRisk']))

    body = re.search(r'<body>(.*)</body>', data['report'], re.S).group(1)
    # The generated report owns an <h1>; this page already has one, and two is
    # an SEO/a11y defect. Demote rather than delete so the report reads whole.
    body = body.replace('<h1>Business file check</h1>',
                        '<h2 style="margin:0 0 .2rem;font-size:1.15rem">Business file check</h2>')

    money = '${:,.0f}'.format(data['atRisk'])
    files = ''.join(
        '<li><code>%s</code> — read as %s, %d rows</li>' % (m['name'], m['label'], m['rows'])
        for m in data['meta'])

    main_html = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">This is what it finds</h1>
  <p class="ex-lede">Below is a real report from the
    <a href="/check/">free business file check</a> &mdash; not a mockup. It was produced by running
    the tool on two sample files, a job log and its invoices, with no configuration and no hints
    about what the columns mean.</p>

  <div class="ex-strip">
    <div class="ex-kpi k-bad"><b>MONEY</b><span>found at risk</span></div>
    <div class="ex-kpi"><b>FINDCOUNT</b><span>findings</span></div>
    <div class="ex-kpi"><b>HIGHCOUNT</b><span>need attention</span></div>
    <div class="ex-kpi"><b>0</b><span>settings to configure</span></div>
  </div>

  <p style="max-width:40rem">The two files it was given:</p>
  <ul style="max-width:40rem;color:var(--ink-soft)">FILELIST</ul>

  <div class="ex-frame">REPORTBODY</div>

  <div class="ex-note"><strong>Why you can trust the number.</strong> Every figure above is
    arithmetic on the files as supplied &mdash; nothing predicted, nothing estimated. The
    <strong>MONEY</strong> is the total on completed jobs that have no matching invoice, counted
    once each even where a row was duplicated. The things a script cannot decide &mdash; which
    duplicate is the real record, what a blank means &mdash; are deliberately left for a human.</div>

  <div class="ex-cta">
    <h2 style="margin-top:0">Now run it on yours</h2>
    <p>Same tool, your file, same privacy: there is no server to send it to. The analysis runs
      inside your browser and nothing is uploaded &mdash; check the network tab if you like.</p>
    <p style="margin-bottom:0"><a class="btn" href="/check/">Open the file check</a>
      &nbsp; <a href="/free-demo/">Or have us do it for you, free &rarr;</a></p>
  </div>
</main>
"""
    main_html = (main_html
                 .replace('REPORTBODY', body)
                 .replace('FILELIST', files)
                 .replace('MONEY', money)
                 .replace('FINDCOUNT', str(data['findings']))
                 .replace('HIGHCOUNT', str(data['high'])))

    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Example Report — Business File Check",
        "url": CANON,
        "description": "A real report produced by the free in-browser business file check, "
                       "run on two sample files with no configuration.",
    }, indent=2)

    s = TEMPLATE.read_text(encoding='utf-8')
    head = s[:s.index('</header>') + len('</header>')]
    footer = s[s.index('<footer'):s.index('</footer>') + len('</footer>')]
    head = re.sub(r'<title>.*?</title>', f'<title>{TITLE}</title>', head, flags=re.S)
    head = re.sub(r'(<meta name="description" content=").*?(">)', rf'\g<1>{DESC}\g<2>', head)
    head = re.sub(r'(<link rel="canonical" href=").*?(">)', rf'\g<1>{CANON}\g<2>', head)
    head = re.sub(r'(<meta property="og:title" content=").*?(">)', rf'\g<1>{TITLE}\g<2>', head)
    head = re.sub(r'(<meta property="og:description" content=").*?(">)', rf'\g<1>{DESC}\g<2>', head)
    head = re.sub(r'(<meta property="og:url" content=").*?(">)', rf'\g<1>{CANON}\g<2>', head)
    head = head.replace('</head>', f'<style>{PAGE_CSS}</style>\n</head>')

    page = (head + main_html + footer +
            '\n<script type="application/ld+json">\n' + ld + '\n</script>\n</body>\n</html>\n')
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print('wrote %s (%d bytes) — %s at risk, %d findings, generated by the live analyzer'
          % (OUT_DIR / 'index.html', len(page), money, data['findings']))


if __name__ == '__main__':
    main()
