# -*- coding: utf-8 -*-
"""AutoQA — the bounded self-checking loop for AWLLC artifacts.

Modelled on Karpathy's AutoResearch structure: an objective metric, a defined
codebase, and hard boundaries on what may change. Ours differs in one deliberate
way — it is aimed at VERIFICATION, not generation. AWLLC's constraint is demand,
not output; a loop that generates more artifacts would accelerate the thing that
is not scarce.

OBJECTIVE METRIC : total defect count (lower is better). Written to history.json
                   so regressions are detectable across runs.
CODEBASE         : awllc-website/ (demo builders + published pages)
BOUNDARIES       : READ-ONLY AND REPORT-ONLY. This script must never push, send,
                   publish, upload, or mutate a live surface. It rebuilds
                   workbooks into their own folders (idempotent) and reads. That
                   is the whole permitted blast radius. If a future edit gives it
                   write access to anything user-facing, that is a bug.

Run:  python _qa/autoqa.py           (human-readable)
      python _qa/autoqa.py --json    (machine)
Exit: 0 = no regression vs last run · 1 = regression · 2 = runner failure
"""
import io, os, re, sys, json, glob, subprocess, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, '_qa', 'history.json')
LIVE = 'https://automatedworkflowllc.com'

BRAND = {'211D14','FBFAF3','F4F1E8','5C5645','6E6555','E4DFD1','D8D2C2','CBC5B1',
         'FFFFFF','1E7A47','B45309','B23B3B','E6F2EC','FBEFE0','F6E7E7'}
# claims that would imply a client base AWLLC does not have
# non-capturing groups: re.findall returns tuples when a pattern has groups,
# which printed "('', '')" instead of the offending phrase
#
# "hundreds of" and "dozens of" were bare here, matching the QUANTITY with no
# regard for what was being counted. On 2026-08-17 the only match site-wide was
# "hundreds of Go modules" in the build log -- counting software dependencies,
# which implies nothing about clients. A build log written by engineers will keep
# producing "dozens of tests", "hundreds of rows", "hundreds of pages"; the check
# would have fired on all of them and been muted, which is the third false alarm
# of this exact shape in one night (a palette gate flagging a hex inside <code>,
# a bounce code read as an outage). TRACTION_DRIFT below already got this right
# and says so: match the NOUN, not just the word near it.
CODE_SPAN = re.compile(r'<code\b[^>]*>.*?</code>', re.S | re.I)

FALSE_PROOF = re.compile(r'plenty of (?:clients|customers)|many (?:clients|customers)|'
                         r'our clients|trusted by|'
                         r'(?:hundreds|dozens) of (?:businesses|business owners|clients|'
                         r'customers|companies|users|owners|shops|firms|accounts)', re.I)

# Traction drift: copy describing system CAPACITY in language that reads as a
# CUSTOMER BASE. This class escaped three times on 2026-07-19 alone ("One
# workflow, many clients" / "serves many businesses" / "ten retainers is one
# maintained workflow") — the phrasing reaches for implied clients naturally,
# nobody is lying, and it keeps having to be pulled back. Present-tense "serves
# N businesses" and "N clients IS/ARE ..." claim traction; the honest forms
# ("can serve", "would be") do not match. Deliberately narrow — a checker that
# cries wolf gets ignored.
TRACTION_DRIFT = re.compile(
    r'\bserves (?:many|dozens of|hundreds of|\d+) (?:businesses|clients|customers)\b|'
    r'\b(?:ten|twenty|\d+) (?:retainers|clients|customers) (?:is|are)\b', re.I)

defects = []
def defect(area, msg):
    defects.append({'area': area, 'msg': msg})

