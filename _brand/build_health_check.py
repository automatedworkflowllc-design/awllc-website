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

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'spreadsheet-health-check'

TITLE = 'Free Spreadsheet Health Check — Nothing Uploads'
DESC = ('Drop any CSV export and get an instant, honest report: dead columns, '
        'status fields that never vary, mixed date formats, duplicate rows. '
        'Runs entirely in your browser — your data never leaves your machine.')
CANON = 'https://automatedworkflowllc.com/spreadsheet-health-check/'

PAGE_CSS = """
/* ---- health check page ---- */
.hc-drop{border:2px dashed var(--line-strong);border-radius:16px;background:var(--card);
padding:2.6rem 1.4rem;text-align:center;cursor:pointer;transition:border-color .15s,background .15s}
.hc-drop.is-over{border-color:var(--accent);background:var(--well)}
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
.hc-clean{border-left:4px solid var(--accent);background:var(--card);border-radius:.6rem;
padding:1rem 1.2rem;color:var(--ink-soft)}
.hc-cta{margin-top:1.6rem;padding:1.3rem;border:1px solid var(--line);border-radius:12px;background:var(--bg-soft)}
.hc-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
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
    <input type="file" id="hc-file" accept=".csv,.tsv,.txt" style="display:none">
  </div>
  <div class="hc-actions">
    <button class="btn" id="hc-sample" type="button">Try the sample file</button>
  </div>
  <p class="hc-note">Using Excel? <code>File &rarr; Save As &rarr; CSV</code> first &mdash; this
    tool deliberately reads only plain text it can analyze in front of you.</p>

  <section id="hc-report" aria-live="polite">
    <h2 id="hc-title" style="margin-bottom:.8rem"></h2>
    <div class="hc-tally" id="hc-tally"></div>
    <div id="hc-findings"></div>
    <div class="hc-cta">
      <strong>Want these fixed by a real person?</strong>
      <p>The <a href="/spreadsheet-cleanup-service/">$300 flat cleanup</a> fixes everything above
      in 24&ndash;48h &mdash; or start with a <a href="/free-demo/">free 1-day demo on your real
      data</a>, keep it either way.</p>
      <a class="btn" href="/spreadsheet-cleanup-service/">See the cleanup service</a>
      <p style="margin:.9rem 0 0;font-size:.85rem">Tracking work against invoices? The
      <a href="/money-leak-finder/">Money Leak Finder</a> lines up both exports and shows only the
      mismatches &mdash; same rule, nothing uploads.</p>
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

function render(name, result){
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

function handleText(name, text){
  try {
    var rows = parseCSV(text);
    if(!rows.length){ alert('That file appears to be empty.'); return; }
    render(name, analyze(rows));
  } catch(e){
    alert('Could not analyze that file. If it is an Excel workbook, save it as CSV first.');
  }
}
function handleFile(f){
  if(!f) return;
  var reader = new FileReader();
  reader.onload = function(){ handleText(f.name, String(reader.result)); };
  reader.readAsText(f);
}

var drop = document.getElementById('hc-drop');
var input = document.getElementById('hc-file');
drop.addEventListener('click', function(){ input.click(); });
drop.addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); input.click(); } });
input.addEventListener('change', function(){ handleFile(input.files[0]); });
['dragover','dragenter'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.add('is-over'); }); });
['dragleave','drop'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.remove('is-over'); }); });
drop.addEventListener('drop', function(e){ handleFile(e.dataTransfer.files[0]); });
document.getElementById('hc-sample').addEventListener('click', function(){ handleText('sample-invoices.csv', SAMPLE); });
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
    head = head.replace('</head>', f'<style>{PAGE_CSS}</style>\n</head>')

    page = head + MAIN + footer + LD + SCRIPT + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
