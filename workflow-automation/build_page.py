# -*- coding: utf-8 -*-
"""Build /workflow-automation/ (STAGED, noindex) from the ai-business-pulse template.

Clones the Pulse page for its head/CSS/nav/footer, swaps <main> for the broader
workflow-automation positioning, and adds an INTERACTIVE approve-gate demo
(sample data, labeled invented; the demo stages, it never sends — which is the point).
Ships noindex per the standing rule: new pages wait for Colin's copy review.
Idempotent: rebuilds output from the source template every run.
"""
import io, os, re

REPO = os.path.expanduser("~/Documents/awllc-website")
SRC = os.path.join(REPO, "ai-business-pulse", "index.html")
OUT_DIR = os.path.join(REPO, "workflow-automation")
OUT = os.path.join(OUT_DIR, "index.html")

s = io.open(SRC, encoding="utf-8").read()

# ---------- head swaps ----------
s = s.replace("<title>AI Business Pulse &mdash; A Weekly Report That Writes Itself</title>",
              "<title>Workflow Automation With a Human Approve Button | Automated Workflow</title>")
s = s.replace('<meta name="robots" content="index,follow">',
              '<meta name="robots" content="noindex,nofollow"><!-- STAGED: awaiting Colin copy review -->')
s = re.sub(r'<meta name="description" content="[^"]*"',
           '<meta name="description" content="I build the automated version of the boring parts of your business — intake, invoicing, follow-ups, weekly reports — with the judgment calls left with you. AI drafts; you approve."',
           s, count=1)
s = re.sub(r'<meta property="og:title" content="[^"]*"',
           '<meta property="og:title" content="Workflow Automation With a Human Approve Button"', s, count=1)
s = re.sub(r'<link rel="canonical" href="[^"]*"',
           '<link rel="canonical" href="https://automatedworkflowllc.com/workflow-automation/"', s, count=1)
s = re.sub(r'<meta property="og:url" content="[^"]*"',
           '<meta property="og:url" content="https://automatedworkflowllc.com/workflow-automation/"', s, count=1)

# ---------- main swap ----------
start = s.index("<main>")
end = s.index("</main>") + len("</main>")

