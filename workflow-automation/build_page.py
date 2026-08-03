# -*- coding: utf-8 -*-
"""Build /workflow-automation/ (STAGED, noindex) -- the flagship page.

v3.0 (2026-08-03). Reconciles three specs: AWLLC-flagship-tech / -design / -copy
(2026-08-03). Architecture, gates and budgets from the tech spec; layout and the
visual system from the design spec; every user-visible word from the copy spec
(transcribed into _copy.py, never parsed at build time).

WHAT CHANGED vs v2.1
  * REPO path bug fixed -- the builder now writes the checkout it lives in
    (v2.1 hardcoded ~/Documents/awllc-website and silently regenerated the OTHER
    clone whichever one you ran it from).
  * Whole-document string surgery replaced with SHELL EXTRACTION (the house
    pattern from build_health_check.py / build_money_leak_page.py): take
    s[:'</header>'] and the <footer> block, compose the middle here. Removal is a
    blacklist and inherits whatever the source page grows next; extraction is a
    whitelist. All three of the Pulse page's ld+json blocks sit AFTER </footer>,
    so this eliminates the schema inheritance by construction.
  * Sections are composable Blocks (_components.py). The id-uniqueness and
    invented-label gates now DERIVE from the section list instead of a hardcoded
    list, so a widget added tomorrow cannot escape them.
  * Every colour comes from _brand/awllc_brand.py. G-BRAND blocks a new hex.
  * The four body webfonts the page declared but never loaded are now embedded,
    lifted from the homepage's own @font-face blocks -- no network, no new asset.

Idempotent: rebuilds the output from source every run. Nothing here may read the
clock, iterate a set, or reach the network.
Run:  python workflow-automation/build_page.py [--check-sources]
"""
import io, os, re, sys, gzip, csv, pathlib, hashlib, datetime

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent                      # <- the checkout THIS file lives in (D1 fix)
sys.path.insert(0, str(ROOT / '_brand'))
sys.path.insert(0, str(HERE))
import awllc_brand as B                                          # noqa: E402
import _copy as C                                                # noqa: E402
from _components import (Block, SCALE, TIERS, tier_for, root_css,  # noqa: E402
                         PAGE_CSS, page_js)

SHELL_SRC = ROOT / 'ai-business-pulse' / 'index.html'
FONT_SRC = ROOT / 'index.html'          # the homepage carries every family we need
LEAK_SRC = ROOT / '_brand' / 'build_money_leak_page.py'
OUT = HERE / 'index.html'

# ---------------------------------------------------------------- brand tokens
T = {'ink': B.INK, 'ink_soft': B.INK_SOFT, 'ink_faint': B.INK_FAINT,
     'line': B.LINE, 'line_strong': B.LINE_STRONG,
     'paper': B.PAPER, 'paper_tint': B.PAPER_TINT, 'well': B.WELL,
     'green': B.GREEN, 'amber': B.AMBER, 'red': B.RED,
     'green_bg': B.GREEN_BG, 'amber_bg': B.AMBER_BG, 'red_bg': B.RED_BG}
ALLOWED = {v.upper() for v in T.values()} | {c.upper() for c in B.RAINBOW}
# rainbow hues legible on the one dark surface (GREEN/RED are too dark on --ink)
RAIN_G, RAIN_R = B.RAINBOW[3], B.RAINBOW[0]

TIER_CLASS = {'green': 'gc-green', 'amber': 'gc-amber', 'red': 'gc-red', 'quiet': 'gc-quiet'}


def esc_js(s):
    """A python string -> a JS string literal (single-quoted, escaped)."""
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ') + "'"


# ================================================================ SECTIONS
def sec_hero(k=C.HERO):
    prim, prim_h = k['cta_primary']
    ghost, ghost_h = k['cta_ghost']
    html = (
        '<section class="hero wide no-rv" id="top">\n'
        '  <div class="hero-grid">\n'
        '    <div>\n'
        '      <p class="eyebrow green"><span class="idx">01</span>' + k['eyebrow'] + '</p>\n'
        '      <h1>' + k['h1_a'] + ' <span class="serif-i">' + k['h1_b'] + '</span></h1>\n'
        '      <p class="subhead">' + k['subhead'] + '</p>\n'
        '      <div class="hero-actions">\n'
        '        <a class="btn btn-primary" href="' + prim_h + '">' + prim + '</a>\n'
        '        <a class="btn btn-ghost" href="' + ghost_h + '">' + ghost + '</a>\n'
        '      </div>\n'
        '      <p class="hero-meta">' + k['meta'] + '</p>\n'
        '    </div>\n'
        '    <aside class="hero-teaser" aria-label="Diagram: work flows through read, compute and '
        'draft, then stops at a human gate">\n'
        '      <div class="ht-rail">\n'
        '        <div class="ht-node"><span class="n">01</span><span class="t">READ</span></div>\n'
        '        <div class="ht-node"><span class="n">02</span><span class="t">COMPUTE</span></div>\n'
        '        <div class="ht-node"><span class="n">03</span><span class="t">DRAFT</span></div>\n'
        '        <div class="ht-node ht-gate"><span class="n">&#9632;</span><span class="t">THE GATE</span></div>\n'
        '        <div class="ht-node ht-dim"><span class="n">04</span><span class="t">SEND</span></div>\n'
        '      </div>\n'
        '      <p class="ht-cap">' + k['teaser_cap'] + ' &middot; '
        '<a href="#gate">' + k['teaser_link'] + '</a></p>\n'
        '    </aside>\n'
        '  </div>\n'
        '</section>')
    return Block(html=html, ids=('top',), needs=(k['h1_a'], k['h1_b']))


