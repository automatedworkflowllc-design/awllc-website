#!/usr/bin/env python3
"""Build /builds/ -- everything Automated Workflow has actually shipped.

A portfolio page for a services business has one job: replace "I could build
that" with "here is the thing, running, go press it." So every entry links to
something a visitor can USE or READ right now -- a live tool, a live demo, a
public repo. Nothing aspirational, nothing screenshotted.

Rule for editing: every number on this page must be one that was measured, and
the card says where it came from. If a figure cannot be checked in under a
minute by a stranger, it does not belong here.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'builds'

TITLE = 'Builds — The Free Tools and Systems Actually Running'
DESC = ('Every tool Automated Workflow has shipped: five free in-browser analyzers, live '
        'dashboard demos, an open-source reliability tool, and a crisis directory.')
CANON = 'https://automatedworkflowllc.com/builds/'

PAGE_CSS = """
/* ---- builds index ---- */
.bd-lede{max-width:42rem;color:var(--ink-soft)}
.bd-sec{margin:2.4rem 0 .9rem;font-size:.8rem;text-transform:uppercase;letter-spacing:.09em;
color:var(--ink-soft);border-bottom:1px solid var(--line);padding-bottom:.4rem}
.bd-grid{display:grid;grid-template-columns:1fr 1fr;gap:.9rem}
@media(max-width:720px){.bd-grid{grid-template-columns:1fr}}
.bd-card{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:1.1rem 1.2rem;
display:flex;flex-direction:column}
.bd-card h3{margin:0 0 .2rem;font-size:1.02rem}
.bd-card h3 a{text-decoration:none}
.bd-card h3 a:hover{text-decoration:underline}
.bd-what{margin:0 0 .6rem;font-size:.9rem;color:var(--ink-soft);flex:1}
.bd-proof{margin:0 0 .7rem;font-size:.82rem;color:var(--ink-soft);border-left:2px solid var(--line-strong);
padding-left:.6rem}
/* purpose & use: a 3-row grid so the labels align and a reader can scan
   "what do I need" without reading prose. Inline spans ran together once the
   text wrapped, which defeated the point. */
