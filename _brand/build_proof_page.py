#!/usr/bin/env python3
"""Build /proof/ -- the public evidence page over our own attest ledger.

Why this page exists: /proof/attest-anchors.txt has been live since 2026-08-04,
and to a stranger it is a file of hashes with no way to interpret or check it.
An anchor nobody can read is not much of a witness. This page explains what the
ledger is, what the anchors prove, and how someone outside this company would
verify a claim we make -- including against us.

The argument the page has to make is uncomfortable on purpose: our own ledger
contains receipts recording runs where OUR audit produced nothing. Those stay.
A ledger that holds only clean runs is a ledger nobody should believe, and the
willingness to publish failures is the only thing that makes the clean ones
worth anything.

HONESTY CONSTRAINTS baked in here, because this page is a trust claim and a
false one would be self-refuting:
  * Counts are read from the real anchors file and ledger, never typed by hand.
  * We say SIX OF EIGHT scheduled jobs, not "every" -- two are unwrapped.
  * attest is not published yet, so the page does not offer an install command
    it cannot honour. It says the tool is being prepared for release.
  * HMAC signing is stated as NOT third-party-verifiable, because it isn't.

Same architecture as the other explainer pages: shell inherited verbatim from
the cleanup-service page so nav, footer and brand tokens never drift. No
JavaScript -- a page about evidence should make no claim it has to compute.
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'proof'
ANCHORS = OUT_DIR / 'attest-anchors.txt'

TITLE = 'Proof — A Public, Tamper-Evident Ledger of Our Own Work'
DESC = ('A public, tamper-evident ledger of our own scheduled jobs: what each run claimed, '
        'what it actually produced, and the runs where ours produced nothing.')
CANON = 'https://automatedworkflowllc.com/proof/'

PAGE_CSS = """
/* ---- proof / evidence ledger ---- */
.pf-lede{font-size:1.08rem;max-width:40rem}
.pf-stats{display:flex;gap:.55rem;flex-wrap:wrap;margin:1.6rem 0 0}
.pf-stat{border:1px solid var(--line);border-radius:.6rem;background:var(--card);padding:.6rem .9rem}
.pf-stat b{display:block;font-family:var(--mono);font-size:1.3rem;line-height:1.15}
.pf-stat span{font-size:.68rem;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.07em}
.pf-bad{border-left:4px solid #B4452C;background:var(--card);border-radius:.6rem;
padding:1rem 1.2rem;margin:1.6rem 0;max-width:42rem}
.pf-steps{display:grid;gap:.8rem;margin:1.2rem 0 0;max-width:44rem}
.pf-step{border:1px solid var(--line);border-radius:.7rem;background:var(--card);padding:1rem 1.2rem}
.pf-step h3{margin:0 0 .3rem;font-size:1rem}
.pf-step p{margin:0;font-size:.92rem;color:var(--ink-soft)}
.pf-code{font-family:var(--mono);font-size:.85rem;background:var(--card);border:1px solid var(--line);
border-radius:.5rem;padding:.8rem 1rem;overflow-x:auto;margin:.9rem 0;max-width:44rem}
.pf-limits{margin:1.1rem 0 0;padding-left:1.15rem;max-width:42rem}
.pf-limits li{margin:.45rem 0;color:var(--ink-soft)}
.pf-limits b{color:var(--ink)}
.pf-cta{margin-top:2rem;padding:1.4rem;border:1px solid var(--line);border-radius:12px;background:var(--card)}
.pf-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">We keep receipts on our own automations.<br>Including the ones that failed.</h1>
  <p class="pf-lede" style="color:var(--ink-soft)">
    Anyone can tell you their systems are working. The failure that costs money does not throw an
    error &mdash; the job runs, the log fills, the exit code is zero, and nothing actually happened.
    So our scheduled jobs write a signed receipt every time they run, recording what each one
    <em>claimed</em> against what it actually <em>produced</em>. This page is that ledger, and how
    you would check it without taking our word for anything.
  </p>

  <div class="pf-stats">
    <div class="pf-stat"><b>__RECEIPTS__</b><span>receipts on record</span></div>
    <div class="pf-stat"><b>__AGENTS__</b><span>systems reporting</span></div>
    <div class="pf-stat"><b>__FAILS__</b><span>recording our own failures</span></div>
    <div class="pf-stat"><b>__ANCHORS__</b><span>public anchors</span></div>
  </div>

  <div class="pf-bad">
    <strong>The uncomfortable part, which is the point.</strong> __FAILS__ of the receipts above
    record runs where <em>our own</em> nightly audit produced nothing at all &mdash; a bug in our
    wrapper meant the tool never ran, twice in a row, while reporting success. The receipts caught
    it at the moment it happened, and they stay in the ledger permanently. A ledger that contains
    only clean runs is a ledger nobody should believe.
  </div>

  <h2>What a receipt actually records</h2>
  <p style="color:var(--ink-soft);max-width:40rem">Each run declares its outputs up front. Afterwards
  the file is hashed again and compared &mdash; so &ldquo;the job succeeded&rdquo; has to survive
  contact with whether anything changed on disk.</p>

  <div class="pf-steps">
    <div class="pf-step">
      <h3>Claimed vs. produced</h3>
      <p>The declared outputs, hashed before and after the run, with the newest date found
      <em>inside</em> each text file recorded alongside. A report can be freshly written and still
      contain last week's numbers; the receipt captures both facts.</p>
    </div>
    <div class="pf-step">
      <h3>The exit code tells the truth</h3>
      <p>A tool that exits zero without touching its declared output fails the receipt, whatever it
      says about itself. That is the whole design: the scheduler learns about the lie at the moment
      it happens, rather than the following week when someone opens the file.</p>
    </div>
    <div class="pf-step">
      <h3>Chained, so history cannot be quietly edited</h3>
      <p>Every receipt carries the hash of the one before it. Rewriting or deleting any entry breaks
      every link after it, and the break is visible to anyone holding the ledger.</p>
    </div>
    <div class="pf-step">
      <h3>Anchored in public, so it binds us too</h3>
      <p>A signed ledger only proves integrity against people without the key &mdash; which does not
      include us. So the chain head is published to this site on a schedule. Once a head is public,
      its history cannot be rewritten by anyone, ourselves included.</p>
    </div>
  </div>

  <h2 style="margin-top:2.4rem">How you would check it</h2>
  <p style="color:var(--ink-soft);max-width:40rem">The anchors file is plain text and append-only.
  Each line is the state of the ledger at the moment it was published.</p>

  <div class="pf-code">__ANCHOR_SAMPLE__</div>

  <p style="color:var(--ink-soft);max-width:42rem">To settle any dispute about work we say we did:
  take the anchor line that was public on the date in question &mdash; this file's history lives in
  a public repository, in CDN caches and in web archives, all of which are witnesses we do not
  control &mdash; then ask us for the ledger and hash its last line at that receipt count. If the
  hashes match, the history you are holding is the history that existed then. If we had edited
  anything behind that anchor, they would not.</p>

  <p style="margin-top:1rem"><a href="/proof/attest-anchors.txt">Read the raw anchors file &rarr;</a></p>

  <h2 style="margin-top:2.4rem">Do it yourself, on your own file</h2>
  <p style="color:var(--ink-soft);max-width:42rem">The limit stated below &mdash; that our receipts
  are signed with a key only we hold &mdash; has an answer, and you can use it right now.
  <a href="/proof/notarize/">Notarize a file in your browser</a>: it hashes the file, signs a
  receipt with an Ed25519 key generated on your device, and hands you the <em>public</em> half so
  anyone can verify it without trusting us, without an account, and without uploading a byte. Drop
  the file back in later &mdash; changed or not &mdash; and it will tell you which.</p>

  <h2 style="margin-top:2.4rem">What this does not prove</h2>
  <ul class="pf-limits">
    <li><b>The signatures are not third-party-verifiable yet.</b> Receipts are signed with a local
      key, which proves nobody without that key altered them &mdash; it does not prove <em>we</em>
      didn't, before publishing. Public anchoring is what closes that gap today; a keypair whose
      public half you can hold is the next step.</li>
    <li><b>It covers six of our eight scheduled jobs</b>, not all of them. The remaining two are
      named in our build log rather than quietly omitted.</li>
    <li><b>A receipt proves an output changed, not that it is correct.</b> Whether yesterday's date
      in today's report is a problem depends on the cadence, which is a judgment call &mdash; so the
      date is recorded as evidence and a separate check decides.</li>
    <li><b>The tool that produces these is not public yet.</b> It is stdlib-only, tested, and being
      prepared for release; we would rather ship it late than link an install command that does not
      work.</li>
  </ul>

  <div class="pf-cta">
    <h2 style="margin-top:0">If your automations report success, and you have not checked</h2>
    <p>That is the normal state of things, and it is where this whole line of work came from &mdash;
    our own stack, failing quietly, four days in a row. We audit for exactly that: the jobs that run,
    report success, and produce nothing. You get the findings with the evidence for each one,
    including the ones that turn out to be fine.</p>
    <p style="margin-bottom:0"><a class="btn" href="/free-demo/">Ask about an automation audit</a>
    &nbsp; <a href="/flatline/">See the open-source detector &rarr;</a></p>
  </div>
