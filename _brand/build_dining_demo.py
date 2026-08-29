# -*- coding: utf-8 -*-
"""Publish the dining ordering demo to /dining/ from oakhammock's build.

WHY THIS EXISTS. The first version of this page was a hand-copy of
oakhammock/web/standalone.html with seven edits layered on top by hand: the
robots tag, a description, a canonical, a visually-hidden h1, the contact
block, a longer title, and the worker endpoint. Every one of those is required
by a gate in this repo, and ALL SEVEN would have been silently wiped by the
next person who re-copied the file -- which is the whole reason a builder
exists instead of a copy step. The commit that shipped it said so in prose,
which is a note, not a control.

Every substitution ASSERTS its anchor first. A str.replace that matches
nothing fails silently, and this workspace has shipped that bug twice: a
priced extra that never reached the line, and a page that looked wired and
behaved offline.

Run:  python _brand/build_dining_demo.py
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, '..', 'oakhammock', 'web', 'standalone.html')
OUT = os.path.join(ROOT, 'dining', 'index.html')

# The deployed worker holds the API key as a Cloudflare secret. The passphrase
# is NOT a secret from the reader -- it rides in this page because anyone who
# can open the page can already call the endpoint. It gates a stranger who
# finds the worker URL. The account credit balance is the real cap.
WORKER = 'https://oakhammock-chat.automaticworkflowllc.workers.dev/'
PASSPHRASE_FILE = os.path.join(HERE, 'dining_passphrase.txt')

TITLE = 'Dining Room Ordering Demo &mdash; Browse or Order by Chat'
DESCRIPTION = ('A working ordering demo for a dining room: browse the real menu, '
               'or order by chat. Built by Automated Workflow, Gainesville FL.')
CANONICAL = 'https://automatedworkflowllc.com/dining/'


def sub(html, anchor, replacement, what, count=1):
    """Replace, refusing to write if the anchor is not there exactly once."""
    n = html.count(anchor)
    if n != count:
        raise SystemExit(
            'BUILD REFUSED: %s -- expected the anchor %r exactly %d time(s), '
            'found %d. The upstream build changed shape; fix this builder '
            'rather than hand-editing dining/index.html, or the next run '
            'silently drops it again.' % (what, anchor[:60], count, n))
    return html.replace(anchor, replacement, count)


def main():
    if not os.path.exists(SRC):
        raise SystemExit('BUILD REFUSED: %s is missing. Run '
                         'python web/build_static.py in oakhammock first.' % SRC)
    if not os.path.exists(PASSPHRASE_FILE):
        raise SystemExit(
            'BUILD REFUSED: %s is missing. It holds the SHARED_PASSPHRASE that '
            'was set on the worker with `wrangler secret put`. Without it this '
            'page would be published pointing at an endpoint it cannot call, '
            'and every chat message would silently fall back to the offline '
            'parser -- which looks like the model being wrong rather than '
            'absent.' % PASSPHRASE_FILE)
    passphrase = io.open(PASSPHRASE_FILE, encoding='utf-8').read().strip()
    html = io.open(SRC, encoding='utf-8').read()

    # 1. The worker. Must land before the page's own scripts read the global.
    cfg = ('<script>window.OH_REMOTE_CHAT={url:%s,passphrase:%s,timeoutMs:20000};'
           '</script>\n' % (json.dumps(WORKER), json.dumps(passphrase)))
    html = sub(html, '<script>', cfg + '<script>', 'worker config', count=html.count('<script>'))

    # 2. Out of organic search on purpose -- the /free-demo/ precedent. The
    #    explanatory comment is REQUIRED by seo_audit, not decoration.
    robots = ('<meta name="robots" content="noindex,nofollow">\n'
              '<!-- Deliberately out of organic search: a CLIENT demo hosted so it can be\n'
              '     opened from any machine, not a page of ours to be found. Linked from\n'
              '     nowhere on purpose. Same decision as /free-demo/. -->\n')
    html = sub(html, '<meta name="viewport"', robots + '<meta name="viewport"',
               'robots tag')

    # 3. Head metadata every page here is required to carry.
    head = ('<meta name="description" content="%s">\n'
            '<link rel="canonical" href="%s">\n' % (DESCRIPTION, CANONICAL))
    html = sub(html, '<meta name="robots"', head + '<meta name="robots"',
               'description and canonical')

    # 4. Title: the upstream one is 18 chars against a 50-60 budget.
    html = sub(html, '<title>Oak Hammock Dining</title>',
               '<title>%s</title>' % TITLE, 'title')

    # 5. Exactly one h1, VISUALLY HIDDEN. The demo's headings are styled
    #    display text; changing a client-facing page to satisfy a checker is
    #    backwards, but the page still needs one, so a screen reader gets it.
    h1 = ('<h1 style="position:absolute;width:1px;height:1px;overflow:hidden;'
          'clip:rect(0 0 0 0);white-space:nowrap">Dining room ordering demo</h1>\n')
    html = sub(html, '<div id="hdr"></div>', h1 + '<div id="hdr"></div>', 'h1')

    # 6. Whose site this is. Woven into the demo's own footer line so it reads
    #    as provenance rather than being bolted on.
    html = sub(html, 'Reset demo',
               'Demo built by Automated Workflow, Gainesville, FL &middot; '
               'colin@automatedworkflowllc.com &middot; (703) 939-1174 '
               '&middot; Reset demo', 'contact block')

    # Refuse to ship a key. The passphrase is expected; an API key never is.
    if re.search(r'sk-ant-[A-Za-z0-9_-]{10,}', html):
        raise SystemExit('BUILD REFUSED: an API key reached the page.')

    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(html)
    print('wrote %s (%d KB) -- worker wired, %d gate requirement(s) applied'
          % (OUT, len(html) // 1024, 6))
    return 0


if __name__ == '__main__':
    sys.exit(main())
