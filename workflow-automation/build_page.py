# -*- coding: utf-8 -*-
"""Build /workflow-automation/ (STAGED, noindex) from the ai-business-pulse template.

v2 (2026-08-02, Colin-authorized "state of the art" pass, spec:
Documents/AWLLC-workflow-automation-upgrade-spec.md):
  - Approve-gate demo rebuilt as stateful CARDS: approve -> "QUEUED" state flip,
    tier legend including the under-15-days SILENCE tier shown live as a 4th
    non-approvable row, and a real OUTCOME PANEL on send ("N leave tomorrow 9:00am,
    M held") instead of a one-line result.
  - NEW animated pipeline figure: 01 READ -> 02 COMPUTE -> 03 DRAFT -> [GATE] -> 04 SEND,
    pure CSS/SVG-free divs; the pulse STOPS at the gate until the visitor flips the
    approve toggle. prefers-reduced-motion => static diagram, gate highlighted.
  - NEW typewriter panel: the Monday narrative types itself over a labeled invented
    KPI strip; caption states the precompute-then-narrate rule. IO-triggered.
  - Scroll reveals on .block sections (CSS + IntersectionObserver, reduced-motion safe).
All sample figures remain INVENTED AND LABELED. Ships noindex per standing rule.
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
              "<title>Automation With a Human Approve Button | Automated Workflow</title>")
s = s.replace('<meta name="robots" content="index,follow">',
              '<meta name="robots" content="noindex,nofollow">\n'
              '<!-- STAGED on purpose: awaiting Colin\'s copy review before publish (standing rule for new pages). '
              'When he approves: flip to index,follow + add to sitemap + link from homepage. -->')
s = re.sub(r'<meta name="description" content="[^"]*"',
           '<meta name="description" content="I build the automated version of the boring parts of a business — intake, invoicing, follow-ups, weekly reports. The AI drafts; you approve."',
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
        <a class="btn btn-ghost" href="/free-demo/">Or send one messy file &mdash; free &rarr;</a>
      </div>
      <p class="hero-meta">A real person in <b>Gainesville, FL</b> &middot; built for small businesses everywhere</p>
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
      <p class="eyebrow">How every build is wired</p>
      <h2>One pipeline. One gate. Watch it.</h2>
      <p>Everything I build follows the same shape: read your live numbers, do the arithmetic in formulas, let the AI draft the words &mdash; and then <b>stop at the gate</b> until a human says go. Flip the switch and watch what changes.</p>
      <div class="pl-wrap" id="plWrap" role="group" aria-label="Animated diagram: data flows through read, compute, draft, then waits at a human gate before send">
        <div class="pl-track">
          <div class="pl-node" data-n="01"><span class="pl-t">READ</span><span class="pl-d">your live numbers</span></div>
          <div class="pl-seg"><span class="pl-dot pl-dot-a" aria-hidden="true"></span></div>
          <div class="pl-node" data-n="02"><span class="pl-t">COMPUTE</span><span class="pl-d">math by formula</span></div>
          <div class="pl-seg"><span class="pl-dot pl-dot-b" aria-hidden="true"></span></div>
          <div class="pl-node" data-n="03"><span class="pl-t">DRAFT</span><span class="pl-d">words by AI</span></div>
          <div class="pl-seg pl-seg-gate"><span class="pl-dot pl-dot-c" aria-hidden="true"></span></div>
          <div class="pl-node pl-gate" id="plGate"><span class="pl-t">THE GATE</span><span class="pl-d" id="plGateD">waiting on you</span></div>
          <div class="pl-seg"><span class="pl-dot pl-dot-d" aria-hidden="true"></span></div>
          <div class="pl-node" data-n="04"><span class="pl-t">SEND</span><span class="pl-d">their inbox</span></div>
        </div>
        <div class="pl-controls">
          <label class="pl-toggle"><input type="checkbox" id="plOk"><span class="pl-slider" aria-hidden="true"></span><span class="pl-label">Give the OK</span></label>
          <span class="pl-status" id="plStatus" role="status" aria-live="polite">Drafts are piling up at the gate &mdash; nothing leaves.</span>
        </div>
      </div>
    </section>

    <section class="block">
      <p class="eyebrow">Try it &mdash; right here</p>
      <h2>The approve button, live</h2>
      <p>This is a working miniature of the follow-up system I build. Overdue invoices get a drafted email in a tone that matches their age &mdash; and one that&rsquo;s <em>too fresh to chase</em> gets deliberate silence. Approve the ones you&rsquo;d actually send. <b>Sample data &mdash; every number and business name invented.</b></p>
      <div class="ag-legend" role="group" aria-label="Tone tiers by invoice age">
        <span class="ag-tier ag-grey">under 15 days &middot; SILENCE</span>
        <span class="ag-tier ag-green">15+ &middot; FRIENDLY</span>
        <span class="ag-tier ag-amber">30+ &middot; FIRMER</span>
        <span class="ag-tier ag-red">60+ &middot; SERIOUS</span>
      </div>
      <div class="ag-demo" id="agDemo" role="group" aria-label="Interactive demo of the approve-gate follow-up queue">
        <div class="ag-card ag-quiet" data-tier="silence">
          <div class="ag-info"><span class="ag-inv">INV-2130 &middot; Fernwood Vet Clinic &middot; $940</span><span class="ag-tier ag-grey">9 days &middot; SILENCE</span>
            <p class="ag-draft">No draft. Nine days is too fresh &mdash; a nudge now reads as twitchy, not attentive. The system waits on purpose.</p></div>
          <span class="ag-held" aria-hidden="true">waits</span>
        </div>
        <div class="ag-card" data-tier="friendly">
          <div class="ag-info"><span class="ag-inv">INV-2123 &middot; Bluebird Print Co. &middot; $1,120</span><span class="ag-tier ag-green">22 days &middot; FRIENDLY</span>
            <p class="ag-draft">&ldquo;Hi &mdash; quick nudge on invoice 2123 from last month. No rush if it&rsquo;s already queued up on your end&hellip;&rdquo;</p></div>
          <button class="ag-btn" type="button" aria-pressed="false">Approve</button>
        </div>
        <div class="ag-card" data-tier="firmer">
          <div class="ag-info"><span class="ag-inv">INV-2118 &middot; Crestline Auto Care &middot; $1,875</span><span class="ag-tier ag-amber">37 days &middot; FIRMER</span>
            <p class="ag-draft">&ldquo;Hi &mdash; invoice 2118 is now a month past due. Could you let me know when payment is scheduled?&hellip;&rdquo;</p></div>
          <button class="ag-btn" type="button" aria-pressed="false">Approve</button>
        </div>
        <div class="ag-card" data-tier="serious">
          <div class="ag-info"><span class="ag-inv">INV-2101 &middot; Harbor Coffee Roasters &middot; $1,450</span><span class="ag-tier ag-red">68 days &middot; SERIOUS</span>
            <p class="ag-draft">&ldquo;Hi &mdash; invoice 2101 is 68 days outstanding. I&rsquo;d like to resolve this week; here are the options&hellip;&rdquo;</p></div>
          <button class="ag-btn" type="button" aria-pressed="false">Approve</button>
        </div>
        <div class="ag-foot">
          <span id="agCount" role="status">0 of 3 approved &middot; 1 held in silence</span>
          <button class="btn btn-primary ag-send" id="agSend" type="button" disabled>Send approved</button>
        </div>
        <div class="ag-outcome" id="agOutcome" role="status" aria-live="polite">
          <p class="ag-outcome-head" id="agOutcomeHead"></p>
          <p class="ag-outcome-body">&hellip;and that&rsquo;s where this demo stops, by design. In the real system that approve click is the moment they actually go out &mdash; and the drafts you didn&rsquo;t approve simply wait for the next queue. Nothing you saw here sent anything anywhere.</p>
        </div>
      </div>
    </section>

    <section class="block">
      <p class="eyebrow">The reporting half</p>
      <h2>Watch a report write itself</h2>
      <div class="tw-panel" id="twPanel" role="group" aria-label="Demo: the Monday narrative types itself over an invented KPI strip">
        <div class="tw-kpis" aria-hidden="false">
          <span class="tw-kpi"><b>$208,900</b> revenue, wk 12</span>
          <span class="tw-kpi"><b>38 &rarr; 61</b> new customers</span>
          <span class="tw-kpi"><b>+47%</b> vs wk 1</span>
          <span class="tw-note">invented sample numbers</span>
        </div>
        <p class="tw-out"><span id="twText"></span><span class="tw-caret" id="twCaret" aria-hidden="true"></span></p>
        <p class="tw-cap"><b>The rule on display:</b> every figure above was computed by formulas before the AI saw a word of it. The model only writes the sentences &mdash; it is never trusted with the arithmetic.</p>
      </div>
      <figure class="pulse-demo" style="margin-top:26px">
        <figcaption class="pulse-demo-cap"><span aria-hidden="true">//</span> The same thing on video, 20 seconds, end to end</figcaption>
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

# ---------- scoped CSS + JS: approve demo v2, pipeline, typewriter, reveals ----------
EXTRA = r"""
<style>
/* ---- approve-gate demo v2 ---- */
.ag-legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.ag-demo{border:1px solid var(--line,#E4DFD1);border-radius:14px;padding:14px 14px 12px;background:var(--paper,#FFFFFF)}
.ag-card{display:flex;gap:14px;align-items:flex-start;justify-content:space-between;padding:14px 12px;border:1px solid var(--line,#E4DFD1);border-left:4px solid var(--line,#E4DFD1);border-radius:10px;margin-bottom:10px;background:var(--paper,#FFF);transition:border-color .25s ease,background-color .25s ease,transform .25s ease}
.ag-card[data-tier="friendly"]{border-left-color:#1E7A47}
.ag-card[data-tier="firmer"]{border-left-color:#B45309}
.ag-card[data-tier="serious"]{border-left-color:#B23B3B}
.ag-card.ag-quiet{border-left-color:#9A937F;background:#FBFAF6;opacity:.85}
.ag-card.ag-on{background:#F2F8F4;border-color:#BBDCC9;transform:translateX(2px)}
.ag-info{flex:1 1 auto;min-width:0}
.ag-inv{font-weight:700;display:inline-block;margin-right:10px}
.ag-tier{font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.06em;padding:2px 8px;border-radius:20px;white-space:nowrap}
.ag-green{background:#E6F2EC;color:#1E7A47}.ag-amber{background:#FBEFE0;color:#B45309}.ag-red{background:#F6E7E7;color:#B23B3B}.ag-grey{background:#EFEDE6;color:#6B6552}
.ag-draft{margin:.45em 0 0;font-size:.92rem;color:var(--ink-soft,#5C5645);font-style:italic}
.ag-btn{flex:0 0 auto;min-width:106px;border:1.5px solid var(--ink,#211D14);background:transparent;border-radius:24px;padding:7px 16px;font-weight:700;cursor:pointer;transition:background-color .2s ease,color .2s ease}
.ag-btn[aria-pressed="true"]{background:#1E7A47;border-color:#1E7A47;color:#fff}
.ag-held{flex:0 0 auto;font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.08em;color:#6B6552;border:1.5px dashed #C9C3B2;border-radius:24px;padding:7px 14px}
.ag-foot{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;padding-top:8px;gap:12px}
.ag-send[disabled]{opacity:.45;cursor:not-allowed}
.ag-outcome{overflow:hidden;max-height:0;opacity:0;margin-top:0;border:0 solid #BBDCC9;border-radius:10px;background:#F2F8F4;padding:0 14px;transition:max-height .3s ease,opacity .3s ease}
.ag-outcome.ag-show{max-height:260px;opacity:1;margin-top:12px;border-width:1px;padding:12px 14px}
.ag-outcome-head{margin:0;font-weight:800;color:#1E7A47}
.ag-outcome-body{margin:.45em 0 0;font-size:.92rem;color:var(--ink-soft,#5C5645)}
@media (max-width:560px){.ag-card{flex-direction:column}.ag-btn,.ag-held{align-self:flex-start}}

/* ---- pipeline figure ---- */
.pl-wrap{border:1px solid var(--line,#E4DFD1);border-radius:14px;background:var(--paper,#FFF);padding:20px 18px 16px}
.pl-track{display:flex;align-items:stretch;gap:0}
.pl-node{flex:0 0 auto;display:flex;flex-direction:column;justify-content:center;gap:2px;border:1.5px solid var(--ink,#211D14);border-radius:10px;padding:10px 12px;min-width:92px;text-align:center;position:relative}
.pl-node::before{content:attr(data-n);position:absolute;top:-9px;left:8px;font-family:ui-monospace,monospace;font-size:10px;background:var(--paper,#FFF);padding:0 4px;color:#6B6552}
.pl-t{font-family:ui-monospace,monospace;font-weight:800;font-size:12px;letter-spacing:.08em}
.pl-d{font-size:11px;color:var(--ink-soft,#5C5645)}
.pl-gate{border-width:2.5px;border-color:#B45309;box-shadow:0 0 0 0 rgba(180,83,9,.35);animation:plGlow 1.6s ease-in-out infinite}
.pl-wrap.pl-open .pl-gate{border-color:#1E7A47;animation:none;box-shadow:0 0 0 3px rgba(30,122,71,.18)}
@keyframes plGlow{0%,100%{box-shadow:0 0 0 0 rgba(180,83,9,.30)}50%{box-shadow:0 0 0 6px rgba(180,83,9,.10)}}
.pl-seg{flex:1 1 34px;min-width:26px;position:relative;align-self:center;height:2px;background:var(--line,#E4DFD1)}
.pl-dot{position:absolute;top:-4px;left:0;width:10px;height:10px;border-radius:50%;background:#1E7A47;opacity:0}
.pl-dot-a{animation:plRun 3.6s linear infinite}
.pl-dot-b{animation:plRun 3.6s linear infinite .9s}
.pl-dot-c{animation:plStall 3.6s linear infinite 1.8s}
.pl-wrap.pl-open .pl-dot-c{animation:plRun 3.6s linear infinite 1.8s}
.pl-dot-d{animation:none}
.pl-wrap.pl-open .pl-dot-d{animation:plRun 3.6s linear infinite 2.7s}
@keyframes plRun{0%{left:0;opacity:0}10%{opacity:1}90%{opacity:1}100%{left:calc(100% - 10px);opacity:0}}
@keyframes plStall{0%{left:0;opacity:0}10%{opacity:1}55%{left:calc(100% - 10px);opacity:1}70%{left:calc(100% - 10px);opacity:1}85%{left:calc(100% - 10px);opacity:0}100%{left:calc(100% - 10px);opacity:0}}
.pl-controls{display:flex;align-items:center;gap:14px;margin-top:16px;flex-wrap:wrap}
.pl-toggle{display:inline-flex;align-items:center;gap:8px;cursor:pointer;font-weight:700}
.pl-toggle input{position:absolute;opacity:0;width:0;height:0}
.pl-slider{width:44px;height:24px;border-radius:24px;background:#C9C3B2;position:relative;transition:background .2s ease;flex:0 0 auto}
.pl-slider::after{content:"";position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:#fff;transition:left .2s ease}
.pl-toggle input:checked + .pl-slider{background:#1E7A47}
.pl-toggle input:checked + .pl-slider::after{left:23px}
.pl-toggle input:focus-visible + .pl-slider{outline:2px solid #1E7A47;outline-offset:2px}
.pl-status{font-size:.92rem;color:var(--ink-soft,#5C5645);font-style:italic}
@media (max-width:700px){.pl-track{flex-direction:column;gap:10px}.pl-seg{width:2px;height:26px;min-width:0;align-self:center;flex:0 0 26px}.pl-dot{left:-4px;top:0}
@keyframes plRun{0%{top:0;left:-4px;opacity:0}10%{opacity:1}90%{opacity:1}100%{top:calc(100% - 10px);left:-4px;opacity:0}}
@keyframes plStall{0%{top:0;left:-4px;opacity:0}10%{opacity:1}55%{top:calc(100% - 10px);left:-4px;opacity:1}70%{top:calc(100% - 10px);opacity:1}85%{opacity:0}100%{top:calc(100% - 10px);opacity:0}}}
@media (prefers-reduced-motion: reduce){.pl-dot{animation:none !important;opacity:0 !important}.pl-gate{animation:none}.tw-caret{animation:none;opacity:0}.ag-outcome{transition:none}}

/* ---- typewriter panel ---- */
.tw-panel{border:1px solid var(--line,#E4DFD1);border-radius:14px;background:var(--paper,#FFF);padding:18px}
.tw-kpis{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:12px}
.tw-kpi{font-family:ui-monospace,monospace;font-size:12px;border:1px solid var(--line,#E4DFD1);border-radius:8px;padding:6px 10px;background:#FBFAF6}
.tw-note{font-size:11px;color:#6B6552;font-style:italic}
.tw-out{min-height:5.2em;margin:0;font-size:1rem;line-height:1.55}
.tw-caret{display:inline-block;width:9px;height:1.05em;background:var(--ink,#211D14);vertical-align:text-bottom;margin-left:2px;animation:twBlink 1s steps(1) infinite}
.tw-caret.tw-done{animation:none;opacity:0}
@keyframes twBlink{0%,49%{opacity:1}50%,100%{opacity:0}}
.tw-cap{margin:.9em 0 0;font-size:.9rem;color:var(--ink-soft,#5C5645);border-top:1px dashed var(--line,#E4DFD1);padding-top:.8em}

/* ---- scroll reveals ---- */
@media (prefers-reduced-motion: no-preference){
  .block.rv{opacity:0;transform:translateY(14px);transition:opacity .5s ease,transform .5s ease}
  .block.rv.rv-in{opacity:1;transform:none}
}
</style>
<script>
(function(){
  /* approve-gate demo v2 */
  var btns=document.querySelectorAll('#agDemo .ag-btn'),send=document.getElementById('agSend'),
      count=document.getElementById('agCount'),outcome=document.getElementById('agOutcome'),
      ohead=document.getElementById('agOutcomeHead'),n=0;
  btns.forEach(function(b){b.addEventListener('click',function(){
    var on=b.getAttribute('aria-pressed')==='true',card=b.closest('.ag-card');
    b.setAttribute('aria-pressed',on?'false':'true');b.textContent=on?'Approve':'Queued ✓';
    if(card){card.classList.toggle('ag-on',!on);}
    n+= on?-1:1;count.textContent=n+' of 3 approved · 1 held in silence';
    send.disabled=(n===0);outcome.classList.remove('ag-show');ohead.textContent='';});});
  send.addEventListener('click',function(){
    ohead.textContent=n+(n===1?' email released':' emails released')+' — this click is the send · '+(3-n)+(3-n===1?' draft waits':' drafts wait')+' for the next queue · 1 invoice stays silent on purpose';
    outcome.classList.add('ag-show');});

  /* pipeline gate */
  var ok=document.getElementById('plOk'),wrap=document.getElementById('plWrap'),
      st=document.getElementById('plStatus'),gd=document.getElementById('plGateD');
  if(ok){ok.addEventListener('change',function(){
    wrap.classList.toggle('pl-open',ok.checked);
    st.textContent=ok.checked?'Approved — the queue flows through. Flip it back and everything waits again.':'Drafts are piling up at the gate — nothing leaves.';
    gd.textContent=ok.checked?'open — you said go':'waiting on you';});}

  /* typewriter */
  var TW='Revenue grew 47% from week 1 to week 12, and new customers rose from 38 to 61 over the same stretch. The growth is broad rather than lumpy: no single week carried it. Worth watching: acquisition is outpacing revenue per customer, so the next lever is ticket size, not traffic.';
  var twText=document.getElementById('twText'),twCaret=document.getElementById('twCaret'),twDone=false;
  function typeIt(){if(twDone)return;twDone=true;
    if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches){twText.textContent=TW;twCaret.classList.add('tw-done');return;}
    var i=0;(function step(){if(i<=TW.length){twText.textContent=TW.slice(0,i);i++;setTimeout(step,18);}else{twCaret.classList.add('tw-done');}})();}
  /* reveals + typewriter trigger */
  var blocks=document.querySelectorAll('main .block');
  if('IntersectionObserver' in window){
    blocks.forEach(function(b){b.classList.add('rv');});
    var io=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting){e.target.classList.add('rv-in');
        if(e.target.querySelector('#twPanel'))typeIt();
        io.unobserve(e.target);}});},{threshold:.18});
    blocks.forEach(function(b){io.observe(b);});
  }else{typeIt();}
})();
</script>
"""
s = s.replace("</body>", EXTRA + "\n</body>")

# ---------- strip JSON-LD inherited from the Pulse page (FAQ/Breadcrumb/Service belong to
# /ai-business-pulse/; carrying them here duplicates schema, and the FAQ text contains
# invented figures whose on-page labels don't travel into crawlable JSON-LD) ----------
before = s.count('application/ld+json')
s = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', '', s, flags=re.S)
print("json-ld blocks stripped:", before)
s = re.sub(r'<meta property="og:description" content="[^"]*"',
           '<meta property="og:description" content="I build the automated version of the boring parts of a business — intake, invoicing, follow-ups, weekly reports. The AI drafts; you approve."',
           s, count=1)

# ---------- GATES FIRST, WRITE SECOND (a failing assert must block the artifact) ----------
# clone audit: no inherited client claims
bad = re.findall(r"[^.]*(?:Plenty of clients|clients do one|trusted by|hundreds of customers|working with local businesses and clients|working with small businesses everywhere)[^.]*\.", s)
print("clone-audit hits:", len(bad))
for b in bad: print("  !!", b.strip()[:120])
assert not bad, "inherited social-proof claims found"
# noindex present?
assert "noindex" in s, "missing noindex"
# v2 self-checks: every interactive id present exactly once in the HTML
for _id in ["agDemo","agSend","agCount","agOutcome","agOutcomeHead","plWrap","plOk","plStatus","plGateD","twPanel","twText","twCaret"]:
    assert s.count('id="%s"' % _id) == 1, "missing or duplicated id: " + _id
# invented-data labels survived
assert "every number and business name invented" in s and "invented sample numbers" in s, "invented-data labels missing"
# no residual JSON-LD
assert 'application/ld+json' not in s, "inherited JSON-LD survived the strip"

os.makedirs(OUT_DIR, exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="\n").write(s)
print("written", OUT, len(s), "bytes")
print("staged (noindex) OK — v2.1 (post-review)")
