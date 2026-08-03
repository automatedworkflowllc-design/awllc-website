# -*- coding: utf-8 -*-
"""Widgets, CSS and JS for /workflow-automation/.

Each widget returns a Block: html + the css/js it owns + the element ids it owns
+ the strings that MUST survive into the final page. build_page.py composes them,
derives its ID-uniqueness and invented-label gates from `ids`/`needs`, and runs
G-BRAND over the CSS this file authors.

Rules enforced by the gates in build_page.py, stated here so they are not
rediscovered:
  * No hex may appear in this file's CSS. Colours come from CSS custom properties
    emitted by root_css() out of _brand/awllc_brand.py. rgba() glows are decorative
    shadows derived from a named token and carry a comment saying which.
  * Every @keyframes name must be neutralised in the prefers-reduced-motion block.
  * No fetch/XHR/sendBeacon/importScripts, and no scroll listeners -- reveals are
    IntersectionObserver-only.
  * Core content renders with JavaScript disabled. `.no-js` may hide CONTROLS and
    reveal FALLBACKS; it may never hide content.
"""
from dataclasses import dataclass, field


@dataclass
class Block:
    html: str
    css: str = ""
    js: str = ""
    ids: tuple = ()
    needs: tuple = ()


# ---------------------------------------------------------------- design scale
# The design spec's numbers, in one place, so a design revision is one diff.
SCALE = {
    'measure': '720px',          # .wrap -- prose
    'wide': '1160px',            # .wide -- consoles, racks, rails
    'section_pad': 'clamp(3.4rem, 7vw, 6.5rem)',
    'radius': '18px',
    'radius_sm': '12px',
    'ease': 'cubic-bezier(.22,.75,.3,1)',
    'space': (4, 8, 12, 16, 24, 32, 48, 72, 112),
    'bp': (900, 800, 700, 620, 560),
}

# ---------------------------------------------------------------- tone tiers
# ONE table. The pill label, the pill colour, the left rule, whether a card is
# approvable and the footer counts all derive from tier_for(days). Two literals
# that can drift is the /shipcheck defect class this replaces.
TIERS = [
    (60, 'serious',  'SERIOUS',  'red'),
    (30, 'firmer',   'FIRMER',   'amber'),
    (15, 'friendly', 'FRIENDLY', 'green'),
    (0,  'silence',  'SILENCE',  'quiet'),
]


def tier_for(days):
    return next(t for t in TIERS if days >= t[0])


def root_css(T):
    """The only place a hex enters this page's authored CSS."""
    return (
        ":root{"
        "--display:'Schibsted Grotesk','Geist',system-ui,'Segoe UI',Roboto,Arial,sans-serif;"
        "--amber:#%s;--red:#%s;--green-bg:#%s;--amber-bg:#%s;--red-bg:#%s;"
        "--panel:#%s;--panel-ink:#%s;--card:#%s;"
        # the two rainbow hues legible as marks on the one dark surface --
        # GREEN/RED are darkened signal colours and go muddy on --ink
        "--rain-g:#%s;--rain-r:#%s;"
        "--ease:cubic-bezier(.22,.75,.3,1);"
        "--wide:%s}"
        % (T['amber'], T['red'], T['green_bg'], T['amber_bg'], T['red_bg'],
           T['ink'], T['paper_tint'], T['paper'], T['rain_g'], T['rain_r'], SCALE['wide'])
    )


