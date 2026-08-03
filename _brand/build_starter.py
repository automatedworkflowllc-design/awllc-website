#!/usr/bin/env python3
"""Build /starter/ -- the tool that asks for nothing.

Every other free tool on this site begins with "show me your mess." That is a
real barrier: a stranger who is curious but not yet ready to hand over their
books sees nothing at all, and the ones who most need help are the least
comfortable uploading. So this one inverts it. Instead of auditing the
spreadsheet you have, it hands you one that cannot develop the disease.

Press a button, get a real .xlsx: a job log, an invoice register, and a
dashboard already wired with the formulas that make the two expensive leaks
impossible to hide. Work with no matching invoice flags itself. An invoice past
60 days flags itself. Nobody has to remember to check, which is the entire
reason those numbers go unnoticed for months.

Built in the browser with no library. A minimal store-only ZIP writer plus
hand-built SpreadsheetML -- roughly 90 lines -- because the alternative is
pulling a CDN bundle, and the promise on every one of these pages is that no
request leaves the page. That promise is worth more than the convenience.

Dates are written as ISO text and the formulas use DATEVALUE() rather than
Excel serial numbers, which lets the workbook skip styles.xml entirely. Fewer
parts is fewer ways to emit a file Excel refuses to open.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'starter'

TITLE = 'Free Job & Invoice Tracker — Built For You In One Click'
DESC = ('Download a working Excel tracker that flags unbilled jobs and overdue invoices '
        'by itself. No upload, no signup, no data required to start.')
CANON = 'https://automatedworkflowllc.com/starter/'

PAGE_CSS = """
/* ---- starter generator ---- */
.st-lede{max-width:41rem;font-size:1.05rem}
.st-panel{border:1px solid var(--line-strong);border-radius:14px;background:var(--card);
padding:1.6rem;margin:1.6rem 0}
.st-opts{display:flex;gap:1.4rem;flex-wrap:wrap;margin:0 0 1.2rem}
.st-opt{display:flex;gap:.5rem;align-items:flex-start;font-size:.93rem;max-width:20rem}
.st-opt input{margin-top:.25rem}
.st-opt span{color:var(--ink-soft);font-size:.85rem;display:block}
.st-go{font:inherit;font-weight:600;font-size:1rem;padding:.8rem 1.5rem;border-radius:.6rem;
border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}
.st-go:hover{filter:brightness(1.08)}
.st-go:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.st-said{margin:.9rem 0 0;font-size:.9rem;color:var(--ink-soft);min-height:1.3em}
.st-sheets{display:grid;gap:.7rem;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));margin:1.2rem 0 0}
.st-sheet{border:1px solid var(--line);border-radius:.7rem;padding:.9rem 1.1rem;background:var(--bg-soft)}
.st-sheet h3{margin:0 0 .3rem;font-size:.95rem}
.st-sheet p{margin:0;font-size:.87rem;color:var(--ink-soft)}
.st-sheet code{font-family:var(--mono);font-size:.78rem}
.st-form{border:1px solid var(--line);border-radius:.7rem;background:var(--card);
padding:1rem 1.2rem;margin:.6rem 0 0}
.st-form h4{margin:0 0 .25rem;font-size:.9rem}
.st-form pre{font-family:var(--mono);font-size:.78rem;background:var(--bg-soft);border:1px solid var(--line);
border-radius:.4rem;padding:.55rem .7rem;overflow-x:auto;margin:.35rem 0}
.st-form p{margin:.3rem 0 0;font-size:.86rem;color:var(--ink-soft)}
.st-cta{margin-top:1.8rem;padding:1.4rem;border:1px solid var(--line);border-radius:12px;background:var(--bg-soft)}
.st-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">You don't have a spreadsheet problem yet.<br>Start without one.</h1>
  <p class="st-lede" style="color:var(--ink-soft)">
    Our other tools ask you to upload a file so they can tell you what is wrong with it. This one
    asks for nothing. Press the button and you get a working Excel tracker where the two mistakes
    that actually cost money &mdash; finishing work you never invoice, and invoices quietly ageing
    past 60 days &mdash; <strong>flag themselves</strong>. Nobody has to remember to check.
  </p>

  <div class="st-panel">
    <div class="st-opts">
      <label class="st-opt"><input type="checkbox" id="st-samples" checked>
        <span style="color:var(--ink)"><strong>Include a few example rows</strong>
        <span>So you can see the flags working before you type anything. Delete them when you start.</span></span></label>
      <label class="st-opt"><input type="checkbox" id="st-guide" checked>
        <span style="color:var(--ink)"><strong>Add a "How this works" sheet</strong>
        <span>Plain-English notes on every formula, so this is yours to change &mdash; not a black box.</span></span></label>
    </div>
    <button class="st-go" id="st-build" type="button">Build my tracker &mdash; download .xlsx</button>
    <p class="st-said" id="st-said">No upload, no signup, no email. The file is assembled in your
      browser and saved straight to your downloads.</p>
  </div>

  <h2>What you get</h2>
  <div class="st-sheets">
    <div class="st-sheet"><h3>Jobs</h3><p>Every job you complete. The
      <code>Invoiced?</code> column watches the invoice register and turns itself into
      <code>NOT INVOICED</code> the moment a finished job has no matching invoice number.</p></div>
    <div class="st-sheet"><h3>Invoices</h3><p>What you billed, and whether it landed.
      <code>Days Outstanding</code> and <code>Status</code> update themselves every time the file
      opens &mdash; <code>OVER 60 DAYS</code> is not a note someone forgot to write.</p></div>
    <div class="st-sheet"><h3>Dashboard</h3><p>Five live totals: money finished but never invoiced,
      money outstanding, money past 60 days, and a duplicate-job-number count that catches
      double entry before it reaches a customer.</p></div>
  </div>

  <h2 style="margin-top:2.2rem">The formulas, in the open</h2>
  <p style="max-width:41rem;color:var(--ink-soft)">These are the whole trick. There is nothing else
    in the file &mdash; no macros, no add-in, no link back to us.</p>

  <div class="st-form">
    <h4>Did we ever invoice this job?</h4>
    <pre>=IF($A2="","",IF(COUNTIF(Invoices!$B:$B,$A2)&gt;0,"Yes","NOT INVOICED"))</pre>
    <p>Looks for this job's number in the invoice register. Absent means finished work nobody
      billed &mdash; the single most common leak we find in real books.</p>
  </div>
  <div class="st-form">
    <h4>How old is this invoice, really?</h4>
    <pre>=IF(OR($C2="",$E2="Yes"),"",TODAY()-DATEVALUE($C2))</pre>
    <p>Recalculates on open, so the number is never stale. Paid invoices go blank rather than
      showing a misleading age.</p>
  </div>
  <div class="st-form">
    <h4>Money finished but never invoiced</h4>
    <pre>=SUMIF(Jobs!$F:$F,"NOT INVOICED",Jobs!$E:$E)</pre>
    <p>The number worth putting on a wall. In the sample rows it is not zero, which is the point.</p>
  </div>

  <div class="st-cta">
    <h2 style="margin-top:0">Already have a spreadsheet full of history?</h2>
    <p>Then the tracker is the wrong end. Run your existing export through the
      <a href="/check/">free file check</a> &mdash; it will tell you what is already stranded in
      there. Or <a href="/check/example/">see a real report first</a> without uploading a thing.</p>
    <p style="margin-bottom:0"><a class="btn" href="/free-demo/">Have us set it up for you, free</a></p>
  </div>
