#!/usr/bin/env python3
"""Build /flatline/ -- the public explainer for the open-source detector.

Why this page exists: flatline was already public on GitHub, but a repo is
written for engineers who already know they have the problem. The people who
most need it -- an owner whose backup has been "succeeding" into a 0-byte file,
an agency whose client Zap stopped returning rows in March -- do not read
READMEs and would not recognize the problem by name.

So this page leads with the symptom, not the tool: your automations report
success, and that is not the same as working. The "How you'd use this" section
is the whole point of the page; everything else supports it.

It doubles as the credibility asset behind the audit offer. Anyone can claim
they will check your automations. This links to the source, the test count, and
the specific bugs it caught, including the ones it caught in itself.

Same architecture as the tool pages: shell inherited verbatim from the
cleanup-service page so the nav, footer and brand tokens never drift. No
JavaScript -- this page makes no claims it has to compute.
"""
from __future__ import annotations

import pathlib
import re

from toolkit import PLAIN_CSS

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'flatline'

TITLE = 'Flatline — Find Automations That Quietly Stopped Working'
DESC = ('Free open-source tool that finds scheduled jobs and reports that succeed while '
        'doing nothing: dead signals, silent no-ops, swallowed errors. MIT licensed.')
CANON = 'https://automatedworkflowllc.com/flatline/'
REPO = 'https://github.com/automatedworkflowllc-design/flatline'