def _queue_cards():
    """Cards, pills, left rules, drafts and the counts all derive from tier_for()."""
    out, ids = [], []
    for i, inv in enumerate(C.INVOICES, 1):
        _, cls, label, colour = tier_for(inv['days'])
        did = 'gcDraft%d' % i
        ids.append(did)
        pill = ('<span class="gc-pill %s">%d days &middot; %s</span>'
                % (TIER_CLASS[colour], inv['days'], label))
        approvable = cls != 'silence'
        ctrl = ('<button class="gc-btn" type="button" aria-pressed="false" aria-describedby="%s">Approve</button>' % did
                if approvable else '<span class="gc-held">waits</span>')
        out.append(
            '        <div class="gc-card" data-tier="' + cls + '" data-ref="' + inv['ref'] + '">\n'
            '          <div class="gc-info"><span class="gc-inv">' + inv['ref'] + ' &middot; '
            + inv['who'] + ' &middot; $' + inv['amt'] + '</span>' + pill + '\n'
            '            <p class="gc-draft" id="' + did + '">' + inv['draft'] + '</p>\n'
            '            <details class="gc-why"><summary>Why this tone?</summary><p>'
            + inv['why'] + '</p></details>\n'
            '          </div>\n'
            '          ' + ctrl + '\n'
            '        </div>')
    return '\n'.join(out), tuple(ids)


def sec_gate(k=C.GATE):
    cards, card_ids = _queue_cards()
    approvable = [i for i in C.INVOICES if tier_for(i['days'])[1] != 'silence']
    silent = len(C.INVOICES) - len(approvable)
    legend = ''.join(
        '<span class="gc-pill %s">%s &middot; %s</span>'
        % (TIER_CLASS[col], ('under 15 days' if lo == 0 else '%d+' % lo), label)
        for lo, cls, label, col in sorted(TIERS, key=lambda t: t[0]))
    html = (
        '<section class="block wide" id="gate">\n'
        '  <p class="eyebrow green"><span class="idx">02</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['intro'] + '</p>\n'
        '  <div class="gc gc-wrap" id="gcWrap" role="group" aria-label="Interactive demo: drafted '
        'follow-up emails wait at a human gate">\n'
        '    <div class="gc-rail" id="gcRail">\n'
        '      <div class="gc-node" data-n="01"><span class="gc-t">READ</span><span class="gc-d">your live numbers</span></div>\n'
        '      <div class="gc-seg"><span class="gc-dot gc-dot-a" aria-hidden="true"></span></div>\n'
        '      <div class="gc-node" data-n="02"><span class="gc-t">COMPUTE</span><span class="gc-d">math by formula</span></div>\n'
        '      <div class="gc-seg"><span class="gc-dot gc-dot-b" aria-hidden="true"></span></div>\n'
        '      <div class="gc-node" data-n="03"><span class="gc-t">DRAFT</span><span class="gc-d">words by AI</span></div>\n'
        '      <div class="gc-seg"><span class="gc-dot gc-dot-c" aria-hidden="true"></span></div>\n'
        '      <div class="gc-node gc-gate"><span class="gc-t">THE GATE</span>'
        '<span class="gc-d" id="gcGateD">waiting on you</span></div>\n'
        '      <div class="gc-seg"><span class="gc-dot gc-dot-d" aria-hidden="true"></span></div>\n'
        '      <div class="gc-node" data-n="04"><span class="gc-t">SEND</span><span class="gc-d">their inbox</span></div>\n'
        '    </div>\n'
        '    <p class="gc-railcap">' + k['rail_cap'] + '</p>\n'
        '    <p class="nojs-note">' + k['nojs'] + '</p>\n'
        '    <div class="gc-cols">\n'
        '      <div>\n'
        '        <div class="gc-legend" role="group" aria-label="Tone tiers by invoice age">' + legend + '</div>\n'
        '        <div id="gcQueue">\n' + cards + '\n        </div>\n'
        '      </div>\n'
        '      <div>\n'
        '        <p class="mono-lab gc-logh">' + k['ledger_head'] + '</p>\n'
        '        <ol class="gc-log" id="gcLedger" aria-live="polite" aria-atomic="false"></ol>\n'
        '        <p class="gc-logn">' + k['ledger_note'] + '</p>\n'
        '      </div>\n'
        '    </div>\n'
        '    <div class="gc-foot">\n'
        '      <div class="gc-ctrls">\n'
        '        <label class="gc-toggle"><input type="checkbox" id="gcToggle">'
        '<span class="gc-slider" aria-hidden="true"></span><span>' + k['toggle'] + '</span></label>\n'
        '        <span class="gc-status" id="gcStatus" role="status" aria-live="polite">'
        + k['status_wait'] + '</span>\n'
        '      </div>\n'
        '      <div class="gc-ctrls">\n'
        '        <span class="data" id="gcCount" role="status">0 of ' + str(len(approvable))
        + ' approved &middot; ' + str(silent) + ' held in silence</span>\n'
        '        <button class="gc-reset" id="gcReset" type="button">' + k['reset'] + '</button>\n'
        '        <button class="btn btn-primary gc-send" id="gcSend" type="button" disabled>'
        + k['send'] + '</button>\n'
        '      </div>\n'
        '    </div>\n'
        '    <div class="gc-outcome" id="gcOutcome" role="status" aria-live="polite">\n'
        '      <p class="gc-outcome-head" id="gcOutcomeHead"></p>\n'
        '      <p class="gc-outcome-body">' + k['outcome_body'] + '</p>\n'
        '    </div>\n'
        '  </div>\n'
        '  <p class="gc-cap">' + k['caption'] + '</p>\n'
        '</section>')
    ids = ('gate', 'gcWrap', 'gcRail', 'gcQueue', 'gcLedger', 'gcToggle', 'gcSend', 'gcReset',
           'gcOutcome', 'gcOutcomeHead', 'gcStatus', 'gcCount', 'gcGateD') + card_ids
    needs = ('every number and business name invented',
             '0 of %d approved &middot; %d held in silence' % (len(approvable), silent))
    return Block(html=html, ids=ids, needs=needs)


