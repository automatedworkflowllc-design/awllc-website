#!/usr/bin/env python3
"""Build /tare/ -- the public page for the telemetry cost-governance gateway.

Why this page exists: Tare has no domain of its own and, for now, is not meant
to have one. Colin's call on 2026-08-24 was to host it here rather than buy
tare.dev out of redemption, which is the right trade -- the argument is worth
more than the address, and this site already carries the evidence culture the
argument depends on.

WHAT THIS PAGE IS CAREFUL ABOUT

Three things make Tare different from the tool pages beside it, and all three
push toward saying LESS rather than more:

1. The repository is PRIVATE. flatline and canary can end with "here is the
   source, go read it"; this cannot. So the page never says open source, never
   links a repo, and leans on what has been observed rather than on what a
   reader can inspect for themselves.

2. It is a working system, not a hosted service, and it has no customers. The
   builds page already established the house rule for this -- status chips that
   say RUNNING rather than LIVE "because no customer is on it yet". Anything
   here that implied sign-up would be a promise nobody can keep today.

3. Pricing is deliberately absent. The project's own roadmap forbids quoting
   production prices derived from its local $0.10/GiB development value, and
   the incumbent's published rates move. A page that priced either would be
   overclaiming within a quarter.

NO DRIFTING NUMBERS. Every figure here is a DATED OBSERVATION of one run -- 80
series measured, cap at 40, that service refused -- not an inventory that grows.
The flatline page sold itself on "122 tests" and was overclaiming by nine within
a fortnight when the suite grew; claim_audit now re-derives that figure on every
push. Nothing on this page needs that treatment, because a record of what
happened on a given day does not rot. If a count is ever added here, it needs a
claim in _qa/claims.toml the same day.

Same architecture as the other tool pages: shell inherited verbatim from the
cleanup-service page so nav, footer and brand tokens cannot drift, and no
JavaScript, because this page computes nothing.
"""
from __future__ import annotations

import pathlib
import re

from toolkit import PLAIN_CSS

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'tare'

TITLE = 'Tare — Stop an Observability Bill Before It Is Spent'
DESC = ('A cost-governance gateway for OpenTelemetry: caps runaway metric cardinality and enforces a hard budget before telemetry leaves your network.')
CANON = 'https://automatedworkflowllc.com/tare/'

PAGE_CSS = """
/* ---- tare explainer ---- */
.tr-lede{font-size:1.08rem;max-width:40rem}
.tr-bad{border-left:4px solid #B23B3B;background:var(--card);border-radius:.6rem;
padding:1rem 1.2rem;margin:1.6rem 0;max-width:42rem}
.tr-bad code{font-family:var(--mono);font-size:.85rem}
.tr-flow{border:1px solid var(--line);border-radius:.7rem;background:var(--card);
padding:1rem 1.2rem;margin:1.4rem 0;max-width:42rem;overflow-x:auto}
.tr-flow pre{margin:0;font-family:var(--mono);font-size:.82rem;line-height:1.6}
.tr-does{display:grid;gap:.8rem;margin:1.2rem 0 0}
.tr-do{border:1px solid var(--line);border-radius:.7rem;background:var(--card);padding:1rem 1.2rem}
.tr-do h3{margin:0 0 .3rem;font-size:1rem}
.tr-do p{margin:0;color:var(--ink-soft);font-size:.92rem}
.tr-do .ev{margin:.5rem 0 0;font-size:.88rem;padding-left:.7rem;border-left:2px solid var(--line-strong)}
.tr-seen{margin:1rem 0 0;padding-left:1.15rem;max-width:42rem}
.tr-seen li{margin:.45rem 0;color:var(--ink-soft)}
.tr-seen strong{color:var(--ink)}
.tr-state{border:1px solid var(--line-strong);border-radius:.7rem;background:var(--well,var(--card));
padding:1.1rem 1.25rem;margin:1.8rem 0;max-width:42rem}
.tr-state h2{margin:0 0 .4rem;font-size:1.05rem}
.tr-state p{margin:.4rem 0 0;color:var(--ink-soft);font-size:.92rem}
.tr-cta{border:1px solid var(--line);border-radius:.7rem;background:var(--card);
padding:1.2rem 1.35rem;margin:2rem 0 0;max-width:42rem}
"""