# ---------------------------------------------------------------- workbooks
def check_workbooks():
    try:
        from openpyxl import load_workbook
    except ImportError:
        defect('setup', 'openpyxl missing — workbook checks skipped'); return
    for f in sorted(glob.glob(os.path.join(ROOT, '*', '*.xlsx'))):
        rel = os.path.relpath(f, ROOT)
        try:
            wb = load_workbook(f)
        except Exception as e:
            defect('workbook', '%s unreadable: %s' % (rel, e)); continue

        # (1) conditional formatting breaks Google's xlsx import
        cf = sum(len(list(ws.conditional_formatting)) for ws in wb)
        if cf:
            defect('workbook', '%s has %d conditional-format rules (breaks Sheets import)' % (rel, cf))

        # (2) every colour must be a canonical brand token
        seen = set()
        for ws in wb:
            for row in ws.iter_rows():
                for c in row:
                    for h in (getattr(c.fill.fgColor, 'rgb', None),
                              getattr(c.font.color, 'rgb', None)):
                        if isinstance(h, str) and len(h) == 8 and h[2:].upper() != '000000':
                            seen.add(h[2:].upper())
        off = sorted(seen - BRAND)
        if off:
            defect('workbook', '%s off-brand colours: %s' % (rel, ','.join(off[:5])))

        # (3) label-vs-value — the 7/19 column-shift class
        for ws in wb:
            for label, col, head, formula in mismatches(ws):
                defect('workbook',
                       '%s [%s] "%s" sums column %s which is headed "%s"'
                       % (rel, ws.title, label[:44], col, head))


# Vocabulary of concepts a summary label and a column header can both name.
# A mismatch is only meaningful between two DIFFERENT known concepts — that is
# the exact signature of the Job Costing defect ("Total quoted" summing the
# actual-cost column). Word-boundary matching, because "Actually invoiced"
# contains "actual" and is not a defect.
CONCEPTS = {
    'quoted':    r'\bquote(d)?\b',
    'actual':    r'\bactual\b|\bactual cost\b',
    'margin':    r'\bmargin\b',
    'invoiced':  r'\binvoice(d)?\b',
    'collected': r'\bcollect(ed)?\b',
    'expense':   r'\bexpense(s)?\b',
    'revenue':   r'\brevenue\b',
    'hours':     r'\bhours?\b',
}

def concepts_in(text):
    t = (text or '').lower()
    return {name for name, pat in CONCEPTS.items() if re.search(pat, t)}

def mismatches(ws):
    """Yield (label, column, header, formula) for summary cells whose label names
    a different concept than the single column they aggregate.

    Deliberately narrow. Only plain single-column SUM/AVERAGE qualifies:
      - an expression combining two aggregates (SUM(D)-SUM(E)) computes a derived
        quantity, so its label legitimately names neither column
      - SUMIF's sum-range is a filtered subset, so the label describes the filter
    Catching four of the five real defects with zero false alarms beats catching
    five with four — a checker that cries wolf gets ignored, which is worse than
    no checker at all.
    """
    headers = {}
    for r in range(1, 16):
        filled = [c for c in ws[r] if isinstance(c.value, str) and c.value.strip()
                  and not c.value.startswith('=')]
        if len(filled) >= 4:
            for c in filled:
                headers[c.column_letter] = str(c.value)
    if not headers:
        return
    for row in ws.iter_rows():
        for c in row:
            f = c.value
            if not (isinstance(f, str) and f.startswith('=')):
                continue
            m = re.fullmatch(r'=(SUM|AVERAGE)\(([A-Z])\d+:\2\d+\)', f.strip())
            if not m:
                continue                       # derived / filtered → not checkable
            col = m.group(2)
            head = headers.get(col)
            if not head:
                continue
            label = None
            for cc in row:
                if (cc.column < c.column and isinstance(cc.value, str)
                        and cc.value.strip() and not cc.value.startswith('=')):
                    label = cc.value.strip()
            if not label:
                continue
            lab_c, head_c = concepts_in(label), concepts_in(head)
            # both must name something known, share nothing, and disagree
            if lab_c and head_c and not (lab_c & head_c):
                yield label, col, head, f

