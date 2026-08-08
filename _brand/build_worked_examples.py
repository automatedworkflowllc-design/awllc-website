#!/usr/bin/env python3
"""Build the three worked-example pages: /job-costing/, /owner-statements/, /reconciler/.

WHY THIS EXISTS. Three finished demo workbooks sat unpublished in a local folder
since mid-July. A LinkedIn post on 2026-08-06 said of four sample builds "they're
all on my site" -- three of them 404'd. The claim was traced against the STALE
Documents/ checkout, which is why the check passed and the claim was still false.
This makes the sentence true, which is the only honest way to fix it.

They are pages, not tools. Every other /builds/ entry is something a visitor
presses; these are worked examples of the paid $650 dashboard -- read the finding,
download the workbook, open it in Excel or Sheets. The page must never blur that
line, so each one says what it is in the first sentence and links the tools
elsewhere.

THE HARD RULE ON THIS PAGE. Every figure here comes from invented sample data,
and each page says so above the numbers, not in a footnote. The original
workbooks were seeded with real Gainesville businesses lifted from the outreach
tracker -- the job-costing sheet had two named real companies losing money on a
job. Those were replaced with plainly fictional names before anything shipped
(see build_job_costing_demo.py / build_owner_statement_demo.py). If a sample row
is ever re-seeded, check it for real names again first.

Numbers below were taken from the builders' own printed sanity math on
2026-08-08, not from the July spec docs.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
# GitHub Pages runs Jekyll here (there is no .nojekyll), so /_brand/ 404s on the
# live domain -- verified. Anything pointing at a builder must point at the repo.
REPO = 'https://github.com/automatedworkflowllc-design/awllc-website/blob/main'

PAGE_CSS = """
/* ---- worked example ---- */
.we-lede{max-width:40rem;color:var(--ink-soft);font-size:1.06rem}
.we-meta{display:grid;grid-template-columns:auto 1fr;gap:.15rem .8rem;margin:1.4rem 0 0;
padding:.8rem .95rem;background:var(--well);border-radius:.5rem;font-size:.86rem;
line-height:1.5;color:var(--ink-soft);max-width:40rem}
.we-meta dt{font-family:var(--mono,monospace);font-size:.62rem;letter-spacing:.09em;
text-transform:uppercase;color:var(--ink-faint);padding-top:.24rem}
.we-meta dd{margin:0}
/* The invented-data band sits ABOVE the numbers on purpose. Under them it reads
   as a disclaimer; above them it reads as a fact about what you are looking at. */