.bd-use{display:grid;grid-template-columns:auto 1fr;gap:.12rem .7rem;margin:0 0 .7rem;
padding:.55rem .7rem;background:var(--bg-soft);border-radius:.45rem;
font-size:.78rem;line-height:1.45;color:var(--ink-soft)}
.bd-use dt{font-family:var(--mono,monospace);font-size:.6rem;letter-spacing:.09em;
text-transform:uppercase;color:var(--line-strong);padding-top:.18rem}
.bd-use dd{margin:0}
.bd-tags{display:flex;gap:.35rem;flex-wrap:wrap;margin-top:auto}
.bd-tag{font-size:.68rem;letter-spacing:.05em;text-transform:uppercase;border:1px solid var(--line);
border-radius:.3rem;padding:.12rem .42rem;color:var(--ink-soft)}
.bd-tag.live{border-color:var(--accent,var(--green,#1E7A47));color:var(--accent,var(--green,#1E7A47))}
.bd-note{margin:2.2rem 0 0;padding:1.1rem 1.2rem;border:1px solid var(--line);border-radius:12px;
background:var(--bg-soft);font-size:.9rem;color:var(--ink-soft)}
/* Ask box. This page is the LinkedIn landing target, and LinkedIn traffic is
   overwhelmingly mobile -- where a mailto: on a phone with no mail app
   configured does nothing at all and the visitor is simply lost. Same failure
   we fixed sitewide on 2026-08-03. A real field beats a link that may be inert. */
.bd-ask{margin:2.2rem 0 0;padding:1.3rem 1.25rem;border:1px solid var(--line);border-radius:12px;
background:var(--bg-soft)}
.bd-ask h2{margin:0 0 .3rem;font-size:1.12rem;letter-spacing:-.01em}
.bd-ask .bd-asklede{margin:0 0 1rem;font-size:.9rem;color:var(--ink-soft);max-width:34rem}
.bd-form{display:grid;gap:.75rem;max-width:30rem;margin:0}
.bd-form label{font-size:.72rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
color:var(--ink-soft);margin-bottom:-.5rem}
.bd-form input[type=email],.bd-form input[type=text]{width:100%;padding:.7rem .8rem;
border:1px solid var(--line);border-radius:9px;font:inherit;font-size:.95rem;
background:var(--bg,#fff);color:var(--ink)}
.bd-form input:focus{outline:none;border-color:var(--green,#1E7A47);
box-shadow:0 0 0 3px rgba(30,122,71,.14)}
.bd-form .btn{width:100%;justify-content:center;cursor:pointer;margin-top:.25rem}
.bd-form .bd-privacy{margin:.1rem 0 0;font-size:.82rem;color:var(--ink-soft)}
#bd-sent{margin:0;font-size:.95rem;color:var(--ink);display:none}
"""

TOOLS = [
    ("Job &amp; Invoice Tracker  ·  no file needed", "/starter/",
     "Every other tool here asks you to upload something first. This one asks for nothing &mdash; "
     "press a button and it builds you a working Excel tracker where unbilled jobs and invoices "
     "past 60 days flag themselves.",
     "A real .xlsx assembled in your browser with no library and no upload &mdash; verified to open "
     "with formulas intact and amounts stored as numbers, not text.",
     ["Live", "Nothing uploads", "Free"]),
    ("Business File Check  ·  start here", "/check/",
     "One drop zone for any business export &mdash; <strong>Excel (.xlsx) works directly</strong>, "
     "no save-as-CSV step. It works out what the file is from its columns, runs every check that "
     "applies, and reconciles two files against each other if you drop a pair. The Excel file is "
     "parsed in your browser with no library and no upload &mdash; nobody else does that.",
     "On its sample pair it returns 8 findings with zero configuration and puts a number on the "
     "damage: <strong>$1,240 of finished work that was never invoiced</strong>. "
     "<a href=\"/check/example/\">See a real report</a> before uploading anything.",
     ["Live", "Nothing uploads", "Free"]),
    ("Spreadsheet Health Check", "/spreadsheet-health-check/",
     "Drop any CSV and get an honest report: columns that carry no information, status fields that "
     "never vary, mixed date formats, duplicate rows. Then download the file with the "
     "judgment-free problems already fixed.",
     "On its sample: 6 findings down to 2 after the automatic fix &mdash; and the two that remain "
     "are exactly the ones a script must not touch.",
     ["Live", "Nothing uploads", "Free"]),
    ("Money Leak Finder", "/money-leak-finder/",
     "Two exports every business already has &mdash; the work log and the invoices &mdash; lined up "
     "so only the mismatches show: finished jobs nobody billed, invoices sitting unpaid past 60 days.",
     "Matches on exact ID only, and says so on the report. Nothing fuzzy, nothing guessed.",
     ["Live", "Nothing uploads", "Free"]),
    ("Duplicate Customer Finder", "/duplicate-customer-finder/",
     "Acme Roofing. Acme Roofing LLC. acme roofing inc. Three rows, one customer &mdash; inflating "
     "your count, splitting revenue history, and sending the mail merge three times.",
     "Every group states why it grouped: identical after ignoring case, punctuation and legal "
     "suffixes, or a near-miss typo worth a human glance.",
     ["Live", "Nothing uploads", "Free"]),
    ("Shift Coverage Check", "/shift-coverage-check/",
     "For anyone who runs on a roster &mdash; senior living, clinics, restaurants, facilities. Finds "
     "days a role is uncovered, staff crossing 40 hours, roles only one person can fill, and "
     "turnarounds too short to be safe.",
     "Reads the columns itself and shows which ones it used. Deliberately never proposes who should "
     "work when &mdash; that is the manager's call, not a CSV's.",
     ["Live", "Nothing uploads", "Free"]),
]

DEMOS = [
    ("How the automation actually works", "/workflow-automation/",
     "The whole method in one page: what gets automated, what deliberately does not, and what each "
     "rung costs. Sensor &rarr; formulas &rarr; AI narrative &rarr; <strong>human approval</strong> "
     "&rarr; audit trail &mdash; with a live console showing how a chase email's tone is "
     "<em>derived</em> from invoice age rather than chosen.",
     "Carries an honesty ledger that opens by stating there are zero paying clients, and status "
     "chips that say RUNNING (on my own business) rather than LIVE, because no customer is on it yet.",
     ["Read first", "The method"]),
    ("Live KPI Dashboard  &middot;  or drop your own file", "/demo/",
     "A real dashboard on sample data &mdash; revenue, receivables, weekly reports. Hover the chart, "
     "open any week's report, or press <strong>Draft chase</strong> on an overdue invoice and watch it "
     "write the email and then stop. <strong>Or drop your own Excel file or CSV on it</strong> and it "
     "rebuilds on your numbers.",
     "Your file is read <strong>in your browser</strong> &mdash; .xlsx works as-is, nothing uploads, and "
     "the page makes zero network requests while it parses. On real data it drops every illustrative "
     "figure rather than inventing a finding about your business.",
     ["Live demo", "Interactive", "Nothing uploads"]),
    ("AI Business Pulse", "/ai-business-pulse/",
     "The flagship retainer: every Monday an AI reads your live numbers, writes a plain-English "
     "summary, and drafts chase emails for money you're owed.",
     "Every draft waits for a human approval before anything sends. That gate is the product.",
     ["Retainer", "Human-gated"]),
    ("Staffing Commission Dashboard", "/staffing-commission-dashboard/",
     "A live commission dashboard for a staffing desk that settles splits, draws and fall-off "
     "clawbacks by rule instead of by argument.",
     "Built for a vertical where the math is the whole disagreement.",
     ["Live demo", "Vertical"]),
]


# The staffing commission tracker was excluded on 8/5 because its page promised
# a sheet that did not exist. The workbook was built the same evening and the
# page rewritten to hand it over unconditionally, so the condition set here is
# met and it is listed. It is a download rather than a Drive copy on purpose:
# a file needs nobody's Google account, which is what keeps the page's
# "not a signup wall" line true.
TEMPLATES = [
    ("Staffing Commission Tracker", "/free-staffing-commission-tracker/",
     "For recruiters and staffing agencies: log placements and it works out perm fees, contract "
     "margins, owner/sourcer splits, each recruiter's draw balance, and which deals are still "
     "inside their guarantee window and could be clawed back.",
     "Five tabs with the formulas already in them and a Read Me explaining each one. Every formula "
     "was evaluated before shipping &mdash; a contract deal at $78/$52 across 36h &times; 26 weeks "
     "returns <strong>$24,336</strong> gross and <strong>$17,035</strong> to the owner at a 70% "
     "split, and all three sample deals correctly flag AT RISK inside their guarantee.",
     ["Free", "No signup", "Download"]),
    ("Executive KPI Dashboard", "/free/executive-kpi-dashboard.html",
     "A one-board view of the numbers an owner actually checks &mdash; revenue, jobs, what is "
     "outstanding &mdash; already wired with the formulas, so you fill in the rows and it keeps "
     "itself current.",
     "Copy it straight from the page. No email, no signup, no follow-up sequence &mdash; the copy "
     "link is right there, and you can take it and never speak to me.",
     ["Free", "No signup", "Google Sheets"]),
    ("Business Expense Tracker", "/free-expense-tracker-template/",
     "Categories already matching a normal small-business chart of accounts, currency formatting "
     "done, header row frozen. Open it and start typing rather than building it first.",
     "Same deal: a copy link on the page, nothing to submit. If you would rather I set it up on "
     "your real numbers, that offer exists separately and is also free.",
     ["Free", "No signup", "Google Sheets"]),
    ("Sales Data Cleanup Template", "/free-sales-cleanup-template/",
     "For an export that arrived messy &mdash; inconsistent names, mixed date formats, duplicate "
     "rows. The template gives it a structure that stays clean as you add to it.",
     "Copy link on the page, no email required.",
     ["Free", "No signup", "Google Sheets"]),
]

# Published 2026-08-08. These three workbooks were built in July and sat in a
# local folder; a LinkedIn post said they were "all on my site" while three of
# the four 404'd. They are worked examples of the paid $650 build, not tools --
# every card here says the numbers are invented, because they are.
WORKED = [
    ("Job Costing  &middot;  which jobs lost money", "/job-costing/",
     "A contractor logs quoted price against real labour and materials, and every job shows its "
     "margin with the losers flagged. Read the finding, then take the workbook.",
     "On invented sample data: <strong>$44,600 booked, $5,550 kept &mdash; and two jobs "
     "underwater by $1,100</strong>. Every figure on the page is stated as invented, and the "
     "workbook recomputes them by formula.",
     ["Worked example", "Sample data", "Download"]),
    ("Owner Statements  &middot;  before the owner calls", "/owner-statements/",
     "Rent in, expenses out, management fee, net payout per owner &mdash; with a flag and a "
     "unit-level reason on any owner whose cheque dropped.",
     "On invented sample data: four of five owners down, and one <strong>negative because a "
     "$3,200 roof repair landed on a $1,750 unit</strong>. The page states plainly that the "
     "reason field assumes a single culprit, which is its real limit.",
     ["Worked example", "Sample data", "Download"]),
    ("The Reconciler  &middot;  delivered vs billed", "/reconciler/",
     "Two systems that should agree &mdash; the schedule and the invoices &mdash; matched row by "
     "row so only the disagreements show. Silence means everything matched.",
     "On invented sample data: <strong>$165 in one week</strong> delivered and never invoiced, "
     "plus one invoice charged against a booking that does not exist. Matches on exact ID only "
     "and says so.",
     ["Worked example", "Sample data", "Download"]),
]

ENGINEERING = [
    ("Automation Monitoring", "/automation-monitoring/",
     "The recurring service: we watch your automations weekly and send an evidence report. "
     "Checks the two things nobody else does &mdash; whether the data <em>inside</em> a fresh file "
     "is actually current, and whether a report has quietly stopped changing.",
     "Sold on a true story: our own trading digest served Friday's data under Monday's timestamp "
     "the day the service page was built. The embedded report is that catch, verbatim.",
     ["Service", "$99/mo"]),
    ("flatline", "/flatline/",
     "An open-source reliability tool that finds signals carrying no information and jobs producing "
     "nothing: a check that fires on 100% of rows, a scheduled task that reports success while "
     "writing nothing, a branch that can never run.",
     "Built after a real scheduled job discarded four days of data while reporting success every "
     "run. 108 tests, MIT, public &mdash; the page shows five ways to use it on your own stack.",
     ["Open source", "MIT"]),
    ("canary", "/canary/",
     "The always-on half of flatline. Point it at the folder where your exports already get saved "
     "and it checks each file the moment it changes &mdash; a column that is one value all the way "
     "down, a field empty on every row, a report that stopped moving weeks ago.",
     "Every tool of this kind waits to be asked, which means the people who most need the check "
     "never run it. This one inverts the trigger. Wheels for both tools download straight from the "
     "page; it reads only, and nothing leaves the machine.",
     ["Open source", "MIT", "Download"]),
    ("Notarize a file", "/proof/notarize/",
     "Drop in any file and your browser hashes it and signs a receipt with an Ed25519 key it "
     "generates on your device. Later, drop the file back in &mdash; it tells you whether a single "
     "byte has changed, and hands you a public key so anyone else can check the signature too.",
     "Hand-built on the Web Crypto API: no library, no account, no upload, and no shared secret. "
     "Verified by notarizing a report, changing one digit of the revenue figure, and watching it "
     "come back ALTERED with both hashes shown.",
     ["Live", "Free", "Ed25519"]),
    ("Build log — including the misses", "/log/",
     "A running record of what actually gets built here, newest first. Every entry states how its "
     "claim was checked, because &ldquo;we tested it&rdquo; is not a test. It regenerates itself "
     "nightly, so it cannot quietly fall behind the work it describes.",
     "The defects stay in &mdash; the dead CSS token that removed the keyboard focus ring, the "
     "check that could never fire, the gate that blocked a page for being right. A log with only "
     "wins is a brochure, and it would undercut the whole argument.",
     ["Live", "Updated nightly"]),
    ("Proof — our own ledger", "/proof/",
     "Every night our scheduled jobs write a signed receipt recording what each run <em>claimed</em> "
     "against what it actually <em>produced</em>. The receipts are hash-chained, and the chain head "
     "is published publicly so the record binds us too.",
     "It includes the receipts where our own nightly audit produced nothing &mdash; kept "
     "deliberately, because a ledger holding only clean runs is one nobody should believe.",
     ["Live", "Evidence"]),
    ("Hearth", "https://automatedworkflowllc-design.github.io/hearth/",
     "A national crisis-resource directory &mdash; food, shelter, health, legal, support &mdash; "
     "built on federal data (HRSA, SAMHSA, USDA, EPA/Hunger Free America) and refreshed "
     "automatically.",
     "60,000+ live records. Its public health endpoint reports freshness per source, so a stale "
     "feed cannot hide behind a fresh one.",
     ["Live", "Public good", "Open data"]),
    ("Build log", "/build-log/",
     "How the multi-tenant reporting pipeline behind Automated Workflow is actually assembled "
     "&mdash; n8n, Google Sheets, an AI narrative step, and a human approval gate.",
     "Written for someone deciding whether this is real engineering or a wrapper.",
     ["Write-up"]),
]



# --- purpose & use -------------------------------------------------------
# Colin, 2026-08-05: the page must be "well descriptive of its purpose and
# use". A description says what a thing is; this says who it is for, what you
# must have in hand, and how long it takes -- which is what actually decides
# whether a stranger presses it. Keyed by href so the existing card tuples
# stay untouched. Every "needs" here was checked against the live page.
USE = {
    "/starter/":                     ("anyone starting without a system", "nothing at all", "one click"),
    "/check/":                       ("any export you are unsure about", "one file &mdash; or two to reconcile", "about a minute"),
    "/spreadsheet-health-check/":    ("a messy sheet you inherited", "one CSV or Excel file", "about a minute"),
    "/money-leak-finder/":           ("service businesses that invoice per job", "a work log + an invoice export", "about two minutes"),
    "/duplicate-customer-finder/":   ("a customer list that grew by hand", "your customer list", "under a minute"),
    "/shift-coverage-check/":        ("anyone who runs on a roster", "a schedule export", "about a minute"),
    "/free/executive-kpi-dashboard.html": ("owners who want one number board", "a Google account to copy it", "no email, no signup"),
    "/free-expense-tracker-template/":    ("sole traders and small teams", "a Google account to copy it", "no email, no signup"),
    "/free-sales-cleanup-template/":      ("anyone with a messy sales export", "a Google account to copy it", "no email, no signup"),
    "/free-staffing-commission-tracker/": ("recruiters and staffing agencies", "nothing &mdash; it downloads", "no email, no signup"),
    "/job-costing/":                 ("trades that quote per job", "nothing to read it; a job list to use it", "a read, plus a free .xlsx"),
    "/owner-statements/":            ("property managers issuing monthly statements", "nothing to read it; a rent roll to use it", "a read, plus a free .xlsx"),
    "/reconciler/":                  ("anyone whose schedule and invoices live in two systems", "one week of each, to use it", "a read, plus a free .xlsx"),
    "/workflow-automation/":         ("owners weighing whether to automate at all", "nothing &mdash; it is a read", "about five minutes"),
    "/demo/":                        ("seeing the $650 build before buying, on your own numbers if you like",
                                      "nothing &mdash; or one export, read in your browser", "seconds"),
    "/automation-monitoring/":       ("anyone already running automations", "the reports you already receive", "$99/mo, weekly evidence"),
    "/proof/notarize/":              ("proving a file has not changed", "the file itself", "seconds, on your device"),
    "/flatline/":                    ("engineers with silent scheduled jobs", "your own stack", "MIT, read the repo"),
    "/canary/":                      ("anyone who sends exports they never check", "a folder where files land", "MIT, download and run"),
}


def use_line(href: str) -> str:
    u = USE.get(href)
    if not u:
        return ""
    who, needs, takes = u
    return ('<dl class="bd-use">'
            f'<dt>For</dt><dd>{who}</dd>'
            f'<dt>Needs</dt><dd>{needs}</dd>'
            f'<dt>Takes</dt><dd>{takes}</dd>'
            '</dl>')


def card(name: str, href: str, what: str, proof: str, tags: list[str]) -> str:
    attrs = ' target="_blank" rel="noopener"' if href.startswith('http') else ''
    tag_html = ''.join(
        f'<span class="bd-tag{" live" if t in ("Live", "Live demo", "Open source") else ""}">{t}</span>'
        for t in tags)
    return (f'<article class="bd-card"><h3><a href="{href}"{attrs}>{name}</a></h3>'
            f'<p class="bd-what">{what}</p>'
            f'{use_line(href)}'
            f'<p class="bd-proof">{proof}</p>'
            f'<div class="bd-tags">{tag_html}</div></article>')


def grid(items) -> str:
    return '<div class="bd-grid">' + ''.join(card(*i) for i in items) + '</div>'


def build_main() -> str:
    return f"""
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3.5rem;max-width:54rem">
  <h1 style="margin-bottom:.4rem">Builds</h1>
  <p class="bd-lede">Everything below is running right now &mdash; a tool you can press, a demo you
  can click, or a repository you can read. No mockups, no "coming soon". If a number appears on this
  page, it is one that was measured, and the card says how.</p>

  <div class="bd-sec">Free tools &mdash; press them, nothing uploads</div>
  <p class="bd-lede" style="margin-bottom:.9rem;font-size:.9rem">Each one runs entirely in your
  browser. There is no server to send your file to &mdash; open the network tab and watch: after the
  page loads, zero requests. That is architecture, not a privacy policy.</p>
  {grid(TOOLS)}

  <div class="bd-sec">Free templates &mdash; copy them, no email</div>
  <p class="bd-lede" style="margin-bottom:.9rem;font-size:.9rem">Working Google Sheets with the
  formulas already in them. The copy link is on the page &mdash; there is nothing to submit and no
  follow-up sequence.</p>
  {grid(TEMPLATES)}

  <div class="bd-sec">The paid work &mdash; see it running first</div>
  {grid(DEMOS)}

  <div class="bd-sec">Worked examples &mdash; the $650 build, on invented data</div>
  <p class="bd-lede" style="margin-bottom:.9rem;font-size:.9rem">Three finished builds you can read
  and then download as a working .xlsx. <strong>Every number in them is invented</strong> &mdash;
  they show the shape of the output, not a client and not a result. Each page says so above its
  figures rather than in a footnote.</p>
  {grid(WORKED)}

  <div class="bd-sec">Engineering</div>
  {grid(ENGINEERING)}

  <div class="bd-note"><strong>Why the tools stop where they stop.</strong> Every free tool above
  ends at the point where a script would have to guess &mdash; which duplicate is the real customer,
  what a blank cell means, who should cover Thursday. Those decisions need a person who can ask you
  a question, which is what the <a href="/spreadsheet-cleanup-service/">$300 cleanup</a> and the
  <a href="/free-demo/">free 1-day demo</a> are. A tool that guessed there would be faster and
  worse.</div>

  <div class="bd-ask">
    <h2>Want one of these pointed at your own numbers?</h2>
    <p class="bd-asklede">Tell me the chore and I&rsquo;ll rebuild a real piece of it on your own
    file, usually within a business day. Free, and yours to keep either way &mdash; there is no
    contract and no follow-up sequence.</p>
    <p id="bd-sent" role="status" tabindex="-1"></p>
    <form class="bd-form" action="https://formspree.io/f/mgojgjwv" method="POST">
      <input type="hidden" name="_subject" value="Free demo request &mdash; /builds/">
      <input type="hidden" name="lead_source" value="builds">
      <input type="hidden" name="offer" value="Free 1-day mini-demo">
      <input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">
      <label for="bd-email">Your email</label>
      <input id="bd-email" type="email" name="email" autocomplete="email" placeholder="you@company.com" required>
      <label for="bd-chore">The chore you want gone (optional)</label>
      <input id="bd-chore" type="text" name="chore" autocomplete="off" placeholder="e.g. I rebuild the same job report every Friday">
      <button class="btn btn-primary" type="submit">Ask for the free demo &rarr;</button>
      <p class="bd-privacy">I reply personally &mdash; no spam, no sequence, no list.</p>
    </form>
  </div>
</main>
"""


ASK_JS = r"""
<script>
/* aw-inpage-form -- identical behaviour to /free-demo/ and the tool pages.
   Formspree IGNORES _next (verified 2026-08-03: its JSON reply is
   {"next":"/thanks","ok":true}), so a plain POST ejects the visitor to a
   third-party page at the highest-intent moment and no conversion fires.
   fetch + Accept: application/json keeps them here. On ANY failure we fall back
   to the normal browser POST -- form.submit() does not re-fire submit, so there
   is no loop and no stranded lead. */
(function () {
  "use strict";
  if (!window.fetch || !window.FormData) { return; }
  var form = document.querySelector('form.bd-form');
  var ok = document.getElementById('bd-sent');
  if (!form || !ok) { return; }
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var btn = form.querySelector('[type="submit"]');
    if (btn) { btn.disabled = true; btn.setAttribute("aria-busy", "true"); }
    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "Accept": "application/json" }
    }).then(function (r) {
      if (!r.ok) { throw new Error("HTTP " + r.status); }
      ok.textContent = "Sent — that’s with Colin now. He replies personally, usually within a business day.";
      ok.style.display = "block";
      form.style.display = "none";
      try { ok.focus(); } catch (e) {}
      /* Once per submission, and it shares the sessionStorage guard with every
         other form on the site so one visitor is never counted twice. */
      var fired = false;
      try { fired = sessionStorage.getItem("aw_lead_fired") === "1"; } catch (e) {}
      if (!fired && typeof gtag === "function") {
        gtag("event", "generate_lead", { method: "builds_form" });
        gtag("event", "conversion", { send_to: "AW-18312491430/t9tRCKHq9M0cEKbjiZxE" });
        try { sessionStorage.setItem("aw_lead_fired", "1"); } catch (e) {}
      }
    })["catch"](function () {
      if (btn) { btn.disabled = false; btn.removeAttribute("aria-busy"); }
      form.submit();
    });
  });
})();
</script>
"""


# The JSON-LD description used to be a second, hand-typed copy of DESC. The two
# drifted: the meta said "five free in-browser analyzers" while the structured
# data search engines actually read still said "four". Derive it from DESC so a
# count can never be right in one place and stale in the other again.
LD = ("""
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "CollectionPage",
  "name": "Builds — Automated Workflow",
  "url": "https://automatedworkflowllc.com/builds/",
  "description": "%s"
}
</script>
""" % DESC.replace('"', '\\"'))


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
    head = head.replace('</head>', f'<style>{PAGE_CSS}</style>\n</head>')

    page = head + build_main() + ASK_JS + footer + LD + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
