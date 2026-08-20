# -*- coding: utf-8 -*-
"""Negative control for the SEO gate. Proves it still fires, and still doesn't.

WHY THIS EXISTS. seo_audit.py runs on every push (refresh_public_log's GATES
list) and guards twelve rules across every tracked page. It had no test of any
kind. That is the gap this week's rule is about: a gate ships with a committed
control or it has not shipped, and a gate nobody has seen go red is not
evidence. It is now the fourth to get one, after the security sweep, the suite
sweep and the palette gate.

Two of its rules are here because they were BUILT from real defects, and those
are the ones a future edit is most likely to quietly loosen:

  - the state beside the city. CANON_CITY used to be the bare "Gainesville",
    which "Gainesville, VA" contains -- so the substring test could never fail
    on the part that was wrong, and two pages advertised the wrong state while
    the gate reported clean.
  - the noindex explanatory comment. free-demo/ is deliberately noindex (it is
    the ads landing page, kept out of organic search on purpose), and a noindex
    with no comment is indistinguishable from an accidental one.

The duty is symmetric throughout. Every planted defect is paired with the
compliant version of the same page, because a rule that fires on everything is
as useless as one that fires on nothing -- and the FIRST case below is the
control for every absence assertion in the file: if the clean fixture were not
actually clean, "this defect is absent" would prove nothing.

Run: python _qa/test_seo_audit.py
"""

import io
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
AUDIT = HERE / 'seo_audit.py'
LIVE = 'https://automatedworkflowllc.com'

CANON_EMAIL = 'colin@automatedworkflowllc.com'
CANON_PHONE = '(703) 939-1174'
CANON_CITY = 'Gainesville, FL'
CANON_NAME = 'Automated Workflow'


def _pad(text, n):
    """Grow text to exactly n characters so a fixture lands inside a length window."""
    filler = ' Checked nightly by a scheduled job that writes a signed receipt.'
    while len(text) < n:
        text += filler
    return text[:n]


TITLE = _pad('Spreadsheet Cleanup and Automation for Small Business', 55)
DESC = _pad('Automated Workflow finds money and mistakes hiding in the spreadsheets a '
            'business already has, and watches the jobs that quietly stop producing.', 140)


def page(slug, links=(), title=TITLE, desc=DESC, canonicals=1, viewports=1, h1s=1,
         robots=None, robots_comment=True, city=CANON_CITY, footer_name=CANON_NAME):
    """One compliant page, with exactly the one thing a caller asks to break."""
    head = ['<!doctype html><html><head><meta charset="utf-8">']
    if title is not None:
        head.append('<title>%s</title>' % title)
    if desc is not None:
        head.append('<meta name="description" content="%s">' % desc)
    head += ['<link rel="canonical" href="%s/%s/">' % (LIVE, slug)] * canonicals
    head += ['<meta name="viewport" content="width=device-width">'] * viewports
    if robots:
        head.append('<meta name="robots" content="%s">' % robots)
        if robots_comment:
            head.append('<!-- deliberately out of organic search; see free-demo -->')
        else:
            head.append('<p>no explanation here</p>')
    head.append('</head><body>')
    body = ['<h1>Heading</h1>'] * h1s
    body += ['<a href="/%s/">to %s</a>' % (t, t) for t in links]
    body.append('<footer><p>%s &middot; %s &middot; %s</p>' % (CANON_EMAIL, CANON_PHONE, city))
    body.append('<p>&copy; <span id="yr">2026</span> %s &middot; all rights reserved</p>'
                '</footer></body></html>' % footer_name)
    return '\n'.join(head + body)


def site(pages, sitemap_urls=None, llms_urls=None):
    """A synthetic git repo whose _qa/ holds the REAL seo_audit.py.

    A git repo because the audit enumerates pages with `git ls-files` -- an
    untracked fixture is invisible to it, which would make every case pass by
    scanning nothing.
    """
    root = pathlib.Path(tempfile.mkdtemp())
    (root / '_qa').mkdir()
    shutil.copy(str(AUDIT), str(root / '_qa' / 'seo_audit.py'))

    urls = []
    for slug, body in pages.items():
        d = root / slug
        d.mkdir()
        io.open(d / 'index.html', 'w', encoding='utf-8').write(body)
        urls.append('/%s/' % slug)

    sm_urls = urls if sitemap_urls is None else sitemap_urls
    io.open(root / 'sitemap.xml', 'w', encoding='utf-8').write(
        '<?xml version="1.0"?><urlset>%s</urlset>'
        % ''.join('<url><loc>%s%s</loc></url>' % (LIVE, u) for u in sm_urls))

    ll_urls = sm_urls if llms_urls is None else llms_urls
    io.open(root / 'llms.txt', 'w', encoding='utf-8').write(
        '# Automated Workflow\n\n## Pages\n%s\n'
        % '\n'.join('- [%s](%s%s)' % (u, LIVE, u) for u in ll_urls))

    for cmd in (['init', '-q'], ['add', '-A']):
        subprocess.run(['git'] + cmd, cwd=str(root), capture_output=True, text=True)
    return root