MAIN = r"""<main>
  <div class="wrap">

    <section class="hero">
      <p class="eyebrow green">Workflow automation &middot; the whole system, not just the sheet</p>
      <h1>Automation <span class="thin">with a human approve button.</span></h1>
      <p class="subhead">Your week is full of handoffs &mdash; inquiry to quote, job to invoice, invoice to follow-up, numbers to &ldquo;how are we actually doing?&rdquo; I build the automated version of the boring parts, and I leave the judgment calls exactly where they belong: <b>with you</b>. The AI drafts. Nothing sends itself.</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="mailto:colin@automatedworkflowllc.com?subject=The%20workflow%20that%20eats%20my%20week&amp;body=Hi%20Colin%2C%0A%0AThe%20repetitive%20part%20of%20my%20week%20I%27d%20most%20like%20to%20stop%20doing%20by%20hand%3A%20">Tell me the workflow that eats your week &rarr;</a>
        <a class="btn btn-ghost" href="/demo/">Touch a live dashboard &rarr;</a>
      </div>
      <p class="hero-meta">A real person in <b>Gainesville, FL</b> &middot; working with small businesses everywhere</p>
    </section>

    <section class="block">
      <p class="eyebrow">The problem</p>
      <h2>It&rsquo;s not the work. It&rsquo;s the work <em>between</em> the work.</h2>
      <p>The job itself usually goes fine. What quietly eats the week is everything around it: retyping the same customer into three places, remembering which quote never got an answer, invoicing the job that finished last Tuesday, chasing the invoice from six weeks ago, and assembling the numbers into something you can act on.</p>
      <p class="lead-line">Every one of those is a handoff. Every handoff depends on somebody remembering. That&rsquo;s the leak.</p>
      <p>Automation done right doesn&rsquo;t replace your judgment &mdash; it replaces the remembering. The system watches the handoffs, does the drafting and the arithmetic, and brings you a short list of decisions instead of a long list of chores.</p>
      <div class="pullquote"><p>The system decides <b>who and what tone</b>. You decide <b>whether</b>.</p></div>
    </section>

    <section class="block">
      <p class="eyebrow">Try it &mdash; right here</p>
      <h2>The approve button, live</h2>
      <p>This is a working miniature of the follow-up system I build. Three overdue invoices, three drafted emails &mdash; the tone escalates with age automatically. Approve the ones you&rsquo;d actually send. <b>Sample data, every number invented</b> &mdash; and in the real system, exactly like this demo, nothing goes out without the approve click.</p>
      <div class="ag-demo" id="agDemo" aria-label="Interactive demo of the approve-gate follow-up queue">
        <div class="ag-row" data-tier="friendly">
          <div class="ag-info"><span class="ag-inv">INV-2123 &middot; Santa Fe Print Shop &middot; $1,120</span><span class="ag-tier ag-green">22 days &middot; FRIENDLY</span>
            <p class="ag-draft">&ldquo;Hi &mdash; quick nudge on invoice 2123 from last month. No rush if it&rsquo;s already queued up on your end&hellip;&rdquo;</p></div>
          <button class="ag-btn" type="button" aria-pressed="false">Approve</button>
        </div>
        <div class="ag-row" data-tier="firmer">
          <div class="ag-info"><span class="ag-inv">INV-2118 &middot; Alachua Auto Care &middot; $1,875</span><span class="ag-tier ag-amber">37 days &middot; FIRMER</span>
            <p class="ag-draft">&ldquo;Hi &mdash; invoice 2118 is now a month past due. Could you let me know when payment is scheduled?&hellip;&rdquo;</p></div>
          <button class="ag-btn" type="button" aria-pressed="false">Approve</button>
        </div>
        <div class="ag-row" data-tier="serious">
          <div class="ag-info"><span class="ag-inv">INV-2101 &middot; Hogtown Coffee Roasters &middot; $1,450</span><span class="ag-tier ag-red">68 days &middot; SERIOUS</span>
            <p class="ag-draft">&ldquo;Hi &mdash; invoice 2101 is 68 days outstanding. I&rsquo;d like to resolve this week; here are the options&hellip;&rdquo;</p></div>
          <button class="ag-btn" type="button" aria-pressed="false">Approve</button>
        </div>
        <div class="ag-foot">
          <span id="agCount">0 of 3 approved</span>
          <button class="btn btn-primary ag-send" id="agSend" type="button" disabled>Send approved</button>
        </div>
        <p class="ag-result" id="agResult" role="status" aria-live="polite"></p>
      </div>
      <figure class="pulse-demo" style="margin-top:34px">
        <figcaption class="pulse-demo-cap"><span aria-hidden="true">//</span> And the reporting half &mdash; watch a report write itself, 20 seconds</figcaption>
        <video src="/ai-business-pulse-demo.mp4" poster="/ai-business-pulse-thumb.jpg" autoplay muted loop playsinline preload="metadata"
               aria-label="Twenty-second demo: the workflow reads your numbers, writes a plain-English summary, and emails it to you."></video>
      </figure>
    </section>

    <section class="block">
      <p class="eyebrow">What I automate</p>
      <h2>The handoffs I build systems for</h2>
      <ul class="checks">
        <li><strong>Invoice follow-up, approve-gated</strong> &mdash; overdue invoices get drafted chase emails in a tone that matches their age. You approve; then they send.</li>
        <li><strong>The weekly report that writes itself</strong> &mdash; an AI reads your live numbers every Monday and writes the three paragraphs you&rsquo;d actually read. Math by formula, words by AI.</li>
        <li><strong>Done-vs-billed reconciliation</strong> &mdash; work you finished but never invoiced, surfaced automatically instead of discovered at tax time.</li>
        <li><strong>Intake that routes itself</strong> &mdash; a form submission becomes a tracked row, a notification, and a draft reply &mdash; not a sticky note.</li>
        <li><strong>Two systems that should agree, checked nightly</strong> &mdash; bookings vs. billing, hours worked vs. hours invoiced, out vs. returned.</li>
        <li><strong>Self-updating dashboards</strong> &mdash; the sheets work this site started with. Still the best $650 I can build you.</li>
      </ul>
      <p>All of it runs on tools you already have &mdash; Google Sheets, Gmail, your existing forms &mdash; so there&rsquo;s no new software for your people to learn.</p>
    </section>

    <section class="block">
      <p class="eyebrow">The rules it&rsquo;s built on</p>
      <h2>Why you can trust a system I automate</h2>
      <ul class="checks">
        <li><strong>The AI never does arithmetic.</strong> Every total is computed by formula before the model sees it. Language models are excellent writers and unreliable accountants &mdash; each does only the part it&rsquo;s good at.</li>
        <li><strong>Nothing sends itself.</strong> Anything that leaves your business with your name on it &mdash; an email, a report, a nudge &mdash; waits for a human approve.</li>
        <li><strong>Every build is documented in public.</strong> The bugs I catch and the checks that catch them are on the <a href="/build-log/">build log</a> &mdash; including the ones I got wrong first.</li>
      </ul>
    </section>

    <section class="block">
      <p class="eyebrow">What it costs</p>
      <h2>Start small. The ladder is the same either way.</h2>
      <ul class="checks">
        <li><strong>$300</strong> &mdash; spreadsheet cleanup: your messiest sheet, rebuilt to update itself.</li>
        <li><strong>$650</strong> &mdash; automated dashboard: your numbers on one live page.</li>
        <li><strong>$1,000 + from $250/mo</strong> &mdash; <a href="/ai-business-pulse/">the AI Business Pulse</a>: the Monday report + approve-gated follow-ups, run for you.</li>
        <li><strong>From $2,000</strong> &mdash; full workflow automation: intake to invoice to follow-up, built end to end around how your business already works.</li>
      </ul>
      <p>Every engagement starts the same free way: <b>send me one messy file</b> &mdash; a job log, an invoice export, an intake sheet &mdash; and I&rsquo;ll send back a working automated version within a day. Free, yours to keep either way.</p>
    </section>

    <section class="block">
      <p class="eyebrow">Who&rsquo;s building it</p>
      <h2>One person. In public. On purpose.</h2>
      <p>I&rsquo;m Colin McCarthy &mdash; I run Automated Workflow from Gainesville, Florida. I&rsquo;m Anthropic Academy certified, I work in operations myself, and I&rsquo;m early enough in this business that every build gets my full attention and my public <a href="/build-log/">build log</a> documents exactly how careful I am with it. I don&rsquo;t have a wall of testimonials yet. I have working systems you can touch, and a free first deliverable that costs you nothing to judge.</p>
    </section>

    <section class="cta-band">
      <p class="eyebrow">The whole pitch, honestly</p>
      <h2>What&rsquo;s the workflow that eats your week?</h2>
      <p>Tell me in one sentence. I&rsquo;ll tell you in one email whether it&rsquo;s automatable, what it would cost, and what I&rsquo;d build first &mdash; and the first artifact is free either way.</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="mailto:colin@automatedworkflowllc.com?subject=The%20workflow%20that%20eats%20my%20week">Email Colin &rarr;</a>
        <a class="btn btn-ghost" href="/free-demo/">Or start with one messy file &rarr;</a>
      </div>
    </section>

  </div>
</main>"""