def sec_problem(k=C.PROBLEM):
    html = (
        '<section class="block">\n'
        '  <p class="eyebrow"><span class="idx">03</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['p1'] + '</p>\n'
        '  <p class="lead-line">' + k['lead'] + '</p>\n'
        '  <p>' + k['p2'] + '</p>\n'
        '  <div class="pullquote"><p>' + k['pull'] + '</p></div>\n'
        '  <p class="statement">' + k['bridge'] + '</p>\n'
        '</section>')
    return Block(html=html, needs=(k['lead'],))


def sec_method(k=C.METHOD):
    rows = []
    for L in k['layers']:
        back = ('\n      <a class="ms-back" href="#gate">' + k['gate_backref_off'] + '</a>'
                if L['n'] == '04' else '')
        rows.append(
            '    <details class="ms-layer' + (' ms-spine' if L['spine'] else '') + '">\n'
            '      <summary><span class="ms-n">' + L['n'] + '</span>'
            '<span class="ms-name">' + L['name'] + '</span>'
            '<span class="ms-rule">' + L['rule'] + '</span></summary>\n'
            '      <div class="ms-body"><p>' + L['body'] + '</p>' + back + '</div>\n'
            '    </details>')
    html = (
        '<section class="block wide" id="method">\n'
        '  <p class="eyebrow"><span class="idx">04</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['intro'] + '</p>\n'
        '  <div class="ms">\n' + '\n'.join(rows) + '\n  </div>\n'
        '  <div class="pullquote"><p>' + k['pull'] + '</p></div>\n'
        '</section>')
    return Block(html=html, ids=('method',), needs=(k['layers'][1]['rule'],))


def sec_bench(k=C.BENCH):
    cards = []
    for t in k['tools']:
        cards.append(
            '    <article class="rk-card">\n'
            '      <span class="rk-chip">Nothing uploads</span>\n'
            '      <h3><a href="' + t['url'] + '">' + t['name'] + '</a></h3>\n'
            '      <p class="rk-what">' + t['what'] + '</p>\n'
            '      <p class="rk-proof">' + t['proof'] + '</p>\n'
            '    </article>')
    sample = '\n'.join(k['sample'])
    html = (
        '<section class="block wide" id="bench">\n'
        '  <p class="eyebrow green"><span class="idx">05</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['intro'] + '</p>\n'
        '  <div class="bn">\n'
        '    <h3>' + k['tool_h3'] + '</h3>\n'
        '    <p class="rk-what">' + k['tool_intro'] + '</p>\n'
        '    <label class="mono-lab" for="bnIn">Customer or vendor list</label>\n'
        '    <textarea id="bnIn" rows="7" spellcheck="false">' + sample + '</textarea>\n'
        '    <p class="mono-lab bn-note">' + k['tool_note'] + '</p>\n'
        '    <div class="bn-acts">\n'
        '      <button id="bnRun" type="button">' + k['tool_run'] + '</button>\n'
        '      <button id="bnClear" class="ghost" type="button">' + k['tool_clear'] + '</button>\n'
        '    </div>\n'
        '    <div class="bn-out" id="bnOut" role="status" aria-live="polite"></div>\n'
        '    <p class="bn-receipts" id="receipts">third-party requests: measured on load</p>\n'
        '    <p class="nojs-note">' + k['nojs'] + '</p>\n'
        '    <p class="bn-after">' + k['tool_after'] + '</p>\n'
        '  </div>\n'
        '  <div class="rk">\n' + '\n'.join(cards) + '\n  </div>\n'
        '  <p class="bn-after">' + k['all_builds'] + '</p>\n'
        '  <p class="statement">' + k['closing'] + '</p>\n'
        '</section>')
    return Block(html=html, ids=('bench', 'bnIn', 'bnRun', 'bnClear', 'bnOut', 'receipts'),
                 needs=(k['tool_note'], '/money-leak-finder/', '/spreadsheet-health-check/',
                        '/duplicate-customer-finder/', '/shift-coverage-check/', '/builds/'))


def sec_dashboard(k=C.DASH):
    label, href = k['cta']
    html = (
        '<section class="block">\n'
        '  <p class="eyebrow"><span class="idx">06</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['p1'] + '</p>\n'
        '  <p>' + k['p2'] + '</p>\n'
        '  <p>' + k['p3'] + '</p>\n'
        '  <div class="hero-actions"><a class="btn btn-ghost" href="' + href + '">' + label + '</a></div>\n'
        '</section>')
    return Block(html=html, needs=('/demo/',))


def sec_report(k=C.REPORT):
    kpis = ''.join('<span class="tw-kpi"><b>%s</b> %s</span>' % (a, b) for a, b in k['kpis'])
    html = (
        '<section class="block wide">\n'
        '  <p class="eyebrow"><span class="idx">07</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <div class="tw-panel" id="twPanel" role="group" aria-label="Demo: the Monday narrative '
        'types itself over an invented sample">\n'
        '    <div class="tw-kpis">' + kpis
        + '<span class="tw-note">' + k['kpi_note'] + '</span></div>\n'
        '    <p class="tw-out"><span id="twText">' + k['narrative'] + '</span>'
        '<span class="tw-caret tw-done" id="twCaret" aria-hidden="true"></span></p>\n'
        '    <div class="tw-acts"><button id="twRun" type="button">' + k['run'] + '</button></div>\n'
        '    <p class="tw-cap">' + k['caption'] + '</p>\n'
        '  </div>\n'
        '  <figure class="pulse-demo">\n'
        '    <figcaption class="pulse-demo-cap"><span aria-hidden="true">//</span> '
        + k['video_cap'] + '</figcaption>\n'
        '    <video src="/ai-business-pulse-demo.mp4" poster="/ai-business-pulse-thumb.jpg" controls '
        'muted loop playsinline preload="none" width="900" height="675" aria-label="'
        + k['video_aria'] + '"></video>\n'
        '  </figure>\n'
        '</section>')
    return Block(html=html, ids=('twPanel', 'twText', 'twCaret', 'twRun'),
                 needs=(k['kpi_note'], '+47%', '38 &rarr; 61'))


