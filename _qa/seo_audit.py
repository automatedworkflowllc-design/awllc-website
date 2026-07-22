# -*- coding: utf-8 -*-
"""SEO audit -- codifies the 2026-07-21 adversarial SEO audit (12/12 findings
confirmed, 0 refuted; 5 independent auditors + 2 verifiers/finding via
dev/workflows-archive/awllc-seo-audit.workflow.js) into a permanent check, so
each fixed defect stays fixed and no new page repeats the same class of gap.

Modelled on _qa/autoqa.py's REGRESSION pattern, not zero-tolerance like
security_sweep.py: at the moment this script was written the site already
carries several of these defects (long titles, /demo/ missing NAP, etc.) that
are Colin's copy/content decisions to fix, not bugs to auto-correct. The gate
is "don't make the score WORSE than last run" -- exactly autoqa.py's model.
Score history lives in seo_history.json (separate file -- autoqa's
history.json tracks a different metric with different meaning).

Checks every git-tracked *.html page:
  1. <title> length 50-60 chars (Google's SERP truncation point)
  2. <meta name="description"> length 120-158 chars
  3. exactly one <link rel="canonical">
  4. exactly one <meta name="viewport">
  5. exactly one <h1>
  6. sitemap.xml <-> tracked-page cross-check: every non-noindex page is in the
     sitemap and vice versa; every noindex tag must carry an explanatory HTML
     comment on the next line (the free-demo/index.html precedent -- a noindex
     with no comment is indistinguishable from an accidental one)
  7. every non-noindex page is linked (href="...") from at least one OTHER
     tracked page -- an unlinked page still ranks worse and users can't
     navigate to it even if a search engine finds it
  8. llms.txt's "## Pages" section lists every sitemap URL (AI-answer-engine
     visibility -- the whole point of the file)
  9. footer NAP: canonical email / phone / "Gainesville" text visible in the
     page body (not just a mailto:/tel: href -- _qa/last_mile_audit.py already
     covers those; this covers what a HUMAN reader actually sees)
 10. footer business-name string is byte-identical across every page that has
     one ("Automated Workflow" vs "Automated Workflow LLC" is a NAP-consistency
     defect, not a stylistic choice)
 11. every JSON-LD Offer block (schema.org) carries a non-empty "price"
 12. og:image file exists on disk; if the page declares no explicit
     og:image:width/height, the file's real dimensions must be close to
     1200x630 (1.91:1, the platform-standard social-card crop)

KNOWN GAPS -- deliberately NOT automated (judgment calls where a heuristic
would cry wolf; left as one-time audit findings instead):
  - Service-schema parity across sibling free-template pages
  - the site-wide absence of any real <img> (screenshot) asset

Run:  python _qa/seo_audit.py           (human-readable)
      python _qa/seo_audit.py --json    (machine)
Exit: 0 = no regression vs last run * 1 = regression * 2 = runner failure
"""
import io, os, re, sys, json, html, datetime, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, '_qa', 'seo_history.json')
LIVE = 'https://automatedworkflowllc.com'

CANON_EMAIL = 'colin@automatedworkflowllc.com'
CANON_PHONE_DISPLAY = '(703) 939-1174'
CANON_CITY = 'Gainesville'
CANON_FOOTER_NAME = 'Automated Workflow'   # majority usage (10/14 tracked pages); the
                                            # homepage uses this form. Check only flags
                                            # a MISMATCH across pages, not the choice itself.

defects = []
def defect(area, msg):
    defects.append({'area': area, 'msg': msg})

def tracked(pat):
    out = subprocess.run(['git', 'ls-files', pat], cwd=ROOT, capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f.strip()]

def read(rel):
    return io.open(os.path.join(ROOT, rel), encoding='utf-8', errors='replace').read()

def file_to_url(rel):
    rel = rel.replace('\\', '/')
    if rel == 'index.html':
        return '/'
    if rel.endswith('/index.html'):
        return '/' + rel[:-len('index.html')]
    return '/' + rel

def tag(src, name_attr, value):
    """Return the full <meta ...> tag text where name/property=value, or None."""
    m = re.search(r'<meta\b[^>]*\b%s="%s"[^>]*>' % (re.escape(name_attr), re.escape(value)), src, re.I)
    return m.group(0) if m else None

def attr(tagtext, attr_name):
    if not tagtext:
        return None
    m = re.search(r'%s="([^"]*)"' % re.escape(attr_name), tagtext, re.I)
    return html.unescape(m.group(1)) if m else None