PAGE_CSS = """
/* ---- flatline explainer ---- */
.fl-lede{font-size:1.08rem;max-width:40rem}
.fl-bad{border-left:4px solid #B4452C;background:var(--card);border-radius:.6rem;
padding:1rem 1.2rem;margin:1.6rem 0;max-width:42rem}
.fl-bad code{font-family:var(--mono);font-size:.85rem}
.fl-uses{display:grid;gap:.8rem;margin:1.2rem 0 0}
.fl-use{border:1px solid var(--line);border-radius:.7rem;background:var(--card);padding:1rem 1.2rem}
.fl-use h3{margin:0 0 .3rem;font-size:1rem}
.fl-use .sym{color:var(--ink-soft);font-size:.92rem;margin:0 0 .5rem}
.fl-use .fix{margin:0;font-size:.9rem;padding-left:.7rem;border-left:2px solid var(--line-strong)}
.fl-use .fix b{font-family:var(--mono);font-size:.82rem}
.fl-checks{display:grid;gap:.6rem;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));margin:1.2rem 0 0}
.fl-check{border:1px solid var(--line);border-radius:.6rem;padding:.8rem 1rem;background:var(--bg-soft)}
.fl-check b{font-family:var(--mono);font-size:.9rem;display:block;margin-bottom:.2rem}
.fl-check span{font-size:.88rem;color:var(--ink-soft)}
.fl-caught{margin:1.2rem 0 0;padding-left:1.15rem;max-width:42rem}
.fl-caught li{margin:.45rem 0}
.fl-run{border:1px solid var(--line);border-radius:12px;background:var(--bg-soft);padding:1.3rem;margin:1.6rem 0 0}
.fl-run pre{font-family:var(--mono);font-size:.85rem;background:var(--card);border:1px solid var(--line);
border-radius:.5rem;padding:.8rem 1rem;overflow-x:auto;margin:.6rem 0}
.fl-cta{margin-top:2rem;padding:1.4rem;border:1px solid var(--line);border-radius:12px;background:var(--card)}
.fl-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">Your automations report success.<br>That is not the same as working.</h1>
<div class="pe">
  <h2>In plain English</h2>
  <dl>
    <dt>What it does</dt><dd>Checks the automatic jobs in your business &mdash; the nightly backup,
      the sync, the weekly report &mdash; and finds the ones that say they worked but did nothing.</dd>
    <dt>Why it helps</dt><dd>A backup that has "succeeded" every night for eight months into an
      empty file looks identical to one that works, right up until you need it.
      <b>The failures that cost real money never show up as errors</b>, which is exactly why nobody
      catches them.</dd>
    <dt>What you need</dt><dd>A little help from whoever is technical &mdash; it is a free tool they
      run, and it only reads; it changes nothing.</dd>
    <dt>How long</dt><dd>About twenty minutes to point it at your stack. Or ask us and we will do it
      and hand you the findings with the evidence.</dd>
  </dl>
</div>
  <p class="fl-lede" style="color:var(--ink-soft)">
    Monitoring watches for errors. The expensive failures do not throw one &mdash; the job runs,
    the log gets written, the exit code is zero, and nothing actually happened. Flatline is a free
    open-source tool that looks for that specific shape of failure.
  </p>

  <div class="fl-bad">
    <strong>The one that started it.</strong> A scheduled job on our own machine ran every weekday
    for four days, wrote a full log each time, and reported success. It had been starting in the
    wrong directory the whole time, so every file it wrote went nowhere. Four days of data, gone,
    with four green checkmarks on top of it.
  </div>

  <h2>How you would use this</h2>
  <p style="color:var(--ink-soft);max-width:40rem">Five shapes of the same problem. If any of these
  sounds familiar, it is worth twenty minutes.</p>

  <div class="fl-uses">
    <div class="fl-use">
      <h3>The backup that backs up nothing</h3>
      <p class="sym">It has succeeded every night for eight months. Nobody has opened the file.</p>
      <p class="fix"><b>jobs</b> &mdash; checks whether the output a job is supposed to write
      actually changed, instead of trusting the job's own exit code. A 0-byte file that keeps its
      timestamp fresh is the classic.</p>
    </div>

    <div class="fl-use">
      <h3>The client automation that stopped firing</h3>
      <p class="sym">A Zap, Make scenario or n8n flow whose trigger has returned zero rows since a
      field got renamed upstream. No error was raised, because finding nothing is not an error.</p>
      <p class="fix"><b>jobs</b> + <b>scan</b> &mdash; a run history where the "records processed"
      column is 0 forever reads as a flat signal, not as activity.</p>
    </div>

    <div class="fl-use">
      <h3>The dashboard column that froze</h3>
      <p class="sym">One field has shown the same value since a schema change three months ago.
      The chart still draws, so nobody noticed.</p>
      <p class="fix"><b>scan</b> &mdash; measures how much a column actually varies. A value that
      never changes carries no information; it is a constant wearing a signal's name.</p>
    </div>

    <div class="fl-use">
      <h3>The alert that has never once fired</h3>
      <p class="sym">You have a threshold alert. It has been quiet for a year. You believe that
      means everything is fine.</p>
      <p class="fix"><b>code</b> &mdash; finds unreachable branches and errors caught and thrown
      away. On our own stack it found a desktop notification that could never fire, because the
      line above it ended the script.</p>
    </div>

    <div class="fl-use">
      <h3>The report that is quietly stale</h3>
      <p class="sym">A weekly summary still arrives on time. The numbers in it stopped moving a
      while ago.</p>
      <p class="fix"><b>verify</b> &mdash; takes a claim ("this refreshed today", "these files are
      tracked") and checks it against the system instead of against another report.</p>
    </div>
  </div>

  <h2 style="margin-top:2.4rem">What it checks</h2>
  <div class="fl-checks">
    <div class="fl-check"><b>scan</b><span>Signals that never vary. Measures information content,
    so a column of identical values is flagged even when it looks populated.</span></div>
    <div class="fl-check"><b>jobs</b><span>Scheduled tasks that ran but produced nothing. Compares
    intent against the output that actually changed on disk.</span></div>
    <div class="fl-check"><b>verify</b><span>Stated claims against the underlying system, because a
    status field is a claim, not evidence.</span></div>
    <div class="fl-check"><b>code</b><span>Unreachable branches and swallowed exceptions &mdash;
    the guard wrapped in a catch that discards the thing it was guarding against.</span></div>
  </div>

  <h2 style="margin-top:2.4rem">What it has actually caught</h2>
  <ul class="fl-caught">
    <li>A job's first-ever scheduled run, <strong>before it ran</strong> &mdash; three file writes
      that would have landed somewhere unrecoverable and reported success.</li>
    <li>A diagnostic flag that fired on <strong>100% of rows for a week</strong>. A warning that is
      always on is not a warning.</li>
    <li>A desktop notification that had <strong>never fired once</strong> in the life of the script,
      because everything after one line was unreachable.</li>
    <li><strong>Three false positives in itself.</strong> Each was fixed by measuring real code
      rather than arguing about it &mdash; which is the standard we would hold your stack to.</li>
  </ul>

  <div class="fl-run">
    <h2 style="margin-top:0">Run it yourself</h2>
    <p style="color:var(--ink-soft);margin-top:.3rem">Free, MIT licensed, 114 tests. It reads; it
    does not change anything it looks at.</p>
    <pre>git clone https://github.com/automatedworkflowllc-design/flatline
pip install ./flatline
flatline scan your-export.csv
flatline jobs</pre>
    <p style="color:var(--ink-soft);font-size:.88rem;margin:.55rem 0 0">Install from the repository,
    not by name: <strong>the name <code>flatline</code> on PyPI belongs to an unrelated project</strong>
    (a Ghidra decompiler wrapper), so <code>pip install flatline</code> would fetch someone else's
    tool. Ours publishes as <code>awllc-flatline</code>.</p>
    <p style="margin:.6rem 0 0"><a href="REPO_URL">Source and documentation on GitHub &rarr;</a></p>
  </div>

  <div class="fl-run">
    <h2 style="margin-top:0">Its other half: canary</h2>
    <p style="color:var(--ink-soft);margin-top:.3rem">flatline waits to be asked. That is backwards
    &mdash; the people who most need the check are the ones who never think to run it. So
    <strong>canary</strong> watches the folders where your exports already get saved and asks
    flatline the moment a file changes. You save an invoice export at 2:14pm; at 2:15 you know what
    is wrong with it.</p>
    <p style="color:var(--ink-soft)"><strong>Software fails loudly. Data fails quietly.</strong>
    flatline is the judgment &mdash; it decides whether a signal still carries information. canary is
    the trigger. <strong>Neither tool will ever call a file clean that it failed to read:</strong> a
    check that could not run is reported as a failure to check, never as a pass &mdash; in code, and
    with a test, in both.</p>
    <pre>git clone https://github.com/automatedworkflowllc-design/canary
pip install ./canary
canary ~/Downloads --report canary.html</pre>
    <p style="margin:.6rem 0 0"><a href="/canary/">What canary does, with downloads &rarr;</a>
    &nbsp; <a href="https://github.com/automatedworkflowllc-design/canary">Source on GitHub</a></p>
    <p style="margin:.6rem 0 0"><a href="/canary/how-it-works/"><b>How the two work together, end
    to end &rarr;</b></a> &nbsp;<span style="color:var(--ink-soft);font-size:.9rem">The full
    pipeline, every verdict, and every exit code.</span></p>
  </div>

  <div class="fl-cta">
    <h2 style="margin-top:0">Or have us point it at your stack</h2>
    <p>The tool finds the dead signals. Deciding which ones cost you money, and fixing them, is the
    part that takes judgment. We do that as a fixed-scope audit &mdash; you get the findings and the
    evidence for each one, including the ones that turn out to be fine.</p>
    <p style="margin-bottom:0"><a class="btn" href="/free-demo/">Ask about an automation audit</a>
    &nbsp; <a href="/builds/">See everything we have built &rarr;</a></p>
  </div>
</main>
"""

LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Flatline",
  "url": "https://automatedworkflowllc.com/flatline/",
  "codeRepository": "https://github.com/automatedworkflowllc-design/flatline",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Any",
  "license": "https://opensource.org/licenses/MIT",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "description": "Open-source detector for scheduled jobs and reports that succeed while doing nothing: dead signals, silent no-ops, unreachable code and swallowed errors."
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

    body = MAIN.replace('REPO_URL', REPO)
    page = head + body + footer + LD + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
