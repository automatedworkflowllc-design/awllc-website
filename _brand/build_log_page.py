# -*- coding: utf-8 -*-
"""Build /log/ — the PUBLIC running build log, generated from dev/BUILD-LOG.html.

Why this exists
---------------
The internal build log is the single best trust asset this business has: it is a
running record that includes its own defects, and nobody else publishes that.
But it is written for Colin, and it mixes in two things that must never appear on
a business website:

  1. THE JOB LANE. Applications, recruiters, resumes. Publishing that on the
     company site broadcasts an active job search to prospects, and risks the day
     job. This is the single highest-consequence leak and it is 35 of ~92 entries.
  2. PERSONAL FINANCE / OTHER PROJECTS. Trading work (GEX, Option Bot, TheDesk,
     the Roth) and unrelated builds. Not AWLLC, not the public's business.

So this builder is a FILTER, not a copy. It whitelists sections, drops any entry
containing a blocked term, and then REFUSES TO WRITE THE FILE AT ALL if a blocked
term survives into the output. A leak here is irreversible once indexed, so the
gate fails closed rather than warning.

House rules honoured: generated page (edit this builder, never the output);
ships STAGED with noindex for Colin's review before publishing.
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)


def _find_source():
    """Locate dev/BUILD-LOG.html without assuming where this checkout lives.

    There are two checkouts of this site on this machine and only one is live, so
    a relative guess is exactly the kind of thing that silently reads the wrong
    file. Walk upward looking for dev/BUILD-LOG.html and take the first hit.
    """
    d = SITE
    for _ in range(6):
        cand = os.path.join(d, "dev", "BUILD-LOG.html")
        if os.path.exists(cand):
            return cand
        cand = os.path.join(d, "BUILD-LOG.html")
        if os.path.exists(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return ""


SRC = _find_source()
OUT_DIR = os.path.join(SITE, "log")
OUT = os.path.join(OUT_DIR, "index.html")

# Only these sections may appear publicly. Anything not listed is dropped whole.
ALLOWED_SECTIONS = {
    "Public tools — automatedworkflowllc.com",
    "Client workflow engine — Zapier",
    "Reliability &amp; discipline tooling",
    "Silent failures killed",
}

# Any entry containing one of these is dropped, wherever it appears — including
# the un-sectioned "latest" entries at the top of the source.
BLOCKED = [
    # the job lane
    "applicat", "recruit", "resume", "cover letter", "greenhouse", "workday",
    "gitlab", "pandadoc", "hologram", "entravision", "oasis security", "upwork",
    "job-engine", "job scout", "job lane", "hiring", "interview",
    # personal finance / other projects
    "gex", "option bot", "thedesk", "portfolio-desk", "portfolio desk", "roth",
    "trading", "robinhood", "hearth",
    # people/prospects
    "oak hammock", "colin mccarthy",
]

ROW_RE = re.compile(r'<div class="row">.*?</div>\s*</div>', re.S)


def entries_from(block):
    return ROW_RE.findall(block)


def blocked_terms_in(text):
    low = re.sub(r"<[^>]+>", " ", text).lower()
    return sorted({t for t in BLOCKED if t in low})


def build():
    if not os.path.exists(SRC):
        sys.exit("REFUSING: source build log not found at %s" % SRC)
    src = io.open(SRC, encoding="utf-8").read()

    parts = re.split(r"<h2>(.*?)</h2>", src)
    kept = []          # list of (section_title_or_None, [entry_html, ...])
    dropped = 0

    # entries above the first <h2> are the "latest" band — allowed, still filtered
    latest = [e for e in entries_from(parts[0])]
    keep_latest = []
    for e in latest:
        if blocked_terms_in(e):
            dropped += 1
        else:
            keep_latest.append(e)
    if keep_latest:
        kept.append((None, keep_latest))

    for i in range(1, len(parts), 2):
        title = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        if title not in ALLOWED_SECTIONS:
            dropped += len(entries_from(body))
            continue
        keep = []
        for e in entries_from(body):
            if blocked_terms_in(e):
                dropped += 1
            else:
                keep.append(e)
        if keep:
            kept.append((title, keep))

    total_kept = sum(len(v) for _, v in kept)
    if total_kept == 0:
        sys.exit("REFUSING: filter removed everything — check ALLOWED_SECTIONS")

    body_html = []
    for title, rows in kept:
        if title:
            body_html.append("<h2>%s</h2>" % title)
        body_html.extend(rows)
    body_html = "\n".join(body_html)

    # ---- the gate: fail closed -------------------------------------------
    leaks = blocked_terms_in(body_html)
    if leaks:
        sys.exit("REFUSING TO WRITE: blocked terms survived filtering -> %s" % leaks)

    page = PAGE.replace("{{BODY}}", body_html).replace("{{COUNT}}", str(total_kept))

    leaks = blocked_terms_in(page)
    if leaks:
        sys.exit("REFUSING TO WRITE: blocked terms in final page -> %s" % leaks)
    if "noindex" not in page:
        sys.exit("REFUSING TO WRITE: staged page lost its noindex tag")

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    io.open(OUT, "w", encoding="utf-8").write(page)
    print("wrote %s" % OUT)
    print("  kept %d entries, dropped %d (job lane, other projects, people)" % (total_kept, dropped))
    print("  STAGED: noindex is set. Remove it + add to sitemap to publish.")


PAGE = u"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<!-- STAGED, NOT PUBLISHED. noindex is ON PURPOSE: this page is generated from an internal build log and is awaiting Colin's copy review. To publish: remove this robots tag, add /log/ to sitemap.xml, and link it from /builds/. Do NOT add to sitemap while noindex is set. -->
<link rel="canonical" href="https://automatedworkflowllc.com/log/">
<title>Build log — every system shipped, and the bugs found</title>
<meta name="description" content="A running record of what actually gets built here, including the parts that broke and how every claim was checked. Automation, Gainesville FL.">
<style>
  :root{
    --paper:#FBFAF3; --well:#F4F1E8; --ink:#211D14; --ink-soft:#5C5645;
    --line:#E4DFD1; --line-strong:#D8D2C2; --green:#1E7A47; --amber:#B45309;
    --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  }
  @media (prefers-color-scheme: dark){
    :root{ --paper:#17150F; --well:#201D16; --ink:#EDE8DA; --ink-soft:#A79E8B;
           --line:#332E23; --line-strong:#4A4335; --green:#4FA69C; --amber:#D8AC55; }
  }
  :root[data-theme="dark"]{ --paper:#17150F; --well:#201D16; --ink:#EDE8DA; --ink-soft:#A79E8B;
           --line:#332E23; --line-strong:#4A4335; --green:#4FA69C; --amber:#D8AC55; }
  :root[data-theme="light"]{ --paper:#FBFAF3; --well:#F4F1E8; --ink:#211D14; --ink-soft:#5C5645;
           --line:#E4DFD1; --line-strong:#D8D2C2; --green:#1E7A47; --amber:#B45309; }
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);
       font:16px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
       -webkit-font-smoothing:antialiased}
  .wrap{max-width:58rem;margin:0 auto;padding:3rem 1.4rem 5rem}
  a{color:inherit}
  h1{font-size:1.9rem;letter-spacing:-.02em;margin:0 0 .4rem;text-wrap:balance}
  .sub{color:var(--ink-soft);margin:0;max-width:42rem;text-wrap:pretty}
  .stamp{font-family:var(--mono);font-size:.76rem;color:var(--ink-soft);margin-top:.9rem}
  h2{font-size:.76rem;text-transform:uppercase;letter-spacing:.1em;color:var(--ink-soft);
     margin:2.7rem 0 .6rem;font-weight:600;padding-bottom:.6rem;border-bottom:1px solid var(--line)}
  .row{display:grid;grid-template-columns:5.4rem 1fr;gap:0 1rem;padding:.9rem 0;
       border-bottom:1px solid var(--line)}
  .date{font-family:var(--mono);font-size:.76rem;color:var(--ink-soft);
        font-variant-numeric:tabular-nums;padding-top:.25rem}
  .name{font-weight:600;font-size:1rem;margin:0;display:flex;gap:.45rem;align-items:baseline;flex-wrap:wrap}
  .chip{font-family:var(--mono);font-size:.62rem;letter-spacing:.06em;text-transform:uppercase;
        border:1px solid var(--line-strong);border-radius:.25rem;padding:.08rem .35rem;
        color:var(--ink-soft);white-space:nowrap;font-weight:500}
  .chip.live{border-color:var(--green);color:var(--green)}
  .chip.staged{border-color:var(--amber);color:var(--amber)}
  .what{margin:.2rem 0 0;color:var(--ink-soft);font-size:.93rem;text-wrap:pretty}
  .proof{margin:.45rem 0 0;font-size:.85rem;color:var(--ink-soft);
         border-left:2px solid var(--line-strong);padding-left:.7rem;text-wrap:pretty}
  .proof b{color:var(--ink);font-weight:600}
  .where{font-family:var(--mono);font-size:.73rem;color:var(--ink-soft);margin:.35rem 0 0}
  code{font-family:var(--mono);font-size:.88em}
  .note{margin-top:2.2rem;padding:1.1rem 1.25rem;border:1px solid var(--line);
        border-radius:.7rem;background:var(--well);font-size:.92rem;color:var(--ink-soft)}
  .note strong{color:var(--ink)}
  footer{margin-top:2.6rem;padding-top:1.1rem;border-top:1px solid var(--line);
         font-size:.82rem;color:var(--ink-soft)}
  @media(max-width:640px){ .row{grid-template-columns:1fr;gap:.25rem} .date{padding-top:0} }
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Build log</h1>
  <p class="sub">A running record of what actually gets built here — including the parts that
  broke. Every entry says how its claim was checked, because "we tested it" is not a test.</p>
  <p class="stamp">{{COUNT}} entries · newest first within each group</p>
</header>

<div class="note">
  <strong>Why a log with failures in it.</strong>
  <p style="margin:.5rem 0 0">This company is pointed at one problem: <b>software that reports
  success while doing nothing.</b> A backup that has "succeeded" every night into an empty file.
  A weekly report that still arrives on time with numbers that stopped updating in March. Those
  never show up as errors, which is exactly why they run for months.</p>
  <p style="margin:.6rem 0 0">A log with only wins would be a brochure, and it would undercut the
  whole argument. So the misses stay in — including the times a check turned out to be wrong
  rather than the thing it was checking.</p>
</div>

{{BODY}}

<footer>
  <p style="margin:0 0 .5rem">Want this kind of scrutiny pointed at your own spreadsheets?
  <a href="/free-demo/">Send one over</a> — you get the fix back either way.</p>
  <p style="margin:0">Automated Workflow · Gainesville, FL ·
  <a href="mailto:colin@automatedworkflowllc.com">colin@automatedworkflowllc.com</a> ·
  <a href="tel:+17039391174">(703) 939-1174</a></p>
</footer>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    build()