def run(root, *args):
    p = subprocess.run([sys.executable, str(root / '_qa' / 'seo_audit.py'), '--json'] + list(args),
                       cwd=str(root), capture_output=True, text=True, timeout=180)
    raw = p.stdout or ''
    try:
        data = json.loads(raw[raw.index('{'):raw.rindex('}') + 1])
    except (ValueError, IndexError):
        return p.returncode, {'defects': [], 'score': None}, raw + (p.stderr or '')
    return p.returncode, data, raw + (p.stderr or '')


def areas(data):
    return [d['area'] for d in data['defects']]


def CLEAN():
    """Two compliant pages that link to each other. Nothing should be wrong here."""
    return site({'alpha': page('alpha', links=['beta']),
                 'beta': page('beta', links=['alpha'])})


def main():
    fails = []

    def ok(name, cond, detail=''):
        if cond:
            print('  [seo-control] %-58s ok' % name)
        else:
            print('  [seo-control] %-58s FAIL  %s' % (name, str(detail)[:300]))
            fails.append(name)

    # 0. THE CONTROL FOR EVERY ABSENCE ASSERTION BELOW. If the compliant fixture
    #    is not actually compliant, "this defect is absent" means nothing --
    #    it could be absent because the audit never looked.
    code, data, raw = run(CLEAN())
    ok('a fully compliant site produces no defects at all',
       data['defects'] == [], data['defects'] or raw)
    ok('and a clean run exits 0', code == 0, 'exit %s | %s' % (code, raw[:200]))

    # 1. Title window.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta'], title='Too short'),
                             'beta': page('beta', links=['alpha'])}))
    ok('a title outside the 50-60 window is caught', 'title' in areas(data), raw)
    ok('and the offending page is NAMED',
       any('alpha' in d['msg'] for d in data['defects'] if d['area'] == 'title'), raw)

    # 2. Description window.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta'], desc='way too short'),
                             'beta': page('beta', links=['alpha'])}))
    ok('a description outside the 120-158 window is caught',
       'meta-description' in areas(data), raw)

    # 3. Exactly-one rules. Two canonicals is the realistic failure (a template
    #    adding one on top of a hand-written one), not zero.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta'], canonicals=2),
                             'beta': page('beta', links=['alpha'])}))
    ok('two canonical links are caught', 'canonical' in areas(data), raw)

    _, data, raw = run(site({'alpha': page('alpha', links=['beta'], h1s=2),
                             'beta': page('beta', links=['alpha'])}))
    ok('two h1 tags are caught', 'h1' in areas(data), raw)

    _, data, raw = run(site({'alpha': page('alpha', links=['beta'], viewports=0),
                             'beta': page('beta', links=['alpha'])}))
    ok('a missing viewport is caught', 'viewport' in areas(data), raw)

    # 4. THE STATE, not the city. This is the rule that was WRONG once: a bare
    #    'Gainesville' substring test passes on 'Gainesville, VA', so the gate
    #    stayed green while two live pages advertised the wrong state.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta'], city='Gainesville, VA'),
                             'beta': page('beta', links=['alpha'])}))
    ok('the WRONG STATE beside the city is caught', 'nap-state' in areas(data), raw)
    ok('and it says which state it found',
       any('VA' in d['msg'] for d in data['defects'] if d['area'] == 'nap-state'), raw)

    # 5. The banned entity claim -- asserting a legal standing never filed.
    bad = page('alpha', links=['beta']).replace(
        '</footer>', '<p>Automated Workflow LLC</p></footer>')
    _, data, raw = run(site({'alpha': bad, 'beta': page('beta', links=['alpha'])}))
    ok('an unquoted "Automated Workflow LLC" is caught', 'entity-claim' in areas(data), raw)

    # 6. ...and the other half, which is why that check is not a plain substring
    #    search: /log/ QUOTES the wrong name while explaining this very defect.
    #    A gate that cannot tell those apart makes the log unable to record its
    #    own bugs.
    quoted = page('alpha', links=['beta']).replace(
        '</footer>', '<p>we shipped &ldquo;Automated Workflow LLC&rdquo; by mistake</p></footer>')
    _, data, raw = run(site({'alpha': quoted, 'beta': page('beta', links=['alpha'])}))
    ok('but QUOTING it while explaining the bug is allowed',
       'entity-claim' not in areas(data), raw)

    # 7. Footer business-name consistency.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta'], footer_name='Automated Workflows'),
                             'beta': page('beta', links=['alpha'])}))
    ok('an inconsistent footer business name is caught',
       'nap-consistency' in areas(data), raw)

    # 8. Missing visible contact details.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta']).replace(CANON_PHONE, ''),
                             'beta': page('beta', links=['alpha'])}))
    ok('a missing visible phone number is caught', 'nap' in areas(data), raw)

    # 9. noindex. The free-demo precedent, both ways round.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta'], robots='noindex, nofollow',
                                           robots_comment=False),
                             'beta': page('beta', links=['alpha'])},
                            sitemap_urls=['/beta/'], llms_urls=['/beta/']))
    ok('an UNDOCUMENTED noindex is caught', 'noindex-undocumented' in areas(data), raw)

    _, data, raw = run(site({'alpha': page('alpha', links=['beta'], robots='noindex, nofollow',
                                           robots_comment=True),
                             'beta': page('beta', links=['alpha'])},
                            sitemap_urls=['/beta/'], llms_urls=['/beta/']))
    ok('a noindex WITH its explanation is left alone (the free-demo case)',
       data['defects'] == [], data['defects'] or raw)

    # 10. Sitemap coverage, both directions.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta']),
                             'beta': page('beta', links=['alpha'])},
                            sitemap_urls=['/beta/'], llms_urls=['/beta/']))
    ok('an indexable page missing from the sitemap is caught',
       'sitemap-coverage' in areas(data), raw)

    _, data, raw = run(site({'alpha': page('alpha', links=['beta']),
                             'beta': page('beta', links=['alpha'])},
                            sitemap_urls=['/alpha/', '/beta/', '/ghost/'],
                            llms_urls=['/alpha/', '/beta/', '/ghost/']))
    ok('a sitemap URL with no matching page is caught',
       any('ghost' in d['msg'] for d in data['defects']), raw)

    # 11. Orphan pages -- nothing links to them.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta']),
                             'beta': page('beta')}))
    ok('a page nothing links to is caught', 'orphan-page' in areas(data), raw)

    # 12. llms.txt coverage -- the AI-answer-engine surface, and the whole point
    #     of the file, so a page silently absent from it defeats its purpose.
    _, data, raw = run(site({'alpha': page('alpha', links=['beta']),
                             'beta': page('beta', links=['alpha'])},
                            llms_urls=['/beta/']))
    ok('a sitemap URL missing from llms.txt is caught', 'llms-txt' in areas(data), raw)

    # 13. THE RATCHET. A gate that records on a failing run launders its own
    #     failure into the baseline: run it twice with nothing fixed and the
    #     second run passes. Demonstrated live on 2026-08-10.
    root = CLEAN()
    run(root, '--record')                                   # establish a clean baseline
    hist = json.loads(io.open(root / '_qa' / 'seo_history.json', encoding='utf-8').read())
    ok('--record on a clean run DOES write the baseline', len(hist) == 1, hist)

    io.open(root / 'alpha' / 'index.html', 'w', encoding='utf-8').write(
        page('alpha', links=['beta'], title='Too short'))
    subprocess.run(['git', 'add', '-A'], cwd=str(root), capture_output=True, text=True)
    code, data, raw = run(root, '--record')
    ok('a regression exits 1', code == 1, 'exit %s | %s' % (code, raw[:200]))
    after = json.loads(io.open(root / '_qa' / 'seo_history.json', encoding='utf-8').read())
    ok('and --record CANNOT move the baseline on a regressed run',
       len(after) == 1, 'history grew to %d entries' % len(after))

    code2, _, raw2 = run(root, '--record')
    ok('so looking twice does not launder the defect into a pass',
       code2 == 1, 'second look exited %s' % code2)

    if fails:
        print('\nSEO CONTROL FAILED on %d check(s). This gate runs on every push and '
              'guards twelve rules across every tracked page; if it cannot go red, '
              'none of them are guarded.' % len(fails))
        return 1
    print('  seo control: still catches each planted defect, still quiet on a clean site')
    return 0


if __name__ == '__main__':
    sys.exit(main())
