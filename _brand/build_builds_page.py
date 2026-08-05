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
.bd-tags{display:flex;gap:.35rem;flex-wrap:wrap;margin-top:auto}
.bd-tag{font-size:.68rem;letter-spacing:.05em;text-transform:uppercase;border:1px solid var(--line);
border-radius:.3rem;padding:.12rem .42rem;color:var(--ink-soft)}
.bd-tag.live{border-color:var(--accent,var(--green,#1E7A47));color:var(--accent,var(--green,#1E7A47))}
.bd-note{margin:2.2rem 0 0;padding:1.1rem 1.2rem;border:1px solid var(--line);border-radius:12px;
background:var(--bg-soft);font-size:.9rem;color:var(--ink-soft)}
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
    ("Live KPI Dashboard", "/demo/",
     "A real, self-updating Google Sheets dashboard on sample data &mdash; revenue, jobs, overdue "
     "invoices. Click the tabs, tap the chart. No login, no signup.",
     "This is the $650 Automated Dashboard, running &mdash; not a screenshot of one.",
     ["Live demo", "Interactive"]),
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
    ("Free templates", "/free/executive-kpi-dashboard.html",
     "Executive KPI dashboard, expense tracker, and a staffing commission tracker &mdash; working "
     "Google Sheets templates, no cost, no email required.",
     "Take them and never speak to us. That is the point.",
     ["Free", "No signup"]),
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
    ("Notarize a file", "/proof/notarize/",
     "Drop in any file and your browser hashes it and signs a receipt with an Ed25519 key it "
     "generates on your device. Later, drop the file back in &mdash; it tells you whether a single "
     "byte has changed, and hands you a public key so anyone else can check the signature too.",
     "Hand-built on the Web Crypto API: no library, no account, no upload, and no shared secret. "
     "Verified by notarizing a report, changing one digit of the revenue figure, and watching it "
     "come back ALTERED with both hashes shown.",
     ["Live", "Free", "Ed25519"]),
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


def card(name: str, href: str, what: str, proof: str, tags: list[str]) -> str:
    attrs = ' target="_blank" rel="noopener"' if href.startswith('http') else ''
    tag_html = ''.join(
        f'<span class="bd-tag{" live" if t in ("Live", "Live demo", "Open source") else ""}">{t}</span>'
        for t in tags)
    return (f'<article class="bd-card"><h3><a href="{href}"{attrs}>{name}</a></h3>'
            f'<p class="bd-what">{what}</p>'
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

  <div class="bd-sec">Client work &mdash; live demos</div>
  {grid(DEMOS)}

  <div class="bd-sec">Engineering</div>
  {grid(ENGINEERING)}

  <div class="bd-note"><strong>Why the tools stop where they stop.</strong> Every free tool above
  ends at the point where a script would have to guess &mdash; which duplicate is the real customer,
  what a blank cell means, who should cover Thursday. Those decisions need a person who can ask you
  a question, which is what the <a href="/spreadsheet-cleanup-service/">$300 cleanup</a> and the
  <a href="/free-demo/">free 1-day demo</a> are. A tool that guessed there would be faster and
  worse.</div>
</main>
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

    page = head + build_main() + footer + LD + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
