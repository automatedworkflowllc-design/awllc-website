#!/usr/bin/env python3
"""Build /money-leak-finder/ -- the outreach hook's missing landing page.

Drop two exports (work log + invoices) and the page shows only the mismatches:
jobs completed but never invoiced, invoices unpaid, unpaid past 60 days. Runs
entirely in the browser -- same architectural privacy promise as the health
check, because these are exactly the files nobody should upload to a stranger.

Shell (head/styles/header/footer) inherited verbatim from the cleanup-service
page. Sample data is the Cedar Field Services set from build_money_leak.py,
UNCHANGED, so the web demo reconciles to the spec's documented numbers:
3 never-invoiced jobs / $1,280 -- 6 unpaid / $5,430 -- $705 past 60 days
(as of the frozen sample date 2026-07-28).
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'money-leak-finder'

TITLE = 'Money Leak Finder — Jobs Done vs. Billed, In Your Browser'
DESC = ('See only the mismatches between your work log and invoice export: jobs '
        'never invoiced, invoices unpaid past 60 days. Runs in your browser — '
        'nothing uploads.')
CANON = 'https://automatedworkflowllc.com/money-leak-finder/'

PAGE_CSS = """
/* ---- money leak finder ---- */
.ml-drops{display:grid;grid-template-columns:1fr 1fr;gap:.9rem}
@media(max-width:640px){.ml-drops{grid-template-columns:1fr}}
.ml-drop{border:2px dashed var(--line-strong);border-radius:14px;background:var(--card);
padding:1.6rem 1rem;text-align:center;cursor:pointer}
.ml-drop.is-over{border-color:var(--accent);background:var(--well)}
.ml-drop.is-set{border-style:solid;border-color:var(--accent)}
.ml-drop:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.ml-drop strong{display:block;margin-bottom:.3rem}
.ml-drop span{color:var(--ink-soft);font-size:.85rem;overflow-wrap:anywhere}
.ml-actions{display:flex;gap:.7rem;justify-content:center;flex-wrap:wrap;margin-top:1rem}
#ml-report{margin-top:2rem;display:none}
.ml-kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem;margin:0 0 1.4rem}
@media(max-width:640px){.ml-kpis{grid-template-columns:1fr}}
.ml-kpi{border:1px solid var(--line);border-radius:.7rem;padding:.9rem 1rem;background:var(--card)}
.ml-kpi b{display:block;font-size:1.6rem;font-family:var(--mono);line-height:1.15}
.ml-kpi.k-bad b{color:#B4452C}
.ml-kpi span{font-size:.78rem;color:var(--ink-soft)}
.ml-table{width:100%;border-collapse:collapse;font-size:.9rem;margin:.4rem 0 1.4rem}
.ml-table th{text-align:left;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;
color:var(--ink-soft);border-bottom:1px solid var(--line-strong);padding:.35rem .5rem}
.ml-table td{border-bottom:1px solid var(--line-soft);padding:.42rem .5rem}
.ml-table td.num{font-family:var(--mono);text-align:right}
.ml-h3{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-soft);margin:1.4rem 0 .4rem}
.ml-note{font-size:.85rem;color:var(--ink-soft)}
.ml-cta{margin-top:1.6rem;padding:1.3rem;border:1px solid var(--line);border-radius:12px;background:var(--bg-soft)}
.ml-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">Money Leak Finder</h1>
  <p style="color:var(--ink-soft);max-width:40rem">
    Two exports every business already has &mdash; the work log (what got done) and the invoices
    (what got billed). This page lines them up and shows <strong>only the mismatches</strong>:
    finished jobs nobody ever invoiced, and invoices sitting unpaid.
  </p>
  <p style="max-width:40rem"><strong>Your books never leave your machine.</strong>
    <span style="color:var(--ink-soft)">The matching runs entirely in your browser &mdash; there is
    no server to send these files to. Check the network tab: zero requests after load.</span></p>

  <div class="ml-drops">
    <div class="ml-drop" id="ml-work" role="button" tabindex="0" aria-label="Choose the work log CSV">
      <strong>1 &middot; Work log</strong>
      <span id="ml-work-label">jobs / tickets / schedule export (.csv)</span>
      <input type="file" accept=".csv,.tsv,.txt" style="display:none">
    </div>
    <div class="ml-drop" id="ml-inv" role="button" tabindex="0" aria-label="Choose the invoices CSV">
      <strong>2 &middot; Invoices</strong>
      <span id="ml-inv-label">invoice / billing export (.csv)</span>
      <input type="file" accept=".csv,.tsv,.txt" style="display:none">
    </div>
  </div>
  <div class="ml-actions">
    <button class="btn" id="ml-sample" type="button">See it on the sample company</button>
  </div>
  <p class="ml-note" style="text-align:center;margin-top:.8rem">The sample is Cedar Field Services
    &mdash; an invented company, every number made up. Excel users: <code>File &rarr; Save As &rarr;
    CSV</code> first.</p>

  <section id="ml-report" aria-live="polite">
    <h2 id="ml-title" style="margin-bottom:.9rem"></h2>
    <div class="ml-kpis" id="ml-kpis"></div>
    <div id="ml-sections"></div>
    <div class="ml-cta">
      <strong>Found real money in the gap?</strong>
      <p>This exact report, built on your real exports and kept current every week, is what the
      <a href="/spreadsheet-cleanup-service/">$300 cleanup</a> and the
      <a href="/free-demo/">free 1-day demo</a> deliver. Messy files are fine &mdash; that's the point.</p>
      <a class="btn" href="/free-demo/">Get it on your real data — free</a>
      <p style="margin:.9rem 0 0;font-size:.85rem">Want the broader once-over first? The
      <a href="/spreadsheet-health-check/">Spreadsheet Health Check</a> reads any single export for
      dead columns, mixed dates and duplicates &mdash; same rule, nothing uploads.</p>
    </div>
  </section>
