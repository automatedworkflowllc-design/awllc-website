#!/usr/bin/env python3
"""Build /canary/ -- the public page for the always-on half of the pair.

Why this page exists separately from /flatline/: they answer different
questions, and collapsing them would hide the one that is actually novel.
flatline answers "is this signal dead" and waits to be asked. canary answers
"what is wrong in the file you just saved" and asks on its own. A visitor
arriving from "my export looks wrong" needs the second page, not a section
buried in the first.

It is also separate from the build log on purpose. The build log is a record of
*work*; a tool needs a page about *itself*, with the thing to download above the
fold rather than a story about how it came to exist.

The download links point at real GitHub release assets. A page that says "get
it here" and then hands you a git clone URL is asking the reader to do the
packaging you skipped.

Same architecture as the other tool pages: shell inherited verbatim from the
cleanup-service page so nav, footer and brand tokens never drift. No
JavaScript -- this page computes nothing, so it claims nothing it would have to
compute.
"""
from __future__ import annotations

import pathlib
import re

from toolkit import PLAIN_CSS

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'canary'

TITLE = 'Canary — Catch a Broken Export Before Anyone Else Sees It'
DESC = ('Free tool that checks every export the moment you save it: constant columns, empty '
        'fields, reports that stopped changing. Runs locally, nothing uploads.')
CANON = 'https://automatedworkflowllc.com/canary/'
REPO = 'https://github.com/automatedworkflowllc-design/canary'
REL = 'https://github.com/automatedworkflowllc-design/canary/releases/download/v0.1.0'
FL_REL = 'https://github.com/automatedworkflowllc-design/flatline/releases/download/v0.2.0'

