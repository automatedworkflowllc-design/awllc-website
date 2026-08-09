#!/usr/bin/env python3
"""Promise audit -- does every page that offers an artifact actually have one?

WHY THIS EXISTS. /free-staffing-commission-tracker/ went live on 2026-07-11
saying "a Google Sheet you can start using today... Free template, yours to
copy" and "not a signup wall". It contained zero copy links, every CTA pointed
at an email form, and the sheet had been specced but never built -- so even the
email path had nothing to send. It stayed that way for three and a half weeks
because nothing looked. Every other gate passed the whole time: the HTML was
valid, the links resolved, the SEO was clean, no secrets leaked. None of them
ask the one question a visitor cares about -- "when I do the thing this page
tells me to do, do I get the thing?"

WHAT IT CHECKS. A page that uses giveaway language ("yours to copy",
"download the template", "free template") must carry at least one artifact
link: a local downloadable file that exists on disk, or a Google Sheets link.
A page that promises and offers nothing is a defect, loudly.

WHAT IT DELIBERATELY DOES NOT DO. It does not call the network. Reachability of
a Google Sheet depends on share settings and an unauthenticated fetch cannot
tell "private" from "fine" reliably -- a gate that is wrong sometimes teaches
people to ignore gates. The structural check is what would have caught the real
defect, and it is deterministic and instant. Sheet reachability is a manual
periodic check; last done 2026-08-05, all three template sheets public and
correctly titled.

Exit code 1 if any page promises something it cannot hand over.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = 'https://automatedworkflowllc.com'     # generated pages use absolute self-links

# Language that tells a visitor they are about to receive an artifact.
PROMISE = re.compile(
    r"yours to copy|yours to download|make your own copy|grab your copy|"
    r"download the (?:template|tracker|workbook|sheet)|free template|"
    r"copy (?:it|the sheet|this sheet)|start using (?:it )?today",
    re.I)

# Things that count as actually handing something over.
LOCAL_FILE = re.compile(r'href="([^"]+\.(?:xlsx|xls|csv|pdf|zip))"', re.I)
SHEET_LINK = re.compile(r'https://docs\.google\.com/spreadsheets/d/[A-Za-z0-9_-]+')
# A page can also hand over a file it generates in the browser (e.g. /starter/).
GENERATES = re.compile(r"\.xlsx['\"]|download\(bytes|createObjectURL", re.I)


def tracked_html() -> list[pathlib.Path]:
    out = subprocess.run(['git', 'ls-files', '*.html'], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return [ROOT / p for p in out.stdout.split() if p]


def _has_artifact(html: str, path: pathlib.Path) -> bool:
    if SHEET_LINK.search(html) or GENERATES.search(html):
        return True
    for href in LOCAL_FILE.findall(html):
        target = (ROOT / href.lstrip('/')) if href.startswith('/') else (path.parent / href)
        if target.exists():
            return True
    return False


def audit() -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []

    # An index page may use giveaway language about pages it links to -- /builds/
    # says "free template" about the template pages. That is describing, not
    # promising, so a page also passes if it links to one that carries the goods.
    pages = {}
    for path in tracked_html():
        try:
            pages[path] = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            pass
    delivering = set()
    for path, html in pages.items():
        if _has_artifact(html, path):
            rel = '/' + path.relative_to(ROOT).as_posix()
            delivering.add(rel)
            if rel.endswith('/index.html'):
                delivering.add(rel[:-len('index.html')])

    for path in tracked_html():
        try:
            html = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        rel = path.relative_to(ROOT).as_posix()

        promises = PROMISE.findall(html)
        if not promises:
            continue

        local = LOCAL_FILE.findall(html)
        sheets = SHEET_LINK.findall(html)
        generates = bool(GENERATES.search(html))

        # a local file link must point at something that exists
        missing = []
        for href in local:
            target = (ROOT / href.lstrip('/')) if href.startswith('/') else (path.parent / href)
            if not target.exists():
                missing.append(href)
        for href in missing:
            findings.append((rel, 'offers %s but that file does not exist' % href))

        if not (local or sheets or generates):
            # Both URL forms. /log/ is generated with ABSOLUTE self-links, so a
            # root-relative-only test concluded it linked to nothing and reported
            # a broken promise on a page that is describing history, not offering
            # anything. This is not a softening -- the target must still be a page
            # that genuinely delivers; it just has to be recognised when written
            # out in full.
            links_to_delivery = any(
                ('href="%s"' % d) in html or ('href="%s%s"' % (SITE, d)) in html
                for d in delivering)
            if not links_to_delivery:
                findings.append((
                    rel,
                    'promises an artifact (%s) but the page contains no download link, no sheet '
                    'link, generates nothing, and links to no page that delivers'
                    % promises[0].strip().lower()))
    return findings


def main() -> int:
    findings = audit()
    print('PROMISE AUDIT  --  %d page(s) with giveaway language checked'
          % len({f[0] for f in findings}) if findings else
          'PROMISE AUDIT  --  every page that promises an artifact has one')
    if not findings:
        print('  clean -- no page offers something it cannot hand over.')
        return 0
    for rel, msg in findings:
        print('  [BROKEN PROMISE] %s -- %s' % (rel, msg))
    print('\n  A page that asks someone to do something and then cannot deliver costs more')
    print('  trust than the missing artifact is worth. Build it or stop promising it.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