def sec_leak(k=C.LEAK, figs=None):
    label, href = k['cta']
    steps = []
    for i, s in enumerate(k['steps']):
        steps.append(
            '    <details class="ml-step"' + (' open' if i == 0 else '') + '>\n'
            '      <summary>' + s['t'] + '</summary>\n'
            '      <div class="b">' + s['b'] + '</div>\n'
            '    </details>')
    html = (
        '<section class="block wide">\n'
        '  <p class="eyebrow"><span class="idx">08</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['intro'] + '</p>\n'
        '  <div class="ml">\n' + '\n'.join(steps) + '\n  </div>\n'
        '  <p class="ml-label">' + k['label'] + '</p>\n'
        '  <div class="hero-actions" style="margin-top:1.2rem">'
        '<a class="btn btn-ghost" href="' + href + '">' + label + '</a></div>\n'
        '</section>')
    return Block(html=html, needs=('$1,280', '$5,430', '$705', '3 jobs', '6 invoices',
                                   'Cedar Field Services is an invented company'))


def sec_engineering(k=C.ENG):
    items = ''.join(
        '  <h3>' + it['h'] + '</h3>\n  <p>' + it['b'] + '</p>\n' for it in k['items'])
    html = (
        '<section class="block">\n'
        '  <p class="eyebrow"><span class="idx">09</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['intro'] + '</p>\n' + items +
        '  <div class="pullquote"><p>' + k['pull'] + '</p></div>\n'
        '</section>')
    return Block(html=html, needs=('/build-log/',))


CHIP_CLASS = {'LIVE': 'wl-live', 'BUILDING': 'wl-building', 'DESIGNED': 'wl-designed'}


def sec_workflows(k=C.WORKFLOWS):
    rows = []
    for w in k['rows']:
        note = ('\n      <p class="wl-note">' + w['note'] + '</p>') if w['note'] else ''
        rows.append(
            '    <div class="wl-row">\n'
            '      <span class="wl-id">' + w['id'] + '</span>\n'
            '      <div><h3 class="wl-name">' + w['name'] + '</h3>\n'
            '      <p class="wl-what">' + w['what'] + '</p>' + note + '</div>\n'
            '      <div class="wl-side"><span class="wl-price">' + w['price'] + '</span>'
            '<span class="wl-chip ' + CHIP_CLASS[w['status']] + '">' + w['status'] + '</span></div>\n'
            '    </div>')
    label, href = k['cta']
    html = (
        '<section class="block wide">\n'
        '  <p class="eyebrow"><span class="idx">10</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['intro'] + '</p>\n'
        '  <div class="wl">\n' + '\n'.join(rows) + '\n  </div>\n'
        '  <p class="wl-honest">' + k['honesty'] + '</p>\n'
        '  <p class="wl-honest">' + k['closing'] + '</p>\n'
        '  <div class="hero-actions"><a class="btn btn-ghost" href="' + href + '">' + label + '</a></div>\n'
        '</section>')
    return Block(html=html, needs=tuple(w['status'] for w in k['rows']))


def sec_templates(k=C.TEMPLATES):
    html = (
        '<section class="block">\n'
        '  <p class="eyebrow"><span class="idx">11</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['intro'] + '</p>\n'
        '</section>')
    return Block(html=html)


def sec_pricing(k=C.PRICING):
    steps = []
    n = len(k['steps'])
    for i, s in enumerate(k['steps']):
        cls = 'pr-step pr-free' if i == 0 else 'pr-step'
        cta = ('\n        <a class="pr-cta" href="/free-demo/">Start here &mdash; free &rarr;</a>'
               if i == 0 else '\n        <a class="pr-cta" href="/free-demo/">Starts with the free demo &rarr;</a>')
        steps.append(
            '    <div class="' + cls + '" style="--i:' + str(n - 1 - i) + '">\n'
            '      <div class="pr-in">\n'
            '        <span class="pr-num">' + s['price'] + '</span>\n'
            '        <div><h3 class="pr-name">' + s['name'] + '</h3>\n'
            '        <p class="pr-body">' + s['body'] + '</p>' + cta + '</div>\n'
            '      </div>\n'
            '    </div>')
    html = (
        '<section class="block wide" id="prices">\n'
        '  <p class="eyebrow"><span class="idx">12</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <div class="pr">\n' + '\n'.join(steps) + '\n  </div>\n'
        '  <p class="pr-under">' + k['under'] + '</p>\n'
        '</section>')
    return Block(html=html, ids=('prices',), needs=('$500&ndash;750', '$300', '$650', 'From $2,000'))


def sec_who(k=C.WHO):
    can = ''.join('<li><span class="m">&#10003;</span><span>' + x + '</span></li>' for x in k['can'])
    wont = ''.join('<li><span class="m">&#10007;</span><span>' + x + '</span></li>' for x in k['wont'])
    html = (
        '<section class="block wide">\n'
        '  <p class="eyebrow"><span class="idx">13</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['p1'] + '</p>\n'
        '  <p>' + k['p2'] + '</p>\n'
        '  <p>' + k['p3'] + '</p>\n'
        '  <div class="hl">\n'
        '    <h3>' + k['ledger_head'] + '</h3>\n'
        '    <div class="hl-cols">\n'
        '      <div class="hl-col hl-can"><h4>What I can prove</h4><ul>' + can + '</ul></div>\n'
        '      <div class="hl-col hl-wont"><h4>What I will not claim</h4><ul>' + wont + '</ul></div>\n'
        '    </div>\n'
        '    <p class="hl-line">' + k['ledger_line'] + '</p>\n'
        '  </div>\n'
        '</section>')
    return Block(html=html, needs=('zero paying customers',))