# ---------------------------------------------------------------- per-page
def check_pages(pages, src_by_page):
    for rel in pages:
        src = src_by_page[rel]

        # 1. title length
        m = re.search(r'<title>(.*?)</title>', src, re.S)
        if not m:
            defect('title', '%s -- missing <title>' % rel)
        else:
            t = html.unescape(m.group(1).strip())
            if not (50 <= len(t) <= 60):
                defect('title', '%s -- title is %d chars (want 50-60): %r' % (rel, len(t), t))

        # 2. meta description length
        desc_tag = tag(src, 'name', 'description')
        d = attr(desc_tag, 'content')
        if not d:
            defect('meta-description', '%s -- missing meta description' % rel)
        elif not (120 <= len(d) <= 158):
            defect('meta-description', '%s -- description is %d chars (want 120-158)' % (rel, len(d)))

        # 3. canonical
        if len(re.findall(r'<link\b[^>]*\brel="canonical"', src, re.I)) != 1:
            defect('canonical', '%s -- expected exactly one canonical link' % rel)

        # 4. viewport
        if len(re.findall(r'<meta\b[^>]*\bname="viewport"', src, re.I)) != 1:
            defect('viewport', '%s -- expected exactly one viewport meta tag' % rel)

        # 5. h1 count
        h1s = len(re.findall(r'<h1\b', src, re.I))
        if h1s != 1:
            defect('h1', '%s -- has %d <h1> tags (want exactly 1)' % (rel, h1s))

        # 9. footer NAP visible text
        missing = [x for x in (CANON_EMAIL, CANON_PHONE_DISPLAY, CANON_CITY) if x not in src]
        if missing:
            defect('nap', '%s -- missing visible %s' % (rel, ', '.join(missing)))

        # 11. JSON-LD Offer price
        for block in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', src, re.S | re.I):
            try:
                data = json.loads(block)
            except Exception:
                defect('jsonld', '%s -- malformed JSON-LD block (invalid JSON)' % rel)
                continue
            for offer in _find_offers(data):
                if not offer.get('price'):
                    defect('jsonld-offer', '%s -- Offer block missing non-empty "price"' % rel)

        # 12. og:image existence + aspect ratio
        og_tag = tag(src, 'property', 'og:image')
        og_url = attr(og_tag, 'content')
        if og_url and og_url.startswith(LIVE):
            local = og_url[len(LIVE):].lstrip('/')
            path = os.path.join(ROOT, local)
            if not os.path.isfile(path):
                defect('og-image', '%s -- og:image %s does not exist on disk' % (rel, local))
            else:
                w = attr(tag(src, 'property', 'og:image:width'), 'content')
                h = attr(tag(src, 'property', 'og:image:height'), 'content')
                if not (w and h):
                    try:
                        from PIL import Image
                        iw, ih = Image.open(path).size
                        ratio = iw / float(ih)
                        if abs(ratio - (1200 / 630.0)) > 0.15:
                            defect('og-image', '%s -- og:image %dx%d (ratio %.2f) is far from the 1.91:1 '
                                   'social standard, and declares no og:image:width/height to compensate' % (rel, iw, ih, ratio))
                    except ImportError:
                        defect('setup', 'Pillow (PIL) missing -- og:image dimension check skipped')

def _find_offers(node):
    """Recursively find every dict that looks like a schema.org Offer."""
    out = []
    if isinstance(node, dict):
        t = node.get('@type')
        if t == 'Offer' or (isinstance(t, list) and 'Offer' in t):
            out.append(node)
        for v in node.values():
            out.extend(_find_offers(v))
    elif isinstance(node, list):
        for v in node:
            out.extend(_find_offers(v))
    return out

# ---------------------------------------------------------------- site-wide
def check_sitemap_and_orphans(pages, src_by_page):
    sitemap_urls = set()
    try:
        sm = read('sitemap.xml')
        sitemap_urls = {u[len(LIVE):] or '/' for u in re.findall(r'<loc>([^<]+)</loc>', sm)}
    except Exception:
        defect('sitemap', 'could not read sitemap.xml')
        return

    noindex_pages = set()
    for rel in pages:
        src = src_by_page[rel]
        robots_tag = tag(src, 'name', 'robots')
        content = attr(robots_tag, 'content') or ''
        if 'noindex' in content.lower():
            noindex_pages.add(rel)
            # explanatory-comment precedent: the noindex line's next non-blank line
            # must be an HTML comment (see free-demo/index.html)
            lines = src.splitlines()
            idx = next((i for i, l in enumerate(lines) if 'name="robots"' in l and 'noindex' in l.lower()), None)
            nxt = ''
            if idx is not None:
                for l in lines[idx + 1: idx + 3]:
                    if l.strip():
                        nxt = l
                        break
            if '<!--' not in nxt:
                defect('noindex-undocumented', '%s -- noindex tag has no explanatory comment '
                       '(compare free-demo/index.html, which states why)' % rel)

    for rel in pages:
        url = file_to_url(rel)
        if rel in noindex_pages:
            continue
        if url not in sitemap_urls:
            defect('sitemap-coverage', '%s (%s) -- indexable page missing from sitemap.xml' % (rel, url))

    tracked_urls = {file_to_url(rel) for rel in pages}
    for url in sitemap_urls:
        if url not in tracked_urls:
            defect('sitemap-coverage', 'sitemap.xml references %s, which has no matching tracked page' % url)

    # 7. orphan pages -- must be linked from at least one OTHER tracked page
    for rel in pages:
        if rel in noindex_pages:
            continue
        url = file_to_url(rel)
        needle = 'href="%s"' % url
        linked = any(needle in src_by_page[other] for other in pages if other != rel)
        if not linked:
            defect('orphan-page', '%s (%s) -- not linked from any other tracked page' % (rel, url))