MAIN = """
<main class="wrap" id="main">
  <h1>Your observability bill is decided before you ever see it</h1>

  <p class="tr-lede" style="color:var(--ink-soft)">
    Metrics pricing is driven by <strong>cardinality</strong> &mdash; the number of distinct
    label combinations you send. One deploy that adds a user ID, a request path or a container ID
    to an existing metric can multiply that overnight. Nothing rejects the data, nothing pages
    anyone, and the number arrives weeks later on an invoice.
  </p>

  <div class="tr-bad">
    <strong>The asymmetry that makes this worth building.</strong> The large vendors bill
    cardinality as a line item. That means a customer&rsquo;s mistake is the vendor&rsquo;s revenue,
    and nothing upstream of the invoice has any reason to stop it. <strong>Tare caps it
    instead of charging for it</strong> &mdash; which is the one position a company funded by that
    line item cannot copy.
  </div>

  <h2>Where it sits</h2>
  <p style="color:var(--ink-soft);max-width:40rem">In front of whatever you already send telemetry
  to. It does not replace your backend, own your data, or ask you to migrate anything.</p>

  <div class="tr-flow">
<pre>your services ──▶  Tare  ──▶  the backend you already pay for
                    │
                    ├─ budget enforced BEFORE anything leaves
                    ├─ runaway cardinality capped, by service, by name
                    └─ "what is this about to cost me?" answered up front</pre>
  </div>

  <h2 style="margin-top:2.4rem">What it actually does</h2>

  <div class="tr-does">
    <div class="tr-do">
      <h3>Refuses over-budget telemetry before the cost exists</h3>
      <p>A budget that is checked after the data has been forwarded is a report, not a control:
      the request gets recorded as blocked and the bill still arrives. Tare refuses at the hop
      <em>before</em> the vendor, so the spend never happens.</p>
      <p class="ev">Verified by standing up a stand-in vendor that records every request it
      receives, then breaching the budget: the refusal was returned and <strong>nothing reached the
      vendor at all</strong>. A companion check confirms traffic resumes once the budget is lifted,
      so that result cannot come from a fixture that quietly died.</p>
    </div>

    <div class="tr-do">
      <h3>Caps the runaway service without silencing the rest</h3>
      <p>A tenant-wide block is self-defeating: it takes away the telemetry you need to diagnose
      the very thing that triggered it. Tare attributes the explosion to a single service and
      refuses that one, naming it and the limit it crossed.</p>
      <p class="ev">Observed under enforcement: 80 distinct series measured and attributed to the
      offending service, the cap set to 40, that service refused with a code naming it &mdash; and
      <strong>a different service in the same workspace still accepted</strong>. That last half is
      the whole point; a tenant-wide cap would look identical without it.</p>
    </div>

    <div class="tr-do">
      <h3>Answers the cost question before the deploy, not after</h3>
      <p>Ask what adding a given number of new series would do to the month before you ship the
      change that adds them.</p>
      <p class="ev">The same measurement drives enforcement, so the forecast and the thing that
      refuses cannot disagree with each other.</p>
    </div>

    <div class="tr-do">
      <h3>Says so when it cannot tell</h3>
      <p>A payload it cannot read reports <em>unknown</em> and the cap stands. A budget it has not
      been able to evaluate says exactly that, rather than showing a reassuring green.</p>
      <p class="ev">This is the discipline the rest of this site is built on: not being able to
      check something is never recorded as having checked it and found nothing wrong.</p>
    </div>
  </div>

  <h2 style="margin-top:2.4rem">How it has been checked</h2>
  <p style="color:var(--ink-soft);max-width:40rem">The interesting failures in this category are
  quiet ones &mdash; a cap that reports as configured and is inert, a budget that meters data the
  backend actually rejected. So the checking is aimed at those.</p>

  <ul class="tr-seen">
    <li><strong>Every guard has been watched failing.</strong> Each rule is deliberately broken in
      turn and the run is only valid if its check goes red for the right reason &mdash; alongside a
      deliberate change that must <em>not</em> be caught, so &ldquo;everything was caught&rdquo;
      cannot be reported by a suite that is simply broken.</li>
    <li><strong>Verified against a running system, not only in tests.</strong> One early round was
      thrown out because it had been reading a container built four hours before the work it was
      supposed to be checking.</li>
    <li><strong>A cap that was configured, reported as configured, and completely inert.</strong>
      Cardinality was only measured while a second budget existed, so a workspace running one
      budget alone enforced forever against a snapshot that never refreshed. No unit test could
      see it; only running it for real did.</li>
    <li><strong>Data the backend rejected was being billed in full.</strong> The protocol has a
      success response that reports partial rejection inside the body. Reading only the status code
      meant the customer paid for records nothing stored.</li>
    <li><strong>Its own verification scripts were wrong more often than the product.</strong> Run as
      a set for the first time, five of fifteen failed &mdash; and four of the five were defects in
      the checks, each announcing a failure against a system that was working correctly.</li>
  </ul>

  <div class="tr-state">
    <h2>Where it honestly stands</h2>
    <p><strong>Tare is a working system, not a hosted service.</strong> There is nothing to sign up
    for on this page, and there are no customers on it. It runs as a single writer &mdash; a
    documented pilot boundary, not a hidden one &mdash; which is fine for one deployment and is the
    work that remains before it is fine for several.</p>
    <p><strong>The source is private</strong>, so unlike the free tools on this site you cannot go
    and read it. That is why this page leads with what has been measured rather than asking you to
    take the architecture on faith.</p>
    <p><strong>No prices are quoted here on purpose.</strong> The development configuration uses a
    placeholder rate, and quoting a number derived from it &mdash; or the incumbent&rsquo;s
    published rates, which move &mdash; would be overclaiming by the quarter.</p>
  </div>

  <div class="tr-cta">
    <h2 style="margin-top:0">If your telemetry bill has ever surprised you</h2>
    <p style="color:var(--ink-soft)">That surprise is the problem this is pointed at, and the
    interesting part of the conversation is usually which of your services would have been the one
    refused. Worth a short conversation either way.</p>
    <p style="margin-bottom:0"><a class="btn" href="/free-demo/">Start a conversation</a>
    &nbsp; <a href="/builds/">See everything we have built &rarr;</a></p>
  </div>
</main>
"""

LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Tare",
  "url": "https://automatedworkflowllc.com/tare/",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Any",
  "description": "A cost-governance gateway for OpenTelemetry that enforces a hard budget and caps runaway metric cardinality before telemetry leaves the network, in front of an existing observability backend."
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

    page = head + MAIN + footer + LD + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
