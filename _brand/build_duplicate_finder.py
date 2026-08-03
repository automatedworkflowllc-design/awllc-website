#!/usr/bin/env python3
"""Build /duplicate-customer-finder/ -- the third free in-browser tool.

The third universal small-business spreadsheet disease, after structure
(health check) and reconciliation (money leak finder): the same customer
entered three ways. "Acme Roofing" / "Acme Roofing LLC" / "acme roofing inc."
inflates the customer count, splits revenue history across phantom accounts,
and quietly breaks every mail merge.

Same architecture as its siblings: shell inherited verbatim from the
cleanup-service page, all matching in the browser, no endpoint, nothing
uploads. Matching is transparent by construction -- every group shows WHY it
grouped (normalized key vs. typo distance), because a merge tool nobody can
audit is one nobody should trust with a customer list.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'duplicate-customer-finder'

TITLE = 'Free Duplicate Customer Finder — Runs In Your Browser'
DESC = ('Find the same customer entered three ways: Acme Roofing vs Acme Roofing LLC '
        'vs acme roofing inc. See your real customer count. Runs in your browser — '
        'nothing uploads.')
CANON = 'https://automatedworkflowllc.com/duplicate-customer-finder/'

PAGE_CSS = """
/* ---- duplicate finder ---- */
.dc-drop{border:2px dashed var(--line-strong);border-radius:16px;background:var(--card);
padding:2.6rem 1.4rem;text-align:center;cursor:pointer}
.dc-drop.is-over{border-color:var(--accent);background:var(--well)}
.dc-drop:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.dc-drop strong{display:block;font-size:1.05rem;margin-bottom:.35rem}
.dc-drop span{color:var(--ink-soft);font-size:.92rem}
.dc-actions{display:flex;gap:.7rem;justify-content:center;flex-wrap:wrap;margin-top:1rem;align-items:center}
.dc-actions label{font-size:.85rem;color:var(--ink-soft)}
.dc-actions select{font:inherit;font-size:.85rem;padding:.35rem .5rem;border:1px solid var(--line-strong);
border-radius:.4rem;background:var(--card);color:var(--ink)}
.dc-note{margin-top:1rem;font-size:.85rem;color:var(--ink-soft);text-align:center}
.dc-note code{font-family:var(--mono);font-size:.8rem}
#dc-report{margin-top:2rem;display:none}
.dc-head{display:flex;gap:.8rem;flex-wrap:wrap;margin:0 0 1.3rem;align-items:stretch}
.dc-kpi{border:1px solid var(--line);border-radius:.7rem;padding:.85rem 1.1rem;background:var(--card)}
.dc-kpi b{display:block;font-size:1.7rem;font-family:var(--mono);line-height:1.1}
.dc-kpi.k-bad b{color:#B4452C}
.dc-kpi span{font-size:.75rem;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.06em}
.dc-group{background:var(--card);border:1px solid var(--line);border-left:4px solid #B4452C;
border-radius:.6rem;padding:.85rem 1.05rem;margin:0 0 .6rem}
.dc-group.soft{border-left-color:#A8842B}
.dc-group h4{margin:0 0 .35rem;font-size:.95rem}
.dc-variants{margin:0;padding-left:1.15rem;font-size:.9rem;color:var(--ink-soft)}
.dc-variants li{margin:.1rem 0}
.dc-variants .cnt{font-family:var(--mono);font-size:.8rem}
.dc-why{margin:.4rem 0 0;font-size:.8rem;color:var(--ink-soft);font-style:italic}
.dc-cta{margin-top:1.6rem;padding:1.3rem;border:1px solid var(--line);border-radius:12px;background:var(--bg-soft)}
.dc-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
.dc-clean{border-left:4px solid var(--accent);background:var(--card);border-radius:.6rem;
padding:1rem 1.2rem;color:var(--ink-soft)}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">Duplicate Customer Finder</h1>
  <p style="color:var(--ink-soft);max-width:40rem">
    <em>Acme Roofing</em>. <em>Acme Roofing LLC</em>. <em>acme roofing inc.</em> Three rows, one
    customer &mdash; and now your customer count is wrong, their revenue history is split three
    ways, and the mail merge sends them three copies.
  </p>
  <p style="max-width:40rem"><strong>Nothing uploads.</strong>
    <span style="color:var(--ink-soft)">The matching runs entirely in your browser &mdash; there is
    no server to send your customer list to. Check the network tab: zero requests after load.</span></p>

  <div class="dc-drop" id="dc-drop" role="button" tabindex="0"
       aria-label="Choose a CSV file of customers to check locally">
    <strong>Drop a .csv here</strong>
    <span>customer list, invoice export, contact export &middot; stays on your machine</span>
    <input type="file" id="dc-file" accept=".csv,.tsv,.txt" style="display:none">
  </div>
  <div class="dc-actions">
    <button class="btn" id="dc-sample" type="button">Try the sample list</button>
    <label for="dc-col">Column:</label>
    <select id="dc-col" aria-label="Which column holds the customer name"></select>
  </div>
  <p class="dc-note">It picks the most name-like column automatically &mdash; switch it above if it
    guessed wrong. Excel users: <code>File &rarr; Save As &rarr; CSV</code> first.</p>

  <section id="dc-report" aria-live="polite">
    <h2 id="dc-title" style="margin-bottom:.9rem"></h2>
    <div class="dc-head" id="dc-kpis"></div>
    <div id="dc-groups"></div>
    <div class="dc-cta">
      <strong>Want them merged properly?</strong>
      <p>Deciding which spelling is the real record &mdash; and re-pointing every invoice, job and
      contact at it without losing history &mdash; is judgment work, not a script. That's what the
      <a href="/spreadsheet-cleanup-service/">$300 flat cleanup</a> does, or start with a
      <a href="/free-demo/">free 1-day demo on your real data</a>.</p>
      <a class="btn" href="/free-demo/">Get it done on your real list — free</a>
      <p style="margin:.9rem 0 0;font-size:.85rem">Also try the
      <a href="/spreadsheet-health-check/">Spreadsheet Health Check</a> (dead columns, mixed dates,
      exact duplicate rows) and the
      <a href="/money-leak-finder/">Money Leak Finder</a> (work done vs. work billed).</p>
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

/* Legal-form suffixes and punctuation are the usual difference between two
   spellings of one company. Stripping them is the FIRST pass; anything caught
   here is reported as an exact normalized match, not a fuzzy guess. */
var SUFFIXES = /\b(inc|llc|ltd|co|corp|corporation|company|incorporated|pllc|pc|lp|llp|plc|group|grp|holdings|enterprises|services|svcs|sons)\b/g;
var NOISE = /[.,'’"()\-_/\\]+/g;

function normName(s){
  var v = String(s).toLowerCase();
  v = v.replace(/&/g, ' and ');
  v = v.replace(NOISE, ' ');
  v = v.replace(SUFFIXES, ' ');
  v = v.replace(/\bthe\b/g, ' ');
  v = v.replace(/\band\b/g, ' ');
  return v.replace(/\s+/g, ' ').trim();
}

/* Bounded Levenshtein: bails as soon as the row minimum exceeds `max`, so a long
   list does not turn into an O(n*m) stall on a phone. */
function withinEdits(a, b, max){
  if(Math.abs(a.length - b.length) > max) return false;
  if(a === b) return true;
  var prev = [], cur = [], i, j;
  for(j = 0; j <= b.length; j++) prev[j] = j;
  for(i = 1; i <= a.length; i++){
    cur[0] = i;
    var best = cur[0];
    for(j = 1; j <= b.length; j++){
      var cost = a.charAt(i-1) === b.charAt(j-1) ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j-1] + 1, prev[j-1] + cost);
      if(cur[j] < best) best = cur[j];
    }
    if(best > max) return false;
    for(j = 0; j <= b.length; j++) prev[j] = cur[j];
  }
  return prev[b.length] <= max;
}

function looksLikeName(header, values){
  if(/name|customer|client|company|account|vendor|payee|contact|organi/i.test(header)) return 3;
  var present = values.filter(Boolean);
  if(!present.length) return -1;
  var alpha = present.filter(function(v){ return /[A-Za-z]{3,}/.test(v) && !/^\d+$/.test(v); }).length;
  var distinct = Object.keys(present.reduce(function(a,v){ a[v]=1; return a; }, {})).length;
  // A name column is mostly words AND repeats (one customer, several rows).
  return (alpha / present.length) > 0.7 && distinct < present.length ? 1 : 0;
}

function pickColumn(header, body){
  var best = -1, bestScore = -1;
  header.forEach(function(h, i){
    var vals = body.map(function(r){ return (r[i]===undefined?'':String(r[i])).trim(); });
    var s = looksLikeName(h, vals);
    if(s > bestScore){ bestScore = s; best = i; }
  });
  return best < 0 ? 0 : best;
}

function findGroups(values){
  // Pass 1: exact match on the normalized key (case/punctuation/suffix differences).
  var byKey = Object.create(null);
  values.forEach(function(v){
    if(!v) return;
    var k = normName(v);
    if(!k) return;
    (byKey[k] = byKey[k] || Object.create(null));
    byKey[k][v] = (byKey[k][v] || 0) + 1;
  });

  var keys = Object.keys(byKey);
  var used = Object.create(null), groups = [];

  // Pass 2: near-miss keys (typos). Threshold scales with length so "Smith"/"Smyth"
  // group while short unrelated names stay apart.
  keys.forEach(function(k){
    if(used[k]) return;
    var members = [k];
    used[k] = 1;
    var max = k.length <= 6 ? 1 : (k.length <= 14 ? 2 : 3);
    keys.forEach(function(other){
      if(used[other] || other === k) return;
      if(withinEdits(k, other, max)){ members.push(other); used[other] = 1; }
    });

    var variants = Object.create(null), total = 0, fuzzy = members.length > 1;
    members.forEach(function(m){
      Object.keys(byKey[m]).forEach(function(form){
        variants[form] = (variants[form] || 0) + byKey[m][form];
        total += byKey[m][form];
      });
    });
    var forms = Object.keys(variants);
    if(forms.length < 2) return;   // one spelling only -- not a duplicate
    forms.sort(function(a,b){ return variants[b] - variants[a]; });
    groups.push({ canonical: forms[0], forms: forms, counts: variants, rows: total, fuzzy: fuzzy });
  });

  groups.sort(function(a,b){ return b.rows - a.rows; });
  return groups;
}

function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

var current = null;   // { name, header, body }

function run(){
  if(!current) return;
  var ci = parseInt(document.getElementById('dc-col').value, 10) || 0;
  var values = current.body.map(function(r){ return (r[ci]===undefined?'':String(r[ci])).trim(); });
  var present = values.filter(Boolean);
  var groups = findGroups(values);

  var distinctRaw = Object.keys(present.reduce(function(a,v){ a[v]=1; return a; }, {})).length;
  var collapsed = groups.reduce(function(n, g){ return n + (g.forms.length - 1); }, 0);
  var realCount = distinctRaw - collapsed;

  document.getElementById('dc-title').textContent =
    'Report: ' + current.name + ' — "' + current.header[ci] + '" column, ' + present.length + ' filled rows';
  document.getElementById('dc-kpis').innerHTML =
    '<div class="dc-kpi"><b>' + distinctRaw + '</b><span>distinct spellings</span></div>' +
    '<div class="dc-kpi' + (collapsed ? ' k-bad' : '') + '"><b>' + realCount + '</b><span>likely real customers</span></div>' +
    '<div class="dc-kpi' + (groups.length ? ' k-bad' : '') + '"><b>' + groups.length + '</b><span>collision' + (groups.length===1?'':'s') + ' found</span></div>';

  var out = '';
  if(!groups.length){
    out = '<div class="dc-clean"><strong>No duplicates found.</strong> Every spelling in that column ' +
      'is distinct even after ignoring case, punctuation and legal suffixes. That is the result you ' +
      'want &mdash; and it is not the same as not having looked.</div>';
  } else groups.forEach(function(g){
    out += '<div class="dc-group' + (g.fuzzy ? ' soft' : '') + '">' +
      '<h4>' + esc(g.canonical) + ' &mdash; ' + g.forms.length + ' spellings, ' + g.rows + ' rows</h4><ul class="dc-variants">';
    g.forms.forEach(function(f){
      out += '<li>' + esc(f) + ' <span class="cnt">&times;' + g.counts[f] + '</span></li>';
    });
    out += '</ul><p class="dc-why">' + (g.fuzzy
      ? 'Grouped by near-identical spelling (small typo distance) after ignoring case, punctuation and legal suffixes — worth a human glance.'
      : 'Grouped because they are identical once case, punctuation and legal suffixes are ignored.') + '</p></div>';
  });
  document.getElementById('dc-groups').innerHTML = out;
  var rep = document.getElementById('dc-report');
  rep.style.display = 'block';
  rep.scrollIntoView({behavior:'smooth', block:'start'});
}

function load(name, text){
  var rows = parseCSV(text);
  if(rows.length < 2){ alert('That file has no data rows to check.'); return; }
  var header = rows[0].map(function(h,i){ return (h||'').trim() || ('column ' + (i+1)); });
  var body = rows.slice(1).filter(function(r){ return r.join('').trim() !== ''; });
  current = { name: name, header: header, body: body };
  var sel = document.getElementById('dc-col');
  sel.innerHTML = header.map(function(h,i){ return '<option value="' + i + '">' + esc(h) + '</option>'; }).join('');
  sel.value = String(pickColumn(header, body));
  run();
}

var SAMPLE = 'Customer,City,Last Invoice,Amount\n' +
'Acme Roofing,Gainesville,2026-07-02,1250\n' +
'Acme Roofing LLC,Gainesville,2026-07-14,980\n' +
'acme roofing inc.,Gainesville,2026-06-28,2100\n' +
'Baker & Sons Law,Ocala,2026-07-05,760\n' +
'Baker and Sons Law LLC,Ocala,2026-07-19,1180\n' +
'Sunrise Veterinary,Alachua,2026-07-08,450\n' +
'Sunrise Vetrinary,Alachua,2026-07-21,390\n' +
'Palm Realty Group,Gainesville,2026-07-09,1420\n' +
'Palm Realty Grp.,Gainesville,2026-07-23,2350\n' +
'Northgate Church,Newberry,2026-07-14,860\n' +
'Marlin Self-Serve,Ocala,2026-07-18,310\n' +
'Rivertown Storage,Gainesville,2026-07-11,1150\n';

var drop = document.getElementById('dc-drop');
var input = document.getElementById('dc-file');
function handleFile(f){
  if(!f) return;
  var reader = new FileReader();
  reader.onload = function(){
    try { load(f.name, String(reader.result)); }
    catch(e){ alert('Could not read that file. If it is an Excel workbook, save it as CSV first.'); }
  };
  reader.readAsText(f);
}
drop.addEventListener('click', function(){ input.click(); });
drop.addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); input.click(); } });
input.addEventListener('change', function(){ handleFile(input.files[0]); });
['dragover','dragenter'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.add('is-over'); }); });
['dragleave','drop'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.remove('is-over'); }); });
drop.addEventListener('drop', function(e){ handleFile(e.dataTransfer.files[0]); });
document.getElementById('dc-sample').addEventListener('click', function(){ load('sample-customers.csv', SAMPLE); });
document.getElementById('dc-col').addEventListener('change', run);
})();
</script>
"""

LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Duplicate Customer Finder",
  "url": "https://automatedworkflowllc.com/duplicate-customer-finder/",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Any",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "description": "Free in-browser duplicate customer detector: finds the same customer entered several ways across case, punctuation, legal suffixes and typos. No upload -- runs locally."
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