def check_llms_txt(pages):
    try:
        sm = read('sitemap.xml')
        sitemap_urls = {u for u in re.findall(r'<loc>([^<]+)</loc>', sm)}
    except Exception:
        return
    try:
        llms = read('llms.txt')
    except Exception:
        defect('llms-txt', 'could not read llms.txt')
        return
    pages_section = llms.split('## Pages', 1)
    body = pages_section[1].split('##', 1)[0] if len(pages_section) > 1 else ''
    listed = set(re.findall(r'\(https://automatedworkflowllc\.com[^)]*\)', body))
    listed = {u.strip('()') for u in listed}
    missing = sorted(u for u in sitemap_urls if u not in listed)
    if missing:
        defect('llms-txt', 'llms.txt Pages section is missing %d/%d sitemap URL(s): %s'
               % (len(missing), len(sitemap_urls), ', '.join(missing[:6]) + (' ...' if len(missing) > 6 else '')))

def check_footer_name_consistency(pages, src_by_page):
    names = {}
    for rel in pages:
        m = re.search(r'&copy;\s*<span id="yr">\d+</span>\s*([A-Za-z0-9 .,&;\-]+?)\s*&middot;', src_by_page[rel])
        if m:
            name = re.sub(r'&amp;', '&', m.group(1)).strip()
            names[rel] = name
    mismatched = {rel: n for rel, n in names.items() if n != CANON_FOOTER_NAME}
    if mismatched:
        defect('nap-consistency', 'footer business-name inconsistent on %d page(s) (canonical: %r): %s'
               % (len(mismatched), CANON_FOOTER_NAME, ', '.join('%s=%r' % (r, n) for r, n in mismatched.items())))

# ---------------------------------------------------------------- main
def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')  # site copy uses em-dashes; avoid console mojibake
    except AttributeError:
        pass
    pages = tracked('*.html')
    src_by_page = {rel: read(rel) for rel in pages}

    for fn, fargs in [
        (check_pages, (pages, src_by_page)),
        (check_sitemap_and_orphans, (pages, src_by_page)),
        (check_llms_txt, (pages,)),
        (check_footer_name_consistency, (pages, src_by_page)),
    ]:
        try:
            fn(*fargs)
        except Exception as e:
            defect('runner', '%s crashed: %s' % (fn.__name__, e))

    score = len(defects)
    hist = []
    if os.path.exists(HIST):
        try: hist = json.load(io.open(HIST, encoding='utf-8'))
        except Exception: hist = []
    prev = hist[-1]['score'] if hist else None
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    hist.append({'when': stamp, 'score': score, 'pages': len(pages),
                 'by_area': {a: sum(1 for d in defects if d['area'] == a) for a in {d['area'] for d in defects}}})
    os.makedirs(os.path.dirname(HIST), exist_ok=True)
    io.open(HIST, 'w', encoding='utf-8').write(json.dumps(hist[-60:], indent=1))

    if '--json' in sys.argv:
        print(json.dumps({'score': score, 'prev': prev, 'defects': defects}, indent=1))
    else:
        print('SEO audit %s -- %d page(s), defects: %d%s' % (
            stamp, len(pages), score, '' if prev is None else '  (previous: %d)' % prev))
        for d in defects:
            print('  [%-18s] %s' % (d['area'], d['msg']))
        if not defects:
            print('  clean')
        if prev is not None and score > prev:
            print('\n  ** REGRESSION: %d new defect(s) since last run **' % (score - prev))

    if prev is not None and score > prev:
        return 1
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('runner failure:', e); sys.exit(2)