def sec_faq(k=C.FAQ):
    qs = ''.join(
        '    <details class="qa"><summary>' + q + '</summary><div class="a">' + a + '</div></details>\n'
        for q, a in k['qs'])
    html = (
        '<section class="block">\n'
        '  <p class="eyebrow"><span class="idx">14</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <div class="faq">\n' + qs + '  </div>\n'
        '</section>')
    return Block(html=html)


def sec_cta(k=C.CTA):
    p_label, p_href = k['primary']
    g_label, g_href = k['ghost']
    html = (
        '<section class="cta-band block no-rv">\n'
        '  <p class="eyebrow"><span class="idx">15</span>' + k['eyebrow'] + '</p>\n'
        '  <h2>' + k['h2'] + '</h2>\n'
        '  <p>' + k['p'] + '</p>\n'
        '  <div class="hero-actions" style="justify-content:center">\n'
        '    <a class="btn btn-primary" href="' + p_href + '">' + p_label + '</a>\n'
        '    <a class="btn btn-ghost" href="' + g_href + '">' + g_label + '</a>\n'
        '  </div>\n'
        '  <p class="cta-sub">' + k['sub'] + '</p>\n'
        '  <p class="cta-nap">' + k['nap'] + '</p>\n'
        '</section>')
    return Block(html=html, needs=(k['nap'],))


SECTIONS = [sec_hero, sec_gate, sec_problem, sec_method, sec_bench, sec_dashboard,
            sec_report, sec_leak, sec_engineering, sec_workflows, sec_templates,
            sec_pricing, sec_who, sec_faq, sec_cta]


# ================================================================ shell
def extract_shell(src):
    s = io.open(src, encoding='utf-8').read()
    head = s[:s.index('</header>') + len('</header>')]
    foot = s[s.index('<footer'):s.index('</footer>') + len('</footer>')]
    return head, foot


def rewrite_head(head):
    h = C.HEAD
    head = head.replace('<html lang="en" data-theme="light">',
                        '<html lang="en" data-theme="light" class="no-js">')
    head = re.sub(r'<title>.*?</title>', '<title>' + h['title'] + '</title>', head, count=1, flags=re.S)
    head = re.sub(r'<meta name="robots" content="[^"]*">',
                  '<meta name="robots" content="noindex,nofollow">\n'
                  '<!-- STAGED on purpose: awaiting Colin\'s copy review before publish (standing rule '
                  'for new pages). When he approves: flip to index,follow + add to sitemap.xml + '
                  'llms.txt + link from the homepage, as its own commit. -->', head, count=1)
    head = re.sub(r'<meta name="description" content="[^"]*"',
                  '<meta name="description" content="' + h['description'] + '"', head, count=1)
    head = re.sub(r'<meta property="og:title" content="[^"]*"',
                  '<meta property="og:title" content="' + h['og_title'] + '"', head, count=1)
    head = re.sub(r'<meta property="og:description" content="[^"]*"',
                  '<meta property="og:description" content="' + h['description'] + '"', head, count=1)
    head = re.sub(r'<link rel="canonical" href="[^"]*"',
                  '<link rel="canonical" href="' + h['canonical'] + '"', head, count=1)
    head = re.sub(r'<meta property="og:url" content="[^"]*"',
                  '<meta property="og:url" content="' + h['canonical'] + '"', head, count=1)
    # the Pulse thumbnail is 900x675 (1.33) and page-specific; the site's own card is 1200x630
    head = re.sub(r'<meta property="og:image" content="[^"]*"',
                  '<meta property="og:image" content="https://automatedworkflowllc.com/og-image.png"', head, count=1)
    head = re.sub(r'<meta property="og:image:width" content="[^"]*"',
                  '<meta property="og:image:width" content="1200"', head, count=1)
    head = re.sub(r'<meta property="og:image:height" content="[^"]*"',
                  '<meta property="og:image:height" content="630"', head, count=1)
    head = re.sub(r'<meta property="og:image:alt" content="[^"]*"',
                  '<meta property="og:image:alt" content="Automated Workflow &mdash; workflow '
                  'automation with a human approve button"', head, count=1)
    # header chrome: the inherited CTA is the Pulse offer and points at a rung page
    nav = ''.join('<a href="%s">%s</a>' % (href, label) for label, href in C.HEADER['nav'])
    cta_label, cta_href = C.HEADER['cta']
    head = re.sub(r'<a class="header-cta"[^>]*>.*?</a>',
                  '<nav class="hdr-nav" aria-label="On this page">' + nav + '</nav>\n'
                  '    <a class="header-cta" href="' + cta_href + '">' + cta_label + '</a>',
                  head, count=1, flags=re.S)
    # skip link + the no-js flag, removed before first paint
    head = head.replace('<body>',
                        '<body>\n<script>document.documentElement.classList.remove(\'no-js\');</script>\n'
                        '<a class="skip" href="#main">' + C.HEADER['skip'] + '</a>', 1)
    return head


