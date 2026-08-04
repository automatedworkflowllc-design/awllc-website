#!/usr/bin/env python3
"""Build /check/ -- one drop zone that works out what your file is.

The four single-purpose tools each solve a real problem, but they push a
decision onto the visitor they cannot make: which tool do I need? A business
owner with a messy export does not think "this is a reconciliation problem."
They think "something is wrong in here."

So this page asks nothing. Drop one or two files; it classifies each by what
the columns MEAN (invoice export, roster, customer list, work log), runs every
check that applies, and merges the findings into one report.

Two things make it a product rather than a demo:

  1. It always runs the structural pass, then adds type-specific passes -- so a
     file it cannot classify still gets a real answer instead of a shrug.
  2. It produces a downloadable, self-contained HTML report. A finding on a
     screen dies when the tab closes; a report gets forwarded to a boss.

Everything stays in the browser. The report is assembled locally and handed to
the browser's own download -- there is no endpoint, here or anywhere on it.
"""
from __future__ import annotations

import pathlib
import re

from toolkit import PARSE_DATE_JS, XLSX_JS

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'check'

TITLE = 'Free Business File Check — Drop Anything, Nothing Uploads'
DESC = ('Drop any business export — Excel (.xlsx) or CSV. It works out what the file is, '
        'runs every check that applies, and puts a dollar figure on the problems.')
CANON = 'https://automatedworkflowllc.com/check/'

PAGE_CSS = """
/* ---- unified check ---- */
.ck-drop{border:2px dashed var(--line-strong);border-radius:18px;background:var(--card);
padding:3rem 1.4rem;text-align:center;cursor:pointer}
.ck-drop.is-over{border-color:var(--accent);background:var(--well)}
.ck-drop:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.ck-drop strong{display:block;font-size:1.15rem;margin-bottom:.35rem}
.ck-drop span{color:var(--ink-soft);font-size:.92rem}
.ck-actions{display:flex;gap:.7rem;justify-content:center;flex-wrap:wrap;margin-top:1rem}
.ck-note{margin-top:1rem;font-size:.85rem;color:var(--ink-soft);text-align:center}
.ck-note code{font-family:var(--mono);font-size:.8rem}
#ck-report{margin-top:2rem;display:none}
.ck-files{display:flex;gap:.6rem;flex-wrap:wrap;margin:0 0 1.2rem}
.ck-file{border:1px solid var(--line);border-radius:.6rem;padding:.55rem .9rem;background:var(--card);
font-size:.85rem}
.ck-file b{display:block;font-family:var(--mono);font-size:.82rem}
.ck-file span{color:var(--ink-soft);font-size:.76rem}
.ck-tally{display:flex;gap:.7rem;flex-wrap:wrap;margin:0 0 1.3rem}
.ck-pill{border:1px solid var(--line);border-radius:.6rem;padding:.55rem .95rem;background:var(--card)}
.ck-pill b{display:block;font-size:1.45rem;line-height:1.1;font-family:var(--mono)}
.ck-pill.k-bad b{color:#B4452C}
.ck-pill span{font-size:.72rem;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.06em}
.ck-sec{margin:1.5rem 0 .5rem;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-soft)}
.ck-summary{border:1px solid var(--line-strong);border-radius:.7rem;background:var(--bg-soft);
padding:.95rem 1.15rem;margin:0 0 .4rem;font-size:1rem;line-height:1.55}
/* money-at-risk visual: every pixel below derives from computed findings */
.ck-viz{border:1px solid var(--line-strong);border-radius:.8rem;background:var(--card);
padding:1.1rem 1.25rem;margin:0 0 1.1rem}
.ck-viz h3{margin:0 0 .15rem;font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-soft)}
.ck-viz .big{font-family:var(--mono);font-size:2.3rem;line-height:1.15;color:#B4452C;font-weight:700;
font-variant-numeric:tabular-nums}
.ck-viz .cap{margin:.1rem 0 .9rem;font-size:.82rem;color:var(--ink-soft)}
.ck-leak{margin:.45rem 0 0}
.ck-leak .lbl{display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:.2rem}
.ck-leak .lbl b{font-family:var(--mono);font-variant-numeric:tabular-nums}
.ck-leak .rail{height:.7rem;border-radius:.35rem;background:var(--bg-soft);border:1px solid var(--line);overflow:hidden}
.ck-leak .fill{height:100%;width:0;border-radius:.35rem;background:#B4452C;
transition:width .9s cubic-bezier(.2,.7,.2,1)}
.ck-leak .fill.med{background:#A8842B}
.ck-find{opacity:1}
@media (prefers-reduced-motion: no-preference){
  .ck-anim .ck-find{opacity:0;transform:translateY(6px);transition:opacity .45s ease,transform .45s ease}
  .ck-anim .ck-find.in{opacity:1;transform:none}
}
.ck-find{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line-strong);
border-radius:.6rem;padding:.85rem 1.05rem;margin:0 0 .55rem}
.ck-find.sev-high{border-left-color:#B4452C}
.ck-find.sev-med{border-left-color:#A8842B}
.ck-find h4{margin:0 0 .2rem;font-size:.96rem}
.ck-find p{margin:0;font-size:.89rem;color:var(--ink-soft)}
.ck-find .src{font-family:var(--mono);font-size:.78rem;color:var(--ink-soft)}
.ck-clean{border-left:4px solid var(--accent);background:var(--card);border-radius:.6rem;
padding:1rem 1.2rem;color:var(--ink-soft)}
.ck-cta{margin-top:1.6rem;padding:1.3rem;border:1px solid var(--line);border-radius:12px;background:var(--bg-soft)}
.ck-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">Business File Check</h1>
  <p style="color:var(--ink-soft);max-width:41rem">
    Don't know which check you need? Neither does anyone else. Drop any export &mdash; invoices,
    a staff roster, a customer list, a job log &mdash; and this works out what the file
    <em>is</em> from its columns, then runs every check that applies. Drop two files and it
    reconciles them against each other.
  </p>
  <p style="max-width:41rem"><strong>Nothing uploads.</strong>
    <span style="color:var(--ink-soft)">Every check runs in your browser. There is no server to
    send your file to &mdash; open the network tab and watch: after this page loads, zero
    requests.</span></p>

  <div class="ck-drop" id="ck-drop" role="button" tabindex="0"
       aria-label="Choose one or two CSV files to analyze locally">
    <strong>Drop a .csv here &mdash; or two</strong>
    <span>invoices &middot; roster &middot; customers &middot; jobs &middot; anything with columns</span>
    <input type="file" id="ck-file" accept=".csv,.tsv,.txt,.xlsx,.xlsm" multiple style="display:none">
  </div>
  <div class="ck-actions">
    <button class="btn" id="ck-sample" type="button">Try it on sample files</button>
  </div>
  <p class="ck-note"><strong>Excel files work directly</strong> &mdash; drop the .xlsx as-is.
  It is read right here in your browser &mdash; every sheet is scanned and the busiest one analyzed &mdash; same as CSV: nothing uploads.</p>

  <section id="ck-report" aria-live="polite">
    <h2 id="ck-title" style="margin-bottom:.7rem"></h2>
    <div class="ck-files" id="ck-files"></div>
    <div class="ck-tally" id="ck-tally"></div>
    <div id="ck-findings"></div>
    <div style="margin-top:1.3rem">
      <button class="btn" id="ck-download" type="button">Download this report (.html)</button>
      <p style="margin:.6rem 0 0;font-size:.83rem;color:var(--ink-soft)">A single self-contained
      file &mdash; forward it, print it, keep it. Assembled here in your browser, same as
      everything else on this page.</p>
    </div>
    <div class="ck-cta">
      <strong>Want the ones a script can't fix?</strong>
      <p>Everything above stops where judgment starts &mdash; which duplicate is the real
      customer, what a blank means, who covers Thursday. That part is the
      <a href="/spreadsheet-cleanup-service/">$300 flat cleanup</a>, or a
      <a href="/free-demo/">free 1-day demo on your real data</a>, keep it either way.</p>
      <a class="btn" href="/free-demo/">Get the fix — free demo</a>
      <p style="margin:.9rem 0 0;font-size:.85rem">Prefer one check at a time?
      <a href="/spreadsheet-health-check/">Health Check</a> &middot;
      <a href="/money-leak-finder/">Money Leak Finder</a> &middot;
      <a href="/duplicate-customer-finder/">Duplicate Customers</a> &middot;
      <a href="/shift-coverage-check/">Shift Coverage</a></p>
    </div>
  </section>
</main>
"""

