#!/usr/bin/env python3
"""Build /canary/how-it-works/ -- the full mechanics of the canary+flatline pair.

Why this page had to exist: we shipped three pages about these tools (/canary/,
/flatline/, and the shared WHY-SEVERAL-TOOLS reasoning page) and none of them
explained how the two actually work *together*. Worse, the single feature that
decides whether a person keeps reading the nightly report -- canary-ignore.txt,
the list of columns that are constant by design -- was implemented in code and
documented in neither the README nor the page. A tool whose most important
knob is undiscoverable is a tool that gets muted after four days.

The three existing pages stay as they are. Each answers "what is this for"; a
reader who has decided to trust the pair needs "what does it actually do", and
that is a different page with a different job. This one is allowed to be long.

Everything on this page was read out of the source before it was written down,
not recalled. Where the page states an exit code, a verdict name, or a
precedence rule, that string exists in canary.py, signals.py, or the README.

Same architecture as the other tool pages: shell inherited verbatim from the
cleanup-service page so nav, footer and brand tokens never drift. No
JavaScript -- the page computes nothing, so it claims nothing it would have to
compute.
"""
from __future__ import annotations

import pathlib
import re

from toolkit import PLAIN_CSS

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'canary' / 'how-it-works'

# Exactly 60 characters, the top of the SEO gate's 50-60 budget. The em-dash
# version was 61 and the gate caught it.
TITLE = 'How Canary and Flatline Work: The Whole Pipeline, End to End'
DESC = ('Exactly what happens between saving a file and reading the report: what flatline '
        'checks, how canary reaches it, the ignore file, and every exit code.')
CANON = 'https://automatedworkflowllc.com/canary/how-it-works/'
REPO = 'https://github.com/automatedworkflowllc-design/canary'
FL_REPO = 'https://github.com/automatedworkflowllc-design/flatline'