def build_footer(head):
    """This page owns its footer: the {a_w} lockup (not the retired rainbow ring),
    plus the homepage's free-tools row, which is this page's best credibility asset."""
    logo = re.search(r'<svg class="brand-logo".*?</svg>', head, re.S).group(0)
    logo = (logo.replace('class="brand-logo"', 'class="fbrand-logo"')
                .replace('awl-g', 'awl-g-f').replace('awl-clip', 'awl-clip-f')
                .replace('aria-label="automated_workflow"', 'aria-label="Automated Workflow"'))
    return (
        '<footer class="site-footer">\n'
        '  <div class="wrap footer-in">\n'
        '    <span class="fbrand"><span class="fbrand-row">' + logo + '</span></span>\n'
        '    <nav class="footer-links" aria-label="Footer">\n'
        '      <a href="/">Home</a>\n'
        '      <a href="/demo/">Live demo</a>\n'
        '      <a href="/builds/">Builds</a>\n'
        '      <a href="/build-log/">Build log</a>\n'
        '      <a href="/ai-business-pulse/">AI Business Pulse</a>\n'
        '      <a href="/free-demo/">Free demo</a>\n'
        '      <a href="mailto:colin@automatedworkflowllc.com">colin@automatedworkflowllc.com</a>\n'
        '      <a href="tel:+17039391174">(703) 939-1174</a>\n'
        '      <a href="https://www.linkedin.com/in/colin-mccarthy-548772423" rel="me">LinkedIn</a>\n'
        '    </nav>\n'
        '    <nav class="footer-links footer-free" aria-label="Free tools and templates">\n'
        '      <span class="footer-free-label">Free tools &amp; templates</span>\n'
        '      <a href="/check/">Business file check</a>\n'
        '      <a href="/spreadsheet-health-check/">Spreadsheet health check</a>\n'
        '      <a href="/money-leak-finder/">Money leak finder</a>\n'
        '      <a href="/duplicate-customer-finder/">Duplicate customer finder</a>\n'
        '      <a href="/shift-coverage-check/">Shift coverage check</a>\n'
        '      <a href="/free/executive-kpi-dashboard.html">KPI dashboard</a>\n'
        '      <a href="/free-expense-tracker-template/">Expense tracker</a>\n'
        '      <a href="/free-staffing-commission-tracker/">Staffing &amp; commission tracker</a>\n'
        '    </nav>\n'
        '    <span class="footer-bar" aria-hidden="true"></span>\n'
        '    <span>&copy; <span id="yr">2026</span> Automated Workflow &middot; Gainesville, FL</span>\n'
        '  </div>\n'
        '</footer>')


def extract_fonts():
    """The page declared Geist / Geist Mono / Newsreader for months and loaded none of
    them, so every visitor saw system fallbacks on the flagship. Lift the blocks from
    the homepage -- same repo, same bytes, no network, one copy to maintain."""
    s = io.open(FONT_SRC, encoding='utf-8').read()
    want = [('Geist', 'normal'), ('Geist Mono', 'normal'),
            ('Schibsted Grotesk', 'normal'), ('Newsreader', 'italic')]
    out = []
    for fam, style in want:
        got = None
        for blk in re.findall(r'@font-face\{[^}]*\}', s):
            if ("font-family:'%s'" % fam) not in blk:
                continue
            is_italic = 'font-style:italic' in blk
            if (style == 'italic') == is_italic:
                got = blk
                break
        assert got, 'font not found in %s: %s %s' % (FONT_SRC.name, fam, style)
        out.append(got)
    return '\n'.join(out)


# ================================================================ G-LEAK
def _js_string(src, name):
    m = re.search(r"var %s = (.*?);\n" % name, src, re.S)
    assert m, 'sample constant not found: ' + name
    return ''.join(re.findall(r"'((?:[^'\\]|\\.)*)'", m.group(1))).replace('\\n', '\n')


def _rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def reconcile_cedar_field():
    src = io.open(LEAK_SRC, encoding='utf-8').read()
    work = _rows(_js_string(src, 'SAMPLE_WORK'))
    inv = _rows(_js_string(src, 'SAMPLE_INV'))
    asof = datetime.date(2026, 7, 28)
    billed = {r['Job No'] for r in inv}
    never = [r for r in work if r['Job No'] not in billed]
    unpaid = [r for r in inv if not (r.get('Paid Date') or '').strip()]
    aged = [r for r in unpaid
            if (asof - datetime.date(*map(int, r['Invoice Date'].split('-')))).days > 60]
    money = lambda rs: sum(float(r['Amount']) for r in rs)      # noqa: E731
    return (len(never), money(never)), (len(unpaid), money(unpaid)), money(aged)


# ================================================================ compose
def compose():
    blocks = [fn() for fn in SECTIONS]
    html = '\n\n'.join(b.html for b in blocks)
    css = '\n'.join(b.css for b in blocks)
    js = '\n'.join(b.js for b in blocks)
    ids = [i for b in blocks for i in b.ids]
    needs = [n for b in blocks for n in b.needs]
    return blocks, html, css, js, ids, needs