# ---------------------------------------------------------------- page CSS
PAGE_CSS = r"""
/* ---------- structure ---------- */
.skip{position:absolute;left:-9999px;top:0;z-index:100;background:var(--ink);color:var(--paper);
  padding:.7rem 1.1rem;border-radius:0 0 10px 0;font-family:var(--mono);font-size:.8rem;text-decoration:none}
.skip:focus{left:0}
/* wide sections escape the 720px prose measure. Centred with margin, NOT transform:
   the reveal animation sets transform:none on .block, which would cancel a
   translateX(-50%) and slam every wide section to the right of centre. */
main .wide{width:min(var(--wide), calc(100vw - 3rem));
  margin-left:calc(50% - min(var(--wide), calc(100vw - 3rem)) / 2);
  margin-right:calc(50% - min(var(--wide), calc(100vw - 3rem)) / 2)}
main section.block{padding:clamp(3.4rem,7vw,6.5rem) 0}
main section.hero{padding:clamp(3rem,6vw,5rem) 0 clamp(2.6rem,5vw,4rem)}
main .idx{font-family:var(--mono);color:var(--ink-faint);margin-right:.5em}
main h1,main h2,main h3{font-family:var(--display);letter-spacing:-.024em}
main h1{font-weight:700;font-size:clamp(2.05rem,4.4vw,3.3rem);line-height:1.05}
main h2{font-weight:680;font-size:clamp(1.7rem,3vw,2.4rem);line-height:1.1}
main h3{font-weight:650;font-size:1.16rem;line-height:1.3;margin:0 0 .35rem}
.serif-i{font-family:var(--serif);font-style:italic;font-weight:440;color:var(--ink-soft)}
.statement{font-family:var(--serif);font-style:italic;font-size:clamp(1.3rem,2vw,1.7rem);
  line-height:1.35;color:var(--ink);margin:1.6rem 0 0}
.data,.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
.mono-lab{font-family:var(--mono);font-size:.68rem;font-weight:600;letter-spacing:.13em;
  text-transform:uppercase;color:var(--ink-faint)}
main a:focus-visible,main button:focus-visible,main summary:focus-visible,
main textarea:focus-visible,main input:focus-visible+.gc-slider{outline:2px solid var(--green);
  outline-offset:2px;border-radius:3px}
main button{font-family:var(--sans)}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px}
.nojs-note{display:none;font-size:.92rem;color:var(--ink-soft);font-style:italic;margin:.6rem 0 0}
.no-js .nojs-note{display:block}

/* ---------- header chrome ---------- */
/* chrome sits on the wide measure so it lines up with the consoles below, not with
   the 720px prose column */
.site-header .wrap,.site-footer .wrap{max-width:min(var(--wide), calc(100% - 0px))}
.hdr-nav{margin-left:auto;display:flex;gap:1.1rem}
.hdr-nav a{font-family:var(--mono);font-size:.72rem;font-weight:600;letter-spacing:.08em;
  text-transform:uppercase;color:var(--ink-soft);text-decoration:none;padding:.35rem 0;
  background-image:linear-gradient(currentColor,currentColor);background-repeat:no-repeat;
  background-position:0 100%;background-size:0% 1.5px;transition:background-size .24s var(--ease),color .18s var(--ease)}
.hdr-nav a:hover{color:var(--ink);background-size:100% 1.5px}
.site-header .header-cta{margin-left:1.1rem}
@media (max-width:800px){.hdr-nav{display:none}.site-header .header-cta{margin-left:auto}}

/* ---------- hero ---------- */
.hero-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);
  gap:clamp(2rem,4vw,3.5rem);align-items:center}
.hero-grid h1{margin:0 0 1.1rem}
.hero-grid .subhead{max-width:54ch}
.hero-teaser{border:1px solid var(--line);border-radius:18px;background:var(--well);padding:20px 18px}
.ht-rail{display:flex;flex-direction:column;gap:8px}
.ht-node{display:flex;align-items:baseline;gap:10px;border:1.5px solid var(--line-strong);
  border-radius:10px;padding:8px 12px;background:var(--card)}
.ht-node .n{font-family:var(--mono);font-size:.66rem;color:var(--ink-faint)}
.ht-node .t{font-family:var(--mono);font-weight:700;font-size:.74rem;letter-spacing:.08em}
.ht-node.ht-gate{border-color:var(--amber);border-width:2.5px;animation:htGlow 1.8s ease-in-out infinite}
.ht-node.ht-dim{opacity:.5}
@keyframes htGlow{0%,100%{box-shadow:0 0 0 0 rgba(180,83,9,.30)}50%{box-shadow:0 0 0 6px rgba(180,83,9,.08)}}
.ht-cap{margin:.9rem 0 0;font-family:var(--mono);font-size:.72rem;letter-spacing:.06em;color:var(--amber)}
.ht-cap a{color:var(--green)}
@media (max-width:900px){.hero-grid{grid-template-columns:1fr}.hero-teaser{order:2}}

/* ---------- gate console ---------- */
.gc{background:var(--well);border:1px solid var(--line);border-radius:18px;padding:clamp(18px,3vw,30px)}
.gc-rail{display:flex;align-items:stretch;gap:0;margin:0 0 22px}
.gc-node{flex:0 0 auto;display:flex;flex-direction:column;justify-content:center;gap:2px;
  border:1.5px solid var(--ink);border-radius:10px;padding:10px 12px;min-width:92px;text-align:center;
  position:relative;background:var(--card)}
.gc-node::before{content:attr(data-n);position:absolute;top:-9px;left:8px;font-family:var(--mono);
  font-size:10px;background:var(--well);padding:0 4px;color:var(--ink-faint)}
.gc-t{font-family:var(--mono);font-weight:800;font-size:12px;letter-spacing:.08em}
.gc-d{font-size:11px;color:var(--ink-soft)}
.gc-gate{border-width:2.5px;border-color:var(--amber);animation:gcGlow 1.6s ease-in-out infinite}
.gc-wrap.gc-open .gc-gate,.gc-wrap:has(#gcToggle:checked) .gc-gate{border-color:var(--green);
  animation:none;box-shadow:0 0 0 3px rgba(30,122,71,.18)}
@keyframes gcGlow{0%,100%{box-shadow:0 0 0 0 rgba(180,83,9,.30)}50%{box-shadow:0 0 0 6px rgba(180,83,9,.10)}}
.gc-seg{flex:1 1 34px;min-width:26px;position:relative;align-self:center;height:2px;background:var(--line-strong)}
.gc-dot{position:absolute;top:-4px;left:0;width:10px;height:10px;border-radius:50%;background:var(--green);opacity:0}
.gc-dot-a{animation:gcRun 3.6s linear infinite}
.gc-dot-b{animation:gcRun 3.6s linear infinite .9s}
.gc-dot-c{animation:gcStall 3.6s linear infinite 1.8s}
.gc-dot-d{animation:none}
.gc-wrap.gc-open .gc-dot-c,.gc-wrap:has(#gcToggle:checked) .gc-dot-c{animation:gcRun 3.6s linear infinite 1.8s}
.gc-wrap.gc-open .gc-dot-d,.gc-wrap:has(#gcToggle:checked) .gc-dot-d{animation:gcRun 3.6s linear infinite 2.7s}
@keyframes gcRun{0%{left:0;opacity:0}10%{opacity:1}90%{opacity:1}100%{left:calc(100% - 10px);opacity:0}}
@keyframes gcStall{0%{left:0;opacity:0}10%{opacity:1}55%{left:calc(100% - 10px);opacity:1}
  70%{left:calc(100% - 10px);opacity:1}85%{left:calc(100% - 10px);opacity:0}100%{left:calc(100% - 10px);opacity:0}}
.gc-railcap{margin:.2rem 0 1.4rem;font-size:.9rem;color:var(--ink-soft)}
.gc-cols{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,.65fr);gap:18px}
.gc-legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.gc-card{display:flex;gap:14px;align-items:flex-start;justify-content:space-between;padding:14px 12px;
  border:1px solid var(--line);border-left:4px solid var(--line);border-radius:12px;margin-bottom:10px;
  background:var(--card);transition:border-color .18s var(--ease),background-color .18s var(--ease),transform .24s var(--ease)}
.gc-card[data-tier="friendly"]{border-left-color:var(--green)}
.gc-card[data-tier="firmer"]{border-left-color:var(--amber)}
.gc-card[data-tier="serious"]{border-left-color:var(--red)}
.gc-card[data-tier="silence"]{border-left-color:var(--line-strong);background:var(--paper)}
.gc-card.gc-on{background:var(--green-bg);border-color:var(--green);transform:translateX(2px)}
.gc-info{flex:1 1 auto;min-width:0;overflow-wrap:anywhere}
.gc-inv{font-weight:700;display:inline-block;margin-right:10px}
.gc-pill{font-family:var(--mono);font-size:11px;letter-spacing:.06em;padding:2px 8px;border-radius:20px;
  white-space:nowrap;background:var(--card);border:1px solid currentColor}
.gc-green{color:var(--green)}.gc-amber{color:var(--amber)}.gc-red{color:var(--red)}
.gc-quiet{color:var(--ink-soft);border-color:var(--line-strong)}
.gc-draft{margin:.45em 0 0;font-size:.92rem;color:var(--ink-soft);font-style:italic}
.gc-why{margin:.5em 0 0;font-size:.86rem;color:var(--ink-soft)}
.gc-why summary{cursor:pointer;font-family:var(--mono);font-size:.68rem;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ink-faint)}
.gc-why p{margin:.45em 0 0}
.gc-btn{flex:0 0 auto;min-width:106px;min-height:44px;border:1.5px solid var(--ink);background:transparent;
  border-radius:24px;padding:7px 16px;font-weight:700;cursor:pointer;
  transition:background-color .18s var(--ease),color .18s var(--ease)}
.gc-btn[aria-pressed="true"]{background:var(--green);border-color:var(--green);color:var(--paper)}
.gc-held{flex:0 0 auto;display:inline-flex;align-items:center;min-height:44px;font-family:var(--mono);
  font-size:11px;letter-spacing:.08em;color:var(--ink-soft);border:1.5px dashed var(--line-strong);
  border-radius:24px;padding:7px 14px}
.no-js .gc-btn,.no-js .gc-send,.no-js .gc-reset{display:none}
.gc-log{margin:0;padding:14px;list-style:none;border:1px solid var(--line);border-radius:12px;
  background:var(--card);font-family:var(--mono);font-size:.72rem;line-height:1.75;color:var(--ink-soft);
  max-height:none;overflow-y:auto}
.gc-log li{overflow-wrap:anywhere}
.gc-log li b{color:var(--ink);font-weight:700}
.gc-logh{margin:0 0 .5rem}
.gc-logn{margin:.6rem 0 0;font-size:.78rem;color:var(--ink-faint);font-style:italic}
.gc-foot{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;
  padding-top:14px;margin-top:4px;border-top:1px dashed var(--line)}
.gc-ctrls{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.gc-toggle{display:inline-flex;align-items:center;gap:8px;cursor:pointer;font-weight:700;min-height:44px}
.gc-toggle input{position:absolute;opacity:0;width:0;height:0}
.gc-slider{width:44px;height:24px;border-radius:24px;background:var(--line-strong);
  border:1.5px solid var(--ink);position:relative;transition:background .18s var(--ease);flex:0 0 auto}
.gc-slider::after{content:"";position:absolute;top:2px;left:2px;width:17px;height:17px;border-radius:50%;
  background:var(--card);border:1px solid var(--ink);transition:left .18s var(--ease)}
.gc-toggle input:checked+.gc-slider{background:var(--green)}
.gc-toggle input:checked+.gc-slider::after{left:21px}
.gc-status{font-size:.92rem;color:var(--ink-soft);font-style:italic}
.gc-send,.gc-reset{min-height:44px}
.gc-send[disabled]{opacity:.45;cursor:not-allowed}
.gc-reset{border:1.5px solid var(--line-strong);background:transparent;border-radius:24px;
  padding:7px 16px;font-weight:600;cursor:pointer;color:var(--ink-soft)}
.gc-outcome{overflow:hidden;max-height:0;opacity:0;margin-top:0;border:0 solid var(--green);
  border-radius:12px;background:var(--green-bg);padding:0 14px;
  transition:max-height .3s var(--ease),opacity .3s var(--ease)}
.gc-outcome.gc-show{max-height:320px;opacity:1;margin-top:14px;border-width:1px;padding:12px 14px}
.gc-outcome-head{margin:0;font-weight:800;color:var(--green)}
.gc-outcome-body{margin:.45em 0 0;font-size:.92rem;color:var(--ink-soft)}
.gc-cap{margin:1.2rem auto 0;max-width:60ch;font-size:.95rem;color:var(--ink-soft)}
/* with JS off the ledger would render as an empty box; the queue itself still reads in full */
.no-js .gc-logh,.no-js .gc-log,.no-js .gc-logn{display:none}
@media (max-width:900px){.gc-cols{grid-template-columns:1fr}}
@media (max-width:700px){.gc-rail{flex-direction:column;gap:10px}
  .gc-seg{width:2px;height:26px;min-width:0;align-self:center;flex:0 0 26px}.gc-dot{left:-4px;top:0}
  @keyframes gcRun{0%{top:0;left:-4px;opacity:0}10%{opacity:1}90%{opacity:1}100%{top:calc(100% - 10px);left:-4px;opacity:0}}
  @keyframes gcStall{0%{top:0;left:-4px;opacity:0}10%{opacity:1}55%{top:calc(100% - 10px);left:-4px;opacity:1}
    70%{top:calc(100% - 10px);opacity:1}85%{opacity:0}100%{top:calc(100% - 10px);opacity:0}}}
@media (max-width:560px){.gc-card{flex-direction:column}.gc-btn,.gc-held{align-self:flex-start}
  .gc-log{max-height:11rem}}

/* ---------- method stack ---------- */
.ms{display:grid;gap:10px}
.ms-layer{border:1px solid var(--line);border-radius:14px;background:var(--card);overflow:hidden;position:relative}
.ms-layer.ms-spine::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--rainbow)}
.ms-layer summary{list-style:none;cursor:pointer;display:grid;
  grid-template-columns:2.6rem minmax(0,1fr) minmax(0,1.1fr) 1.2rem;gap:14px;align-items:baseline;
  padding:16px 18px;min-height:44px}
.ms-layer summary::-webkit-details-marker{display:none}
.ms-layer summary::after{content:"+";font-family:var(--mono);color:var(--ink-faint);justify-self:end}
.ms-layer[open] summary::after{content:"\2013"}
.ms-n{font-family:var(--mono);font-weight:700;font-size:.8rem;color:var(--ink-faint)}
.ms-name{font-family:var(--display);font-weight:650;font-size:1.05rem;color:var(--ink)}
.ms-rule{font-size:.92rem;color:var(--ink-soft)}
.ms-body{padding:0 18px 18px 18px;color:var(--ink-soft);font-size:.97rem;line-height:1.6}
.ms-body em{color:var(--ink);font-style:italic}
.ms-back{display:inline-block;margin-top:.6rem;font-family:var(--mono);font-size:.72rem;
  letter-spacing:.06em;color:var(--green)}
@media (max-width:700px){.ms-layer summary{grid-template-columns:2.4rem minmax(0,1fr) 1.2rem}
  .ms-rule{grid-column:2/4}}

/* ---------- the bench ---------- */
.bn{border:1px solid var(--line);border-radius:18px;background:var(--well);padding:clamp(16px,2.5vw,24px)}
.bn label{display:block;margin:.9rem 0 .4rem}
.bn textarea{width:100%;font-family:var(--mono);font-size:.82rem;line-height:1.6;padding:12px;
  border:1px solid var(--line-strong);border-radius:12px;background:var(--card);color:var(--ink);resize:vertical}
.bn-note{margin:.45rem 0 .9rem}
.bn-acts{display:flex;gap:10px;flex-wrap:wrap}
.bn-acts button{min-height:44px;border-radius:24px;padding:8px 18px;font-weight:700;cursor:pointer;
  border:1.5px solid var(--ink);background:var(--ink);color:var(--paper)}
.bn-acts button.ghost{background:transparent;color:var(--ink-soft);border-color:var(--line-strong);font-weight:600}
.bn-out{margin-top:14px;font-family:var(--mono);font-size:.8rem;line-height:1.7;color:var(--ink-soft)}
.bn-out .hd{color:var(--ink);font-weight:700}
.bn-out .grp{border-top:1px dashed var(--line);padding-top:.4rem;margin-top:.4rem;overflow-wrap:anywhere}
.bn-receipts{margin-top:12px;display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);
  font-size:.7rem;letter-spacing:.06em;color:var(--green);border:1px solid var(--green);
  border-radius:20px;padding:6px 12px;background:var(--green-bg)}
.bn-after{margin:.9rem 0 0;font-size:.92rem;color:var(--ink-soft)}
.rk{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:32px}
.rk-card{border:1px solid var(--line);border-radius:18px;background:var(--card);padding:18px;
  display:flex;flex-direction:column;gap:.5rem;transition:transform .24s var(--ease),box-shadow .24s var(--ease)}
.rk-card:hover{transform:translateY(-4px);box-shadow:var(--shadow)}
.rk-card h3{margin:0}
.rk-card h3 a{text-decoration:none}
.rk-card h3 a:hover{text-decoration:underline}
.rk-what{margin:0;font-size:.93rem;color:var(--ink-soft)}
.rk-proof{margin:0;font-size:.85rem;color:var(--ink-soft);border-top:1px dashed var(--line);padding-top:.6rem}
.rk-chip{align-self:flex-start;font-family:var(--mono);font-size:.62rem;letter-spacing:.12em;
  text-transform:uppercase;color:var(--green);border:1px solid var(--green);border-radius:20px;padding:3px 9px}
@media (max-width:900px){.rk{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:620px){.rk{grid-template-columns:1fr}}

/* ---------- typewriter + video ---------- */
.tw-panel{border:1px solid var(--line);border-radius:18px;background:var(--card);padding:20px}
.tw-kpis{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:12px}
.tw-kpi{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:12px;border:1px solid var(--line);
  border-radius:8px;padding:6px 10px;background:var(--paper)}
.tw-note{font-size:11px;color:var(--ink-faint);font-style:italic}
.tw-out{min-height:6.4em;margin:0;font-size:1rem;line-height:1.55}
.tw-caret{display:inline-block;width:9px;height:1.05em;background:var(--ink);vertical-align:text-bottom;
  margin-left:2px;animation:twBlink 1s steps(1) infinite}
.tw-caret.tw-done{animation:none;opacity:0}
@keyframes twBlink{0%,49%{opacity:1}50%,100%{opacity:0}}
.tw-acts{display:flex;gap:10px;margin-top:12px}
.tw-acts button{min-height:44px;border-radius:24px;padding:8px 18px;font-weight:600;cursor:pointer;
  border:1.5px solid var(--line-strong);background:transparent;color:var(--ink)}
.no-js .tw-acts{display:none}
.tw-cap{margin:.9em 0 0;font-size:.9rem;color:var(--ink-soft);border-top:1px dashed var(--line);padding-top:.8em}

/* ---------- money-leak storyboard ---------- */
.ml{display:grid;gap:10px;margin-top:1.2rem}
.ml-step{border:1px solid var(--line);border-radius:14px;background:var(--card);overflow:hidden}
.ml-step summary{list-style:none;cursor:pointer;padding:14px 18px;min-height:44px;display:flex;
  align-items:center;gap:12px;font-family:var(--mono);font-size:.76rem;letter-spacing:.08em;
  text-transform:uppercase;color:var(--ink);font-weight:700}
.ml-step summary::-webkit-details-marker{display:none}
.ml-step summary::after{content:"+";margin-left:auto;color:var(--ink-faint)}
.ml-step[open] summary::after{content:"\2013"}
.ml-step .b{padding:0 18px 16px;color:var(--ink-soft);font-size:.96rem;line-height:1.6}
.ml-step .b b{color:var(--ink)}
.ml-label{margin:1rem 0 0;font-size:.88rem;color:var(--ink-soft);border-left:3px solid var(--amber);
  padding-left:.9rem}

/* ---------- workflow rail ---------- */
.wl{display:grid;gap:0;border-top:1px solid var(--line);margin-top:1.4rem}
.wl-row{display:grid;grid-template-columns:3rem minmax(0,1fr) minmax(0,.6fr);gap:16px;
  padding:22px 0;border-bottom:1px solid var(--line);align-items:start}
.wl-id{font-family:var(--mono);font-weight:700;color:var(--ink-faint)}
.wl-name{font-family:var(--display);font-weight:650;font-size:1.1rem;margin:0 0 .35rem}
.wl-what{margin:0;font-size:.95rem;color:var(--ink-soft)}
.wl-note{margin:.5rem 0 0;font-size:.9rem;color:var(--ink-soft);font-style:italic}
.wl-side{display:flex;flex-direction:column;gap:.5rem;align-items:flex-start}
.wl-price{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:.86rem;color:var(--ink)}
.wl-chip{font-family:var(--mono);font-size:.62rem;font-weight:700;letter-spacing:.12em;
  border-radius:20px;padding:3px 10px;border:1px solid currentColor}
.wl-live{color:var(--green);background:var(--green-bg)}
.wl-building{color:var(--amber);background:var(--amber-bg)}
.wl-designed{color:var(--ink-soft);border-style:dashed;border-color:var(--line-strong)}
.wl-honest{margin:1.2rem 0 0;font-size:.95rem;color:var(--ink-soft)}
@media (max-width:700px){.wl-row{grid-template-columns:3rem minmax(0,1fr)}
  .wl-side{grid-column:2;flex-direction:row;align-items:center;gap:.8rem;flex-wrap:wrap}}

/* ---------- price stair ---------- */
.pr{display:grid;gap:0;margin-top:1.4rem}
.pr-step{border-left:1px solid var(--line-strong);padding:18px 0 18px 22px;position:relative}
.pr-step .pr-in{display:grid;grid-template-columns:minmax(0,.34fr) minmax(0,1fr);gap:16px;align-items:baseline}
.pr-num{font-family:var(--mono);font-variant-numeric:tabular-nums;font-weight:700;font-size:1.22rem;color:var(--ink)}
.pr-name{font-family:var(--display);font-weight:650;font-size:1.02rem;margin:0 0 .3rem}
.pr-body{margin:0;font-size:.95rem;color:var(--ink-soft)}
.pr-free{background:var(--well);border-radius:14px;border-left:0;padding:20px 22px;position:relative;overflow:hidden}
.pr-free::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--rainbow)}
.pr-cta{display:inline-block;margin-top:.6rem;font-family:var(--mono);font-size:.72rem;
  letter-spacing:.08em;text-transform:uppercase;color:var(--green)}
.pr-under{margin:1.6rem 0 0;font-size:.95rem;color:var(--ink-soft)}
@media (min-width:701px){.pr-step{margin-left:calc(var(--i) * 28px)}}
@media (max-width:700px){.pr-step .pr-in{grid-template-columns:1fr;gap:6px}}

/* ---------- honesty ledger (the page's one dark surface) ---------- */
.hl{background:var(--panel);color:var(--panel-ink);border-radius:18px;padding:clamp(20px,3vw,32px);
  margin-top:1.6rem}
.hl h3{color:var(--panel-ink);font-family:var(--mono);font-size:.72rem;letter-spacing:.16em;
  text-transform:uppercase;margin:0 0 1.2rem;font-weight:600}
.hl-cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.hl-col h4{margin:0 0 .7rem;font-family:var(--mono);font-size:.68rem;font-weight:600;letter-spacing:.12em;
  text-transform:uppercase;color:var(--line-strong);border-bottom:1px solid var(--ink-soft);padding-bottom:.5rem}
.hl-col ul{list-style:none;margin:0;padding:0;display:grid;gap:.5rem;font-size:.95rem}
.hl-col li{display:flex;gap:.6rem;align-items:baseline;overflow-wrap:anywhere}
.hl-col .m{font-family:var(--mono);flex:0 0 auto}
.hl-can .m{color:var(--rain-g)}
.hl-wont .m{color:var(--rain-r)}
.hl-line{margin:1.6rem 0 0;padding-top:1.2rem;border-top:1px solid var(--ink-soft);font-size:1rem;
  color:var(--panel-ink)}
@media (max-width:620px){.hl-cols{grid-template-columns:1fr}}

/* ---------- cta band ---------- */
main section.cta-band{background:var(--well);border-radius:18px;padding:clamp(2.2rem,5vw,3.4rem) 1.5rem;
  position:relative;overflow:hidden;margin-bottom:clamp(3rem,6vw,5rem)}
.cta-band::before{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:var(--rainbow)}
.cta-sub{margin-top:1.1rem;font-size:.9rem;color:var(--ink-faint);max-width:52ch;margin-left:auto;margin-right:auto}
.cta-nap{margin-top:.6rem;font-family:var(--mono);font-size:.76rem;color:var(--ink-faint)}

/* ---------- footer additions ---------- */
.fbrand-row{display:inline-flex;align-items:center;gap:.5rem}
.fbrand-logo{height:22px;width:auto;display:block}
.footer-free{border-top:1px dashed var(--line-strong);padding-top:.9rem}
.footer-free-label{font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink-faint)}

/* ---------- scroll reveals (added by JS only; never emitted in the HTML) ---------- */
@media (prefers-reduced-motion: no-preference){
  .block.rv{opacity:0;transform:translateY(14px);transition:opacity .5s var(--ease),transform .5s var(--ease)}
  .block.rv.rv-in{opacity:1;transform:none}
}
@media (prefers-reduced-motion: reduce){
  .gc-dot{animation:none !important;opacity:0 !important}
  .gc-gate{animation:gcGlow 0s}
  .ht-node.ht-gate{animation:htGlow 0s}
  .tw-caret{animation:twBlink 0s;opacity:0}
  .gc-outcome,.gc-card,.rk-card,.hdr-nav a{transition:none}
}
"""