s = s[:start] + MAIN + s[end:]

# ---------- scoped CSS + JS for the approve-gate demo ----------
EXTRA = r"""
<style>
.ag-demo{border:1px solid var(--line,#E4DFD1);border-radius:14px;padding:18px 18px 14px;background:var(--paper,#FFFFFF)}
.ag-row{display:flex;gap:14px;align-items:flex-start;justify-content:space-between;padding:12px 6px;border-bottom:1px solid var(--line,#E4DFD1)}
.ag-info{flex:1 1 auto;min-width:0}
.ag-inv{font-weight:700;display:inline-block;margin-right:10px}
.ag-tier{font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.06em;padding:2px 8px;border-radius:20px;white-space:nowrap}
.ag-green{background:#E6F2EC;color:#1E7A47}.ag-amber{background:#FBEFE0;color:#B45309}.ag-red{background:#F6E7E7;color:#B23B3B}
.ag-draft{margin:.45em 0 0;font-size:.92rem;color:var(--ink-soft,#5C5645);font-style:italic}
.ag-btn{flex:0 0 auto;border:1.5px solid var(--ink,#211D14);background:transparent;border-radius:24px;padding:7px 16px;font-weight:700;cursor:pointer}
.ag-btn[aria-pressed="true"]{background:#1E7A47;border-color:#1E7A47;color:#fff}
.ag-foot{display:flex;align-items:center;justify-content:space-between;padding-top:12px;gap:12px}
.ag-send[disabled]{opacity:.45;cursor:not-allowed}
.ag-result{margin:.7em 2px 0;font-size:.95rem;font-weight:600;color:#1E7A47;min-height:1.4em}
@media (max-width:560px){.ag-row{flex-direction:column}.ag-btn{align-self:flex-start}}
</style>
<script>
(function(){
  var rows=document.querySelectorAll('#agDemo .ag-btn'),send=document.getElementById('agSend'),
      count=document.getElementById('agCount'),result=document.getElementById('agResult'),n=0;
  rows.forEach(function(b){b.addEventListener('click',function(){
    var on=b.getAttribute('aria-pressed')==='true';
    b.setAttribute('aria-pressed',on?'false':'true');b.textContent=on?'Approve':'Approved ✓';
    n+= on?-1:1;count.textContent=n+' of 3 approved';send.disabled=(n===0);result.textContent='';});});
  send.addEventListener('click',function(){
    result.textContent=n+(n===1?' email':' emails')+' staged — and that’s where this demo stops. Sample data, invented numbers; in the real system, this click is when they actually go out. The '+(3-n)+' you didn’t approve? They wait. That’s the point.';});
})();
</script>
"""
s = s.replace("</body>", EXTRA + "\n</body>")

os.makedirs(OUT_DIR, exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="\n").write(s)
print("written", OUT, len(s), "bytes")

# ---------- clone audit: no inherited client claims ----------
bad = re.findall(r"[^.]*(?:Plenty of clients|clients do one|trusted by|hundreds of customers|working with local businesses and clients)[^.]*\.", s)
print("clone-audit hits:", len(bad))
for b in bad: print("  !!", b.strip()[:120])
assert not bad, "inherited social-proof claims found"
# noindex present?
assert "noindex" in s, "missing noindex"
print("staged (noindex) OK")
