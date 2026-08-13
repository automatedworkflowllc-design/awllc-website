#!/usr/bin/env python3
"""Build /spreadsheet-health-check/ from the cleanup-service template.

Head, site styles, header and footer are inherited verbatim from
spreadsheet-cleanup-service/index.html so the page can never drift from the
site shell; only <main>, the page meta, page CSS and the analyzer script are new.

The product promise is architectural: the analyzer runs entirely in the
browser. This page makes zero network requests after load -- there is no
endpoint to receive a file even if we wanted one.
"""
from __future__ import annotations

import pathlib
import re

from toolkit import with_core, with_xlsx, PLAIN_CSS, plain_english, with_plain

PLAIN = plain_english(
    'Looks at a spreadsheet you already have and tells you which parts of it can no longer be trusted &mdash; columns that are empty, dates written five different ways, the same row entered twice.',
    'Bad data quietly makes bad numbers. If a column is half blank or a customer is in there twice, <b>every total built on it is wrong</b> and nothing warns you. This shows you exactly where, and offers a cleaned copy back.',
    'One file you already have &mdash; an export from Excel, Google Sheets, QuickBooks or your job software. Spreadsheet (.xlsx) or CSV both work.',
    'About ten seconds. The file never leaves your computer &mdash; there is nowhere here to send it.')


ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'spreadsheet-health-check'

# 2026-08-12 retitle. "spreadsheet health" is not merely unsearched -- it points at the
# WRONG UNIVERSE. Google autocomplete returns spreadsheet health tracker, health
# spreadsheet template, healthcare spreadsheet template, spreadsheet to compare health
# insurance plans. Anyone arriving on that phrasing wanted a fitness or insurance
# document and bounces on sight. Verified against the live suggest endpoint today.
# What people actually type for this job: "clean up excel data" (ten suggestions,
# including clean up excel spreadsheet / excel file), and "csv validator online free".
TITLE = 'Clean Up Excel Data Automatically — Free Spreadsheet Error Checker'
DESC = ('Drop any CSV and get an instant, honest report: dead columns, mixed date '
        'formats, duplicate rows. Runs in your browser — your data never leaves '
        'your machine.')
CANON = 'https://automatedworkflowllc.com/spreadsheet-health-check/'