# ---------------------------------------------------------------- page JS
def page_js(cfg):
    """One IIFE, five modules. cfg carries the strings the JS needs so no copy
    is duplicated between Python and JavaScript."""
    return (r"""
(function(){'use strict';
var D=document, H=D.documentElement;
/* ---- gate console ---- */
var q=function(s,r){return (r||D).querySelector(s)},
    qa=function(s,r){return Array.prototype.slice.call((r||D).querySelectorAll(s))};
var btns=qa('#gcQueue .gc-btn'), send=q('#gcSend'), reset=q('#gcReset'),
    cnt=q('#gcCount'), out=q('#gcOutcome'), oh=q('#gcOutcomeHead'), log=q('#gcLedger'),
    tog=q('#gcToggle'), wrap=q('#gcWrap'), stat=q('#gcStatus'), gd=q('#gcGateD');
var APPROVABLE=""" + str(cfg['approvable']) + r""", SILENT=""" + str(cfg['silent']) + r""", n=0, t=0;
function stamp(){t+=7;var m=2+Math.floor(t/60),s=t%60;
  return '09:0'+m+':'+(s<10?'0':'')+s;}
function line(tag,msg){if(!log)return;var li=D.createElement('li');
  li.innerHTML='<b>'+stamp()+'</b> '+tag+' &middot; '+msg;log.appendChild(li);
  while(log.children.length>14)log.removeChild(log.firstChild);}
function counter(){cnt.textContent=n+' of '+APPROVABLE+' approved · '+SILENT+' held in silence';}
function armSend(){send.disabled=!(n>0&&tog&&tog.checked);}
btns.forEach(function(b){b.addEventListener('click',function(){
  var on=b.getAttribute('aria-pressed')==='true', card=b.closest('.gc-card');
  b.setAttribute('aria-pressed',on?'false':'true');
  b.textContent=on?'Approve':'Queued ✓';
  if(card){card.classList.toggle('gc-on',!on);}
  n+=on?-1:1;counter();armSend();
  out.classList.remove('gc-show');oh.textContent='';
  line('GATE',(on?'un-approved ':'approved ')+(card?card.getAttribute('data-ref'):''));
});});
if(tog){tog.addEventListener('change',function(){
  wrap.classList.toggle('gc-open',tog.checked);
  stat.innerHTML=tog.checked?""" + cfg['status_open'] + r""":""" + cfg['status_wait'] + r""";
  gd.textContent=tog.checked?'open — you said go':'waiting on you';
  line('GATE',tog.checked?'OPENED BY YOU':'CLOSED — everything waits');
  armSend();H.setAttribute('data-gate-used','1');
  qa('.ms-back').forEach(function(a){a.innerHTML=""" + cfg['backref_on'] + r""";});
});}
if(send){send.addEventListener('click',function(){
  var held=APPROVABLE-n;
  oh.textContent=n+(n===1?' email released':' emails released')+' — this click is the send · '
    +held+(held===1?' draft waits':' drafts wait')+' for the next queue · '
    +SILENT+' invoice stays silent on purpose';
  out.classList.add('gc-show');
  line('LEDGER','run closed · '+n+' sent · '+held+' held · '+SILENT+' silent');
});}
if(reset){reset.addEventListener('click',function(){
  btns.forEach(function(b){b.setAttribute('aria-pressed','false');b.textContent='Approve';
    var c=b.closest('.gc-card');if(c)c.classList.remove('gc-on');});
  if(tog){tog.checked=false;wrap.classList.remove('gc-open');
    stat.innerHTML=""" + cfg['status_wait'] + r""";gd.textContent='waiting on you';}
  n=0;t=0;counter();armSend();out.classList.remove('gc-show');oh.textContent='';
  if(log){log.innerHTML='';seedLog();}
});}
function seedLog(){if(!log)return;t=-7+0;
  line('SENSOR','read 42 rows, wrote nothing');
  line('MATH','4 past due, 1 too fresh');
  line('BRAIN','3 drafts written');
  line('GATE','HELD — waiting on a human');}
seedLog();counter();armSend();

/* ---- method stack back-reference ---- */
if(H.getAttribute('data-gate-used')==='1'){
  qa('.ms-back').forEach(function(a){a.innerHTML=""" + cfg['backref_on'] + r""";});}

/* ---- the bench: same normalization as /duplicate-customer-finder/ ---- */
var SUF=/\b(inc|llc|ltd|co|corp|corporation|company|incorporated|pllc|pc|lp|llp|plc|group|grp|holdings|enterprises|services|svcs|sons)\b/g,
    NOISE=/[.,'’"()\-_\/\\]+/g;
function normName(s){var v=String(s).toLowerCase();
  v=v.replace(/&/g,' and ');v=v.replace(NOISE,' ');v=v.replace(SUF,' ');
  v=v.replace(/\bthe\b/g,' ');v=v.replace(/\band\b/g,' ');
  return v.replace(/\s+/g,' ').trim();}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
/* bounded Levenshtein, same bail-out as the full tool so a long paste can't stall a phone */
function withinEdits(a,b,max){
  if(Math.abs(a.length-b.length)>max)return false;
  if(a===b)return true;
  var prev=[],cur=[],i,j;
  for(j=0;j<=b.length;j++)prev[j]=j;
  for(i=1;i<=a.length;i++){cur[0]=i;var best=cur[0];
    for(j=1;j<=b.length;j++){var cost=a.charAt(i-1)===b.charAt(j-1)?0:1;
      cur[j]=Math.min(prev[j]+1,cur[j-1]+1,prev[j-1]+cost);if(cur[j]<best)best=cur[j];}
    if(best>max)return false;
    for(j=0;j<=b.length;j++)prev[j]=cur[j];}
  return prev[b.length]<=max;}
var bnIn=q('#bnIn'), bnRun=q('#bnRun'), bnClear=q('#bnClear'), bnOut=q('#bnOut');
function runBench(){
  var lines=bnIn.value.split(/\r?\n/).map(function(x){return x.trim();}).filter(Boolean);
  var capped=lines.length>500;if(capped)lines=lines.slice(0,500);
  if(!lines.length){bnOut.innerHTML='<span class="hd">Nothing to check yet.</span> Paste one name per line.';return;}
  /* pass 1: exact match on the normalized key (case / punctuation / legal suffix) */
  var by={},keys=[];
  lines.forEach(function(v){var k=normName(v);if(!k)return;
    if(!by[k]){by[k]={};keys.push(k);}by[k][v]=(by[k][v]||0)+1;});
  /* pass 2: near-miss keys (typos), threshold scaling with length -- same rule as the full tool */
  var used={},groups=[];
  keys.forEach(function(k){
    if(used[k])return;
    var members=[k];used[k]=1;
    var max=k.length<=6?1:(k.length<=14?2:3);
    keys.forEach(function(o){if(used[o]||o===k)return;
      if(withinEdits(k,o,max)){members.push(o);used[o]=1;}});
    var forms=[],fuzzy=members.length>1;
    members.forEach(function(m){Object.keys(by[m]).forEach(function(f){
      if(forms.indexOf(f)<0)forms.push(f);});});
    groups.push({v:forms,fuzzy:fuzzy});});
  var multi=groups.filter(function(g){return g.v.length>1;});
  var h='<span class="hd">'+lines.length+' lines in · '+groups.length+' real customers · '
        +multi.length+' group'+(multi.length===1?'':'s')+' with variants</span>';
  multi.forEach(function(g){h+='<div class="grp">'+esc(g.v[0])+' ▸ '+g.v.length+' spellings ▸ '
    +g.v.map(esc).join(' / ')+' <em>('+(g.fuzzy?'near-miss spelling — worth a human glance'
    :'identical once case, punctuation and legal suffixes are ignored')+')</em></div>';});
  if(!multi.length)h+='<div class="grp">No two lines collapse to the same name. That is a clean list.</div>';
  if(capped)h+='<div class="grp">Only the first 500 lines were checked — the full tool takes the whole export.</div>';
  bnOut.innerHTML=h;receipts();}
if(bnRun)bnRun.addEventListener('click',runBench);
if(bnClear)bnClear.addEventListener('click',function(){bnIn.value='';bnIn.focus();
  bnOut.innerHTML='<span class="hd">Box cleared.</span> Paste your own list and press Check it.';});

/* ---- receipts badge: measured, never hardcoded ---- */
var rc=q('#receipts');
function receipts(){
  if(!rc||!window.performance||!performance.getEntriesByType)return;
  var es=performance.getEntriesByType('resource'),third=0,first=0;
  es.forEach(function(e){try{
    if(new URL(e.name,location.href).origin===location.origin)first++;else third++;
  }catch(err){third++;}});
  rc.textContent='third-party requests: '+third+' · first-party files: '+first
    +' · your text never left this tab';}
if(window.PerformanceObserver){try{
  new PerformanceObserver(receipts).observe({type:'resource',buffered:true});
}catch(e){}}
window.addEventListener('load',receipts);

/* ---- typewriter: the sentence lives in the DOM, JS only re-types it ---- */
var twText=q('#twText'), twCaret=q('#twCaret'), twRun=q('#twRun'), FULL=twText?twText.textContent:'', twTimer=null;
function reduced(){return window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;}
function typeIt(){
  if(!twText)return;
  if(twTimer){clearTimeout(twTimer);twTimer=null;}
  if(reduced()){twText.textContent=FULL;twCaret.classList.add('tw-done');return;}
  var i=0,started=Date.now();twCaret.classList.remove('tw-done');
  (function step(){
    if(i<=FULL.length&&Date.now()-started<8000&&!D.hidden){
      twText.textContent=FULL.slice(0,i);i++;twTimer=setTimeout(step,18);
    }else{twText.textContent=FULL;twCaret.classList.add('tw-done');twTimer=null;}
  })();}
if(twRun)twRun.addEventListener('click',typeIt);
var twAuto=false;

/* ---- reveals: IntersectionObserver only, never a scroll listener ---- */
var blocks=qa('main .block:not(.no-rv)');
if('IntersectionObserver' in window){
  blocks.forEach(function(b){b.classList.add('rv');});
  var io=new IntersectionObserver(function(es){es.forEach(function(e){
    if(e.isIntersecting){e.target.classList.add('rv-in');
      if(!twAuto&&e.target.querySelector('#twPanel')){twAuto=true;typeIt();}
      io.unobserve(e.target);}});},{threshold:.18});
  blocks.forEach(function(b){io.observe(b);});
}
})();
""")