SCRIPT = r"""
<script>
(function(){
'use strict';
/* All local. No fetch, no XHR, no beacon. */

var DECISION = /(^|_|\b)(status|flag|state|result|outcome|approved|paid|active|valid|check|verified|error)(\b|_|$)/i;
var IDISH    = /(^|_|\b)(id|invoice|number|no|ref|sku|key|job)(\b|_|$)/i;
var NAMEISH  = /name|customer|client|company|account|vendor|payee|contact|organi|employee|staff/i;
var DATEISH  = /date|day\b/i;
var MONEYISH = /amount|total|price|value|charge|cost|fee|rate/i;
var TIMEISH  = /start|end|time.?in|time.?out|shift|from|to\b/i;
var SEP = '||';   /* composite-key separator: names contain spaces, dates contain
                     dashes, but nothing in a business export contains a double pipe */

var DATE_SHAPES = [
  [/^\d{4}-\d{1,2}-\d{1,2}/, 'YYYY-MM-DD'],
  [/^\d{1,2}\/\d{1,2}\/\d{2,4}$/, 'M/D/Y'],
  [/^\d{1,2}-[A-Za-z]{3}/, 'D-Mon'],
  [/^[A-Za-z]{3,9} \d{1,2},? \d{4}$/, 'Month D, Y']
];

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
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function dateShape(v){ for(var k=0;k<DATE_SHAPES.length;k++) if(DATE_SHAPES[k][0].test(v)) return DATE_SHAPES[k][1]; return null; }
function numberShape(v){
  if(/^-?\$?[\d,]+(\.\d+)?$/.test(v)) return v.indexOf('$')>=0 ? 'currency' : (v.indexOf(',')>=0 ? 'thousands' : 'plain');
  if(/^\(\$?[\d,]+(\.\d+)?\)$/.test(v)) return 'parens-negative';
  return null;
}
function money(v){
  var m = String(v).replace(/[$,\s]/g,'').replace(/^\((.*)\)$/, '-$1');
  var n = parseFloat(m); return isFinite(n) ? n : null;
}
function parseTime(v){
  v = String(v).trim().toLowerCase().replace(/\s+/g,'');
  if(!v) return null;
  var m = v.match(/^(\d{1,2}):(\d{2})(a|p|am|pm)?$/);
  if(m){ var h=+m[1]; if(m[3]&&m[3].charAt(0)==='p'&&h<12)h+=12; if(m[3]&&m[3].charAt(0)==='a'&&h===12)h=0; return h*60 + (+m[2]); }
  return null;
}

function table(rows){
  var header = rows[0].map(function(h,i){ return (h||'').trim() || ('column '+(i+1)); });
  var body = rows.slice(1).filter(function(r){ return r.join('').trim() !== ''; });
  return { header: header, body: body,
    col: function(i){ return body.map(function(r){ return (r[i]===undefined?'':String(r[i])).trim(); }); } };
}

/* ---- classify by what the columns MEAN, not by filename ---------------- */
function classify(t){
  var score = { invoices:0, roster:0, customers:0, jobs:0 };
  var hasDate=false, hasMoney=false, timeCols=0, hasName=false, hasId=false, hasPaid=false;
  t.header.forEach(function(h, i){
    var vals = t.col(i).filter(Boolean);
    if(!vals.length) return;
    var dateFrac = vals.filter(function(v){ return dateShape(v); }).length / vals.length;
    var numFrac  = vals.filter(function(v){ return money(v) !== null; }).length / vals.length;
    var timeFrac = vals.filter(function(v){ return parseTime(v) !== null; }).length / vals.length;
    if(DATEISH.test(h) || dateFrac > 0.7) hasDate = true;
    if(MONEYISH.test(h) && numFrac > 0.6) hasMoney = true;
    if(TIMEISH.test(h) && timeFrac > 0.6) timeCols++;
    if(NAMEISH.test(h)) hasName = true;
    if(IDISH.test(h)) hasId = true;
    if(/paid/i.test(h)) hasPaid = true;
    if(/invoice/i.test(h)) score.invoices += 2;
    if(/job|ticket|work.?order/i.test(h)) score.jobs += 2;
    if(/employee|staff|shift|caregiver|nurse/i.test(h)) score.roster += 2;
  });
  if(timeCols >= 2 && hasDate) score.roster += 3;
  if(hasPaid && hasMoney) score.invoices += 2;
  if(hasMoney && hasId && hasDate) score.jobs += 1;
  if(hasName && !timeCols) score.customers += 1;

  var best = 'generic', bestScore = 0;
  Object.keys(score).forEach(function(k){ if(score[k] > bestScore){ bestScore = score[k]; best = k; } });
  var kind = bestScore >= 2 ? best : 'generic';
  return { kind: kind,
           label: { invoices:'invoice / billing export', roster:'staff roster',
                    customers:'customer or contact list', jobs:'job / work log',
                    generic:'general spreadsheet' }[kind] };
}

/* ---- structural pass: runs on EVERY file -------------------------------- */
function structural(t, src, findings){
  var n = t.body.length;
  if(n < 3) return;
  var seen = Object.create(null), dup = 0;
  t.body.forEach(function(r){ var k = r.join(SEP); if(seen[k]) dup++; else seen[k]=1; });
  if(dup) findings.push({sev: dup > n*0.02 ? 'high':'med', src: src,
    title: dup + ' exact duplicate row' + (dup===1?'':'s'),
    detail: 'Identical rows usually mean a paste happened twice. Any total built on this file is inflated.'});

  t.header.forEach(function(name, ci){
    var vals = t.col(ci), present = vals.filter(Boolean);
    var blanks = n - present.length;
    if(blanks === n){ findings.push({sev:'med', src:src, title:'"'+name+'" is completely empty',
      detail:'All '+n+' rows blank. A column nobody fills is a column nobody can use.'}); return; }
    if(blanks > n*0.5) findings.push({sev:'med', src:src, title:'"'+name+'" is '+Math.round(100*blanks/n)+'% blank',
      detail:'Half-empty usually means the process that fills it broke, or nobody agrees whose job it is.'});

    var counts = Object.create(null); present.forEach(function(v){ counts[v]=(counts[v]||0)+1; });
    var distinct = Object.keys(counts);
    if(present.length >= 8 && distinct.length === 1 && DECISION.test(name))
      findings.push({sev:'high', src:src, title:'"'+name+'" is "'+distinct[0].slice(0,28)+'" on every row',
        detail:'A column whose job is to flag things has never once flagged anything. It cannot distinguish.'});

    var canon = Object.create(null), variants = 0;
    distinct.forEach(function(v){ var k=v.toLowerCase().replace(/\s+/g,' ').trim();
      if(canon[k] !== undefined) variants++; else canon[k]=v; });
    if(variants && distinct.length < 40) findings.push({sev:'med', src:src,
      title:'"'+name+'" has '+variants+' spelling/spacing variant'+(variants===1?'':'s'),
      detail:'e.g. "Paid" vs "paid " — filters and pivot tables count these as different things.'});

    var shapes = Object.create(null);
    present.forEach(function(v){ var s=dateShape(v); if(s) shapes[s]=1; });
    if(Object.keys(shapes).length > 1) findings.push({sev:'high', src:src,
      title:'"'+name+'" mixes '+Object.keys(shapes).length+' date formats',
      detail:Object.keys(shapes).join(', ')+' in one column — sorting and date math silently give wrong answers.'});

    var nsh = Object.create(null), num = 0;
    present.forEach(function(v){ var s=numberShape(v); if(s){ nsh[s]=1; num++; } });
    if(Object.keys(nsh).length > 1 && num > present.length*0.6) findings.push({sev:'med', src:src,
      title:'"'+name+'" mixes number formats',
      detail:Object.keys(nsh).join(', ')+' — some are text to Excel, and SUM() skips text without telling you.'});

    if(IDISH.test(name) && present.length >= 8 && present.length > distinct.length)
      findings.push({sev:'high', src:src, title:'"'+name+'" has '+(present.length-distinct.length)+' duplicate value(s)',
        detail:'A column named like an identifier should be unique. Duplicates usually mean double-entered records.'});
  });
}

/* ---- customer-name collisions ------------------------------------------ */
var SUFFIXES = /\b(inc|llc|ltd|co|corp|corporation|company|incorporated|pllc|pc|lp|llp|plc|group|grp|holdings|enterprises|services|svcs|sons)\b/g;
function normName(s){
  return String(s).toLowerCase().replace(/&/g,' and ').replace(/[.,'’"()\-_/\\]+/g,' ')
    .replace(SUFFIXES,' ').replace(/\bthe\b/g,' ').replace(/\band\b/g,' ').replace(/\s+/g,' ').trim();
}
function nameCollisions(t, src, findings){
  var ci = -1;
  t.header.forEach(function(h,i){ if(ci<0 && NAMEISH.test(h)) ci = i; });
  if(ci < 0) return;
  var groups = Object.create(null);
  t.col(ci).filter(Boolean).forEach(function(v){
    var k = normName(v); if(!k) return;
    (groups[k] = groups[k] || Object.create(null))[v] = 1;
  });
  Object.keys(groups).forEach(function(k){
    var forms = Object.keys(groups[k]);
    if(forms.length < 2) return;
    findings.push({sev:'high', src:src, title:'Same "'+t.header[ci]+'" spelled '+forms.length+' ways',
      detail: forms.join('  |  ') + ' — identical once case, punctuation and legal suffixes are ignored. Your count, revenue history and mail merge are all split.'});
  });
}

/* ---- roster checks ------------------------------------------------------ */
function rosterChecks(t, src, findings){
  var d=-1,p=-1,r=-1,s=-1,e=-1;
  t.header.forEach(function(h,i){
    if(d<0 && DATEISH.test(h)) d=i;
    if(p<0 && /employee|name|staff|caregiver|nurse|tech/i.test(h)) p=i;
    if(r<0 && /role|position|title|dept|unit/i.test(h)) r=i;
    if(s<0 && /start|time.?in/i.test(h)) s=i;
    if(e<0 && /end|time.?out/i.test(h)) e=i;
  });
  if(d<0 || p<0) return;
  var hoursBy = Object.create(null), byRole = Object.create(null);
  var unparsedDates = 0, timedRows = 0;
  t.body.forEach(function(row){
    var person = String(row[p]||'').trim(); if(!person) return;
    if(r>=0){ var role=String(row[r]||'').trim();
      if(role) (byRole[role] = byRole[role] || Object.create(null))[person]=1; }
    if(s>=0 && e>=0){
      var a=parseTime(row[s]), b=parseTime(row[e]);
      if(a===null||b===null) return;
      var span=b-a; if(span<=0) span+=1440;
      timedRows++;
      /* Month key must come from a PARSED date. Slicing the raw string worked
         for 2026-07-14 and silently broke for 07/14/2026, where slice(0,7)
         yields "07/14/2" -- a per-DAY bucket. Hours never accumulated into a
         month, so this check could never fire on a US-formatted file. It
         reported nothing, which reads exactly like a clean result. */
      var dt = parseDate(row[d]);
      if(!dt){ unparsedDates++; return; }
      var month = dt.getFullYear() + '-' + ('0' + (dt.getMonth()+1)).slice(-2);
      hoursBy[person + SEP + month] = (hoursBy[person + SEP + month]||0) + span/60;
    }
  });
  /* Never fail silently: if we had hours but could not date them, say so
     rather than returning an empty result that reads as "no overtime". */
  if(unparsedDates && unparsedDates > timedRows * 0.5){
    findings.push({sev:'med', src:src,
      title:'Could not read the date on ' + unparsedDates + ' shift row(s)',
      detail:'Hours were found but could not be totalled per month, so the overtime check was ' +
        'skipped for those rows. Recognised formats are 2026-07-14 and 07/14/2026.'});
  }
  Object.keys(byRole).forEach(function(role){
    var who = Object.keys(byRole[role]);
    if(who.length === 1) findings.push({sev:'high', src:src,
      title:'Only ' + who[0] + ' ever covers "' + role + '"',
      detail:'One person deep. A single call-out has no backup, and nobody else is trained in.'});
  });
  Object.keys(hoursBy).forEach(function(k){
    if(hoursBy[k] > 160){
      var parts = k.split(SEP);
      findings.push({sev:'med', src:src, title:parts[0]+' scheduled '+Math.round(hoursBy[k])+'h in '+parts[1],
        detail:'Well past a 40-hour weekly average. Overtime at premium rate, and the fatigue is real.'});
    }
  });
}

/* ---- reconciliation across two files ------------------------------------ */
function reconcile(a, b, findings){
  function cols(t){
    return t.header.map(function(h,i){ return {i:i, name:h, vals:t.col(i).filter(Boolean)}; })
      .filter(function(c){ return c.vals.length; });
  }
  var best=null;
  cols(a).forEach(function(ca){
    var set = Object.create(null); ca.vals.forEach(function(v){ set[v]=1; });
    cols(b).forEach(function(cb){
      var hits = cb.vals.filter(function(v){ return set[v]; }).length;
      var score = hits / Math.max(ca.vals.length, cb.vals.length);
      if(hits >= 2 && (!best || score > best.score)) best = {score:score, ca:ca, cb:cb};
    });
  });
  if(!best || best.score < 0.2) return false;

  /* Which column carries the money, if any. A finding that says "3 job numbers
     are missing" is a curiosity; one that says "$1,280 of finished work was
     never invoiced" is the reason someone calls. Same arithmetic, and the
     dollar figure is the honest unit for it. */
  function amountCol(t){
    var bestC = -1, bestFrac = 0;
    t.header.forEach(function(h, i){
      if(!MONEYISH.test(h)) return;
      var vals = t.col(i).filter(Boolean);
      if(!vals.length) return;
      var frac = vals.filter(function(v){ return money(v) !== null; }).length / vals.length;
      if(frac > 0.6 && frac > bestFrac){ bestFrac = frac; bestC = i; }
    });
    return bestC;
  }
  /* First amount seen per key. Keys repeat when a file has duplicate rows, and
     counting a duplicate twice would inflate the very number we are asking a
     business to trust. */
  function sumFor(t, keyIdx, amtIdx, keys){
    if(amtIdx < 0) return null;
    var want = Object.create(null); keys.forEach(function(k){ want[k] = 1; });
    var taken = Object.create(null), total = 0, counted = 0;
    t.body.forEach(function(r){
      var k = String(r[keyIdx]||'').trim();
      if(!k || !want[k] || taken[k]) return;
      var v = money(r[amtIdx]);
      if(v === null) return;
      taken[k] = 1; total += v; counted++;
    });
    return counted ? {total: total, counted: counted} : null;
  }
  function fmt(n){ return '$' + Math.abs(n).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }

  var aAmt = amountCol(a), bAmt = amountCol(b);

  function side(from, to, fromCol, toCol, fromAmt, label, meaning, sev){
    var inTo = Object.create(null); toCol.vals.forEach(function(v){ inTo[v]=1; });
    var seen = Object.create(null), missing = [];
    fromCol.vals.forEach(function(v){ if(!inTo[v] && !seen[v]){ seen[v]=1; missing.push(v); } });
    if(!missing.length) return 0;
    var sum = sumFor(from, fromCol.i, fromAmt, missing);
    var f = {sev: sev, src:'both files',
      title: missing.length + ' "' + fromCol.name + '" value(s) ' + label +
             (sum ? ' — ' + fmt(sum.total) : ''),
      detail:'Matched on ' + fromCol.name + ' ↔ ' + toCol.name + ' by exact ID, nothing fuzzy. ' +
        (sum ? meaning + ' Total across ' + sum.counted + ' row(s): ' + fmt(sum.total) + '. ' : meaning + ' ') +
        'Unmatched: ' + missing.slice(0,12).join(', ') + (missing.length>12 ? ' …' : '') + '.'};
    if(sum) f.money = sum.total;
    findings.push(f);
    return sum ? sum.total : 0;
  }

  /* Both directions, because they are different business problems. Work with
     no invoice is revenue you never billed. An invoice with no work order is
     either a billing error or work nobody logged -- the first is a refund
     waiting to happen, and it is the one that reaches a customer. */
  side(a, b, best.ca, best.cb, aAmt,
       'in file 1 with no match in file 2', 'If file 1 is work done and file 2 is work billed, that is finished work nobody invoiced.', 'high');
  side(b, a, best.cb, best.ca, bAmt,
       'in file 2 with no match in file 1', 'Billed with no matching record in file 1 — either a billing error or work that was never logged.', 'med');
  return true;
}

/* ---- run everything ----------------------------------------------------- */
function runAll(files){
  var findings = [], meta = [];
  var tables = files.map(function(f){
    var t = table(parseCSV(f.text));
    var c = classify(t);
    meta.push({name:f.name, rows:t.body.length, cols:t.header.length, label:c.label});
    return {t:t, c:c, name:f.name};
  });
  tables.forEach(function(x){
    structural(x.t, x.name, findings);
    if(x.c.kind !== 'roster') nameCollisions(x.t, x.name, findings);
    if(x.c.kind === 'roster') rosterChecks(x.t, x.name, findings);
  });
  var reconciled = false;
  if(tables.length === 2) reconciled = reconcile(tables[0].t, tables[1].t, findings);
  var order = {high:0, med:1, info:2};
  /* Within a severity band, lead with the largest dollar figure. Someone
     skimming reads the first line, and it should be the expensive one. */
  findings.sort(function(a,b){
    return (order[a.sev]-order[b.sev]) || ((b.money||0) - (a.money||0));
  });
  /* Only money that is genuinely at risk -- unbilled work and billing with no
     backing record. Deliberately NOT a sum of every dollar in the files, which
     would be a big meaningless number. */
  var atRisk = findings.reduce(function(s, f){ return s + (f.money || 0); }, 0);
  return { findings: findings, meta: meta, atRisk: atRisk, reconciled: reconciled,
           filesGiven: tables.length };
}

var last = null;

function render(res){
  var counts = {high:0, med:0, info:0};
  res.findings.forEach(function(f){ counts[f.sev]++; });
  document.getElementById('ck-title').textContent =
    'Report — ' + res.meta.length + ' file' + (res.meta.length===1?'':'s') + ' checked';
  document.getElementById('ck-files').innerHTML = res.meta.map(function(m){
    return '<div class="ck-file"><b>'+esc(m.name)+'</b><span>read as: '+esc(m.label)+
      ' &middot; '+m.rows+' rows &times; '+m.cols+' cols</span></div>';
  }).join('');
  function fmtUSD(n){ return '$' + Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  document.getElementById('ck-tally').innerHTML =
    (res.atRisk > 0 ? '<div class="ck-pill k-bad"><b>'+fmtUSD(res.atRisk)+'</b><span>money at risk</span></div>' : '') +
    '<div class="ck-pill'+(counts.high?' k-bad':'')+'"><b>'+counts.high+'</b><span>needs attention</span></div>' +
    '<div class="ck-pill"><b>'+counts.med+'</b><span>worth checking</span></div>';
  var out='', lastSev=null;

  /* Plain-language summary before the list. Someone who reads one sentence
     should still leave knowing whether this cost them anything, and the
     summary must never imply we checked something we did not. */
  var summary;
  if(res.atRisk > 0){
    summary = 'Across ' + res.meta.length + ' file' + (res.meta.length===1?'':'s') + ', ' +
      fmtUSD(res.atRisk) + ' is sitting in records that do not agree with each other, plus ' +
      counts.high + ' other item' + (counts.high===1?'':'s') + ' worth attention.';
  } else if(res.findings.length){
    summary = 'No money was found stranded between these files, but ' + counts.high +
      ' item' + (counts.high===1?' needs':'s need') + ' attention and ' + counts.med + ' more ' +
      (counts.med===1?'is':'are') + ' worth a look.';
  } else { summary = ''; }
  if(res.filesGiven === 1){
    summary += ' Only one file was given, so nothing could be cross-checked — ' +
      'add the matching file (jobs and invoices, hours and payroll) to find money stranded between them.';
  } else if(res.filesGiven === 2 && !res.reconciled){
    summary += ' The two files share no column with matching values, so they could not be ' +
      'cross-checked against each other. Each was still checked on its own.';
  }
  if(summary) out += '<div class="ck-summary">'+esc(summary.trim())+'</div>';

  /* Money visual: a counter that counts to the EXACT computed figure and one
     proportional bar per money finding. Widths are arithmetic on the same
     findings shown below -- nothing decorative carries a number. */
  if(res.atRisk > 0){
    var mf = res.findings.filter(function(f){ return f.money > 0; });
    var viz = '<div class="ck-viz"><h3>Money sitting in records that disagree</h3>' +
      '<div class="big" id="ck-big" data-target="' + Math.round(res.atRisk) + '">$0</div>' +
      '<p class="cap">Counted once per record, from your file' + (res.meta.length > 1 ? 's' : '') +
      ' only — nothing estimated.</p>';
    mf.forEach(function(f){
      var pct = Math.max(2, Math.round(100 * f.money / res.atRisk));
      viz += '<div class="ck-leak"><div class="lbl"><span>' + esc(f.title.replace(/ —.*$/, '')) +
        '</span><b>' + fmtUSD(f.money) + '</b></div>' +
        '<div class="rail"><div class="fill' + (f.sev === 'med' ? ' med' : '') +
        '" data-w="' + pct + '"></div></div></div>';
    });
    out += viz + '</div>';
  }
  if(!res.findings.length){
    out = '<div class="ck-clean"><strong>Nothing found.</strong> Every column varies, dates and ' +
      'numbers are consistent, no duplicate rows, no name collisions. That is the result you ' +
      'want &mdash; and it is not the same as not having looked.</div>';
  } else res.findings.forEach(function(f){
    if(f.sev !== lastSev){ lastSev=f.sev;
      out += '<div class="ck-sec">'+({high:'Needs attention',med:'Worth checking',info:'For information'}[f.sev])+'</div>'; }
    out += '<div class="ck-find sev-'+f.sev+'"><h4>'+esc(f.title)+'</h4>' +
      '<div class="src">'+esc(f.src)+'</div><p>'+esc(f.detail)+'</p></div>';
  });
  document.getElementById('ck-findings').innerHTML = out;

  /* Motion, honestly: the counter always LANDS on the exact figure, bars are
     CSS transitions to computed widths, findings stagger in. Reduced-motion
     users get the final state immediately -- same numbers, no theater. */
  var findsBox = document.getElementById('ck-findings');
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var big = document.getElementById('ck-big');
  if(big){
    var target = +big.getAttribute('data-target');
    if(reduce){ big.textContent = fmtUSD(target); }
    else {
      var t0 = null;
      var tick = function(ts){
        if(t0 === null) t0 = ts;
        var p = Math.min(1, (ts - t0) / 900);
        big.textContent = fmtUSD(target * (1 - Math.pow(1 - p, 3)));
        if(p < 1) requestAnimationFrame(tick);
        else big.textContent = fmtUSD(target);
      };
      requestAnimationFrame(tick);
    }
  }
  var fills = findsBox.querySelectorAll('.fill');
  requestAnimationFrame(function(){ requestAnimationFrame(function(){
    for(var i = 0; i < fills.length; i++) fills[i].style.width = fills[i].getAttribute('data-w') + '%';
  }); });
  if(!reduce){
    findsBox.classList.add('ck-anim');
    var cards = findsBox.querySelectorAll('.ck-find');
    for(var ci = 0; ci < cards.length; ci++)(function(el, d){
      setTimeout(function(){ el.classList.add('in'); }, 80 + d * 70);
    })(cards[ci], ci);
  }
  last = res;
  var rep = document.getElementById('ck-report');
  rep.style.display = 'block';
  rep.scrollIntoView({behavior:'smooth', block:'start'});
}

function reportHTML(res){
  var when = new Date().toLocaleString();
  var rows = res.findings.map(function(f){
    return '<div class="f '+f.sev+'"><h3>'+esc(f.title)+'</h3><div class="s">'+esc(f.src)+
      '</div><p>'+esc(f.detail)+'</p></div>';
  }).join('') || '<p class="clean">Nothing found. Every column varies, formats are consistent, ' +
    'no duplicates. That is the result you want — and it is not the same as not having looked.</p>';
  return '<!doctype html><html lang="en"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>File check report</title><style>' +
    'body{font:16px/1.6 system-ui,sans-serif;max-width:44rem;margin:2rem auto;padding:0 1.2rem;color:#1F1C15;background:#F3F0E7}' +
    'h1{font-size:1.5rem;margin:0 0 .2rem}.sub{color:#4A4538;font-size:.9rem;margin:0 0 1.6rem}' +
    '.file{border:1px solid #D8D1BD;border-radius:.5rem;padding:.5rem .8rem;margin:0 0 .4rem;background:#E9E4D4;font-size:.85rem}' +
    '.f{background:#E9E4D4;border:1px solid #D8D1BD;border-left:4px solid #B0A78D;border-radius:.5rem;padding:.8rem 1rem;margin:0 0 .5rem}' +
    '.f.high{border-left-color:#B4452C}.f.med{border-left-color:#A8842B}' +
    '.f h3{margin:0 0 .2rem;font-size:1rem}.f p{margin:.2rem 0 0;color:#4A4538;font-size:.9rem}' +
    '.s{font-family:ui-monospace,monospace;font-size:.78rem;color:#4A4538}' +
    '.clean{border-left:4px solid #1F6E66;padding:.8rem 1rem;background:#E9E4D4;border-radius:.5rem}' +
    '.risk{border:1px solid #B0A78D;border-left:4px solid #B4452C;background:#E9E4D4;border-radius:.5rem;' +
    'padding:.8rem 1rem;margin:0 0 1rem}.risk strong{font-size:1.3rem;font-family:ui-monospace,monospace}' +
    'footer{margin-top:2rem;padding-top:1rem;border-top:1px solid #D8D1BD;font-size:.82rem;color:#4A4538}' +
    '</style></head><body>' +
    '<h1>Business file check</h1><p class="sub">Generated ' + esc(when) +
    ' &middot; analysis ran entirely in the browser; no file was uploaded.</p>' +
    (res.atRisk > 0 ? '<div class="risk"><strong>' +
      '$' + Math.round(res.atRisk).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') +
      '</strong> is sitting in records that do not agree with each other. Detail below.' +
      /* Static leak bars for the forwarded file: inline widths, no script.
         Same rule as on the page -- every width is arithmetic on the findings. */
      res.findings.filter(function(f){ return f.money > 0; }).map(function(f){
        var pct = Math.max(2, Math.round(100 * f.money / res.atRisk));
        return '<div style="margin-top:.55rem"><div style="display:flex;justify-content:space-between;' +
          'font-size:.82rem"><span>' + esc(f.title.replace(/ —.*$/, '')) + '</span>' +
          '<b style="font-family:ui-monospace,monospace">$' +
          Math.round(f.money).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '</b></div>' +
          '<div style="height:.55rem;border-radius:.3rem;background:#F3F0E7;border:1px solid #D8D1BD">' +
          '<div style="height:100%;width:' + pct + '%;border-radius:.3rem;background:' +
          (f.sev === 'med' ? '#A8842B' : '#B4452C') + '"></div></div></div>';
      }).join('') + '</div>' : '') +
    res.meta.map(function(m){ return '<div class="file"><strong>'+esc(m.name)+'</strong> — read as ' +
      esc(m.label) + ', ' + m.rows + ' rows &times; ' + m.cols + ' cols</div>'; }).join('') +
    '<h2 style="font-size:1rem;margin:1.4rem 0 .6rem">Findings</h2>' + rows +
    '<footer>Every finding above is arithmetic on the file as supplied — nothing predicted, ' +
    'nothing guessed. The items a script cannot decide (which duplicate is the real record, ' +
    'what a blank means) are deliberately left alone.<br><br>' +
    'automatedworkflowllc.com &middot; free check at /check/</footer></body></html>';
}

/* ---- invented samples: a work log and its invoices ---------------------- */
var SAMPLE_A = 'Job No,Date,Customer,Description,Amount\n' +
'J-101,2026-06-22,Hargrove Property Grp,Irrigation repair,740.00\n' +
'J-102,2026-06-25,Bell & Sons HOA,Storm cleanup,1280.00\n' +
'J-103,2026-06-28,Rivertown Storage,Gate motor,965.00\n' +
'J-104,07/01/2026,Hargrove Property Group,Leak call-out,"$410.00"\n' +
'J-105,2026-07-02,Coastal Dental,Pressure wash,380.00\n' +
'J-106,2026-07-06,Bell and Sons HOA LLC,Fence rebuild,"1,620.00"\n' +
'J-107,2026-07-08,Marlin Self-Serve,Door track,540.00\n' +
'J-108,2026-07-09,Rivertown Storage,Unit doors,1150.00\n' +
'J-108,2026-07-09,Rivertown Storage,Unit doors,1150.00\n' +
'J-109,2026-07-12,Coastal Dental,Lighting fix,295.00\n' +
'J-110,2026-07-14,Northgate Church,Grounds cleanup,860.00\n' +
'J-111,2026-07-16,Hargrove Property Grp,Weekend call-out,520.00\n' +
'J-112,2026-07-18,Marlin Self-Serve,Camera pole,310.00\n';
var SAMPLE_B = 'Invoice No,Job No,Invoice Date,Amount,Paid\n' +
'INV-2201,J-101,2026-06-24,740.00,Yes\n' +
'INV-2202,J-102,2026-06-27,1280.00,Yes\n' +
'INV-2203,J-103,2026-06-30,965.00,Yes\n' +
'INV-2204,J-105,2026-07-04,380.00,Yes\n' +
'INV-2205,J-106,2026-07-08,1620.00,Yes\n' +
'INV-2206,J-107,2026-07-10,540.00,Yes\n' +
'INV-2207,J-108,2026-07-11,1150.00,Yes\n' +
'INV-2208,J-110,2026-07-15,860.00,Yes\n' +
'INV-2209,J-109,2026-07-22,295.00,Yes\n';

var drop = document.getElementById('ck-drop');
var input = document.getElementById('ck-file');
function handleFiles(list){
  if(!list || !list.length) return;
  var files = Array.prototype.slice.call(list, 0, 2), loaded = [], done = 0;
  function finish(){
    if(++done !== files.length) return;
    try { render(runAll(loaded)); }
    catch(err){ alert('Could not analyze that file. If it is very old (.xls) Excel, save it as .xlsx or CSV first.'); }
  }
  files.forEach(function(f){
    var reader = new FileReader();
    if(/\.(xlsx|xlsm)$/i.test(f.name)){
      /* Native Excel intake -- parsed right here, no library, no upload.
         The first sheet is read; dates convert only when Excel styled the
         cell as a date, so a plain number can never be invented into one. */
      reader.onload = function(){
        xlsxToRows(reader.result).then(function(rows){
          loaded.push({name:f.name, text:rowsToCSV(rows)});
          finish();
        }).catch(function(err){
          alert('Could not read ' + f.name + ' as an Excel workbook (' + err.message +
                '). Save it as CSV and try again.');
        });
      };
      reader.readAsArrayBuffer(f);
    } else {
      reader.onload = function(){
        loaded.push({name:f.name, text:String(reader.result)});
        finish();
      };
      reader.readAsText(f);
    }
  });
}
drop.addEventListener('click', function(){ input.click(); });
drop.addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); input.click(); } });
input.addEventListener('change', function(){ handleFiles(input.files); });
['dragover','dragenter'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.add('is-over'); }); });
['dragleave','drop'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.remove('is-over'); }); });
drop.addEventListener('drop', function(e){ handleFiles(e.dataTransfer.files); });
document.getElementById('ck-sample').addEventListener('click', function(){
  render(runAll([{name:'sample-jobs.csv', text:SAMPLE_A}, {name:'sample-invoices.csv', text:SAMPLE_B}]));
});
document.getElementById('ck-download').addEventListener('click', function(){
  if(!last) return;
  var blob = new Blob([reportHTML(last)], {type:'text/html;charset=utf-8'});
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = 'file-check-report.html';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(function(){ URL.revokeObjectURL(url); }, 1000);
});
})();
</script>
"""

LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Business File Check",
  "url": "https://automatedworkflowllc.com/check/",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Any",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "description": "Free in-browser analyzer that identifies what a business CSV is (invoices, roster, customer list, job log) and runs every applicable check, then produces a downloadable report. No upload."
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

    # The roster overtime check needs a real parsed date, not a sliced string.
    # Taken from the shared toolkit rather than hand-copied, so it cannot drift
    # from the identical parser the other tool pages use.
    script = SCRIPT.replace('function parseTime(', PARSE_DATE_JS.strip() + '\n\nfunction parseTime(', 1)
    if 'function parseDate' not in script:
        raise SystemExit('parseDate was not injected -- the parseTime anchor moved; fix before shipping')
    # Native .xlsx intake from the shared toolkit -- injected, not hand-copied.
    script = script.replace('function parseTime(', XLSX_JS.strip() + '\n\nfunction parseTime(', 1)
    if 'function xlsxToRows' not in script or 'function rowsToCSV' not in script:
        raise SystemExit('xlsx reader was not injected -- fix before shipping')
    page = head + MAIN + footer + LD + script + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