PAGE_CSS = """
/* ---- canary page ---- */
.cy-lede{font-size:1.08rem;max-width:40rem;color:var(--ink-soft)}
.cy-clock{display:grid;grid-template-columns:auto 1fr;gap:.5rem 1rem;margin:1.6rem 0;
max-width:42rem;align-items:baseline}
.cy-clock dt{font-family:var(--mono);font-size:.95rem;font-weight:600;color:var(--green,#1E7A47);
white-space:nowrap}
.cy-clock dd{margin:0;color:var(--ink-soft)}
.cy-sample{border:1px solid var(--line);border-radius:.7rem;overflow:hidden;margin:1.2rem 0 .4rem;
background:var(--card)}
.cy-sample .bar{background:var(--bg-soft);border-bottom:1px solid var(--line);padding:.55rem .9rem;
font-family:var(--mono);font-size:.78rem;color:var(--ink-soft)}
.cy-sample table{border-collapse:collapse;width:100%;font-size:.86rem}
.cy-sample td{border-top:1px solid var(--line);padding:.5rem .9rem;vertical-align:top}
.cy-sample tr:first-child td{border-top:none}
.cy-sample .st{font-family:var(--mono);font-size:.76rem;font-weight:600;white-space:nowrap}
.cy-sample .bad .st{color:#B4452C}
.cy-sample .err .st{color:#8A6A16}
.cy-sample .ok .st{color:#1E7A47}
.cy-sample .fn{font-family:var(--mono);font-size:.8rem}
.cy-cap{font-size:.82rem;color:var(--ink-soft);margin:0 0 1.4rem;max-width:42rem}
.cy-cards{display:grid;gap:.6rem;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));margin:1.2rem 0 0}
.cy-card{border:1px solid var(--line);border-radius:.6rem;padding:.8rem 1rem;background:var(--bg-soft)}
.cy-card b{font-family:var(--mono);font-size:.9rem;display:block;margin-bottom:.2rem}
.cy-card span{font-size:.88rem;color:var(--ink-soft)}
.cy-get{border:1px solid var(--line);border-radius:12px;background:var(--bg-soft);
padding:1.3rem;margin:1.8rem 0 0}
.cy-get pre{font-family:var(--mono);font-size:.85rem;background:var(--card);border:1px solid var(--line);
border-radius:.5rem;padding:.8rem 1rem;overflow-x:auto;margin:.7rem 0}
.cy-dl{display:flex;flex-wrap:wrap;gap:.5rem;margin:.9rem 0 .2rem}
.cy-dl a{display:inline-block;border:1px solid var(--line);border-radius:.5rem;
padding:.45rem .8rem;font-family:var(--mono);font-size:.8rem;text-decoration:none;background:var(--card)}
.cy-dl a:hover{border-color:var(--green,#1E7A47)}
.cy-dl a.primary{background:var(--green,#1E7A47);color:#fff;border-color:var(--green,#1E7A47);
font-size:.9rem;padding:.6rem 1.1rem}
.cy-dl a.primary:hover{filter:brightness(1.08)}
.cy-warn{border-left:4px solid #8A6A16;background:var(--card);border-radius:.6rem;
padding:.9rem 1.1rem;margin:1.2rem 0;max-width:42rem;font-size:.9rem}
.cy-codes{border-collapse:collapse;margin:1rem 0 0;font-size:.9rem}
.cy-codes td{border-top:1px solid var(--line);padding:.45rem .9rem .45rem 0;vertical-align:top}
.cy-codes td:first-child{font-family:var(--mono);font-weight:600;white-space:nowrap}
.cy-pair{margin-top:2rem;padding:1.4rem;border:1px solid var(--line);border-radius:12px;
background:var(--card)}
.cy-pair p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">You saved the export at 2:14.<br>At 2:15 you know what is wrong with it.</h1>

<div class="pe">
  <h2>In plain English</h2>
  <dl>
    <dt>What it does</dt><dd>Watches the folder where your spreadsheets and exports already get
      saved. Every time a file changes it checks it and tells you what looks broken &mdash; a column
      that is the same value all the way down, a field that is empty on every row, a report that
      stopped changing weeks ago.</dd>
    <dt>Why it helps</dt><dd>Every tool like this waits for you to bring it a file, which means you
      have to already suspect something is wrong. <b>The people who most need the check are the ones
      who never think to run it.</b> This one runs itself.</dd>
    <dt>What you need</dt><dd>A folder where files land, and someone technical for about ten minutes
      to install it. It only reads &mdash; it changes nothing, and sends nothing anywhere.</dd>
    <dt>How long</dt><dd>Minutes to set up, then never again. It runs on a schedule or watches
      continuously.</dd>
  </dl>
</div>

  <p class="cy-lede">Nobody checks the export before it goes out, because checking it is a chore and
  it has been fine for a year. The one time it is not fine, it looks exactly the same.</p>

  <dl class="cy-clock">
    <dt>2:14pm</dt><dd>Your system writes <code>invoices-august.csv</code> to the usual folder.</dd>
    <dt>2:15pm</dt><dd>canary has already read it: <b>the <code>status</code> column is
      &ldquo;OPEN&rdquo; on all 412 rows</b>, and <code>paid_date</code> is empty on every one.</dd>
    <dt>2:16pm</dt><dd>You discover the billing sync stopped writing three weeks ago &mdash; instead
      of discovering it when a client asks why they were never invoiced.</dd>
  </dl>

  <h2 style="margin-top:2.2rem">What the report looks like</h2>
  <div class="cy-sample">
    <div class="bar">What is in your files right now &middot; 3 files checked &middot; 1 with findings &middot; 1 could not be checked</div>
    <table>
      <tr class="bad"><td class="fn">invoices-august.csv</td><td class="st">FINDINGS</td>
        <td>status: CONSTANT &mdash; identical value &lsquo;OPEN&rsquo; on all 412 rows<br>paid_date: empty on every row</td></tr>
      <tr class="err"><td class="fn">payroll-q3.csv</td><td class="st">COULD NOT CHECK</td>
        <td>file locked by another process &mdash; this is <b>not</b> a pass</td></tr>
      <tr class="ok"><td class="fn">crew-hours.csv</td><td class="st">CLEAN</td>
        <td>nothing to report</td></tr>
    </table>
  </div>
  <p class="cy-cap">An illustration of the real output format. The middle row is the entire point of
  the tool: a file it could not read is reported as a failure to read it, never quietly counted as
  fine.</p>

  <h2 style="margin-top:2.2rem">Three decisions that decide whether you keep reading it</h2>
  <div class="cy-cards">
    <div class="cy-card"><b>content, not timestamps</b><span>Files are compared by hash. A file
      re-saved with identical bytes has not changed in any way you care about, and re-reporting it
      every night is how a tool teaches you to ignore it.</span></div>
    <div class="cy-card"><b>news, not inventory</b><span>It raises the alarm for findings in files
      it actually re-checked. Everything known stays in the report, but a known-bad file sitting
      untouched is not an alarm &mdash; a guard that shouts nightly gets muted.</span></div>
    <div class="cy-card"><b>never a false all-clear</b><span>A check that could not run is reported
      as a failure to check. The report says so in plain words, because a tool that says &ldquo;no
      findings&rdquo; when it never looked is the exact failure this exists to catch.</span></div>
  </div>

  <div class="cy-get">
    <h2 style="margin-top:0">Get it</h2>
    <p style="color:var(--ink-soft);margin-top:.3rem">Free, MIT licensed, runs on your machine.
    canary calls <a href="/flatline/">flatline</a> for the analysis rather than reimplementing it,
    so you install both &mdash; two files, no account, no service.</p>

    <p style="margin:.2rem 0 0"><b>If you just want to use it &mdash; Windows, one file, nothing to
    install:</b></p>
    <div class="cy-dl">
      <a class="primary" href="CANARY_EXE">&darr; canary.exe &mdash; 13 MB, no Python needed</a>
    </div>
    <p style="color:var(--ink-soft);font-size:.88rem;margin:.5rem 0 0">Double-click it, pick your
    folder, and the report opens in your browser. Everything happens on your machine.</p>

    <div class="cy-warn"><strong>Windows will warn you the first time.</strong> This download is not
    code-signed &mdash; a certificate costs a few hundred dollars a year and we have not bought one
    &mdash; so SmartScreen shows &ldquo;Windows protected your PC&rdquo;. That warning means
    <em>unrecognized</em>, not <em>unsafe</em>. Click <b>More info &rarr; Run anyway</b>, or skip the
    app entirely and install from source below &mdash; it is the same code you can read on GitHub.</div>

    <p style="margin:1.2rem 0 0"><b>If you are technical, or not on Windows:</b></p>
    <div class="cy-dl">
      <a href="CANARY_WHL">&darr; canary 0.1.0 (wheel)</a>
      <a href="CANARY_SRC">&darr; canary 0.1.0 (source)</a>
      <a href="FLATLINE_WHL">&darr; flatline 0.2.0 (wheel)</a>
      <a href="FLATLINE_SRC">&darr; flatline 0.2.0 (source)</a>
    </div>

    <pre>pip install awllc_flatline-0.2.0-py3-none-any.whl
pip install awllc_canary-0.1.0-py3-none-any.whl

canary ~/Downloads --report canary.html</pre>

    <div class="cy-warn"><strong>Install from these files, not by name.</strong> The names
    <code>canary</code> and <code>flatline</code> on PyPI belong to unrelated projects, so
    <code>pip install canary</code> would fetch someone else&rsquo;s tool. Ours publish as
    <code>awllc-canary</code> and <code>awllc-flatline</code>. canary checks for this too &mdash; if
    the wrong package is installed it says so, rather than blaming your data for a packaging
    mistake.</div>

    <p style="margin:.6rem 0 0"><a href="REPO_URL">Source, tests and documentation on GitHub &rarr;</a></p>
  </div>

  <h2 style="margin-top:2.2rem">Running it on a schedule</h2>
  <p style="color:var(--ink-soft);max-width:42rem">Give it <code>--fail-on-findings</code> so it has
  something to say, and let your scheduler read the exit code. Watching the report file instead
  would prove nothing: it carries a timestamp, so it changes every run whether or not anything
  happened.</p>
  <table class="cy-codes">
    <tr><td>0</td><td>every re-examined file came back clean</td></tr>
    <tr><td>1</td><td>a file could not be checked &mdash; worse than a finding, because it hides an
      unknown number of them</td></tr>
    <tr><td>2</td><td>new findings</td></tr>
  </table>

  <h2 style="margin-top:2.2rem">What it does not see</h2>
  <p style="color:var(--ink-soft);max-width:42rem">Only files that change on disk. It knows nothing
  about whether a scheduled job ran at all, or whether an output went stale between runs &mdash;
  different questions, different tools. Saying so is the point: a tool that implies it covers more
  than it does is how coverage comes to be assumed instead of checked.</p>

  <div class="cy-pair">
    <h2 style="margin-top:0">The other half: flatline</h2>
    <p><strong>Software fails loudly. Data fails quietly.</strong> flatline is the judgment &mdash;
    it decides whether a signal still carries information. canary is the trigger. <strong>Neither
    tool will ever call a file clean that it failed to read:</strong> a check that could not run is
    reported as a failure to check, never as a pass &mdash; in code, and with a test, in both.</p>
    <p style="margin-bottom:0"><a class="btn" href="/flatline/">See flatline</a>
    &nbsp; <a href="/automation-monitoring/">Or have us watch your stack &rarr;</a></p>
  </div>
</main>
"""

LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Canary",
  "url": "https://automatedworkflowllc.com/canary/",
  "codeRepository": "https://github.com/automatedworkflowllc-design/canary",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Any",
  "softwareVersion": "0.1.0",
  "license": "https://opensource.org/licenses/MIT",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "description": "Open-source watcher that checks each export the moment it is saved: constant columns, empty fields, files that stopped changing. Local only; nothing uploads."
}
</script>
"""


def main() -> None:
    s = TEMPLATE.read_text(encoding='utf-8')
    head = s[:s.index('</header>') + len('</header>')]
    footer = s[s.index('<footer'):s.index('</footer>') + len('</footer>')]

    head = re.sub(r'<title>.*?</title>', f'<title>{TITLE}</title>', head, flags=re.S)
    head = re.sub(r'(<meta name="description" content=").*?(">)', rf'\g<1>{DESC}\g<2>', head)
    head = re.sub(r'(<link rel="canonical" href=").*?(">)', rf'\g<1>{CANON}\g<2>', head)
    head = re.sub(r'(<meta property="og:title" content=").*?(">)', rf'\g<1>{TITLE}\g<2>', head)
    head = re.sub(r'(<meta property="og:description" content=").*?(">)', rf'\g<1>{DESC}\g<2>', head)
    head = re.sub(r'(<meta property="og:url" content=").*?(">)', rf'\g<1>{CANON}\g<2>', head)
    head = head.replace('</head>', f'<style>{PAGE_CSS}{PLAIN_CSS}</style>\n</head>')

    body = (MAIN.replace('REPO_URL', REPO)
                .replace('CANARY_EXE', f'{REL}/canary.exe')
                .replace('CANARY_WHL', f'{REL}/awllc_canary-0.1.0-py3-none-any.whl')
                .replace('CANARY_SRC', f'{REL}/awllc_canary-0.1.0.tar.gz')
                .replace('FLATLINE_WHL', f'{FL_REL}/awllc_flatline-0.2.0-py3-none-any.whl')
                .replace('FLATLINE_SRC', f'{FL_REL}/awllc_flatline-0.2.0.tar.gz'))

    # Refuse rather than ship a page whose download buttons are decoration. A
    # placeholder that survives to the page is a link that goes nowhere, and this
    # page's whole job is handing someone a file.
    for token in ('REPO_URL', 'CANARY_EXE', 'CANARY_WHL', 'CANARY_SRC',
                  'FLATLINE_WHL', 'FLATLINE_SRC'):
        if token in body:
            raise SystemExit(f'refusing to build /canary/: placeholder {token} was never replaced')

    page = head + body + footer + LD + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