.we-fake{margin:1.8rem 0 1.2rem;padding:.85rem 1rem;border:1px solid var(--line-strong);
border-left:3px solid #F08A24;border-radius:.5rem;background:var(--card);
font-size:.9rem;color:var(--ink-soft);max-width:44rem}
.we-fake strong{color:var(--ink)}
.we-sec{margin:2.6rem 0 .9rem;font-size:.8rem;text-transform:uppercase;letter-spacing:.09em;
color:var(--ink-soft);border-bottom:1px solid var(--line);padding-bottom:.4rem}
.we-tw{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 1rem}
table.we-t{border-collapse:collapse;width:100%;font-size:.88rem;min-width:30rem}
table.we-t th,table.we-t td{text-align:left;padding:.5rem .7rem;border-bottom:1px solid var(--line)}
table.we-t th{font-family:var(--mono,monospace);font-size:.66rem;letter-spacing:.08em;
text-transform:uppercase;color:var(--ink-soft);font-weight:600}
table.we-t td.num{text-align:right;font-variant-numeric:tabular-nums}
table.we-t tr.bad td{background:rgba(225,72,62,.06)}
table.we-t tr.tot td{font-weight:600;border-top:2px solid var(--line-strong)}
.we-tabs{display:grid;gap:.7rem;margin:0 0 1rem;padding:0;list-style:none}
.we-tabs li{border:1px solid var(--line);border-radius:.5rem;padding:.7rem .9rem;
background:var(--card);font-size:.9rem;color:var(--ink-soft)}
.we-tabs b{color:var(--ink);font-weight:600}
.we-get{margin:2rem 0 0;padding:1.2rem 1.25rem;border:1px solid var(--line);border-radius:12px;
background:var(--well)}
.we-get h2{margin:0 0 .3rem;font-size:1.1rem}
.we-get p{margin:0 0 .9rem;font-size:.9rem;color:var(--ink-soft);max-width:36rem}
.we-dl{display:inline-flex;align-items:center;gap:.5rem;padding:.7rem 1.05rem;border-radius:9px;
border:1px solid var(--ink);background:var(--ink);color:#fff;text-decoration:none;
font-size:.95rem;font-weight:500}
.we-dl:hover{opacity:.88}
.we-dlnote{margin:.6rem 0 0;font-size:.8rem;color:var(--ink-soft)}
.we-limits{margin:2.4rem 0 0;padding:1.1rem 1.2rem;border:1px solid var(--line);border-radius:12px;
background:var(--card);font-size:.9rem;color:var(--ink-soft)}
.we-limits h2{margin:0 0 .5rem;font-size:1.05rem;color:var(--ink)}
.we-limits ul{margin:0;padding-left:1.1rem}
.we-limits li{margin:.35rem 0}
.we-also{margin:2rem 0 0;font-size:.9rem;color:var(--ink-soft)}
.we-ask{margin:2.2rem 0 0;padding:1.3rem 1.25rem;border:1px solid var(--line);border-radius:12px;
background:var(--well)}
.we-ask h2{margin:0 0 .3rem;font-size:1.12rem;letter-spacing:-.01em}
.we-ask .we-asklede{margin:0 0 1rem;font-size:.9rem;color:var(--ink-soft);max-width:34rem}
.we-form{display:grid;gap:.75rem;max-width:30rem;margin:0}
.we-form label{font-size:.72rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
color:var(--ink-soft);margin-bottom:-.5rem}
.we-form input[type=email],.we-form input[type=text]{width:100%;padding:.7rem .8rem;
border:1px solid var(--line);border-radius:9px;font:inherit;font-size:.95rem;
background:var(--card,#fff);color:var(--ink)}
.we-form input:focus{outline:none;border-color:var(--green,#1E7A47);
box-shadow:0 0 0 3px rgba(30,122,71,.14)}
.we-form .btn{width:100%;justify-content:center;cursor:pointer;margin-top:.25rem}
.we-form .we-privacy{margin:.1rem 0 0;font-size:.82rem;color:var(--ink-soft)}
#we-sent{margin:0;font-size:.95rem;color:var(--ink);display:none}
"""

# The form script is byte-for-byte the behaviour shipped on /builds/ and
# /free-demo/: Formspree ignores _next, so a plain POST throws the visitor to a
# third-party page at the highest-intent moment. fetch keeps them here and any
# failure falls back to the normal browser POST, which cannot loop because
# form.submit() does not re-fire submit.
ASK_JS = r"""
<script>
(function () {
  "use strict";
  if (!window.fetch || !window.FormData) { return; }
  var form = document.querySelector('form.we-form');
  var ok = document.getElementById('we-sent');
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
      var fired = false;
      try { fired = sessionStorage.getItem("aw_lead_fired") === "1"; } catch (e) {}
      if (!fired && typeof gtag === "function") {
        gtag("event", "generate_lead", { method: "worked_example_form" });
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

FAKE_BAND = (
    '<div class="we-fake"><strong>Every number below is invented.</strong> '
    'This is a sample workbook built to show the shape of the output &mdash; the '
    'businesses named in it do not exist, and neither do the amounts. Nothing here '
    'is a client, a result, or a case study. {extra}</div>'
)


def _numeric(c) -> bool:
    """True for a cell that should right-align. &minus; is how negatives are
    written here, so it has to count as a leading sign."""
    c = str(c).replace('&minus;', '-')
    return bool(re.match(r'^[-+$(\d]', c))


def table(headers, rows, total=None) -> str:
    """Rows are (cells, css_class). Cells beginning with '$' or a digit right-align."""
    th = ''.join(f'<th>{h}</th>' for h in headers)
    body = ''
    for cells, cls in rows:
        tds = ''.join(
            f'<td class="num">{c}</td>' if i and _numeric(c) else f'<td>{c}</td>'
            for i, c in enumerate(cells))
        body += f'<tr class="{cls}">{tds}</tr>' if cls else f'<tr>{tds}</tr>'
    if total:
        tds = ''.join(
            f'<td class="num">{c}</td>' if i and _numeric(c) else f'<td>{c}</td>'
            for i, c in enumerate(total))
        body += f'<tr class="tot">{tds}</tr>'
    return (f'<div class="we-tw"><table class="we-t"><thead><tr>{th}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def tabs(items) -> str:
    return '<ul class="we-tabs">' + ''.join(
        f'<li><b>{n}</b> &mdash; {d}</li>' for n, d in items) + '</ul>'


# ---------------------------------------------------------------------------
# The three pages. Figures come from each builder's printed sanity math, run
# 2026-08-08 after the fictional re-seed; the workbook recomputes them from
# formulas, so the page and the file cannot disagree unless the seed changes.
# ---------------------------------------------------------------------------
PAGES = [
    dict(
        slug='job-costing',
        xlsx='job-costing-tracker-demo.xlsx',
        source='build_job_costing_demo.py',
        title='Job Costing Tracker — Which Jobs Made Money, Which Lost It',
        desc=('A worked example for contractors: quoted price against real labour and '
              'materials, margin on every job, losers flagged. Free sample workbook, '
              'invented data.'),
        h1='Which jobs made money, and which you paid to do',
        lede=('A contractor logs what a job was quoted at and what it actually cost in labour '
              'and materials. The dashboard works out the margin on every single job and flags '
              'the ones that went underwater. This page is a worked example of that build, with '
              'the sample workbook to download.'),
        meta=[('For', 'trades that quote per job &mdash; lawn, fence, paint, cleaning, pest, hardscape'),
              ('Needs', 'a job list with quoted price, labour cost and materials cost'),
              ('This page', 'a read, plus a free .xlsx to open in Excel or Google Sheets'),
              ('The paid build', '$650 one-time, on your job types and cost categories')],
        fake_extra=('The client names were rewritten to fictional ones before this page was '
                    'published, because the original sample was seeded from a real local '
                    'contact list.'),
        finding_head='What the sample shows',
        finding=(
            '<p>Twelve jobs. Booked <strong>$44,600</strong>, spent <strong>$39,050</strong>, '
            'kept <strong>$5,550</strong> &mdash; a blended margin of <strong>12.4%</strong>. '
            'That is the number most owners can estimate.</p>'
            '<p>The number they usually cannot: <strong>two jobs lost $1,100 between them</strong>, '
            'and four of the twelve came in either over budget or under a 15% margin. On a real '
            'book that money does not appear as a line item anywhere. It is simply absent from '
            'the total, which is why nobody goes looking for it.</p>'
            + table(
                ['Job', 'Quoted', 'Actual cost', 'Margin', 'Margin %'],
                [(['J-03 Bellamy Exterior Painting &middot; exterior paint', '$4,800', '$5,300',
                   '&minus;$500', '&minus;10.4%'], 'bad'),
                 (['J-08 Ridgeway Hardscapes &middot; retaining wall', '$6,800', '$7,400',
                   '&minus;$600', '&minus;8.8%'], 'bad'),
                 (['J-06 Brightline Cleaning &middot; deep-clean contract', '$1,800', '$1,700',
                   '$100', '5.6%'], ''),
                 (['J-11 Trailhead Cycles &middot; deck build', '$3,100', '$2,800',
                   '$300', '9.7%'], '')],
                total=['All 12 jobs', '$44,600', '$39,050', '$5,550', '12.4%'])
            + '<p>Sort by margin and the losses usually cluster by <em>job type</em> rather than by '
              'client &mdash; which is the actual finding, because a job type you lose money on is '
              'one you are still quoting the same way next month.</p>'),
        tabs_head='What is in the workbook',
        tabs=[('Jobs', 'one row per job &mdash; quoted, labour, materials, status. This is the only '
                       'tab you type in.'),
              ('Job Dashboard', 'margin per job, computed by formula, with each row coloured green '
                                '(healthy), amber (thin, under 15%) or red (over budget), plus the '
                                'portfolio totals and the money lost on over-budget work.')],
        limits=[
            'It is a spreadsheet, not software. Nothing syncs; you type the jobs in or paste an '
            'export into the Jobs tab.',
            'It only knows the costs you give it. Overhead, drive time and warranty callbacks are '
            'not in the sample &mdash; on a real build those become their own columns, which is '
            'most of what the paid version is.',
            'There is no AI anywhere in it. The margin, the flags and the thresholds are '
            'arithmetic, and that is deliberate: a number that decides whether you re-quote a job '
            'type should be one you can check by hand.',
            'The 15% "thin margin" line is a default, not a fact about your trade. It is one cell.'],
        ld_name='Job Costing Tracker (worked example)',
    ),
    dict(
        slug='owner-statements',
        xlsx='owner-statement-tracker-demo.xlsx',
        source='build_owner_statement_demo.py',
        title='Owner Statements — Have the Answer Before the Owner Calls',
        desc=('A worked example for property managers: rent, expenses, fee and net payout per owner, plus a reason on any owner whose cheque dropped. Invented data.'),
        h1='&ldquo;Why is my cheque smaller this month?&rdquo;',
        lede=('Owner statements get hand-assembled off the rent roll every month, and then the '
              'call comes. This builds each owner&rsquo;s statement automatically &mdash; rent '
              'collected, expenses, your management fee, net payout &mdash; and flags the owners '
              'whose payout dropped, with the unit-level reason attached. This page is a worked '
              'example of that build, with the sample workbook to download.'),
        meta=[('For', 'property managers who issue monthly owner statements'),
              ('Needs', 'a rent roll: unit, owner, rent due, rent collected, expenses'),
              ('This page', 'a read, plus a free .xlsx to open in Excel or Google Sheets'),
              ('The paid build', '$650 one-time, on your units, owners and management-fee %')],
        fake_extra=('The owners, buildings and street addresses were rewritten to fictional ones '
                    'before this page was published, because the original sample was seeded from '
                    'a real local contact list.'),
        finding_head='What the sample shows',
        finding=(
            '<p>Twelve units across five owners. <strong>$17,300</strong> collected, '
            '<strong>$6,210</strong> in expenses, <strong>$1,384</strong> in management fees at 8%, '
            '<strong>$9,706</strong> paid out to owners.</p>'
            '<p><strong>Four of the five owners were down against last month</strong>, and one went '
            'negative: a <strong>$3,200 roof-leak repair landed on a single $1,750 unit</strong>, '
            'so that owner is invoiced rather than paid.</p>'
            + table(
                ['Owner', 'Collected', 'Expenses', 'Net payout', 'vs last month'],
                [(['Redbrick Partners', '$1,750', '$3,200', '&minus;$1,590', '&minus;$3,175'], 'bad'),
                 (['Ardsley Holdings', '$2,950', '$490', '$2,224', '&minus;$1,398'], 'bad'),
                 (['Fenmore Rentals', '$4,650', '$1,190', '$3,088', '&minus;$1,054'], 'bad'),
                 (['Kestrel Property Trust', '$3,900', '$890', '$2,698', '&minus;$784'], 'bad'),
                 (['Ironwood Commercial', '$4,050', '$440', '$3,286', '+$136'], '')],
                total=['Portfolio', '$17,300', '$6,210', '$9,706', ''])
            + '<p>The flag is the easy half. The half that ends the call is the <em>reason</em>, '
              'attached at unit level &mdash; a vacancy, an AC repair, a water heater, the roof. '
              'Obvious once the sheet says it; invisible in a stack of numbers.</p>'),
        tabs_head='What is in the workbook',
        tabs=[('Rent Roll', 'one row per unit &mdash; owner, address, rent due, rent collected, '
                            'expenses, last month&rsquo;s net, and a note. This is the tab you '
                            'maintain.'),
              ('Owner Statements', 'portfolio totals, a statement per owner (rent, expenses, '
                                   'management fee, net payout, change vs last month) and a '
                                   '&ldquo;why the drops happened&rdquo; table down at unit level.')],
        limits=[
            'It is a spreadsheet, not a portal. Owners do not log into it; you send them their '
            'statement.',
            'The reason field is one per unit. Five small expenses drifting up would still raise '
            'the flag, but the reason attached would be whichever line was typed in &mdash; the '
            'honest version of that is a ranked list, and it is not in this sample.',
            'The 8% management fee is one cell. So is the comparison month.',
            'No AI. The flag is arithmetic &mdash; this month&rsquo;s net against last '
            'month&rsquo;s &mdash; and the reason comes from the expense line you recorded, not '
            'from a model&rsquo;s guess about what happened.'],
        ld_name='Property Owner Statement Tracker (worked example)',
    ),
    dict(
        slug='reconciler',
        xlsx='reconciler-demo.xlsx',
        source='build_reconciler_demo.py',
        title='The Reconciler — What You Delivered vs What You Billed',
        desc=('A worked example: the schedule and the invoices lined up so only the rows that '
              'disagree show up. Free sample workbook, invented data, no signup.'),
        h1='What you delivered, against what you actually billed',
        lede=('Two systems that should match &mdash; what got <em>booked</em> and what got '
              '<em>billed</em> &mdash; reconciled row by row, so only the ones that disagree show '
              'up. Silence means everything matched. This page is a worked example of that build, '
              'with the sample workbook to download.'),
        meta=[('For', 'anyone whose schedule and invoices live in two different systems'),
              ('Needs', 'one week of each: what was booked, and what was invoiced'),
              ('This page', 'a read, plus a free .xlsx to open in Excel or Google Sheets'),
              ('The paid build', '$650 one-time, or from $250/mo to run it weekly and email you '
                                 'only the disagreements')],
        fake_extra='',
        finding_head='What the sample shows',
        finding=(
            '<p>One week at a fictional bay-rental shop: 14 sessions on the schedule, 13 invoices '
            'out. Ten matched to the dollar and are not worth your attention. Five did not.</p>'
            + table(
                ['Row', 'What happened', 'Flag', 'Impact'],
                [(['B-204', 'Two hours played, never invoiced', 'NOT BILLED', '&minus;$90'], 'bad'),
                 (['B-212', 'One hour played, never invoiced', 'NOT BILLED', '&minus;$45'], 'bad'),
                 (['B-203', 'Three hours booked, invoice billed two', 'HOURS MISMATCH', '&minus;$45'], 'bad'),
                 (['B-208', 'Right hours, charged $50/hr instead of $45', 'AMOUNT MISMATCH', '+$15'], ''),
                 (['INV-89', 'Invoice against a booking that is not on the schedule', 'PHANTOM', '$90 at risk'], 'bad')],
                total=['Delivered but never collected', '', '', '$165'])
            + '<p><strong>$165 in one week on fourteen sessions.</strong> At that rate it is about '
              '<strong>$8,580 a year</strong> &mdash; work that was genuinely done and simply never '
              'made it onto an invoice. The phantom row is the other direction: someone was charged '
              '$90 with no session behind it, which is a refund or a chargeback waiting to happen.</p>'
            '<p>The annualised figure is the weekly gap multiplied by 52, which assumes this week '
              'is typical. On invented data it is arithmetic, not a forecast &mdash; the point of '
              'the number is the order of magnitude, not the digits.</p>'),
        tabs_head='What is in the workbook',
        tabs=[('Bookings', 'what was scheduled &mdash; 14 sessions, with expected '
                                            'value computed as hours &times; rate.'),
              ('Invoices', 'what was billed &mdash; 13 invoices that should line '
                                             'up by booking ID.'),
              ('Reconciliation', 'the match itself: matched rows go green and stay quiet, the rest '
                                 'are flagged by type, and the net gap is headlined. Change either '
                                 'side and it recomputes.')],
        limits=[
            'It matches on an exact shared ID. If your two systems have no common key, that is a '
            'real problem and this sheet will not paper over it &mdash; it will show every row as '
            'unmatched, which is the honest answer.',
            'It surfaces disagreements; it does not decide them. Whether a missed session gets '
            're-billed or written off is a judgement about a customer relationship, and the sheet '
            'is not entitled to make it.',
            'The weekly version that emails you is the retainer, not this file. This file is the '
            'reconciliation itself, run by hand whenever you want.',
            'No AI. Every flag is a comparison you could do by hand &mdash; it is just that nobody '
            'does it 14 times a week.'],
        ld_name='The Reconciler (worked example)',
    ),
]


def build_main(p: dict) -> str:
    fake = FAKE_BAND.format(extra=p['fake_extra'])
    meta = '<dl class="we-meta">' + ''.join(
        f'<dt>{k}</dt><dd>{v}</dd>' for k, v in p['meta']) + '</dl>'
    limits = '<ul>' + ''.join(f'<li>{l}</li>' for l in p['limits']) + '</ul>'
    return f"""
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3.5rem;max-width:54rem">
  <p class="eyebrow" style="margin-bottom:.5rem"><a href="/builds/" style="text-decoration:none">&larr; Builds</a>
  &nbsp;&middot;&nbsp; Worked example</p>
  <h1 style="margin-bottom:.5rem">{p['h1']}</h1>
  <p class="we-lede">{p['lede']}</p>
  {meta}

  {fake}

  <div class="we-sec">{p['finding_head']}</div>
  {p['finding']}

  <div class="we-sec">{p['tabs_head']}</div>
  {tabs(p['tabs'])}

  <div class="we-get">
    <h2>Take the workbook</h2>
    <p>Free, no email, no signup, no follow-up sequence. It opens in Excel, Numbers or Google
    Sheets &mdash; the formulas are already in it, so you can delete the sample rows and put your
    own in.</p>
    <a class="we-dl" href="/{p['slug']}/{p['xlsx']}" download>Download the .xlsx &darr;</a>
    <p class="we-dlnote">Built by <a href="{REPO}/_brand/{p['source']}">this script</a>, which is
    public along with everything else on this site. The site does not serve <code>_brand/</code>
    itself &mdash; GitHub Pages hides underscore directories &mdash; so the link goes to the
    repository.</p>
  </div>

  <div class="we-limits">
    <h2>What it does not do</h2>
    {limits}
  </div>

  <p class="we-also">Prefer something you can press right now instead of a file to open?
  The <a href="/demo/">live dashboard demo</a> takes your own export and rebuilds itself on your
  numbers in the browser, and the <a href="/builds/">free tools</a> run without uploading anything.</p>

  <div class="we-ask">
    <h2>Want this one on your own numbers?</h2>
    <p class="we-asklede">Send the chore and I&rsquo;ll rebuild a real piece of it on your own
    file, usually within a business day. Free, and yours to keep either way &mdash; no contract
    and no follow-up sequence.</p>
    <p id="we-sent" role="status" tabindex="-1"></p>
    <form class="we-form" action="https://formspree.io/f/mgojgjwv" method="POST">
      <input type="hidden" name="_subject" value="Free demo request &mdash; /{p['slug']}/">
      <input type="hidden" name="lead_source" value="{p['slug']}">
      <input type="hidden" name="offer" value="Free 1-day mini-demo">
      <input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">
      <label for="we-email">Your email</label>
      <input id="we-email" type="email" name="email" autocomplete="email" placeholder="you@company.com" required>
      <label for="we-chore">The chore you want gone (optional)</label>
      <input id="we-chore" type="text" name="chore" autocomplete="off" placeholder="e.g. I rebuild owner statements by hand every month">
      <button class="btn btn-primary" type="submit">Ask for the free demo &rarr;</button>
      <p class="we-privacy">I reply personally &mdash; no spam, no sequence, no list.</p>
    </form>
  </div>
</main>
"""


def ld(p: dict) -> str:
    canon = f"https://automatedworkflowllc.com/{p['slug']}/"
    return ("""
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "%s",
  "url": "%s",
  "description": "%s",
  "isPartOf": {"@type": "WebSite", "url": "https://automatedworkflowllc.com/"}
}
</script>
""" % (p['ld_name'], canon, p['desc'].replace('"', '\\"')))


def main() -> None:
    s = TEMPLATE.read_text(encoding='utf-8')
    head_src = s[:s.index('</header>') + len('</header>')]
    footer = s[s.index('<footer'):s.index('</footer>') + len('</footer>')]

    for p in PAGES:
        canon = f"https://automatedworkflowllc.com/{p['slug']}/"
        head = re.sub(r'<title>.*?</title>', f"<title>{p['title']}</title>", head_src, flags=re.S)
        head = re.sub(r'(<meta name="description" content=").*?(">)', rf"\g<1>{p['desc']}\g<2>", head)
        head = re.sub(r'(<link rel="canonical" href=").*?(">)', rf'\g<1>{canon}\g<2>', head)
        head = re.sub(r'(<meta property="og:title" content=").*?(">)', rf"\g<1>{p['title']}\g<2>", head)
        head = re.sub(r'(<meta property="og:description" content=").*?(">)', rf"\g<1>{p['desc']}\g<2>", head)
        head = re.sub(r'(<meta property="og:url" content=").*?(">)', rf'\g<1>{canon}\g<2>', head)
        head = head.replace('</head>', f'<style>{PAGE_CSS}</style>\n</head>')

        page = head + build_main(p) + ASK_JS + footer + ld(p) + '\n</body>\n</html>\n'

        out_dir = ROOT / p['slug']
        out_dir.mkdir(exist_ok=True)
        # The workbook is the page's whole promise -- refuse to write a page that
        # would offer a download that is not there. This is the exact failure
        # /free-staffing-commission-tracker/ shipped with for three weeks.
        book = out_dir / p['xlsx']
        if not book.exists():
            raise SystemExit(f'{book} missing -- run _brand/{p["source"]} first')
        (out_dir / 'index.html').write_text(page, encoding='utf-8')
        print(f'wrote {out_dir / "index.html"} ({len(page)} bytes, workbook {book.stat().st_size} B)')


if __name__ == '__main__':
    main()