</main>
"""

SCRIPT = r"""
<script>
(function(){
'use strict';
/* All local. No fetch, no XHR, no beacon. */

function parseCSV(text){
  var rows=[], row=[], cell='', q=false, i=0, c;
  var delim = (text.split('\t').length > text.split(',').length) ? '\t' : ',';
  while(i < text.length){
    c = text[i];
    if(q){ if(c === '"'){ if(text[i+1] === '"'){ cell+='"'; i++; } else q=false; } else cell += c; }
    else if(c === '"') q = true;
    else if(c === delim){ row.push(cell); cell=''; }
    else if(c === '\n' || c === '\r'){
      if(c === '\r' && text[i+1] === '\n') i++;
      row.push(cell); cell='';
      if(row.length > 1 || row[0] !== '') rows.push(row);
      row=[];
    } else cell += c;
    i++;
  }
  if(cell !== '' || row.length){ row.push(cell); rows.push(row); }
  return rows;
}

function toTable(rows){
  var header = rows[0].map(function(h,i){ return (h||'').trim() || ('col'+(i+1)); });
  var body = rows.slice(1).filter(function(r){ return r.join('').trim() !== ''; });
  return { header: header, body: body };
}
function colValues(t, ci){ return t.body.map(function(r){ return (r[ci]===undefined?'':String(r[ci])).trim(); }); }

/* Join key: the column PAIR whose non-blank value sets overlap most. */
function detectJoin(a, b){
  var best = {score: 0, ai: 0, bi: 0};
  for(var i=0;i<a.header.length;i++){
    var av = colValues(a,i).filter(Boolean);
    if(!av.length) continue;
    var aset = {}; av.forEach(function(v){ aset[v]=1; });
    for(var j=0;j<b.header.length;j++){
      var bv = colValues(b,j).filter(Boolean);
      if(!bv.length) continue;
      var hits = 0; bv.forEach(function(v){ if(aset[v]) hits++; });
      var score = hits / Math.max(av.length, bv.length);
      if(hits >= 2 && score > best.score) best = {score:score, ai:i, bi:j};
    }
  }
  return best.score > 0.2 ? best : null;
}
function money(v){
  var m = String(v).replace(/[$,\s]/g,'').replace(/^\((.*)\)$/, '-$1');
  var n = parseFloat(m);
  return isFinite(n) ? n : null;
}
function detectAmount(t){
  var byName = -1, bestNum = -1, bestFrac = 0;
  t.header.forEach(function(h,i){
    if(byName < 0 && /amount|total|price|value|charge|cost/i.test(h)) byName = i;
    var vals = colValues(t,i).filter(Boolean);
    if(!vals.length) return;
    var frac = vals.filter(function(v){ return money(v) !== null; }).length / vals.length;
    if(frac > bestFrac){ bestFrac = frac; bestNum = i; }
  });
  return byName >= 0 ? byName : (bestFrac > 0.7 ? bestNum : -1);
}
function parseDate(v){
  v = String(v).trim();
  var m = v.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if(m) return new Date(+m[1], +m[2]-1, +m[3]);
  m = v.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/);
  if(m) return new Date(m[3].length===2 ? 2000+ +m[3] : +m[3], +m[1]-1, +m[2]);
  return null;
}
function detectDate(t, prefer){
  var byName = -1, best = -1, bestFrac = 0;
  t.header.forEach(function(h,i){
    if(byName < 0 && prefer.test(h)) byName = i;
    var vals = colValues(t,i).filter(Boolean);
    if(!vals.length) return;
    var frac = vals.filter(function(v){ return parseDate(v) !== null; }).length / vals.length;
    if(frac > bestFrac){ bestFrac = frac; best = i; }
  });
  if(byName >= 0){
    var vals = colValues(t, byName).filter(Boolean);
    var ok = vals.length && vals.filter(function(v){ return parseDate(v)!==null; }).length / vals.length > 0.6;
    if(ok) return byName;
  }
  return bestFrac > 0.6 ? best : -1;
}
function detectPaid(t){
  for(var i=0;i<t.header.length;i++) if(/paid/i.test(t.header[i]) && !/unpaid/i.test(t.header[i])) return i;
  return -1;
}

function fmt(n){ return '$' + n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

function reconcile(work, inv, asOf){
  var join = detectJoin(work, inv);
  if(!join) return { error: 'Could not find a shared reference column (a job number or ID that appears in both files). Every match here is by exact ID -- no guessing.' };
  var wAmt = detectAmount(work), iAmt = detectAmount(inv);
  var invKeys = {}; colValues(inv, join.bi).forEach(function(v){ if(v) invKeys[v]=1; });

  var never = [], neverTotal = 0;
  work.body.forEach(function(r){
    var k = (r[join.ai]||'').trim();
    if(!k || invKeys[k]) return;
    var amt = wAmt >= 0 ? money(r[wAmt]) : null;
    if(amt !== null) neverTotal += amt;
    never.push({ key:k, row:r, amt:amt });
  });

  var paidCol = detectPaid(inv), dateCol = detectDate(inv, /invoice date|inv date|date/i);
  var unpaid = [], unpaidTotal = 0, agedTotal = 0, aged = [];
  if(paidCol >= 0){
    inv.body.forEach(function(r){
      var paidVal = (r[paidCol]||'').trim();
      var isPaid = paidVal !== '' && !/^(no|n|false|unpaid|0)$/i.test(paidVal);
      if(isPaid) return;
      var amt = iAmt >= 0 ? money(r[iAmt]) : null;
      if(amt !== null) unpaidTotal += amt;
      var days = null;
      if(dateCol >= 0){
        var d = parseDate(r[dateCol]);
        if(d) days = Math.floor((asOf - d) / 86400000);
      }
      /* Display the invoice's own reference (first cell), not the join key --
         the aged table says "Invoice", so it must show INV-2210, not J-104. */
      var rec = { key:(r[0]||r[join.bi]||'').trim(), amt:amt, days:days };
      unpaid.push(rec);
      if(days !== null && days > 60){ aged.push(rec); if(amt !== null) agedTotal += amt; }
    });
  }
  return {
    join: { workCol: work.header[join.ai], invCol: inv.header[join.bi] },
    never: never, neverTotal: neverTotal,
    paidDetected: paidCol >= 0, unpaid: unpaid, unpaidTotal: unpaidTotal,
    aged: aged, agedTotal: agedTotal
  };
}

function render(names, r, asOfLabel){
  var rep = document.getElementById('ml-report');
  document.getElementById('ml-title').textContent = 'Leak report: ' + names + (asOfLabel ? ' (as of ' + asOfLabel + ')' : '');
  if(r.error){
    document.getElementById('ml-kpis').innerHTML = '';
    document.getElementById('ml-sections').innerHTML = '<p class="ml-note">' + esc(r.error) + '</p>';
    rep.style.display = 'block'; return;
  }
  var k = '<div class="ml-kpi' + (r.never.length? ' k-bad':'') + '"><b>' + fmt(r.neverTotal) + '</b><span>' + r.never.length + ' job' + (r.never.length===1?'':'s') + ' completed, never invoiced</span></div>';
  if(r.paidDetected){
    k += '<div class="ml-kpi"><b>' + fmt(r.unpaidTotal) + '</b><span>' + r.unpaid.length + ' invoice' + (r.unpaid.length===1?'':'s') + ' unpaid</span></div>';
    k += '<div class="ml-kpi' + (r.aged.length? ' k-bad':'') + '"><b>' + fmt(r.agedTotal) + '</b><span>unpaid past 60 days</span></div>';
  } else {
    k += '<div class="ml-kpi"><b>&mdash;</b><span>no paid/unpaid column found in the invoice file</span></div>';
  }
  document.getElementById('ml-kpis').innerHTML = k;

  var out = '<p class="ml-note">Matched on <strong>' + esc(r.join.workCol) + '</strong> &harr; <strong>' + esc(r.join.invCol) + '</strong> by exact ID &mdash; nothing fuzzy, nothing guessed.</p>';
  if(r.never.length){
    out += '<h3 class="ml-h3">A &middot; Completed but never invoiced</h3><table class="ml-table"><tr><th>Ref</th><th>Details</th><th style="text-align:right">Amount</th></tr>';
    r.never.forEach(function(x){
      var detail = x.row.filter(function(v,i){ return v && i !== 0; }).slice(0,3).join(' · ');
      out += '<tr><td>' + esc(x.key) + '</td><td>' + esc(detail) + '</td><td class="num">' + (x.amt===null?'—':fmt(x.amt)) + '</td></tr>';
    });
    out += '</table>';
  } else {
    out += '<h3 class="ml-h3">A &middot; Completed but never invoiced</h3><p class="ml-note">None -- every job in the work log has a matching invoice. That is the result you want.</p>';
  }
  if(r.paidDetected && r.aged.length){
    out += '<h3 class="ml-h3">B &middot; Unpaid past 60 days</h3><table class="ml-table"><tr><th>Invoice</th><th>Days outstanding</th><th style="text-align:right">Amount</th></tr>';
    r.aged.forEach(function(x){
      out += '<tr><td>' + esc(x.key) + '</td><td>' + (x.days===null?'—':x.days + 'd') + '</td><td class="num">' + (x.amt===null?'—':fmt(x.amt)) + '</td></tr>';
    });
    out += '</table>';
  }
  document.getElementById('ml-sections').innerHTML = out;
  rep.style.display = 'block';
  rep.scrollIntoView({behavior:'smooth', block:'start'});
}

/* Cedar Field Services -- INVENTED sample, identical to the workbook build. */
var SAMPLE_WORK = 'Job No,Date,Client,Description,Amount\n' +
'J-101,2026-06-22,Hargrove Property Grp,Irrigation main repair,740.00\n' +
'J-102,2026-06-25,Bell & Sons HOA,"Storm cleanup, common area",1280.00\n' +
'J-103,2026-06-28,Rivertown Storage,Gate motor replacement,965.00\n' +
'J-104,2026-07-01,Hargrove Property Grp,Emergency leak call-out,410.00\n' +
'J-105,2026-07-02,Coastal Dental,Parking lot pressure wash,380.00\n' +
'J-106,2026-07-06,Bell & Sons HOA,Fence section rebuild,1620.00\n' +
'J-107,2026-07-08,Marlin Self-Serve,Bay door track repair,540.00\n' +
'J-108,2026-07-09,Rivertown Storage,Unit door replacements (x3),1150.00\n' +
'J-109,2026-07-12,Coastal Dental,After-hours lighting fix,295.00\n' +
'J-110,2026-07-14,Northgate Church,Grounds cleanup + haul-away,860.00\n' +
'J-111,2026-07-16,Hargrove Property Grp,Weekend emergency call-out,520.00\n' +
'J-112,2026-07-18,Marlin Self-Serve,Camera pole reset,310.00\n' +
'J-113,2026-07-21,Bell & Sons HOA,Playground mulch install,990.00\n' +
'J-114,2026-07-24,Northgate Church,"Gutter clear, full building",450.00\n';
var SAMPLE_INV = 'Invoice No,Job No,Invoice Date,Amount,Paid Date\n' +
'INV-2201,J-101,2026-06-24,740.00,2026-07-02\n' +
'INV-2202,J-102,2026-06-27,1280.00,2026-07-18\n' +
'INV-2203,J-103,2026-06-30,965.00,\n' +
'INV-2204,J-105,2026-07-04,380.00,2026-07-11\n' +
'INV-2205,J-106,2026-07-08,1620.00,\n' +
'INV-2206,J-107,2026-07-10,540.00,2026-07-22\n' +
'INV-2207,J-108,2026-07-11,1150.00,\n' +
'INV-2208,J-110,2026-07-15,860.00,2026-07-24\n' +
'INV-2209,J-113,2026-07-22,990.00,\n' +
'INV-2210,J-104,2026-05-12,410.00,\n' +
'INV-2211,J-109,2026-04-20,295.00,\n';

var files = { work: null, inv: null };
function wire(id, slot){
  var el = document.getElementById(id);
  var input = el.querySelector('input');
  function set(f){
    if(!f) return;
    var reader = new FileReader();
    reader.onload = function(){
      files[slot] = { name: f.name, text: String(reader.result) };
      el.classList.add('is-set');
      document.getElementById(id + '-label').textContent = f.name;
      maybeRun();
    };
    reader.readAsText(f);
  }
  el.addEventListener('click', function(){ input.click(); });
  el.addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); input.click(); } });
  input.addEventListener('change', function(){ set(input.files[0]); });
  ['dragover','dragenter'].forEach(function(ev){ el.addEventListener(ev, function(e){ e.preventDefault(); el.classList.add('is-over'); }); });
  ['dragleave','drop'].forEach(function(ev){ el.addEventListener(ev, function(e){ e.preventDefault(); el.classList.remove('is-over'); }); });
  el.addEventListener('drop', function(e){ set(e.dataTransfer.files[0]); });
}
function maybeRun(){
  if(!files.work || !files.inv) return;
  try {
    var r = reconcile(toTable(parseCSV(files.work.text)), toTable(parseCSV(files.inv.text)), new Date());
    render(files.work.name + ' vs ' + files.inv.name, r, 'today');
  } catch(e){
    alert('Could not reconcile those files. If they are Excel workbooks, save as CSV first.');
  }
}
wire('ml-work','work'); wire('ml-inv','inv');
document.getElementById('ml-sample').addEventListener('click', function(){
  var r = reconcile(toTable(parseCSV(SAMPLE_WORK)), toTable(parseCSV(SAMPLE_INV)), new Date(2026, 6, 28));
  render('Cedar Field Services (invented sample)', r, '2026-07-28, frozen');
});
})();
</script>
"""

LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Money Leak Finder",
  "url": "https://automatedworkflowllc.com/money-leak-finder/",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Any",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "description": "Free in-browser reconciler: jobs completed but never invoiced, invoices unpaid past 60 days. No upload -- your books never leave your machine."
}
</script>
"""


def main() -> None:
    s = TEMPLATE.read_text(encoding='utf-8')
    head = s[:s.index('</header>') + len('</header>')]
    footer = s[s.index('<footer'):s.index('</footer>') + len('</footer>')]

    head = re.sub(r'<title>.*?</title>', f'<title>{TITLE}</title>', head, flags=re.S)
    head = re.sub(r'(<meta name="description" content=").*?(">)', rf'\g<1>{DESC}\g<2>', head)
    head = re.sub(r'(<link rel="canonical" href=").*?(">)', rf'\g<1>{CANON}\g<2>', head)
    head = re.sub(r'(<meta property="og:title" content=").*?(">)', rf'\g<1>{TITLE}\g<2>', head)
    head = re.sub(r'(<meta property="og:description" content=").*?(">)', rf'\g<1>{DESC}\g<2>', head)
    head = re.sub(r'(<meta property="og:url" content=").*?(">)', rf'\g<1>{CANON}\g<2>', head)
    head = head.replace('</head>', f'<style>{PAGE_CSS}</style>\n</head>')

    page = head + MAIN + footer + LD + SCRIPT + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