PAGE_CSS = """
/* ---- health check page ---- */
.hc-drop{border:2px dashed var(--line-strong);border-radius:16px;background:var(--card);
padding:2.6rem 1.4rem;text-align:center;cursor:pointer;transition:border-color .15s,background .15s}
.hc-drop.is-over{border-color:var(--accent,var(--green,#1E7A47));background:var(--well)}
.hc-drop:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.hc-drop strong{display:block;font-size:1.05rem;margin-bottom:.35rem}
.hc-drop span{color:var(--ink-soft);font-size:.92rem}
.hc-actions{display:flex;gap:.7rem;justify-content:center;flex-wrap:wrap;margin-top:1rem}
.hc-note{margin-top:1rem;font-size:.85rem;color:var(--ink-soft);text-align:center}
.hc-note code{font-family:var(--mono);font-size:.8rem}
#hc-report{margin-top:2rem;display:none}
.hc-tally{display:flex;gap:.7rem;flex-wrap:wrap;margin:0 0 1.2rem}
.hc-pill{border:1px solid var(--line);border-radius:.6rem;padding:.55rem .95rem;background:var(--card)}
.hc-pill b{display:block;font-size:1.45rem;line-height:1.1;font-family:var(--mono)}
.hc-pill span{font-size:.72rem;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.07em}
.hc-find{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line-strong);
border-radius:.6rem;padding:.9rem 1.1rem;margin:0 0 .6rem}
.hc-find.sev-high{border-left-color:#B4452C}
.hc-find.sev-med{border-left-color:#A8842B}
.hc-find.sev-info{border-left-color:var(--line-strong)}
.hc-find h4{margin:0 0 .25rem;font-size:.98rem}
.hc-find p{margin:0;color:var(--ink-soft);font-size:.9rem}
.hc-find .hc-where{font-family:var(--mono);font-size:.8rem;color:var(--ink-soft)}
.hc-clean{border-left:4px solid var(--accent,var(--green,#1E7A47));background:var(--card);border-radius:.6rem;
padding:1rem 1.2rem;color:var(--ink-soft)}
.hc-cta{margin-top:1.6rem;padding:1.3rem;border:1px solid var(--line);border-radius:12px;background:var(--bg-soft)}
.hc-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
.hc-fix{margin-top:1.8rem;padding:1.3rem;border:1px solid var(--line-strong);border-radius:12px;background:var(--card)}
.hc-fix h3{margin:0 0 .3rem;font-size:1.05rem}
.hc-fix > p{margin:0 0 .9rem;color:var(--ink-soft);font-size:.92rem}
.hc-changes{margin:0 0 1rem;padding-left:1.15rem;color:var(--ink-soft);font-size:.9rem}
.hc-changes li{margin:.15rem 0}
.hc-limits{margin:1rem 0 0;font-size:.85rem;color:var(--ink-soft);border-top:1px solid var(--line-soft);padding-top:.8rem}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">Spreadsheet Health Check</h1>
  <p style="color:var(--ink-soft);max-width:40rem">
    Drop any CSV export from Excel, Google Sheets, QuickBooks or your job software and get an
    instant, honest report: columns that carry no information, status fields that never vary,
    mixed date formats, duplicate rows.
  </p>
  <p style="max-width:40rem"><strong>Nothing uploads. Ever.</strong>
    <span style="color:var(--ink-soft)">The analysis runs entirely in your browser &mdash; this
    page has no server to send your file to. Verify it yourself: open your browser's network tab;
    after the page loads it makes zero requests.</span></p>

  <div class="hc-drop" id="hc-drop" role="button" tabindex="0"
       aria-label="Choose a CSV file to analyze locally">
    <strong>Drop a .csv file here</strong>
    <span>or click to choose one &middot; stays on your machine</span>
    <input type="file" id="hc-file" accept=".csv,.tsv,.txt,.xlsx,.xlsm" style="display:none">
  </div>
  <div class="hc-actions">
    <button class="btn" id="hc-sample" type="button">Try the sample file</button>
  </div>
  <p class="hc-note"><strong>Excel files work directly</strong> &mdash; drop the .xlsx as-is (every sheet is scanned, the busiest analyzed); this
    tool deliberately reads only plain text it can analyze in front of you.</p>

  <section id="hc-report" aria-live="polite">
    <h2 id="hc-title" style="margin-bottom:.8rem"></h2>
    <div class="hc-tally" id="hc-tally"></div>
    <div id="hc-findings"></div>

    <div class="hc-fix" id="hc-fix" style="display:none">
      <h3>Want it fixed?</h3>
      <p>Some of what's above a script can fix deterministically &mdash; no judgment calls, no
      guessing. Here's what it would change, and you can download the result:</p>
      <ul class="hc-changes" id="hc-change-list"></ul>
      <button class="btn" id="hc-download" type="button">Download cleaned .csv</button>
      <p class="hc-limits" id="hc-limits"></p>
    </div>

    <div class="hc-cta">
      <strong>Want these fixed by a real person?</strong>
      <p>The <a href="/spreadsheet-cleanup-service/">$300 flat cleanup</a> fixes everything above
      in 24&ndash;48h &mdash; or start with a <a href="/free-demo/?from=health-check">free 1-day demo on your real
      data</a>, keep it either way.</p>
      <a class="btn" href="/spreadsheet-cleanup-service/">See the cleanup service</a>
      <!-- Filled in by render() ONLY for a visitor's own file. mailto:, never a form POST: this
           page says the file "never leaves your computer -- there is nowhere here to send it",
           and a POST would make that sentence false. -->
      <div id="hc-send" hidden></div>
      <p style="margin:.9rem 0 0;font-size:.85rem">Tracking work against invoices? The
      <a href="/money-leak-finder/">Money Leak Finder</a> lines up both exports and shows only the
      mismatches &mdash; same rule, nothing uploads. Same customer entered three ways? The
      <a href="/duplicate-customer-finder/">Duplicate Customer Finder</a> shows your real count.</p>
    </div>
  </section>
</main>
"""