PAGE_CSS = """
/* ---- how-it-works ---- */
.hw-lede{font-size:1.08rem;max-width:42rem;color:var(--ink-soft)}
.hw-split{display:grid;gap:.7rem;grid-template-columns:repeat(auto-fit,minmax(17rem,1fr));
margin:1.5rem 0 .5rem}
.hw-half{border:1px solid var(--line);border-radius:.7rem;padding:1rem 1.1rem;background:var(--bg-soft)}
.hw-half b{font-family:var(--mono);font-size:.95rem;display:block;margin-bottom:.35rem}
.hw-half .q{font-size:.88rem;color:var(--ink);margin:0 0 .5rem}
.hw-half .w{font-size:.85rem;color:var(--ink-soft);margin:0}
.hw-steps{counter-reset:hw;list-style:none;padding:0;margin:1.3rem 0 0;max-width:44rem}
.hw-steps li{counter-increment:hw;position:relative;padding:0 0 1.15rem 2.6rem;
border-left:1px solid var(--line);margin-left:.85rem}
.hw-steps li:last-child{border-left-color:transparent;padding-bottom:.2rem}
.hw-steps li::before{content:counter(hw);position:absolute;left:-.85rem;top:-.1rem;
width:1.7rem;height:1.7rem;border-radius:50%;background:var(--card);
border:1px solid var(--line);font-family:var(--mono);font-size:.8rem;font-weight:600;
display:flex;align-items:center;justify-content:center;color:var(--green,#1E7A47)}
.hw-steps b{display:block;font-size:.97rem;margin-bottom:.2rem}
.hw-steps span{font-size:.9rem;color:var(--ink-soft)}
.hw-tbl{border-collapse:collapse;width:100%;font-size:.89rem;margin:1rem 0 .3rem;
max-width:44rem}
.hw-tbl th{text-align:left;font-size:.76rem;letter-spacing:.06em;text-transform:uppercase;
color:var(--ink-soft);border-bottom:1px solid var(--line);padding:0 .9rem .45rem 0;font-weight:600}
.hw-tbl td{border-top:1px solid var(--line);padding:.5rem .9rem .5rem 0;vertical-align:top}
.hw-tbl td:first-child{font-family:var(--mono);font-size:.83rem;font-weight:600;white-space:nowrap}
.hw-wrap{overflow-x:auto}
.hw-code{font-family:var(--mono);font-size:.84rem;background:var(--card);
border:1px solid var(--line);border-radius:.5rem;padding:.85rem 1.05rem;overflow-x:auto;
margin:.9rem 0;max-width:44rem;line-height:1.55}
.hw-code .c{color:var(--ink-soft)}
.hw-note{border-left:4px solid var(--green,#1E7A47);background:var(--bg-soft);
border-radius:.6rem;padding:.9rem 1.1rem;margin:1.2rem 0;max-width:44rem;font-size:.9rem}
.hw-note b{display:block;margin-bottom:.25rem}
.hw-warn{border-left:4px solid #8A6A16}
.hw-cant{margin:1rem 0 0;padding:0;list-style:none;max-width:44rem}
.hw-cant li{padding:.5rem 0 .5rem 1.4rem;border-top:1px solid var(--line);font-size:.9rem;
color:var(--ink-soft);position:relative}
.hw-cant li::before{content:"\\2014";position:absolute;left:0;color:var(--ink-soft)}
.hw-more{margin-top:2rem;padding:1.4rem;border:1px solid var(--line);border-radius:12px;
background:var(--card)}
.hw-more p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <p style="font-family:var(--mono);font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;
     color:var(--ink-soft);margin:0 0 .5rem"><a href="/canary/" style="color:inherit">Canary</a>
     &nbsp;/&nbsp; How it works</p>
  <h1 style="margin-bottom:.4rem">The whole pipeline, end to end</h1>
  <p class="hw-lede">What happens between the moment a file lands in a watched folder and the
  moment a report says something about it &mdash; including the one setting that decides whether
  you are still reading the report a month from now.</p>

<div class="pe">
  <h2>Two tools, because they answer different questions</h2>
  <p>They are shipped separately and either one runs without the other. That is a deliberate
  cost: it means two repositories, two release processes, and this page. The reason it is worth
  paying is that the questions do not collapse into one.</p>

  <div class="hw-split">
    <div class="hw-half">
      <b>flatline</b>
      <p class="q">&ldquo;Is this column still carrying information?&rdquo;</p>
      <p class="w">Give it a table, it scores every column and answers. It has no opinion about
      when to run &mdash; it waits to be asked. That is what makes it usable inside someone
      else&rsquo;s script, build pipeline, or nightly job that has nothing to do with us.</p>
    </div>
    <div class="hw-half">
      <b>canary</b>
      <p class="q">&ldquo;What is wrong in the file that just landed?&rdquo;</p>
      <p class="w">Watches folders, decides when to ask, remembers the last answer, and reports
      what changed. It does none of the analysis itself &mdash; it calls flatline. Two copies of
      the same analysis diverge the first time only one of them gets fixed.</p>
    </div>
  </div>
</div>

<div class="pe">
  <h2>What actually happens, in order</h2>
  <p>This is a real sequence &mdash; each step depends on the one above it, and step 2 exists
  specifically so that the rest cannot quietly be skipped.</p>

  <ol class="hw-steps">
    <li><b>A file changes in a watched folder</b>
      <span>Canary is pointed at the folders where your exports already get saved. It compares
      each file against what it recorded last time &mdash; size, modification time, content
      fingerprint &mdash; so an untouched file is not re-analysed just because the clock
      moved.</span></li>
    <li><b>Canary checks it can reach flatline &mdash; before analysing anything</b>
      <span>Availability is settled up front rather than discovered halfway through. If flatline
      cannot be reached, that is an <b>ERROR</b> and a non-zero exit, never a quiet
      &ldquo;nothing found&rdquo;. A checker that reports clean because it never ran is the
      exact failure these tools exist to catch.</span></li>
    <li><b>Flatline reads the table and scores every column</b>
      <span>It normalises values, counts how they are distributed, and computes how much
      information each column is actually carrying. Verdicts and severities below.</span></li>
    <li><b>Canary compares the answer against the last look</b>
      <span>It keeps the previous result per file, so it can tell you what is <i>new</i> rather
      than re-reading the same twenty findings at you every night.</span></li>
    <li><b>Columns you have marked as expected-constant are set aside</b>
      <span>Named and counted in the report, not deleted from it. This is the step most people
      need and the one that was undocumented until now &mdash; see below.</span></li>
    <li><b>The report is written and the exit code is set</b>
      <span>Human-readable HTML for you; an exit code for whatever scheduler is running it. The
      exit code reports news, not inventory.</span></li>
  </ol>
</div>

<div class="pe">
  <h2>What flatline looks for</h2>
  <p>The core check is information content: a column whose value never changes cannot be
  affecting any decision downstream, whatever the report built on top of it implies.</p>

  <div class="hw-wrap">
  <table class="hw-tbl">
    <tr><th>Verdict</th><th>Meaning</th><th>Severity</th></tr>
    <tr><td>CONSTANT</td><td>Every row carries the same value. The column is decoration.</td>
      <td>HIGH if the column name looks like a decision signal, otherwise INFO</td></tr>
    <tr><td>NEAR_CONSTANT</td><td>Nearly every row is the same value &mdash; a signal that has
      mostly stopped moving.</td>
      <td>MEDIUM if it looks like a decision signal, otherwise INFO</td></tr>
  </table>
  </div>

  <div class="hw-note">
    <b>Why the name changes the severity</b>
    A constant column called <span style="font-family:var(--mono)">export_format</span> is
    fine &mdash; it is supposed to be constant. A constant column called
    <span style="font-family:var(--mono)">risk_flag</span> or
    <span style="font-family:var(--mono)">approved</span> means something that was meant to
    vary has stopped varying. Flatline reads the column name to decide which of those it is
    looking at, and only raises the severity for the second kind.
  </div>

  <div class="hw-note">
    <b>Files with no header row</b>
    If the first row is data rather than names, flatline says
    <span style="font-family:var(--mono)">column 4 (file has no header row)</span> instead of
    inventing a column called <span style="font-family:var(--mono)">2026-07-30</span>. This was
    a real defect: treating the first data row as headers both produced nonsense findings and
    silently swallowed a row of actual data.
  </div>
</div>

<div class="pe">
  <h2>How canary reaches flatline</h2>
  <p>Three paths, because the tool ships in two very different shapes and the third case must
  not be silent.</p>

  <div class="hw-wrap">
  <table class="hw-tbl">
    <tr><th>Situation</th><th>What canary does</th></tr>
    <tr><td>installed</td>
      <td>Runs <span style="font-family:var(--mono)">python -m flatline scan &lt;file&gt;</span>
      as a subprocess and reads what it prints.</td></tr>
    <tr><td>frozen .exe</td>
      <td>Calls flatline&rsquo;s own <span style="font-family:var(--mono)">cli.main</span>
      in-process. In a bundled application a subprocess would relaunch the application itself,
      not flatline.</td></tr>
    <tr><td>not found</td>
      <td><b>ERROR</b> and a non-zero exit. Never a clean report.</td></tr>
  </table>
  </div>

  <div class="hw-note hw-warn">
    <b>It verifies the flatline it found is ours</b>
    Asking Python whether a module named <span style="font-family:var(--mono)">flatline</span>
    exists is not enough: the name <span style="font-family:var(--mono)">flatline</span> on PyPI
    belongs to an unrelated project, and so do
    <span style="font-family:var(--mono)">attest</span>,
    <span style="font-family:var(--mono)">canary</span>,
    <span style="font-family:var(--mono)">watchpost</span> and
    <span style="font-family:var(--mono)">custody</span>. So canary confirms the package it found
    contains the files it expects before trusting it, and it does that by looking at the
    filesystem rather than by importing a stranger&rsquo;s code to ask. Our distributions publish
    under <span style="font-family:var(--mono)">awllc-</span> names for the same reason.
  </div>
</div>

<div class="pe">
  <h2>canary-ignore.txt &mdash; the setting that decides whether you keep reading</h2>
  <p>Without this, canary is correct and unusable. On the first real folder we pointed it at, two
  columns &mdash; a ruleset version and a regime code &mdash; produced two thirds of every
  finding, every night. Both are constant <i>by design</i>. Nothing in the data can tell canary
  that. Only the person who owns the file knows, so they say it once, in a plain text file they
  can open and read.</p>

  <div class="hw-code">
<span class="c"># canary-ignore.txt &mdash; columns that are supposed to be constant</span>
<span class="c"># one per line; everything after a # is a comment</span>

ruleset_version   <span class="c"># pinned on purpose, changes only on release</span>
regime_code       <span class="c"># single-regime export</span>
export_format
</div>

  <p>It lives beside canary&rsquo;s state file, and the report tells you the exact path it looked
  at. The same list can be passed on the command line with
  <span style="font-family:var(--mono)">--ignore</span>.</p>

  <div class="hw-note">
    <b>Set aside, not hidden</b>
    Ignored findings are counted and named in the report &mdash; a file whose findings are all
    ignored reads as clean but still says what was set aside and why. A checker that quietly
    stops mentioning things is the precise failure this tool is pointed at, and it would be a
    strange thing to build into the tool itself.
  </div>
</div>

<div class="pe">
  <h2>Exit codes</h2>
  <p>For whatever is running canary on a schedule. Two rules in here are deliberate and worth
  knowing, because both look wrong at first glance.</p>

  <div class="hw-wrap">
  <table class="hw-tbl">
    <tr><th>Code</th><th>Meaning</th></tr>
    <tr><td>0</td><td>Every re-examined file came back clean.</td></tr>
    <tr><td>1</td><td>A file <b>could not be checked</b>.</td></tr>
    <tr><td>2</td><td>New findings &mdash; only with
      <span style="font-family:var(--mono)">--fail-on-findings</span>.</td></tr>
  </table>
  </div>

  <div class="hw-note">
    <b>1 outranks 2 on purpose</b>
    A finding is one known problem. A file that could not be checked hides an unknown number of
    them. The louder signal belongs to the case you know least about.
  </div>

  <div class="hw-note">
    <b>The exit code reports news, not inventory</b>
    It is raised for files actually re-examined on this run. A known-bad file sitting unchanged
    on disk does not re-raise it every night forever. This was a real defect: canary cried wolf
    on the same twenty-one stable findings on every single run, which is how a monitoring tool
    teaches you to ignore it.
  </div>
</div>

<div class="pe">
  <h2>What the pair cannot see</h2>
  <ul class="hw-cant">
    <li>Whether a number is <i>correct</i>. A column full of varied, confidently wrong values
      looks healthy to flatline.</li>
    <li>Whether the job that was supposed to write the file ran at all. Canary sees files, not
      work &mdash; a job that dies before writing produces no event to react to.</li>
    <li>Anything in a folder it was not pointed at.</li>
    <li>Whether a constant column is <i>supposed</i> to be constant. That is what the ignore file
      is for, and why it is yours to write rather than something we guess.</li>
  </ul>
  <p style="margin-top:1rem;font-size:.9rem;color:var(--ink-soft)">The first two are covered by
  other tools in the set, which is the whole reason there is more than one.</p>
</div>

<div class="hw-more">
  <h2 style="margin-top:0">Read the source</h2>
  <p>Every claim on this page is a few lines of readable Python away. Both are MIT.</p>
  <p style="margin-bottom:0"><a href="REPO_URL">canary on GitHub</a> &nbsp;&middot;&nbsp;
  <a href="FL_REPO_URL">flatline on GitHub</a> &nbsp;&middot;&nbsp;
  <a href="/canary/">back to Canary</a> &nbsp;&middot;&nbsp;
  <a href="/flatline/">Flatline</a></p>
</div>
</main>
"""

LD = """
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"TechArticle",
"headline":"How Canary and Flatline Work: The Whole Pipeline, End to End",
"url":"https://automatedworkflowllc.com/canary/how-it-works/",
"about":["data quality monitoring","spreadsheet validation"],
"publisher":{"@type":"Organization","name":"Automated Workflow LLC",
"url":"https://automatedworkflowllc.com"}}
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

    # FL_REPO_URL must be substituted FIRST: it contains REPO_URL as a
    # substring, so the other order rewrites it to "FL_<canary url>" and leaves
    # a broken link that the guard below cannot see -- neither token survives to
    # be detected. Caught before this file was ever run.
    body = MAIN.replace('FL_REPO_URL', FL_REPO).replace('REPO_URL', REPO)

    # Same refusal as the other tool pages: a placeholder that survives to the
    # page is a link that goes nowhere.
    for token in ('REPO_URL', 'FL_REPO_URL'):
        if token in body:
            raise SystemExit(f'refusing to build: placeholder {token} was never replaced')
    if 'FL_http' in body:
        raise SystemExit('refusing to build: FL_REPO_URL was mangled by substring replacement')

    page = head + body + footer + LD + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