def main():
    head, _shell_footer = extract_shell(SHELL_SRC)
    head = rewrite_head(head)
    footer = build_footer(head)

    blocks, sections_html, block_css, block_js, ids, needs = compose()

    # exactly ONE wrapper, emitted here and never by a section (R1)
    main_html = ('<main id="main">\n  <div class="wrap">\n' + sections_html + '\n  </div>\n</main>')

    authored_css = (root_css(dict(T, rain_g=RAIN_G, rain_r=RAIN_R)) + PAGE_CSS + block_css)
    js = page_js({
        'approvable': len([i for i in C.INVOICES if tier_for(i['days'])[1] != 'silence']),
        'silent': len([i for i in C.INVOICES if tier_for(i['days'])[1] == 'silence']),
        'status_open': esc_js(C.GATE['status_open']),
        'status_wait': esc_js(C.GATE['status_wait']),
        'backref_on': esc_js(C.METHOD['gate_backref_on']),
    }) + block_js

    # the stylesheet belongs in the head -- a 200KB+ <style> after the footer means the
    # page paints once on the shell's CSS and then again on this one
    fonts = extract_fonts()
    head = head.replace('</head>', '<style>\n' + fonts + '\n' + authored_css + '\n</style>\n</head>', 1)
    page = (head + '\n\n' + main_html + '\n\n' + footer + '\n'
            + '<script>' + js + '</script>\n'
            + "<script>document.getElementById('yr').textContent=(new Date().getFullYear());</script>\n"
            + '</body>\n</html>\n')

    # ============================================================ GATES FIRST, WRITE SECOND
    fails = []

    def gate(name, ok, detail=''):
        print('%-10s %s  %s' % (name, 'ok ' if ok else 'FAIL', detail))
        if not ok:
            fails.append(name + ': ' + detail)

    # --- G-BRAND: only this builder's own CSS is in scope; the inherited shell has
    #     legitimate values (the rainbow logo gradient) that are not this page's business.
    used = {h.upper() for h in re.findall(r'#([0-9A-Fa-f]{6})\b', authored_css)}
    off = sorted(used - ALLOWED)
    gate('G-BRAND', not off, '%d hexes, %d off-brand %s' % (len(used), len(off), off or ''))

    # --- G-WRAP: the wrap div is the only thing constraining measure; losing it ships
    #     edge-to-edge prose that renders fine and passes every other check.
    m = re.search(r'<main[^>]*>(.*)</main>', page, re.S)
    wrap_ok, wrap_msg = True, ''
    if not m or page.count('<main') != 1 or page.count('</main>') != 1:
        wrap_ok, wrap_msg = False, 'expected exactly one <main>'
    else:
        inner = m.group(1)
        if not re.match(r'\s*<div class="wrap">', inner):
            wrap_ok, wrap_msg = False, 'main does not open with <div class="wrap">'
        elif not inner.rstrip().endswith('</div>'):
            wrap_ok, wrap_msg = False, 'main does not close the wrap div'
        elif inner.count('<div') != inner.count('</div>'):
            wrap_ok, wrap_msg = False, 'unbalanced <div> inside <main>'
        else:
            first, last = inner.index('<div class="wrap">'), inner.rindex('</div>')
            for tag in re.finditer(r'<section\b', inner):
                if not (first < tag.start() < last):
                    wrap_ok, wrap_msg = False, 'a <section> escaped the wrap div'
            wrap_msg = '1 <main>, 1 wrap, %d sections inside it' % len(re.findall(r'<section\b', inner))
    gate('G-WRAP', wrap_ok, wrap_msg)

    # --- G-LEAK: recompute Cedar Field from the money-leak builder's OWN sample and
    #     assert this page quotes the same truth. Two surfaces, one arithmetic.
    (nn, nv), (un, uv), av = reconcile_cedar_field()
    leak_ok = (nn, int(nv), un, int(uv), int(av)) == (3, 1280, 6, 5430, 705)
    for s in ('$1,280', '$5,430', '$705', '3 jobs', '6 invoices'):
        if s not in page:
            leak_ok = False
    gate('G-LEAK', leak_ok, '%d/$%s - %d/$%s - $%s @ 2026-07-28 vs _brand/build_money_leak_page.py'
         % (nn, '{:,}'.format(int(nv)), un, '{:,}'.format(int(uv)), int(av)))

    # --- G-CLONE: shell extraction should make inheritance vacuous. Verify it did.
    inherited = re.findall(r'Plenty of clients|clients do one|trusted by|hundreds of customers|'
                           r'working with local businesses and clients|Get your pulse', page, re.I)
    ld = page.count('application/ld+json')
    robots = len(re.findall(r'<meta name="robots"', page))
    ring = 'viewBox="0 0 256 256"' in page          # the retired rainbow-ring wordmark
    clone_ok = not inherited and ld == 0 and robots == 1 and not ring
    gate('G-CLONE', clone_ok, '%d inherited claims, %d ld+json, %d robots, ring=%s'
         % (len(inherited), ld, robots, ring))

    # --- SHELL_META_OK: the head is inherited wholesale, so enumerate it. An unknown
    #     meta tag arriving from the source page must fail the build, not ship silently.
    SHELL_META_OK = {
        'og:type': 'website',
        'og:title': C.HEAD['og_title'],
        'og:description': C.HEAD['description'],
        'og:url': C.HEAD['canonical'],
        'og:image': 'https://automatedworkflowllc.com/og-image.png',
        'og:image:width': '1200', 'og:image:height': '630',
        'og:image:alt': 'Automated Workflow &mdash; workflow automation with a human approve button',
        'twitter:card': 'summary_large_image',
    }
    metas = dict(re.findall(r'<meta (?:property|name)="((?:og|twitter):[^"]+)" content="([^"]*)"', page))
    unknown = {k: v for k, v in metas.items() if SHELL_META_OK.get(k) != v}
    gate('G-META', not unknown, '%d social meta enumerated%s'
         % (len(metas), '' if not unknown else ' UNKNOWN: %s' % sorted(unknown)))

    # --- ids: derived from the section list, never a hand-kept roster
    dupes = [i for i in ids if page.count('id="%s"' % i) != 1]
    gate('G-IDS', not dupes, '%d owned ids unique%s' % (len(ids), '' if not dupes else ' BAD: %s' % dupes))

    # --- needs: each block's must-survive strings (invented labels, headline figures)
    missing = [n for n in needs if n not in page]
    gate('G-NEEDS', not missing, '%d strings present%s'
         % (len(needs), '' if not missing else ' MISSING: %s' % missing))

    # --- the QA regexes, mirrored so a copy defect fails HERE and not at push time
    FALSE_PROOF = re.compile(r'plenty of (?:clients|customers)|many (?:clients|customers)|'
                             r'our clients|trusted by|hundreds of|dozens of', re.I)
    TRACTION_DRIFT = re.compile(r'\bserves (?:many|dozens of|hundreds of|\d+) (?:businesses|clients|customers)\b|'
                                r'\b(?:ten|twenty|\d+) (?:retainers|clients|customers) (?:is|are)\b', re.I)
    fp, td = FALSE_PROOF.findall(page), TRACTION_DRIFT.findall(page)
    gate('G-HONEST', not fp and not td, 'FALSE_PROOF %s / TRACTION_DRIFT %s' % (fp or 0, td or 0))

    # --- status chips can only be one of three values, and they live in one list
    chips = [w['status'] for w in C.WORKFLOWS['rows']]
    gate('G-CHIPS', all(c in ('LIVE', 'BUILDING', 'DESIGNED') for c in chips), ' '.join(chips))

    # --- motion: every keyframe is neutralised under prefers-reduced-motion, or exempt
    MOTION_EXEMPT = {'gcRun': '.gc-dot animation:none !important in the reduce block',
                     'gcStall': '.gc-dot animation:none !important in the reduce block'}
    reduce_blk = authored_css[authored_css.find('@media (prefers-reduced-motion: reduce)'):]
    kf = set(re.findall(r'@keyframes ([A-Za-z0-9_-]+)', authored_css))
    unguarded = sorted(k for k in kf if k not in reduce_blk and k not in MOTION_EXEMPT)
    gate('G-MOTION', not unguarded, '%d keyframes, %d exempt%s'
         % (len(kf), len(MOTION_EXEMPT), '' if not unguarded else ' UNGUARDED: %s' % unguarded))

    # --- no-JS: reveals must never ship in the HTML, and the flag must have landed
    nojs_ok = ('class="block rv"' not in page and 'class="no-js"' in page
               and "classList.remove('no-js')" in page)
    gate('G-NOJS', nojs_ok, 'no baked-in .rv, no-js flag present and cleared by script')

    # --- G-PERF. The tech spec's 122KB raw budget assumed one webfont; this build
    #     embeds the four body families the page had been declaring and not loading
    #     (272KB of base64, ~= the homepage's payload, all same-origin). So the budget
    #     is enforced on the bytes this builder AUTHORS, with the font payload
    #     measured separately.
    font_bytes = sum(len(b) for b in re.findall(r'@font-face\{[^}]*\}', page))
    content = len(page) - font_bytes
    ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', page)
    # canonical/og are same-site metadata; LinkedIn is an <a href>, which costs no
    # request. Anything else -- a CDN, a font host, an analytics beacon -- fails.
    OUTBOUND_OK = ('https://automatedworkflowllc.com/',
                   'https://www.linkedin.com/in/colin-mccarthy-548772423')
    bad_ext = [u for u in ext if not u.startswith(OUTBOUND_OK)]
    net = [b for b in ('fetch(', 'XMLHttpRequest', 'sendBeacon', 'importScripts',
                       "addEventListener('scroll'") if b in js]
    perf_ok = content <= 92_000 and len(js) <= 12_000 and not bad_ext and not net
    gate('G-PERF', perf_ok, '%d content + %d font = %d raw / %d gzip - js %d - %d external refs%s'
         % (content, font_bytes, len(page), len(gzip.compress(page.encode('utf-8'), 9)),
            len(js), len(bad_ext), '' if not net else ' NETWORK CALL: %s' % net))

    # --- SEO shape, asserted here so _qa/seo_audit.py can never be the first to know
    title = re.search(r'<title>(.*?)</title>', page, re.S).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', page).group(1)
    seo_ok = (50 <= len(title) <= 60 and 120 <= len(desc) <= 158
              and page.count('<h1') == 1 and len(re.findall(r'rel="canonical"', page)) == 1
              and len(re.findall(r'name="viewport"', page)) == 1
              and 'noindex' in page and 'STAGED on purpose' in page)
    gate('G-SEO', seo_ok, 'title %d, desc %d, 1 h1, 1 canonical, noindex + explanatory comment'
         % (len(title), len(desc)))

    # --- footer NAP survived the swap (a shell change upstream would otherwise strip it
    #     and only trip seo_audit at push time)
    nap_ok = all(x in footer for x in ('colin@automatedworkflowllc.com', '939-1174', 'Gainesville'))
    gate('G-NAP', nap_ok, 'canonical email / phone / Gainesville present in the footer')

    if fails:
        print('\nBUILD BLOCKED -- %d gate(s) failed:' % len(fails))
        for f in fails:
            print('  !!', f)
        raise SystemExit(1)

    # per-invoice derivation, printed so a label/value mismatch is visible in the log
    print('tiers    ', ' | '.join('%s %sd -> %s' % (i['ref'], i['days'], tier_for(i['days'])[2])
                                  for i in C.INVOICES))
    print('sections ', '%d composed - %d ids - %d needs' % (len(blocks), len(ids), len(needs)))
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(page)
    print('written  ', OUT, len(page), 'bytes - STAGED (noindex), out of sitemap.xml and llms.txt - v3.0')


def check_sources():
    """Report drift between _copy.py's provenance hash and the copy spec on disk."""
    doc = pathlib.Path(os.path.expanduser('~')) / C.SOURCE['doc']
    if not doc.exists():
        print('copy spec not found at', doc, '(this is fine on a clean clone)')
        raise SystemExit(0)
    h = hashlib.sha256(doc.read_bytes()).hexdigest()
    print('copy spec :', doc)
    print('recorded  :', C.SOURCE['sha256'])
    print('on disk   :', h)
    if h != C.SOURCE['sha256']:
        print('DRIFT: the copy spec has changed since transcription. Re-read it before shipping.')
        raise SystemExit(1)
    print('no drift.')


if __name__ == '__main__':
    if '--check-sources' in sys.argv:
        check_sources()
    else:
        main()