SCRIPT = r"""
<script>
(function(){
'use strict';
/* All local. No fetch, no XHR, no beacon -- the privacy claim on this page is
   architectural, not a policy. */

var DECISION = /(^|_|\b)(status|flag|state|result|outcome|approved|paid|active|valid|check|verified|error)(\b|_|$)/i;
var IDISH = /(^|_|\b)(id|invoice|number|no|ref|sku|key)(\b|_|$)/i;
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
    if(q){
      if(c === '"'){ if(text[i+1] === '"'){ cell+='"'; i++; } else q=false; }
      else cell += c;
    } else if(c === '"') q = true;
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

function dateShape(v){
  for(var k=0;k<DATE_SHAPES.length;k++) if(DATE_SHAPES[k][0].test(v)) return DATE_SHAPES[k][1];
  return null;
}
function numberShape(v){
  if(/^-?\$?[\d,]+(\.\d+)?$/.test(v)) return v.indexOf('$')>=0 ? 'currency' : (v.indexOf(',')>=0 ? 'thousands' : 'plain');
  if(/^\(\$?[\d,]+(\.\d+)?\)$/.test(v)) return 'parens-negative';
  return null;
}

function analyze(rows){
  var header = rows[0].map(function(h,i){ return (h||'').trim() || ('column ' + (i+1)); });
  var body = rows.slice(1);
  var n = body.length, findings = [];
  function add(sev, title, where, detail){ findings.push({sev:sev,title:title,where:where,detail:detail}); }

  if(n < 3){ return { header:header, n:n, findings:[{sev:'info',title:'Not enough rows to judge',where:'', detail:'Fewer than 3 data rows -- nothing meaningful to analyze.'}] }; }

  var seen = Object.create(null), dupRows = 0;
  body.forEach(function(r){ var k = r.join(''); if(seen[k]) dupRows++; else seen[k]=1; });
  if(dupRows > 0) add(dupRows > n*0.02 ? 'high' : 'med', dupRows + ' exact duplicate row' + (dupRows>1?'s':''), 'whole sheet',
    'Identical rows usually mean a paste happened twice. Totals built on this sheet are inflated.');

  header.forEach(function(name, ci){
    var vals = body.map(function(r){ return (r[ci] === undefined ? '' : String(r[ci])).trim(); });
    var blanks = vals.filter(function(v){ return v === ''; }).length;
    var present = vals.filter(function(v){ return v !== ''; });
    var counts = Object.create(null);
    present.forEach(function(v){ counts[v] = (counts[v]||0)+1; });
    var distinct = Object.keys(counts);

    if(blanks === n){ add('med', '"' + name + '" is completely empty', 'column ' + (ci+1),
      'Every one of ' + n + ' rows is blank. A column nobody fills in is a column nobody can use.'); return; }
    if(blanks > n*0.5) add('med', '"' + name + '" is ' + Math.round(100*blanks/n) + '% blank', 'column ' + (ci+1),
      'Half-empty columns usually mean the process that fills them broke, or nobody agrees whose job it is.');

    if(present.length >= 8 && distinct.length === 1){
      var isDecision = DECISION.test(name);
      add(isDecision ? 'high' : 'info',
        '"' + name + '" is the same value on every row: "' + distinct[0].slice(0,30) + '"',
        'column ' + (ci+1),
        isDecision
          ? 'A ' + name.toLowerCase() + ' column that never varies cannot tell you anything -- if it is supposed to catch problems, it has never caught one.'
          : 'Constant on all ' + present.length + ' filled rows. Fine if intentional; dead weight if not.');
    }

    var canon = Object.create(null), variants = 0;
    distinct.forEach(function(v){ var k = v.toLowerCase().replace(/\s+/g,' ').trim();
      if(canon[k] !== undefined) variants++; else canon[k]=v; });
    if(variants > 0 && distinct.length < 40) add('med',
      '"' + name + '" has ' + variants + ' spelling/spacing variant' + (variants>1?'s':'') + ' of the same value',
      'column ' + (ci+1),
      'e.g. "Paid" vs "paid " -- filters and pivot tables count these as different things.');

    var shapes = Object.create(null);
    present.forEach(function(v){ var s = dateShape(v); if(s) shapes[s]=(shapes[s]||0)+1; });
    var shapeKeys = Object.keys(shapes);
    if(shapeKeys.length > 1) add('high', '"' + name + '" mixes ' + shapeKeys.length + ' date formats',
      'column ' + (ci+1), shapeKeys.join(', ') + ' in one column -- sorting and date math silently give wrong answers.');

    var nshapes = Object.create(null), numeric = 0;
    present.forEach(function(v){ var s = numberShape(v); if(s){ nshapes[s]=(nshapes[s]||0)+1; numeric++; } });
    if(numeric > present.length*0.6 && Object.keys(nshapes).length > 1) add('med',
      '"' + name + '" mixes number formats', 'column ' + (ci+1),
      Object.keys(nshapes).join(', ') + ' -- some of these are text to Excel, and SUM() skips text without telling you.');

    if(IDISH.test(name) && present.length >= 8){
      var dupIds = present.length - distinct.length;
      if(dupIds > 0) add('high', '"' + name + '" has ' + dupIds + ' duplicate value' + (dupIds>1?'s':''),
        'column ' + (ci+1), 'A column named like an identifier should be unique -- duplicates here usually mean double-entered records.');
    }
  });

  return { header: header, n: n, findings: findings };
}

/* ---- the fix half ----------------------------------------------------------
   Deterministic transforms ONLY. Every change here is one a script can make
   without deciding anything a human would have to weigh in on. Where judgment
   is required (which duplicate is the real customer, which formula broke, what
   a blank means) it does NOTHING and says so -- that boundary is the honest
   line between this button and the paid cleanup. */

function pad2(n){ return (n < 10 ? '0' : '') + n; }
var MONTHS = {jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12};

function toISO(v, fallbackYear){
  var m = v.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if(m) return m[1] + '-' + pad2(+m[2]) + '-' + pad2(+m[3]);
  m = v.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/);
  if(m){ var y = m[3].length === 2 ? 2000 + (+m[3]) : +m[3]; return y + '-' + pad2(+m[1]) + '-' + pad2(+m[2]); }
  m = v.match(/^(\d{1,2})-([A-Za-z]{3})$/);
  // A bare "3-Jul" has no year in the file. Borrow the year the rest of the
  // column agrees on rather than inventing one; skip if the column has none.
  if(m && fallbackYear && MONTHS[m[2].toLowerCase()]) return fallbackYear + '-' + pad2(MONTHS[m[2].toLowerCase()]) + '-' + pad2(+m[1]);
  m = v.match(/^([A-Za-z]{3,9}) (\d{1,2}),? (\d{4})$/);
  if(m && MONTHS[m[1].slice(0,3).toLowerCase()]) return m[3] + '-' + pad2(MONTHS[m[1].slice(0,3).toLowerCase()]) + '-' + pad2(+m[2]);
  return null;
}

function normalize(rows){
  var header = rows[0].slice();
  var body = rows.slice(1).map(function(r){ return r.slice(); });
  var changes = [], limits = [];
  var n = body.length;

  // 1. trim surrounding whitespace (safe everywhere)
  var trimmed = 0;
  body.forEach(function(r){
    for(var i=0;i<r.length;i++){
      var before = r[i] === undefined ? '' : String(r[i]);
      var after = before.trim().replace(/\s+/g, ' ');
      if(after !== before){ r[i] = after; trimmed++; }
    }
  });
  if(trimmed) changes.push('Trimmed stray spaces in ' + trimmed + ' cell' + (trimmed===1?'':'s'));

  // 2. drop exact duplicate rows (keep first occurrence)
  var seen = Object.create(null), kept = [], dropped = 0;
  body.forEach(function(r){
    var k = r.join('');
    if(seen[k]){ dropped++; return; }
    seen[k] = 1; kept.push(r);
  });
  body = kept;
  if(dropped) changes.push('Removed ' + dropped + ' exact duplicate row' + (dropped===1?'':'s') + ' (kept the first of each)');

  header.forEach(function(name, ci){
    var vals = body.map(function(r){ return (r[ci]===undefined?'':String(r[ci])); });
    var present = vals.filter(Boolean);
    if(!present.length) return;

    // 3. case/spacing variants -> the most common spelling in that column
    var groups = Object.create(null);
    present.forEach(function(v){
      var k = v.toLowerCase();
      (groups[k] = groups[k] || Object.create(null));
      groups[k][v] = (groups[k][v] || 0) + 1;
    });
    var canon = Object.create(null), variantFixes = 0;
    Object.keys(groups).forEach(function(k){
      var forms = Object.keys(groups[k]);
      if(forms.length < 2) return;
      forms.sort(function(a,b){ return groups[k][b] - groups[k][a]; });
      canon[k] = forms[0];
    });
    if(Object.keys(canon).length){
      body.forEach(function(r){
        var v = r[ci] === undefined ? '' : String(r[ci]);
        var k = v.toLowerCase();
        if(canon[k] && canon[k] !== v){ r[ci] = canon[k]; variantFixes++; }
      });
      if(variantFixes) changes.push('Unified ' + variantFixes + ' value' + (variantFixes===1?'':'s') +
        ' in "' + name + '" to the spelling already used most often');
    }

    // 4. mixed date formats -> ISO (only when the column IS mostly dates AND mixed)
    var shapes = Object.create(null), dateCount = 0, years = Object.create(null);
    present.forEach(function(v){
      var s = dateShape(v); if(!s) return;
      shapes[s] = (shapes[s]||0)+1; dateCount++;
      var ym = v.match(/(\d{4})/); if(ym) years[ym[1]] = (years[ym[1]]||0)+1;
    });
    if(Object.keys(shapes).length > 1 && dateCount > present.length*0.7){
      var yearKeys = Object.keys(years).sort(function(a,b){ return years[b]-years[a]; });
      var fallbackYear = yearKeys.length ? yearKeys[0] : null;
      var dateFixes = 0, dateSkips = 0;
      body.forEach(function(r){
        var v = r[ci] === undefined ? '' : String(r[ci]);
        if(!v || !dateShape(v)) return;
        var iso = toISO(v, fallbackYear);
        if(iso === null){ dateSkips++; return; }
        if(iso !== v){ r[ci] = iso; dateFixes++; }
      });
      if(dateFixes) changes.push('Converted ' + dateFixes + ' date' + (dateFixes===1?'':'s') +
        ' in "' + name + '" to one format (YYYY-MM-DD)' +
        (fallbackYear ? ', using ' + fallbackYear + ' where the file gave no year' : ''));
      if(dateSkips) limits.push(dateSkips + ' value' + (dateSkips===1?'':'s') + ' in "' + name +
        '" were left alone -- the date was too ambiguous to convert safely');
    }

    // 5. mixed number formats -> plain numbers (parens = negative, per accounting convention)
    var nshapes = Object.create(null), numCount = 0;
    present.forEach(function(v){ var s = numberShape(v); if(s){ nshapes[s]=(nshapes[s]||0)+1; numCount++; } });
    if(Object.keys(nshapes).length > 1 && numCount > present.length*0.6){
      var numFixes = 0;
      body.forEach(function(r){
        var v = r[ci] === undefined ? '' : String(r[ci]);
        if(!v || !numberShape(v)) return;
        var neg = /^\(.*\)$/.test(v);
        var plain = v.replace(/[$,\s()]/g, '');
        if(neg) plain = '-' + plain;
        if(plain !== v){ r[ci] = plain; numFixes++; }
      });
      if(numFixes) changes.push('Made ' + numFixes + ' value' + (numFixes===1?'':'s') + ' in "' + name +
        '" plain numbers so SUM() stops skipping them (kept parentheses as negatives)');
    }
  });

  return { rows: [header].concat(body), changes: changes, limits: limits, removed: dropped };
}

function toCSV(rows){
  return rows.map(function(r){
    return r.map(function(cell){
      var v = cell === undefined || cell === null ? '' : String(cell);
      return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
    }).join(',');
  }).join('\r\n') + '\r\n';
}

var SAMPLE = 'Invoice No,Date,Customer,Amount,Status,Notes\n' +
'1001,2026-07-01,Acme Roofing,"$1,250.00",Paid,\n' +
'1002,07/02/2026,Baker Law,1980,Paid ,\n' +
'1003,2026-07-03,Acme Roofing,"$2,100.00",Paid,\n' +
'1003,2026-07-03,Acme Roofing,"$2,100.00",Paid,\n' +
'1004,3-Jul,Sunrise Vet,(450.00),paid,\n' +
'1005,2026-07-08,Baker Law,760,Paid,\n' +
'1006,07/09/2026,Palm Realty,"1,420",Paid,\n' +
'1007,2026-07-10,Sunrise Vet,890,Paid,\n' +
'1008,2026-07-11,Acme Roofing,,Paid,\n' +
'1009,2026-07-14,Palm Realty,2350,Paid,\n';

function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

/* Severity COUNTS only -- never a finding's text, which quotes real column names and cell
   values straight out of the visitor's file. */
function sendBlock(counts, rows, cols){
  var host = document.getElementById('hc-send');
  if(!host) return;
  if(!(counts.high + counts.med)){ host.hidden = true; host.innerHTML = ''; return; }
  var body = 'Hi Colin,\n\nI ran the spreadsheet health check on my own file (' + rows +
             ' rows, ' + cols + ' columns). It found:\n\n' +
             '- ' + counts.high + ' needing attention\n' +
             '- ' + counts.med + ' worth checking\n' +
             '- ' + counts.info + ' informational\n\n' +
             'I have not sent you the file itself.\n\n[Anything you want to add]\n';
  var href = 'mailto:colin@automatedworkflowllc.com' +
             '?subject=' + encodeURIComponent('Spreadsheet health check - what it found on my file') +
             '&body=' + encodeURIComponent(body);
  host.hidden = false;
  host.innerHTML =
    '<p style="margin:.9rem 0 .5rem;font-size:.85rem">Or send Colin just the tally &mdash; opens your ' +
    'own email app, already written. Your file stays in this browser; nothing is attached.</p>' +
    '<a class="btn" id="hc-mail" href="' + href + '">Email this tally to Colin</a>';
}

function render(name, result, isSample){
  var rep = document.getElementById('hc-report');
  var SEV = {high:0, med:1, info:2};
  var LABEL = {high:'Needs attention', med:'Worth checking', info:'For information'};
  var fs = result.findings.slice().sort(function(a,b){ return SEV[a.sev]-SEV[b.sev]; });
  var counts = {high:0, med:0, info:0};
  fs.forEach(function(f){ counts[f.sev]++; });
  document.getElementById('hc-title').textContent = 'Report: ' + name + ' — ' + result.n + ' rows, ' + result.header.length + ' columns';
  document.getElementById('hc-tally').innerHTML =
    '<div class="hc-pill"><b>' + counts.high + '</b><span>needs attention</span></div>' +
    '<div class="hc-pill"><b>' + counts.med + '</b><span>worth checking</span></div>' +
    '<div class="hc-pill"><b>' + counts.info + '</b><span>informational</span></div>';

  if(isSample){
    var sh = document.getElementById('hc-send');
    if(sh){ sh.hidden = true; sh.innerHTML = ''; }
  } else {
    sendBlock(counts, result.n, result.header.length);
  }
  var out = '', lastSev = null;
  if(!fs.length){
    out = '<div class="hc-clean"><strong>Nothing found.</strong> Every column varies, dates are consistent, no duplicate rows. That is the result you want -- and it is not the same as not having looked.</div>';
  } else fs.forEach(function(f){
    if(f.sev !== lastSev){ lastSev = f.sev; out += '<h3 style="font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-soft);margin:1.2rem 0 .5rem">' + LABEL[f.sev] + '</h3>'; }
    out += '<div class="hc-find sev-' + f.sev + '"><h4>' + esc(f.title) + '</h4>' +
      (f.where ? '<div class="hc-where">' + esc(f.where) + '</div>' : '') +
      '<p>' + esc(f.detail) + '</p></div>';
  });
  document.getElementById('hc-findings').innerHTML = out;
  rep.style.display = 'block';
  rep.scrollIntoView({behavior:'smooth', block:'start'});
}

var pendingClean = null;

function showFix(name, rows){
  var panel = document.getElementById('hc-fix');
  var result;
  try { result = normalize(rows); } catch(e){ panel.style.display = 'none'; return; }
  if(!result.changes.length){
    panel.style.display = 'none';   // nothing a script can safely fix -- don't offer
    pendingClean = null;
    return;
  }
  pendingClean = { name: name.replace(/\.(csv|tsv|txt)$/i, '') + '-cleaned.csv', rows: result.rows };
  document.getElementById('hc-change-list').innerHTML =
    result.changes.map(function(c){ return '<li>' + esc(c) + '</li>'; }).join('');
  var limits = result.limits.slice();
  limits.push('It will NOT guess: blanks stay blank, near-duplicate rows that are not identical ' +
    'stay put, and no formula is touched. Those need a person to decide -- that is what the $300 cleanup is.');
  document.getElementById('hc-limits').innerHTML = limits.map(esc).join(' ');
  panel.style.display = 'block';
}

function handleText(name, text, isSample){
  try {
    var rows = parseCSV(text);
    if(!rows.length){ alert('That file appears to be empty.'); return; }
    render(name, analyze(rows), isSample);
    showFix(name, rows);
  } catch(e){
    alert('Could not analyze that file. If it is an Excel workbook, save it as CSV first.');
  }
}
function handleFile(f){
  if(!f) return;
  readAny(f, function(text){ handleText(f.name, text); });
}

var drop = document.getElementById('hc-drop');
var input = document.getElementById('hc-file');
drop.addEventListener('click', function(){ input.click(); });
drop.addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); input.click(); } });
input.addEventListener('change', function(){ handleFile(input.files[0]); });
['dragover','dragenter'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.add('is-over'); }); });
['dragleave','drop'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.remove('is-over'); }); });
drop.addEventListener('drop', function(e){ handleFile(e.dataTransfer.files[0]); });
document.getElementById('hc-sample').addEventListener('click', function(){ handleText('sample-invoices.csv', SAMPLE, true); });
document.getElementById('hc-download').addEventListener('click', function(){
  if(!pendingClean) return;
  // Blob + object URL: the file is assembled in the page and handed to the
  // browser's own download. Still nothing leaves the machine.
  var blob = new Blob([toCSV(pendingClean.rows)], {type:'text/csv;charset=utf-8'});
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = pendingClean.name;
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
  "name": "Spreadsheet Health Check",
  "url": "https://automatedworkflowllc.com/spreadsheet-health-check/",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Any",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "description": "Free in-browser spreadsheet analyzer: dead columns, constant status fields, mixed date formats, duplicate rows. No upload -- runs locally."
}
</script>
"""


def main() -> None:
    s = TEMPLATE.read_text(encoding='utf-8')
    header_end = s.index('</header>') + len('</header>')
    head = s[:header_end]
    footer_start = s.index('<footer')
    footer_end = s.index('</footer>') + len('</footer>')
    footer = s[footer_start:footer_end]

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
