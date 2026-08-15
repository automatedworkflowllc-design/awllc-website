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

from toolkit import with_core, with_xlsx, PLAIN_CSS, plain_english, with_plain

PLAIN = plain_english(
    'Lines up the work you finished against the invoices you sent, and shows you only the places they do not match.',
    '<b>It finds money you already earned but never collected</b> &mdash; jobs completed and never billed, and invoices that quietly went unpaid. It will even write the follow-up emails for you, though it cannot send them; you always press send.',
    'Two files you already have: a list of jobs or work done, and a list of invoices.',
    'About ten seconds. Your books never leave your machine.')


ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'money-leak-finder'

# 2026-08-12 retitle. "money leak" autocompletes to money leakage meaning / money leaks
# feng shui -- consumer personal-finance and superstition intent, not a business tool.
# The name is ours, so it has no searchers except us.
# ⚠ The SEO audit proposed leading with "Unbilled Jobs". CHECKED IT: "unbilled jobs"
# returns ZERO autocomplete suggestions -- swapping one invented phrase for another.
# "invoice aging" returns ten (invoice aging report, invoice aging calculator, invoice
# aging formula in excel) and "accounts receivable aging" fills all ten slots. That is
# the searchable name for what this tool already does: unpaid past 60 days, from the
# user's own export. Brand name kept in the H1, not the title.
TITLE = 'Free Invoice Aging Report — Find Unpaid & Unbilled Jobs'
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
.ml-drop.is-over{border-color:var(--accent,var(--green,#1E7A47));background:var(--well)}
.ml-drop.is-set{border-style:solid;border-color:var(--accent,var(--green,#1E7A47))}
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
/* --- section C: the drafts --- */
.ml-drafts{display:flex;flex-direction:column;gap:.9rem;margin:.6rem 0 1.4rem}
.ml-draft{border:1px solid var(--line);border-radius:12px;background:var(--card);padding:.85rem .95rem}
.ml-draft-head{display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;margin-bottom:.6rem}
.ml-draft-ref{font-family:var(--mono);font-size:.76rem;color:var(--ink-soft);overflow-wrap:anywhere}
.ml-tier{font-family:var(--mono);font-size:.66rem;text-transform:uppercase;letter-spacing:.07em;
border:1px solid currentColor;border-radius:.3rem;padding:.1rem .4rem;white-space:nowrap}
.ml-tier.t-neutral{color:#3F6B57}
.ml-tier.t-firm{color:#8A6A16}
.ml-tier.t-serious{color:#B4452C}
.ml-tier.t-unbilled{color:#2E5AAC}
.ml-tier.t-unknown{color:var(--ink-soft)}
.ml-copy{margin-left:auto;font:inherit;font-size:.78rem;padding:.28rem .8rem;cursor:pointer;
border:1px solid var(--line-strong);border-radius:.4rem;background:var(--bg-soft);color:var(--ink)}
.ml-copy:hover{border-color:var(--accent,var(--green,#1E7A47))}
.ml-copy:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.ml-draft-sub{display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;
color:var(--ink-soft);margin-bottom:.5rem}
.ml-draft-sub input{display:block;width:100%;margin-top:.2rem;font:inherit;font-size:.88rem;
color:var(--ink);background:var(--bg-soft);border:1px solid var(--line);border-radius:.4rem;padding:.4rem .5rem}
.ml-draft textarea{width:100%;font:inherit;font-size:.88rem;line-height:1.5;color:var(--ink);
background:var(--bg-soft);border:1px solid var(--line);border-radius:.4rem;padding:.5rem;resize:vertical}
.ml-draft input:focus-visible,.ml-draft textarea:focus-visible{outline:3px solid var(--focus);outline-offset:1px}
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
      <input type="file" accept=".csv,.tsv,.txt,.xlsx,.xlsm" style="display:none">
    </div>
    <div class="ml-drop" id="ml-inv" role="button" tabindex="0" aria-label="Choose the invoices CSV">
      <strong>2 &middot; Invoices</strong>
      <span id="ml-inv-label">invoice / billing export (.csv)</span>
      <input type="file" accept=".csv,.tsv,.txt,.xlsx,.xlsm" style="display:none">
    </div>
  </div>
  <div class="ml-actions">
    <button class="btn" id="ml-sample" type="button">See it on the sample company</button>
  </div>
  <p class="ml-note" style="text-align:center;margin-top:.8rem">The sample is Cedar Field Services
    &mdash; an invented company, every number made up. <strong>Excel .xlsx files work directly.</strong> Otherwise <code>File &rarr; Save As &rarr;
    CSV</code> first.</p>

  <section id="ml-report" aria-live="polite">
    <h2 id="ml-title" style="margin-bottom:.9rem"></h2>
    <div class="ml-kpis" id="ml-kpis"></div>
    <div id="ml-sections"></div>
    <div class="ml-cta">
      <strong>Found real money in the gap?</strong>
      <p>This exact report, built on your real exports and kept current every week, is what the
      <a href="/spreadsheet-cleanup-service/">$300 cleanup</a> and the
      <a href="/free-demo/?from=money-leak">free 1-day demo</a> deliver. Messy files are fine &mdash; that's the point.</p>
      <a class="btn" href="/free-demo/?from=money-leak">Get it on your real data — free</a>
      <!-- Filled in by render() ONLY for a visitor's own file, never for the sample: a mailto:
           carrying the totals this page just computed, so a prospect who has seen a number does
           not have to restate it on a blank form. mailto: issues NO network request, so the
           page's "zero requests after load" promise and "there is nowhere here to send it"
           survive intact -- the visitor's own mail client sends it, and only if they press send. -->
      <div id="ml-send" hidden></div>
      <p style="margin:.9rem 0 0;font-size:.85rem">Want the broader once-over first? The
      <a href="/spreadsheet-health-check/">Spreadsheet Health Check</a> reads any single export for
      dead columns, mixed dates and duplicates &mdash; same rule, nothing uploads. Same customer entered three ways? The
      <a href="/duplicate-customer-finder/">Duplicate Customer Finder</a> shows your real count.</p>
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
/* A join key is an IDENTIFIER. Two properties follow from that, and this function used to
   assume neither -- which produced the worst output this tool can produce: a confident
   "every job in the work log has a matching invoice" over a book with a real uninvoiced job.
   Reproduced 2026-08-14 with three jobs and two invoices.

   1. IT IS CASE-INSENSITIVE. Two systems exporting the same job write JOB-1042 and job-1042.
      Matching those as different values did not merely miss one row -- it dropped the ID
      column's hit count below a coincidentally-matching AMOUNT column, so the amount column
      silently won and became the join key.

   2. IT IS NEARLY UNIQUE. An amount is not an identifier: two jobs at $500 are ordinary. Once
      Amount was the key, an uninvoiced $500 job matched a DIFFERENT job's $500 invoice and was
      counted as billed. The leak the page exists to surface was reported as clean.

   So candidates are now scored on normalised values and must be >=90% unique on the work side.
   The uniqueness test is what actually rejects Amount, and it does so on principle rather than
   by guessing at column names -- a column called "Total" or "Value" would fail it too. */
function normKey(v){ return String(v).replace(/\s+/g,' ').trim().toLowerCase(); }
function detectJoin(a, b){
  var best = {score: 0, ai: 0, bi: 0};
  for(var i=0;i<a.header.length;i++){
    var av = colValues(a,i).filter(Boolean).map(normKey);
    if(!av.length) continue;
    var aset = {}; av.forEach(function(v){ aset[v]=1; });
    var uniq = 0; for(var k in aset){ if(aset.hasOwnProperty(k)) uniq++; }
    if(uniq / av.length < 0.9) continue;          /* not an identifier -- repeats too much */
    for(var j=0;j<b.header.length;j++){
      var bv = colValues(b,j).filter(Boolean).map(normKey);
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
  /* Only a header containing "paid" used to match, so a column called STATUS --
     what QuickBooks, Xero and Jobber all emit -- was invisible, and the tool's
     second headline promise ("invoices unpaid past 60 days") silently did
     nothing on the most common export there is. Found 2026-08-09 by running the
     tool on a realistic file instead of its own sample. /demo/ already looked
     for status|state|settled; the tool did not, so the demo was more capable
     than the product it demonstrates. */
  for(var i=0;i<t.header.length;i++) if(/paid|status|state|settled/i.test(t.header[i]) && !/unpaid/i.test(t.header[i])) return i;
  return -1;
}
/* Widening the header match ALONE would have been worse than the bug. The old
   value rule was "anything non-empty means paid", which is right for a Date
   Paid column and catastrophically wrong for a Status column: "Open" would
   read as PAID and the tool would UNDERSTATE what you are owed -- a confident
   wrong answer in the direction that costs money. So a value counts as settled
   only if it is a recognised settled word, or a real date (a Date Paid column
   carrying a date means exactly that). Everything else -- Open, Sent, Overdue,
   Partial, Due, blank -- is unpaid. */
function looksSettled(v, parseDateFn){
  if(v === '') return false;
  if(/^(paid|yes|y|true|settled|complete|completed|closed|1)$/i.test(v)) return true;
  return parseDateFn(v) !== null;
}
function detectClient(t){
  for(var i=0;i<t.header.length;i++) if(/client|customer|account|company|payer/i.test(t.header[i])) return i;
  return -1;
}
function detectDesc(t){
  for(var i=0;i<t.header.length;i++) if(/desc|work|service|detail|notes?/i.test(t.header[i])) return i;
  return -1;
}
/* Tone is DERIVED from how late the invoice is -- never chosen, never escalated
   by mood. Same rule the approve-gate uses: the data picks the register. */
function tierFor(days){
  if(days === null) return { id:'unknown', label:'Needs a look' };
  if(days > 120) return { id:'serious', label:'Serious' };
  if(days > 90)  return { id:'firm',    label:'Firm' };
  return { id:'neutral', label:'Neutral' };
}

/* Build a draft from ONLY what the two files actually contain: who, which
   reference, how much, how late. No invented urgency, no legal threats, no
   promises about what happens next -- those are the sender's to add, if ever. */
function draftFor(rec, kind){
  var who = rec.client ? rec.client : 'there';
  var greet = 'Hi ' + who + ',';
  var amt = (rec.amt === null || rec.amt === undefined) ? null : fmt(rec.amt);
  var job = rec.desc ? rec.desc : '';

  if(kind === 'never'){
    return {
      subject: 'Invoice for ' + (job || ('job ' + rec.key)),
      tier: { id:'unbilled', label:'Never billed' },
      body: greet + '\n\n' +
        'Going back through our records for ' + (job ? ('"' + job + '"') : ('job ' + rec.key)) +
        ' — it looks like we completed this one but never sent you an invoice for it. That is on us.\n\n' +
        'Reference: ' + rec.key + (amt ? ('\nAmount: ' + amt) : '') + '\n\n' +
        'I can send the invoice over today unless you would rather I hold it. Let me know if anything about the job looks wrong on your side and I will sort it before it goes out.\n\n' +
        'Thanks,'
    };
  }

  var t = tierFor(rec.days);
  var late = rec.days === null ? null : rec.days;
  var base = 'Reference: ' + rec.key + (amt ? ('\nAmount: ' + amt) : '') +
             (late !== null ? ('\nOutstanding: ' + late + ' days') : '');

  if(t.id === 'neutral'){
    return { subject: 'Quick check on invoice ' + rec.key, tier: t, body:
      greet + '\n\nJust circling back on this one — it is still showing as open on my end, and I would rather ask than assume it got lost.\n\n' +
      base + '\n\nIf it has already gone out, ignore me entirely. If something is holding it up, tell me what and I will work with it.\n\nThanks,' };
  }
  if(t.id === 'firm'){
    return { subject: 'Invoice ' + rec.key + ' — still open', tier: t, body:
      greet + '\n\nThis one has been outstanding a while now and I want to get it closed out rather than let it drift further.\n\n' +
      base + '\n\nCould you let me know where it sits in your process, and roughly when I should expect it? If there is a problem with the invoice itself, I would rather hear that than keep sending reminders.\n\nThanks,' };
  }
  if(t.id === 'serious'){
    return { subject: 'Invoice ' + rec.key + ' — need to get this resolved', tier: t, body:
      greet + '\n\nI have followed up on this a few times and it is now well past terms, so I want to deal with it directly rather than send another reminder.\n\n' +
      base + '\n\nCan you tell me whether this is going to be paid, and when? If there is a dispute or a problem on your side I would genuinely rather know now so we can settle it properly.\n\nThanks,' };
  }
  return { subject: 'Invoice ' + rec.key, tier: t, body:
    greet + '\n\nThis invoice is showing as open, but there is no invoice date in the file I have, so I cannot tell how long it has been outstanding.\n\n' +
    base + '\n\nWorth checking the date on your copy before sending anything — a reminder with the wrong age in it does more harm than no reminder.\n\nThanks,' };
}

function fmt(n){ return '$' + n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

function reconcile(work, inv, asOf){
  var join = detectJoin(work, inv);
  if(!join) return { error: 'Could not find a shared reference column (a job number or ID that appears in both files). Every match here is by exact ID -- no guessing.' };
  var wAmt = detectAmount(work), iAmt = detectAmount(inv);
  /* Keys normalised the SAME way detectJoin scored them. Choosing the right column and then
     matching it case-sensitively would reintroduce the identical bug one step later. */
  var invKeys = {}; colValues(inv, join.bi).forEach(function(v){ if(v) invKeys[normKey(v)]=1; });

  /* Map the shared job key -> client + description from the WORK log, so a chase
     draft can name the customer and the job. Invoice files often carry neither. */
  var wClient = detectClient(work), wDesc = detectDesc(work);
  var meta = {};
  work.body.forEach(function(r){
    var k = normKey(r[join.ai]||'');
    if(!k) return;
    meta[k] = {
      client: wClient >= 0 ? (r[wClient]||'').trim() : '',
      desc:   wDesc   >= 0 ? (r[wDesc]||'').trim()   : ''
    };
  });

  var never = [], neverTotal = 0;
  work.body.forEach(function(r){
    var k = normKey(r[join.ai]||'');
    if(!k || invKeys[k]) return;
    var amt = wAmt >= 0 ? money(r[wAmt]) : null;
    if(amt !== null) neverTotal += amt;
    var m = meta[k] || { client:'', desc:'' };
    /* MATCH on the normalised key, but SHOW the spelling from their own file. Displaying
       a lower-cased version of someone's own job number is a small lie about their data,
       and this page is read as a report on that data. */
    never.push({ key:(r[join.ai]||'').trim() || k, row:r, amt:amt, client:m.client, desc:m.desc });
  });

  var paidCol = detectPaid(inv), dateCol = detectDate(inv, /invoice date|inv date|date/i);
  var unpaid = [], unpaidTotal = 0, agedTotal = 0, aged = [];
  if(paidCol >= 0){
    inv.body.forEach(function(r){
      var paidVal = (r[paidCol]||'').trim();
      if(looksSettled(paidVal, parseDate)) return;
      var amt = iAmt >= 0 ? money(r[iAmt]) : null;
      if(amt !== null) unpaidTotal += amt;
      var days = null;
      if(dateCol >= 0){
        var d = parseDate(r[dateCol]);
        if(d) days = Math.floor((asOf - d) / 86400000);
      }
      /* Display the invoice's own reference (first cell), not the join key --
         the aged table says "Invoice", so it must show INV-2210, not J-104. */
      var jk = normKey(r[join.bi]||'');
      var m = meta[jk] || { client:'', desc:'' };
      var rec = { key:(r[0]||r[join.bi]||'').trim(), amt:amt, days:days,
                  client:m.client, desc:m.desc };
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

/* Build the "send me these numbers" action. TOTALS AND COUNTS ONLY -- never a customer
   name, an invoice line or a file name. The promise on this page is that the file stays
   here, and a summary that leaked client names would violate the spirit of it even though
   the file itself never moved. Sample data never reaches this: nobody should email Colin
   about Cedar Field Services, which does not exist. */
function sendBlock(r){
  var host = document.getElementById('ml-send');
  if(!host) return;
  var lines = [];
  if(r.never.length){
    lines.push('- ' + fmt(r.neverTotal) + ' across ' + r.never.length + ' job' +
               (r.never.length===1?'':'s') + ' completed but never invoiced');
  }
  if(r.paidDetected){
    if(r.unpaid.length){
      lines.push('- ' + fmt(r.unpaidTotal) + ' across ' + r.unpaid.length + ' unpaid invoice' +
                 (r.unpaid.length===1?'':'s'));
    }
    if(r.aged.length){
      lines.push('- ' + fmt(r.agedTotal) + ' of that is past 60 days');
    }
  }
  if(!lines.length){ host.hidden = true; host.innerHTML = ''; return; }

  var body = 'Hi Colin,\n\nI ran the money leak finder on my own exports. It found:\n\n' +
             lines.join('\n') +
             '\n\nI have not sent you the files themselves.\n\n' +
             '[Anything you want to add about your setup]\n';
  var href = 'mailto:colin@automatedworkflowllc.com' +
             '?subject=' + encodeURIComponent('Money leak finder - what it found on my books') +
             '&body=' + encodeURIComponent(body);

  host.hidden = false;
  host.innerHTML =
    '<p class="ml-note" style="margin:.9rem 0 .5rem">Or send Colin just these figures &mdash; ' +
    'this opens your own email app with the totals above already written in. ' +
    'Your files stay in this browser; nothing is attached.</p>' +
    '<a class="btn" id="ml-mail" href="' + href + '">Email these numbers to Colin</a> ' +
    '<button type="button" class="ml-copy" id="ml-copysum">Copy the summary instead</button>';

  var cp = document.getElementById('ml-copysum');
  cp.addEventListener('click', function(){
    var done = function(){ cp.textContent = 'Copied'; setTimeout(function(){ cp.textContent = 'Copy the summary instead'; }, 1600); };
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(body).then(done, done);
    } else { done(); }
  });
}

function render(names, r, asOfLabel, isReal){
  var rep = document.getElementById('ml-report');
  document.getElementById('ml-title').textContent = 'Leak report: ' + names + (asOfLabel ? ' (as of ' + asOfLabel + ')' : '');
  var sendHost = document.getElementById('ml-send');
  if(sendHost){ sendHost.hidden = true; sendHost.innerHTML = ''; }
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

  /* The dollars count up -- and always LAND on the exact computed figure.
     Same rule as /check/'s visual: motion never touches the arithmetic.
     Reduced-motion users get the final numbers immediately. */
  (function(){
    var els = document.getElementById('ml-kpis').querySelectorAll('.ml-kpi b');
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    for(var i = 0; i < els.length; i++)(function(el){
      var m = /^\$([\d,]+(?:\.\d+)?)$/.exec(el.textContent.trim());
      if(!m || reduce) return;
      var target = parseFloat(m[1].replace(/,/g, '')), final = el.textContent;
      var t0 = null;
      var tick = function(ts){
        if(t0 === null) t0 = ts;
        var p = Math.min(1, (ts - t0) / 900);
        el.textContent = '$' + Math.round(target * (1 - Math.pow(1 - p, 3)))
          .toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        if(p < 1) requestAnimationFrame(tick); else el.textContent = final;
      };
      requestAnimationFrame(tick);
    })(els[i]);
  })();

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
  /* C -- the half every other tool leaves out: what to actually send.
     Drafts are built here, in the page, and go nowhere on their own. */
  var items = [];
  r.never.forEach(function(x){ items.push({ rec:x, kind:'never' }); });
  if(r.paidDetected) r.aged.forEach(function(x){ items.push({ rec:x, kind:'aged' }); });

  if(items.length){
    out += '<h3 class="ml-h3">C &middot; Drafts you can send</h3>';
    out += '<p class="ml-note">One draft per row above, written from your file and nothing else. ' +
           'The tone is <strong>derived from how late the invoice is</strong>, not chosen &mdash; that is ' +
           'the whole idea. Edit anything, copy what you want, send it yourself. ' +
           '<strong>Nothing here can send: this page has no server and no mail access.</strong></p>';
    out += '<div class="ml-drafts">';
    items.forEach(function(it, i){
      var d = draftFor(it.rec, it.kind);
      out += '<div class="ml-draft">' +
        '<div class="ml-draft-head">' +
          '<span class="ml-tier t-' + d.tier.id + '">' + esc(d.tier.label) + '</span>' +
          '<span class="ml-draft-ref">' + esc(it.rec.key) +
            (it.rec.client ? ' &middot; ' + esc(it.rec.client) : '') +
            (it.rec.days !== null && it.rec.days !== undefined ? ' &middot; ' + it.rec.days + 'd' : '') +
          '</span>' +
          '<button type="button" class="ml-copy" data-i="' + i + '">Copy</button>' +
        '</div>' +
        '<label class="ml-draft-sub">Subject <input type="text" id="ml-sub-' + i + '" value="' + esc(d.subject) + '"></label>' +
        '<textarea id="ml-body-' + i + '" rows="12" spellcheck="true">' + esc(d.body) + '</textarea>' +
      '</div>';
    });
    out += '</div>';
  }

  document.getElementById('ml-sections').innerHTML = out;

  if(isReal){ sendBlock(r); }

  Array.prototype.forEach.call(document.querySelectorAll('.ml-copy'), function(btn){
    /* The summary button in #ml-send shares this class for styling but carries no data-i
       and wires its own handler. Without this guard it would throw on click. */
    if(btn.getAttribute('data-i') === null) return;
    btn.addEventListener('click', function(){
      var i = btn.getAttribute('data-i');
      var sub = document.getElementById('ml-sub-' + i);
      var body = document.getElementById('ml-body-' + i);
      var text = 'Subject: ' + sub.value + '\n\n' + body.value;
      var done = function(){ btn.textContent = 'Copied'; setTimeout(function(){ btn.textContent = 'Copy'; }, 1600); };
      if(navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(text).then(done, function(){ body.select(); done(); });
      } else { body.select(); try{ document.execCommand('copy'); }catch(e){} done(); }
    });
  });

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
    readAny(f, function(text){
      files[slot] = { name: f.name, text: text };
      el.classList.add('is-set');
      document.getElementById(id + '-label').textContent = f.name;
      maybeRun();
    });
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
    render(files.work.name + ' vs ' + files.inv.name, r, 'today', true);
  } catch(e){
    alert('Could not reconcile those files. If they are Excel workbooks, save as CSV first.');
  }
}
wire('ml-work','work'); wire('ml-inv','inv');
document.getElementById('ml-sample').addEventListener('click', function(){
  var r = reconcile(toTable(parseCSV(SAMPLE_WORK)), toTable(parseCSV(SAMPLE_INV)), new Date(2026, 6, 28));
  render('Cedar Field Services (invented sample)', r, '2026-07-28, frozen', false);
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
    head = head.replace('</head>', f'<style>{PAGE_CSS}{PLAIN_CSS}</style>\n</head>')

    page = head + with_plain(MAIN, PLAIN) + footer + LD + with_xlsx(with_core(SCRIPT)) + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