# ---------------------------------------------------------------- pages
def check_pages():
    for f in sorted(glob.glob(os.path.join(ROOT, '*', 'index.html'))
                    + glob.glob(os.path.join(ROOT, 'index.html'))):
        rel = os.path.relpath(f, ROOT)
        s = io.open(f, encoding='utf-8', errors='replace').read()
        # A phrase inside <code> is being QUOTED, not claimed. Caught 2026-08-17:
        # a build-log entry describing this very rule quoted "trusted by hundreds
        # of businesses" as the example it must catch, and /log/ then failed the
        # rule over its own documentation. Left alone, the effective policy is
        # "the log may never name the phrases we screen for", which is not the
        # policy anyone wants. Same fix the palette gate took a day earlier, for
        # the same reason: ask the question about the page's CLAIMS, not about
        # its description of a check. FALSE_PROOF itself is untouched, so the 12
        # pinned cases in test_autoqa.py still hold it at full strength.
        claims = CODE_SPAN.sub(' ', s)
        for m in set(FALSE_PROOF.findall(claims)):
            defect('page', '%s implies a client base: %r' % (rel, m))
        for m in set(TRACTION_DRIFT.findall(s)):
            defect('page', '%s traction drift (capacity phrased as customers): %r' % (rel, m))
        # every ld+json block must parse (template-clone trap)
        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                json.loads(blk)
            except Exception:
                defect('page', '%s has invalid ld+json' % rel)
        # conflicting robots directives — a clone leftover. /build-log/ shipped
        # with BOTH "index,follow" (inherited from the page it was cloned from)
        # and the "noindex,follow" that was meant to stage it. Crawlers resolve
        # a conflict to the most restrictive, so it happened to stay staged —
        # but a staging guard that works by luck is not a staging guard.
        robots = re.findall(r'<meta name="robots" content="([^"]*)"', s, re.I)
        if len(robots) > 1:
            defect('page', '%s has %d conflicting robots tags: %s'
                   % (rel, len(robots), ' | '.join(robots)))

        # a published page must not still be noindex while sitemapped
        sm = os.path.join(ROOT, 'sitemap.xml')
        if os.path.exists(sm):
            smtxt = io.open(sm, encoding='utf-8').read()
            # Anchor on the full path segment. Matching a bare "<slug>/" is a
            # substring test, so /log/ matched the sitemap's /build-log/ entry
            # and a correctly-noindexed staging page was reported as a defect --
            # the checker was wrong, not the page. Requiring the leading slash
            # makes "/log/" fail to match "/build-log/" while still matching a
            # genuine "/log/" entry.
            # ...and test for an actual robots directive, not the word appearing
            # anywhere in the file. /log/ publishes entries that DISCUSS noindex
            # work in their prose, so a bare substring search flagged a page
            # carrying zero <meta name="robots"> tags. Same failure as the slug
            # bug above, one layer in: the checker was wrong, not the page. Any
            # page whose body may quote its own markup would have hit this.
            slug = os.path.basename(os.path.dirname(f))
            robots = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*>', s, re.I)
            if slug and '/' + slug + '/' in smtxt and robots and 'noindex' in robots.group(0).lower():
                defect('page', '%s is in sitemap but still noindex' % rel)

# ---------------------------------------------------------------- staleness
def content_digest(path):
    """Hash the sheet content of an xlsx, ignoring docProps/.

    An xlsx is a zip, and openpyxl stamps a fresh created/modified time into
    docProps/core.xml on every write — so a plain byte compare reports every
    rebuilt file as stale even when not one cell changed. That fired on 5 of 8
    demos and would have had me overwrite good copies on a meaningless signal.
    """
    import zipfile, hashlib
    z = zipfile.ZipFile(path)
    names = [n for n in sorted(z.namelist()) if not n.startswith('docProps/')]
    return hashlib.sha256(b''.join(n.encode() + z.read(n) for n in names)).hexdigest()

def check_staleness():
    dl = os.path.join(os.path.expanduser('~'), 'Downloads')
    if not os.path.isdir(dl):
        return
    for f in sorted(glob.glob(os.path.join(ROOT, '*', '*.xlsx'))):
        b = os.path.basename(f)
        d = os.path.join(dl, b)
        if not os.path.exists(d):
            continue
        try:
            if content_digest(f) != content_digest(d):
                defect('stale', 'Downloads/%s differs from the build — sharing it sends the wrong version' % b)
        except Exception as e:
            defect('stale', 'could not compare Downloads/%s: %s' % (b, e))

# ---------------------------------------------------------------- live site
def check_live():
    sm = os.path.join(ROOT, 'sitemap.xml')
    if not os.path.exists(sm):
        return
    urls = re.findall(r'<loc>([^<]+)</loc>', io.open(sm, encoding='utf-8').read())
    for u in urls:
        try:
            out = subprocess.run(['curl', '-s', '-o', os.devnull, '-w', '%{http_code}',
                                  '-A', 'Mozilla/5.0', u],
                                 capture_output=True, text=True, timeout=25).stdout.strip()
        except Exception as e:
            defect('live', 'could not reach %s (%s)' % (u, e)); continue
        if out != '200':
            defect('live', '%s returns %s' % (u, out))