</main>
"""


def _stats() -> dict:
    """Real counts from the published anchors file plus the local ledger.

    The anchor count comes from the file this page ships beside, so the page
    cannot claim more anchors than are actually public. The receipt count comes
    from the newest anchor line -- again the published number, not a private
    one -- so the page is never ahead of its own evidence.
    """
    lines = [ln.strip() for ln in ANCHORS.read_text(encoding='utf-8').splitlines()
             if ln.strip() and not ln.startswith('#')]
    if not lines:
        raise SystemExit('refusing to build /proof/: no anchor lines published')
    last = lines[-1]
    m = re.search(r'receipts=(\d+)', last)
    if not m:
        raise SystemExit('refusing to build /proof/: newest anchor line has no receipt count')
    stats = {'anchors': len(lines), 'receipts': int(m.group(1)), 'sample': last}

    ledger = pathlib.Path.home() / '.attest' / 'ledger.jsonl'
    if not ledger.exists():
        raise SystemExit('refusing to build /proof/: no ledger to count agents and failures from')
    recs = [json.loads(l) for l in ledger.read_text(encoding='utf-8').splitlines() if l.strip()]
    recs = recs[:stats['receipts']]          # never describe beyond what is anchored
    # "systems reporting" must mean SYSTEMS. Seal receipts are pre-registered
    # claims filed under a person or a desk, not automations writing receipts --
    # counting them here would inflate the headline number on a trust page.
    runs = [r for r in recs if r.get('kind') != 'seal']
    stats['agents'] = len({r.get('agent') for r in runs if r.get('agent')})
    stats['fails'] = sum(1 for r in runs if r.get('problems'))
    stats['seals'] = len(recs) - len(runs)
    if stats['fails'] < 1:
        raise SystemExit('refusing to build /proof/: the page argues from our own recorded '
                         'failures and found none -- check the ledger before publishing')
    return stats


def main() -> None:
    st = _stats()
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

    body = (MAIN
            .replace('__RECEIPTS__', str(st['receipts']))
            .replace('__AGENTS__', str(st['agents']))
            .replace('__FAILS__', str(st['fails']))
            .replace('__ANCHORS__', str(st['anchors']))
            .replace('__ANCHOR_SAMPLE__', st['sample']))
    for token in ('__RECEIPTS__', '__AGENTS__', '__FAILS__', '__ANCHORS__', '__ANCHOR_SAMPLE__'):
        if token in body:
            raise SystemExit(f'refusing to build /proof/: {token} left unsubstituted')

    page = head + body + footer + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes) '
          f'-- {st["receipts"]} receipts, {st["agents"]} agents, {st["fails"]} failure receipts, '
          f'{st["anchors"]} anchors')


if __name__ == '__main__':
    main()
