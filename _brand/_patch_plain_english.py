#!/usr/bin/env python3
"""One-shot: add the plain-English block to every tool builder.

Every one of these pages opened by explaining itself to someone who already knew
the vocabulary. The owner who most needs the money-leak tool does not know what
"reconciles two exports" means, and will not stay to find out. Expertise in
running a business is not expertise in spreadsheets, and writing for the second
group quietly loses the first.

Patches the six uniform tool builders in place: import the helpers, append
PLAIN_CSS to the style block, and wrap MAIN in with_plain(). Exits on ANY
unmatched pattern rather than patching four of six and reporting success --
the same rule the xlsx rollout used, for the same reason.

Idempotent: a builder already carrying the block is skipped, not double-patched.
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

# what it does / why it helps / what you need / how long -- no jargon anywhere
COPY = {
    'build_health_check.py': (
        'Looks at a spreadsheet you already have and tells you which parts of it can no longer '
        'be trusted &mdash; columns that are empty, dates written five different ways, the same '
        'row entered twice.',
        'Bad data quietly makes bad numbers. If a column is half blank or a customer is in there '
        'twice, <b>every total built on it is wrong</b> and nothing warns you. This shows you '
        'exactly where, and offers a cleaned copy back.',
        'One file you already have &mdash; an export from Excel, Google Sheets, QuickBooks or your '
        'job software. Spreadsheet (.xlsx) or CSV both work.',
        'About ten seconds. The file never leaves your computer &mdash; there is nowhere here to '
        'send it.'),
    'build_money_leak_page.py': (
        'Lines up the work you finished against the invoices you sent, and shows you only the '
        'places they do not match.',
        '<b>It finds money you already earned but never collected</b> &mdash; jobs completed and '
        'never billed, and invoices that quietly went unpaid. It will even write the follow-up '
        'emails for you, though it cannot send them; you always press send.',
        'Two files you already have: a list of jobs or work done, and a list of invoices.',
        'About ten seconds. Your books never leave your machine.'),
    'build_duplicate_finder.py': (
        'Finds the same customer entered more than once under slightly different names &mdash; '
        '<em>Acme Roofing</em>, <em>Acme Roofing LLC</em>, <em>acme roofing inc.</em>',
        'Your customer count is wrong, and one customer\'s history is split across three records '
        '&mdash; so <b>your best client may not look like your best client</b>. It also stops the '
        'mail merge sending the same person three copies.',
        'One file with a customer or company name column.',
        'About ten seconds, and it tells you why it grouped each one so you can disagree.'),
    'build_shift_coverage.py': (
        'Reads your staff schedule and points out the four problems that cost money: a shift '
        'nobody is covering, someone drifting into overtime, a job only one person can do, and '
        'shifts too close together to be safe.',
        'These are normally noticed on Friday &mdash; <b>after</b> the overtime is already owed or '
        'the shift already went uncovered. This finds them while you can still move someone.',
        'Your schedule export: who works, what role, which day.',
        'About ten seconds. Nothing about your staff is uploaded anywhere.'),
    'build_check_page.py': (
        'You do not need to know which check you need. Drop in any business file and it works out '
        'what kind of file it is, then runs every check that applies. Drop in two and it compares '
        'them against each other.',
        '<b>It puts a dollar figure on what it finds</b> &mdash; for example, finished work that '
        'was never invoiced &mdash; so you can see what is worth chasing first instead of reading '
        'a list of complaints.',
        'Any export you already have. One file works; two work better.',
        'About ten seconds, and you get a report you can download and forward.'),
    'build_starter.py': (
        'Builds you a working Excel spreadsheet from scratch &mdash; a job log, an invoice list '
        'and a summary page &mdash; without asking you for anything.',
        'It arrives already set up so the two most expensive mistakes <b>flag themselves</b>: work '
        'you finished but never invoiced, and invoices sitting unpaid past 60 days. Nobody has to '
        'remember to check.',
        'Nothing at all. Press one button.',
        'About five seconds, and you get a real .xlsx file that opens in Excel or Google Sheets.'),
}

IMPORT_RE = re.compile(r'^from toolkit import (.+)$', re.M)
STYLE_RE = re.compile(r"f'<style>\{PAGE_CSS\}</style>\\n</head>'")
PAGE_RE = re.compile(r'^(\s*page = head \+ )MAIN( \+ )', re.M)


def patch(name: str, copy: tuple) -> str:
    p = HERE / name
    src = p.read_text(encoding='utf-8')
    if 'with_plain' in src:
        return f'{name}: already patched, skipped'

    block = ("\n\nPLAIN = plain_english(\n"
             "    %r,\n    %r,\n    %r,\n    %r)\n" % copy)

    m = IMPORT_RE.search(src)
    if m:
        names = [n.strip() for n in m.group(1).split(',')]
        for extra in ('PLAIN_CSS', 'plain_english', 'with_plain'):
            if extra not in names:
                names.append(extra)
        new_import = 'from toolkit import ' + ', '.join(names)
        src = IMPORT_RE.sub(lambda mm: new_import + block, src, count=1)
    else:
        # /starter/ builds a file rather than parsing one, so it never needed
        # the toolkit. It still needs to explain itself, so add the import.
        anchor = re.compile(r'^import re$', re.M)
        if not anchor.search(src):
            raise SystemExit(f'{name}: no toolkit import and no "import re" to anchor a new one')
        src = anchor.sub(
            'import re\n\nfrom toolkit import PLAIN_CSS, plain_english, with_plain' + block,
            src, count=1)

    src, n_style = STYLE_RE.subn("f'<style>{PAGE_CSS}{PLAIN_CSS}</style>\\\\n</head>'", src, count=1)
    if n_style != 1:
        raise SystemExit(f'{name}: style anchor not found exactly once')

    src, n_page = PAGE_RE.subn(r'\1with_plain(MAIN, PLAIN)\2', src, count=1)
    if n_page != 1:
        raise SystemExit(f'{name}: page-assembly anchor not found exactly once')

    p.write_text(src, encoding='utf-8')
    return f'{name}: patched'


if __name__ == '__main__':
    results = [patch(n, c) for n, c in COPY.items()]
    print('\n'.join(results))
    if not all(('patched' in r) or ('skipped' in r) for r in results):
        sys.exit(1)