def check_deploy():
    """Is the live site serving the commit we pushed?

    QUESTION: did the last push actually reach the public site?
    BLIND SPOT: it trusts GitHub's build record rather than the served bytes, so
    a CDN handing out stale content after a successful build would slip past.

    check_live above asks whether every URL returns 200, which is a DIFFERENT
    question and cannot answer this one -- a site four commits behind returns
    200 on every page. That exact mistake is already in the workspace notes: an
    HTTP 200 "confirmed" a deploy that the old page was still serving.

    Found 2026-08-17, when a push passed all nine gates, reported success, and
    the site did not change: one Pages build had errored and the next sat in
    'building' for fifteen minutes against a thirty-eight second norm. Nothing
    anywhere would have told anyone. A deploy that silently does not happen is
    the exact failure this company sells against, so it cannot be the one thing
    we leave unwatched.
    """
    try:
        head = subprocess.run(['git', 'rev-parse', 'origin/main'], cwd=ROOT,
                              capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception as e:
        defect('deploy', 'could not read origin/main (%s)' % e)
        return
    if not head:
        defect('deploy', 'could not read origin/main -- cannot verify the deploy')
        return
    try:
        out = subprocess.run(
            ['gh', 'api', 'repos/automatedworkflowllc-design/awllc-website/pages/builds/latest',
             '--jq', '.status + " " + .commit + " " + .updated_at'],
            cwd=ROOT, capture_output=True, text=True, timeout=40).stdout.strip()
    except Exception as e:
        defect('deploy', 'could not reach the Pages build API (%s)' % e)
        return
    parts = out.split()
    if len(parts) != 3:
        defect('deploy', 'Pages build API returned %r -- cannot verify the deploy' % out[:80])
        return
    status, built, when = parts
    if status == 'built' and built == head:
        return

    # NOT serving origin/main. Whether that is a PROBLEM depends on how long it
    # has been true. Learned the hard way on 2026-08-17: two pushes minutes apart
    # left the first build 'errored' in this API purely because the second one
    # superseded it -- the workflow run says 'cancelled'. Reporting that as a
    # failure is crying wolf, and a guard nobody trusts is worse than no guard,
    # which is the lesson the Hearth monitor already paid for. Normal builds here
    # finish in ~40s; the worst legitimate wait observed was ~15 minutes during a
    # GitHub incident. So churn is silent and only a genuinely stuck or failed
    # deploy speaks up.
    try:
        age_min = (datetime.datetime.now(datetime.timezone.utc)
                   - datetime.datetime.fromisoformat(when.replace('Z', '+00:00'))
                   ).total_seconds() / 60.0
    except Exception:
        age_min = 999.0
    if age_min < 30:
        return
    if status != 'built':
        defect('deploy', 'the newest Pages build has been %s for %d minutes (commit %s) -- '
                         'the site is NOT serving what was pushed' % (status, age_min, built[:7]))
    else:
        defect('deploy', 'live site has been serving %s for %d minutes but origin/main is %s -- '
                         'a push did not deploy' % (built[:7], age_min, head[:7]))


# ---------------------------------------------------------------- main
def check_analytics():
    """The measurement split must hold in both directions.

    Two failures are possible and both are silent. A page that promises an empty
    network tab and quietly gains a tag turns published copy -- in emails and in
    LinkedIn posts -- into a false statement. A page that loses its tag goes dark
    without anyone noticing, which is how 32 of 34 pages ended up unmeasured for
    weeks while we argued about whether the problem was reach.

    Source of truth is _brand/apply_analytics.py; this asserts the result.
    """
    sys.path.insert(0, os.path.join(ROOT, '_brand'))
    from apply_analytics import NO_ANALYTICS, pages, GA_ID
    for rel in pages():
        path = os.path.join(ROOT, rel)
        try:
            html = io.open(path, encoding='utf-8').read()
        except Exception as e:
            defect('analytics', '%s unreadable: %s' % (rel, e)); continue
        n = html.count('googletagmanager')
        if rel in NO_ANALYTICS:
            if n:
                defect('analytics',
                       '%s promises an empty network tab but loads a tag -- that '
                       'makes published copy false' % rel)
        elif n == 0:
            defect('analytics', '%s has no analytics tag -- it is invisible' % rel)
        elif n > 1:
            defect('analytics', '%s loads the tag %d times' % (rel, n))
        elif GA_ID not in html:
            defect('analytics', '%s loads a tag but not %s' % (rel, GA_ID))



SURFACE = ('background', 'background-color', 'border', 'border-color')
STATE = (':hover', ':focus', ':active', ':visited', ':disabled')


def _has_surface(decls):
    """Does this declaration block give the element an edge you can see?

    'transparent' is the whole point: the shared .btn base sets
    `border:1px solid transparent` and no background, which is geometry with
    no surface -- so a rule may only count if it names a colour that is not
    transparent. var(), a hex and rgb() all count; none/inherit/initial do not.
    """
    for prop, val in decls:
        if prop not in SURFACE:
            continue
        v = val.lower()
        if 'transparent' in v or 'none' in v:
            continue
        if 'var(' in v or '#' in v or 'rgb' in v or 'hsl' in v:
            return True
    return False


def _rules(css):
    out = []
    css = re.sub(r'/\*.*?\*/', ' ', css, flags=re.S)
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        decls = []
        for d in m.group(2).split(';'):
            if ':' in d:
                p, _, v = d.partition(':')
                decls.append((p.strip().lower(), v.strip()))
        out.append((' '.join(m.group(1).split()), decls))
    return out


def _provides(sel, classes, tag):
    """Conservative selector match, base state only.

    Deliberately PERMISSIVE where it cannot be sure. A selector it cannot parse
    but which mentions .btn is treated as providing a surface, so an unusual
    rule produces a miss rather than a false alarm -- the same trade the compose
    sweep makes. A gate people learn to ignore is worse than a narrow one.
    """
    for alt in sel.split(','):
        alt = alt.strip()
        if any(s in alt for s in STATE):
            continue
        last = re.split(r'[ >+~]', alt)[-1]
        conds = re.findall(r':not\(\[class\*=[\'"]([^\'"]+)[\'"]\]\)', last)
        bare = re.sub(r':not\([^)]*\)', '', last)
        if not re.match(r'^(\w+)?(\.[\w-]+)*$', bare):
            # Unparsed. Assume covered ONLY if the selector actually mentions one
            # of this element's classes. The first version returned True here
            # unconditionally, so `body{background:...}` matched every button and
            # the gate stayed green with the fix deleted -- it could not go red.
            if any('.' + c in alt for c in classes):
                return True
            continue
        want_tag = re.match(r'^(\w+)', bare)
        if want_tag and want_tag.group(1).lower() != tag:
            continue
        need = set(re.findall(r'\.([\w-]+)', bare))
        if not need.issubset(classes):
            continue
        if any(any(c in k for k in classes) for c in conds):
            continue                          # the :not() excludes this element
        return True
    return False


def check_controls():
    """Does any page ship a control with button geometry and no visible surface?

    WHY THIS EXISTS. Measured 2026-08-28: 24 elements across 15 pages carried
    the shared `btn` class with no colour modifier. The base rule gives them
    pill geometry, padding and weight but no background and a TRANSPARENT
    border, so 18 of them computed as bare text and the rest fell back to the
    browser's grey. Four were the "Email these numbers to Colin" link injected
    after a successful run -- the conversion step on four free tools. Eleven
    gates passed all of it, because none of them asks the only question that
    would have caught it: can you see the button?

    BLIND SPOT, stated rather than discovered later. This reads each page's own
    CSS with a small matcher; it cannot resolve a surface inherited from an
    ancestor, and it says nothing about CONTRAST -- a control the same colour as
    its background passes here. It answers "is there a surface at all", which is
    the failure that actually shipped.
    """
    sys.path.insert(0, os.path.join(ROOT, '_brand'))
    from apply_analytics import pages
    # SELF-CONTAINED PAGES DO NOT SHARE THIS SITE'S `btn` SYSTEM, so the whole
    # premise of this check is wrong for them. It assumes bare `.btn` comes
    # from the shared stylesheet, where the base rule supplies geometry and
    # strips the browser's own button surface -- which is exactly why a bare
    # `.btn` there renders as naked text. /dining/ is a generated demo that
    # inlines its OWN complete stylesheet, defines no bare `.btn` rule at all,
    # and therefore keeps the browser default. Verified visually rather than
    # argued: every control on that page was screenshotted rendering with a
    # visible surface before this exemption was written.
    # It must keep earning itself -- if the file stops existing, this fails.
    SELF_CONTAINED = {'dining/index.html'}
    for rel in SELF_CONTAINED:
        if not os.path.exists(os.path.join(ROOT, rel)):
            defect('controls', 'exempt page %s no longer exists -- drop the '
                               'exemption rather than leaving it covering nothing' % rel)
    examined = 0
    for rel in pages():
        if rel.replace('\\', '/') in SELF_CONTAINED:
            continue
        try:
            html = io.open(os.path.join(ROOT, rel), encoding='utf-8').read()
        except Exception as e:
            defect('controls', '%s unreadable: %s' % (rel, e)); continue
        rules = []
        for blk in re.findall(r'<style[^>]*>(.*?)</style>', html, re.S | re.I):
            rules.extend(_rules(blk))
        if not rules:
            continue
        seen = set()
        for m in re.finditer(r'class=["\']([^"\']*)["\']', html):
            classes = set(m.group(1).split())
            if 'btn' not in classes:
                continue
            j = html.rfind('<', 0, m.start())
            t = re.match(r'<(\w+)', html[j:])
            tag = t.group(1).lower() if t else 'a'
            key = (tuple(sorted(classes)), tag)
            if key in seen:
                continue
            seen.add(key)
            examined += 1
            if not any(_provides(s, classes, tag) and _has_surface(d)
                       for s, d in rules):
                defect('controls',
                       '%s: <%s class="%s"> has button geometry but no visible '
                       'surface -- it renders as bare text'
                       % (rel, tag, ' '.join(sorted(classes))))
    # Extraction control. "No defects" and "looked at nothing" print the same
    # way, and this check depends on two things that move independently: the
    # page list, and `btn` still being the shared button class. If a rename ever
    # empties this, it must be loud rather than green. 30-odd controls is the
    # standing figure; anything near zero means the check has stopped looking.
    if examined < 10:
        defect('controls',
               'examined only %d control(s) site-wide -- this check has stopped '
               'finding buttons, so its green result means nothing' % examined)


def main():
    # --fast skips the network sweep. Used by the pre-push hook, where the live
    # site is still the OLD build and so tells you nothing about what you're
    # about to ship.
    checks = [check_workbooks, check_pages, check_staleness, check_analytics,
              check_controls]
    if '--fast' not in sys.argv:
        # Both need the network, so both stay out of the push gate -- and
        # check_deploy would be meaningless there anyway, since the deploy it
        # asks about happens AFTER the push it would be gating.
        checks.append(check_live)
        checks.append(check_deploy)
    for fn in checks:
        try:
            fn()
        except Exception as e:
            defect('runner', '%s crashed: %s' % (fn.__name__, e))

    score = len(defects)
    mode = 'fast' if '--fast' in sys.argv else 'full'
    hist = []
    if os.path.exists(HIST):
        try: hist = json.load(io.open(HIST, encoding='utf-8'))
        except Exception: hist = []
    # compare like with like — a fast run inspects fewer surfaces, so scoring it
    # against a full run would read as an improvement that never happened
    same = [h for h in hist if h.get('mode', 'full') == mode]
    prev = same[-1]['score'] if same else None
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    # THE BASELINE MOVES ONLY WHEN ASKED, AND ONLY DOWNWARD-OR-FLAT.
    # Same defect and same fix as seo_audit.py -- see the long note there. In
    # short: writing unconditionally let the gate launder its own failures, because
    # running it twice with nothing fixed turned the first run's defect count into
    # the baseline and the second run exited 0. The nightly public-log job runs
    # this, so it happened by itself. --record is now required to move the
    # baseline, and a regressed run never records.
    regressed = prev is not None and score > prev
    if '--record' in sys.argv and not regressed:
        hist.append({'when': stamp, 'mode': mode, 'score': score,
                     'by_area': {a: sum(1 for d in defects if d['area'] == a)
                                 for a in {d['area'] for d in defects}}})
        os.makedirs(os.path.dirname(HIST), exist_ok=True)
        io.open(HIST, 'w', encoding='utf-8').write(json.dumps(hist[-60:], indent=1))

    if '--json' in sys.argv:
        print(json.dumps({'score': score, 'prev': prev, 'defects': defects}, indent=1))
    else:
        print('AutoQA %s  —  defects: %s%s' % (
            stamp, score,
            '' if prev is None else '  (previous: %s)' % prev))
        for d in defects:
            print('  [%-8s] %s' % (d['area'], d['msg']))
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