</main>
"""

SCRIPT = r"""
<script>
(function(){
'use strict';
/* All local. No fetch, no XHR, no beacon. The .xlsx is assembled here. */

function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

/* ---- CRC32, needed by the ZIP container ------------------------------- */
var CRC = (function(){
  var t = new Uint32Array(256), c, n, k;
  for(n=0;n<256;n++){ c=n; for(k=0;k<8;k++) c = (c&1) ? (0xEDB88320 ^ (c>>>1)) : (c>>>1); t[n]=c>>>0; }
  return t;
})();
function crc32(bytes){
  var c = 0xFFFFFFFF;
  for(var i=0;i<bytes.length;i++) c = CRC[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

/* ---- minimal ZIP writer, stored (no compression) -----------------------
   Store rather than deflate on purpose: it costs a few KB on a file this
   small and removes an entire class of "Excel says the file is corrupt"
   bugs. Correctness beats bytes here. */
function zip(files){
  var enc = new TextEncoder(), parts = [], central = [], offset = 0;
  function u16(n){ return [n & 255, (n>>>8) & 255]; }
  function u32(n){ return [n & 255, (n>>>8) & 255, (n>>>16) & 255, (n>>>24) & 255]; }

  files.forEach(function(f){
    var name = enc.encode(f.name), data = enc.encode(f.data), crc = crc32(data);
    var local = [].concat([0x50,0x4B,0x03,0x04], u16(20), u16(0), u16(0), u16(0), u16(0),
      u32(crc), u32(data.length), u32(data.length), u16(name.length), u16(0));
    parts.push(new Uint8Array(local), name, data);
    central.push([].concat([0x50,0x4B,0x01,0x02], u16(20), u16(20), u16(0), u16(0), u16(0), u16(0),
      u32(crc), u32(data.length), u32(data.length), u16(name.length),
      u16(0), u16(0), u16(0), u16(0), u32(0), u32(offset), Array.from(name)));
    offset += local.length + name.length + data.length;
  });

  var cd = [];
  central.forEach(function(c){ cd = cd.concat(c); });
  var eocd = [].concat([0x50,0x4B,0x05,0x06], u16(0), u16(0),
    u16(files.length), u16(files.length), u32(cd.length), u32(offset), u16(0));

  var total = offset + cd.length + eocd.length;
  var out = new Uint8Array(total), p = 0;
  parts.forEach(function(b){ out.set(b, p); p += b.length; });
  out.set(new Uint8Array(cd), p); p += cd.length;
  out.set(new Uint8Array(eocd), p);
  return out;
}

/* ---- SpreadsheetML ------------------------------------------------------
   Values are typed deliberately. A number written as an inline string is the
   classic "SUM() skips it and nobody notices" bug -- the exact defect our own
   health check reports -- so it would be indefensible to ship it here. */
function cell(ref, v){
  if(v === null || v === undefined || v === '') return '';
  if(typeof v === 'object' && v.f) return '<c r="' + ref + '"><f>' + esc(v.f) + '</f></c>';
  if(typeof v === 'number') return '<c r="' + ref + '"><v>' + v + '</v></c>';
  return '<c r="' + ref + '" t="inlineStr"><is><t>' + esc(v) + '</t></is></c>';
}
function colName(i){
  var s = '';
  do { s = String.fromCharCode(65 + (i % 26)) + s; i = Math.floor(i/26) - 1; } while(i >= 0);
  return s;
}
function sheetXML(rows){
  var body = rows.map(function(cells, r){
    var xml = cells.map(function(v, c){ return cell(colName(c) + (r+1), v); }).join('');
    return '<row r="' + (r+1) + '">' + xml + '</row>';
  }).join('');
  return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
    '<sheetData>' + body + '</sheetData></worksheet>';
}
function workbook(sheets){
  var ct = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' +
    '<Default Extension="xml" ContentType="application/xml"/>' +
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' +
    sheets.map(function(s,i){ return '<Override PartName="/xl/worksheets/sheet' + (i+1) +
      '.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'; }).join('') +
    '</Types>';
  var rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>' +
    '</Relationships>';
  var wb = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ' +
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' +
    sheets.map(function(s,i){ return '<sheet name="' + esc(s.name) + '" sheetId="' + (i+1) +
      '" r:id="rId' + (i+1) + '"/>'; }).join('') + '</sheets></workbook>';
  var wbRels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
    sheets.map(function(s,i){ return '<Relationship Id="rId' + (i+1) +
      '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet' +
      (i+1) + '.xml"/>'; }).join('') + '</Relationships>';

  var files = [
    {name:'[Content_Types].xml', data:ct},
    {name:'_rels/.rels', data:rels},
    {name:'xl/workbook.xml', data:wb},
    {name:'xl/_rels/workbook.xml.rels', data:wbRels}
  ];
  sheets.forEach(function(s,i){
    files.push({name:'xl/worksheets/sheet' + (i+1) + '.xml', data:sheetXML(s.rows)});
  });
  return zip(files);
}

/* ---- the tracker itself ------------------------------------------------ */
var ROWS = 300;   // formulas pre-filled this far down; plenty for a small book

function buildRows(withSamples){
  var jobs = [['Job No','Date','Customer','Description','Amount','Invoiced?']];
  var samples = [
    ['J-101','2026-06-22','Hargrove Property Grp','Irrigation repair',740],
    ['J-102','2026-06-25','Bell & Sons HOA','Storm cleanup',1280],
    ['J-103','2026-07-01','Coastal Dental','Pressure wash',380]
  ];
  for(var r=1; r<=ROWS; r++){
    var s = withSamples ? samples[r-1] : null;
    jobs.push([ s?s[0]:'', s?s[1]:'', s?s[2]:'', s?s[3]:'', s?s[4]:'',
      {f:'IF($A' + (r+1) + '="","",IF(COUNTIF(Invoices!$B:$B,$A' + (r+1) + ')>0,"Yes","NOT INVOICED"))'} ]);
  }

  var inv = [['Invoice No','Job No','Invoice Date','Amount','Paid','Days Outstanding','Status']];
  var isamp = [
    ['INV-2201','J-101','2026-06-24',740,'Yes'],
    ['INV-2202','J-102','2026-05-28',1280,'No']
  ];
  for(var i=1; i<=ROWS; i++){
    var v = withSamples ? isamp[i-1] : null;
    inv.push([ v?v[0]:'', v?v[1]:'', v?v[2]:'', v?v[3]:'', v?v[4]:'',
      {f:'IF(OR($C' + (i+1) + '="",$E' + (i+1) + '="Yes"),"",TODAY()-DATEVALUE($C' + (i+1) + '))'},
      {f:'IF($C' + (i+1) + '="","",IF($E' + (i+1) + '="Yes","Paid",IF(TODAY()-DATEVALUE($C' + (i+1) +
         ')>60,"OVER 60 DAYS",IF(TODAY()-DATEVALUE($C' + (i+1) + ')>30,"Over 30 days","Current"))))'} ]);
  }

  var dash = [
    ['What this tells you',''],
    ['Money finished but never invoiced', {f:'SUMIF(Jobs!$F:$F,"NOT INVOICED",Jobs!$E:$E)'}],
    ['Jobs finished but never invoiced',  {f:'COUNTIF(Jobs!$F:$F,"NOT INVOICED")'}],
    ['Money invoiced and still unpaid',   {f:'SUMIF(Invoices!$E:$E,"No",Invoices!$D:$D)'}],
    ['Of that, past 60 days',             {f:'SUMIFS(Invoices!$D:$D,Invoices!$E:$E,"No",Invoices!$G:$G,"OVER 60 DAYS")'}],
    ['Duplicate job numbers',             {f:'SUMPRODUCT((Jobs!$A$2:$A$301<>"")*1)-SUMPRODUCT((Jobs!$A$2:$A$301<>"")/COUNTIF(Jobs!$A$2:$A$301,Jobs!$A$2:$A$301&""))'}],
    ['',''],
    ['These update themselves every time you open the file.','']
  ];

  var sheets = [ {name:'Jobs', rows:jobs}, {name:'Invoices', rows:inv}, {name:'Dashboard', rows:dash} ];
  return sheets;
}

var GUIDE = [
  ['How this workbook works',''],
  ['',''],
  ['Jobs > Invoiced?','Looks up each job number in the Invoices sheet. "NOT INVOICED" means you finished work nobody billed.'],
  ['Invoices > Days Outstanding','Todays date minus the invoice date, recalculated every time the file opens. Blank once paid.'],
  ['Invoices > Status','Current, Over 30 days, or OVER 60 DAYS. Past 60 is where collectability starts dropping fast.'],
  ['Dashboard','Adds those columns up. Nothing here is typed by hand, so it cannot drift out of date.'],
  ['',''],
  ['Dates','Type them as 2026-07-14. The formulas read that format directly.'],
  ['Amounts','Type plain numbers, no $ sign. A number stored as text is skipped by SUM without warning.'],
  ['Adding rows','Formulas are filled to row 301. Past that, copy the last row down.'],
  ['',''],
  ['Made by','Automated Workflow - automatedworkflowllc.com'],
  ['Nothing phones home','There are no macros and no links back to us. Change anything you like.']
];

function download(bytes, name){
  var blob = new Blob([bytes], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(function(){ URL.revokeObjectURL(url); }, 1000);
}

document.getElementById('st-build').addEventListener('click', function(){
  var said = document.getElementById('st-said');
  try {
    var sheets = buildRows(document.getElementById('st-samples').checked);
    if(document.getElementById('st-guide').checked) sheets.push({name:'How this works', rows:GUIDE});
    var bytes = workbook(sheets);
    download(bytes, 'job-and-invoice-tracker.xlsx');
    said.textContent = 'Done — job-and-invoice-tracker.xlsx is in your downloads (' +
      Math.round(bytes.length/1024) + ' KB, ' + sheets.length + ' sheets). Open it in Excel, ' +
      'Numbers or Google Sheets.';
  } catch(e){
    said.textContent = 'Could not build the file in this browser (' + e.message +
      '). Tell us and we will email you the same workbook.';
  }
});
})();
</script>
"""

LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Free Job & Invoice Tracker Generator",
  "url": "https://automatedworkflowllc.com/starter/",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Any",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "description": "Generates a working Excel job and invoice tracker in your browser. Unbilled jobs and invoices past 60 days flag themselves. No upload, no signup."
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
