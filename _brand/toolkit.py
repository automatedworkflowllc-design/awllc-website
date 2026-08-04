#!/usr/bin/env python3
"""Shared browser-side primitives for the free tool pages.

Every tool page ships one self-contained HTML file with its analysis inlined --
that is the product promise (nothing uploads, no endpoint exists), so these are
source strings pasted into each page rather than a script tag someone could
point at a CDN.

Sharing them here is about drift, not bytes. By 2026-08-03 five builders each
carried their own `parseCSV`, and the health-check copy had already diverged
from the other four. That divergence was cosmetic -- reflowed lines, identical
behavior -- but it was diverging, and the next one would not necessarily be
cosmetic. A CSV parser that disagrees with itself across five tools is the kind
of bug that shows up as "the health check found 8 rows but the leak finder
found 9" in front of a prospect.

Only genuinely universal primitives belong here. `normName` (legal-suffix
stripping) is specific to matching customer names and stays in the duplicate
finder; a rate table has no LLCs in it.
"""
from __future__ import annotations

import re

# --- HTML escaping -----------------------------------------------------------
# Every tool renders user cell values into its report. This is the only thing
# standing between a spreadsheet containing "<script>" and a self-XSS demo.
ESC_JS = """
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
"""

# --- CSV parsing -------------------------------------------------------------
# Handles quoted fields, escaped quotes, CRLF, and tab-delimited files (people
# paste from Excel more often than they export). Delimiter is sniffed by
# counting, because a file with commas inside quoted addresses is normal.
PARSE_CSV_JS = """
function parseCSV(text){
  var rows=[], row=[], cell='', q=false, i=0, c;
  var delim = (text.split('\\t').length > text.split(',').length) ? '\\t' : ',';
  while(i < text.length){
    c = text[i];
    if(q){ if(c === '"'){ if(text[i+1] === '"'){ cell+='"'; i++; } else q=false; } else cell += c; }
    else if(c === '"') q = true;
    else if(c === delim){ row.push(cell); cell=''; }
    else if(c === '\\n' || c === '\\r'){
      if(c === '\\r' && text[i+1] === '\\n') i++;
      row.push(cell); cell='';
      if(row.length > 1 || row[0] !== '') rows.push(row);
      row=[];
    } else cell += c;
    i++;
  }
  if(cell !== '' || row.length){ row.push(cell); rows.push(row); }
  return rows;
}
"""

# --- Money -------------------------------------------------------------------
# Returns null rather than NaN or 0 for unparseable input, so callers must
# decide what a missing amount means instead of silently summing it as zero.
# Accounting parentheses are negatives: (1,250.00) is -1250.
MONEY_JS = """
function money(v){
  var m = String(v).replace(/[$,\\s]/g,'').replace(/^\\((.*)\\)$/, '-$1');
  var n = parseFloat(m);
  return isFinite(n) ? n : null;
}
"""

# --- Dates -------------------------------------------------------------------
# ISO and US only, on purpose. Guessing between 03/04 as March 4th and April 3rd
# is how a tool quietly reports the wrong aging; unrecognized formats return
# null and the caller says so out loud.
PARSE_DATE_JS = """
function parseDate(v){
  v = String(v).trim();
  var m = v.match(/^(\\d{4})-(\\d{1,2})-(\\d{1,2})/);
  if(m) return new Date(+m[1], +m[2]-1, +m[3]);
  m = v.match(/^(\\d{1,2})\\/(\\d{1,2})\\/(\\d{2,4})$/);
  if(m) return new Date(m[3].length===2 ? 2000+ +m[3] : +m[3], +m[1]-1, +m[2]);
  return null;
}
"""

# --- Free-text normalization -------------------------------------------------
# For grouping descriptions that are "the same thing typed twice": case,
# punctuation and spacing only. Deliberately dumber than name matching -- it
# never merges two strings that differ by an actual word.
NORM_TEXT_JS = """
function normText(s){
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, ' ').replace(/\\s+/g, ' ').trim();
}
"""

CORE_JS = ESC_JS + PARSE_CSV_JS + MONEY_JS + PARSE_DATE_JS + NORM_TEXT_JS

# --- XLSX intake, no library ---------------------------------------------
# "Save it as CSV first" is where prospects quietly leave: small businesses
# have .xlsx files. Every other tool solves this with SheetJS off a CDN, which
# would break the one promise every tool page makes -- no request ever leaves
# the page. So this is a hand-rolled reader, the mirror image of /starter/'s
# ZIP writer: EOCD scan -> central directory -> DecompressionStream
# ('deflate-raw', native in every modern browser) -> worksheet XML.
#
# Date discipline: Excel stores dates as serial numbers, distinguishable from
# plain numbers ONLY by cell style. Serials convert to ISO dates strictly when
# the style's number format is a date format (builtin ids 14-22/45-47 or a
# custom code containing y/m/d/h outside brackets and quotes). Anything else
# stays a number -- converting on a guess would INVENT dates, and every
# downstream check trusts dates. Fails loud: a workbook this cannot parse
# raises, and the caller shows "save as CSV" -- never a silently empty table.
XLSX_JS = r"""
function xlsxToRows(buf){
  var u8 = new Uint8Array(buf), dv = new DataView(buf);
  function findEOCD(){
    for(var i = u8.length - 22; i >= Math.max(0, u8.length - 65558); i--)
      if(dv.getUint32(i, true) === 0x06054b50) return i;
    throw new Error('not a zip');
  }
  var eocd = findEOCD();
  var count = dv.getUint16(eocd + 10, true), cdOff = dv.getUint32(eocd + 16, true);
  var entries = {}, p = cdOff;
  for(var e = 0; e < count; e++){
    if(dv.getUint32(p, true) !== 0x02014b50) throw new Error('bad central dir');
    var method = dv.getUint16(p + 10, true), csize = dv.getUint32(p + 20, true);
    var nlen = dv.getUint16(p + 28, true), xlen = dv.getUint16(p + 30, true),
        clen = dv.getUint16(p + 32, true), lho = dv.getUint32(p + 42, true);
    var name = new TextDecoder().decode(u8.subarray(p + 46, p + 46 + nlen));
    entries[name] = {method: method, csize: csize, lho: lho};
    p += 46 + nlen + xlen + clen;
  }
  function inflate(ent){
    var q = ent.lho;
    if(dv.getUint32(q, true) !== 0x04034b50) throw new Error('bad local header');
    var nl = dv.getUint16(q + 26, true), xl = dv.getUint16(q + 28, true);
    var data = u8.subarray(q + 30 + nl + xl, q + 30 + nl + xl + ent.csize);
    if(ent.method === 0) return Promise.resolve(new TextDecoder().decode(data));
    if(ent.method !== 8) throw new Error('unsupported compression ' + ent.method);
    var ds = new DecompressionStream('deflate-raw');
    return new Response(new Blob([data]).stream().pipeThrough(ds)).text();
  }
  function unesc(s){
    return s.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"')
            .replace(/&apos;/g,"'").replace(/&#x([0-9a-fA-F]+);/g,
              function(_, h){ return String.fromCodePoint(parseInt(h, 16)); })
            .replace(/&#(\d+);/g, function(_, d){ return String.fromCodePoint(+d); })
            .replace(/&amp;/g,'&');
  }
  function texts(xml){   // concat all <t> runs inside one <si>/<is> (rich text)
    var out = '', m, re = /<t(?:\s[^>]*)?>([\s\S]*?)<\/t>/g;
    while((m = re.exec(xml))) out += unesc(m[1]);
    return out;
  }
  var BUILTIN_DATE = {14:1,15:1,16:1,17:1,18:1,19:1,20:1,21:1,22:1,45:1,46:1,47:1};
  function isDateCode(code){
    var bare = code.replace(/\[[^\]]*\]/g, '').replace(/"[^"]*"/g, '');
    return /[ymdhs]/i.test(bare) && !/General/i.test(bare);
  }
  function serialToISO(n){
    // Excel 1900 epoch (day 1 = 1900-01-01, with the fictitious Feb 29 1900
    // baked in, hence the -25569 against the Unix epoch working for n >= 61;
    // sub-61 serials are Jan/Feb 1900 -- not business data, left numeric).
    if(n < 61 || n > 2958465) return null;
    var d = new Date(Math.round((n - 25569) * 86400000));
    return d.toISOString().slice(0, 10);
  }
  var wanted = ['xl/workbook.xml', 'xl/_rels/workbook.xml.rels',
                'xl/sharedStrings.xml', 'xl/styles.xml'];
  return Promise.all(wanted.map(function(n){
    return entries[n] ? inflate(entries[n]) : Promise.resolve('');
  })).then(function(parts){
    var wb = parts[0], rels = parts[1], sstXml = parts[2], styles = parts[3];
    /* Every sheet, not just the first: real workbooks often lead with a cover
       or notes tab, and "first sheet" reads the wrong one while looking like
       it worked. All sheets (capped at 8) are parsed and the busiest wins --
       most rows containing data, ties to workbook order. The choice is
       attached to the result so callers can SAY which sheet was read. */
    var sheets = [], sm, shRe = /<sheet\b[^>]*>/g;
    while((sm = shRe.exec(wb))){
      var tag = sm[0];
      var nm = /name="([^"]*)"/.exec(tag);
      var rid = /r:id="(rId\d+)"/.exec(tag) || /\bid="(rId\d+)"/.exec(tag);
      var tgt = null;
      if(rid && rels){
        var rel = new RegExp('Id="' + rid[1] + '"[^>]*Target="([^"]+)"').exec(rels) ||
                  new RegExp('Target="([^"]+)"[^>]*Id="' + rid[1] + '"').exec(rels);
        if(rel) tgt = 'xl/' + rel[1].replace(/^\//, '').replace(/^xl\//, '');
      }
      if(!tgt) tgt = 'xl/worksheets/sheet' + (sheets.length + 1) + '.xml';
      if(entries[tgt]) sheets.push({name: nm ? unesc(nm[1]) : ('Sheet' + (sheets.length + 1)), target: tgt});
    }
    if(!sheets.length && entries['xl/worksheets/sheet1.xml'])
      sheets.push({name: 'Sheet1', target: 'xl/worksheets/sheet1.xml'});
    if(!sheets.length) throw new Error('no worksheet found');

    var sst = [], m, siRe = /<si>([\s\S]*?)<\/si>/g;
    while((m = siRe.exec(sstXml))) sst.push(texts(m[1]));

    var custom = {}, fmRe = /<numFmt\s[^>]*numFmtId="(\d+)"[^>]*formatCode="([^"]*)"/g;
    while((m = fmRe.exec(styles))) custom[+m[1]] = unesc(m[2]);
    var dateStyle = [];
    var xfsBlock = /<cellXfs[^>]*>([\s\S]*?)<\/cellXfs>/.exec(styles);
    if(xfsBlock){
      var xfRe = /<xf\b[^>]*numFmtId="(\d+)"[^>]*/g, i = 0;
      while((m = xfRe.exec(xfsBlock[1]))){
        var id = +m[1];
        dateStyle[i++] = !!(BUILTIN_DATE[id] || (custom[id] && isDateCode(custom[id])));
      }
    }
    function parseWS(ws){
      var rows = [], occupied = 0, rowRe = /<row\b[^>]*>([\s\S]*?)<\/row>/g, rm;
      while((rm = rowRe.exec(ws))){
        var cells = [], cRe = /<c\b([^>]*)(?:\/>|>([\s\S]*?)<\/c>)/g, cm;
        while((cm = cRe.exec(rm[1]))){
          var attrs = cm[1], body = cm[2] || '';
          var ref = /r="([A-Z]+)\d+"/.exec(attrs);
          var col = 0;
          if(ref) for(var k = 0; k < ref[1].length; k++) col = col * 26 + (ref[1].charCodeAt(k) - 64);
          else col = cells.length + 1;
          var t = (/t="(\w+)"/.exec(attrs) || [])[1] || 'n';
          var sIdx = (/s="(\d+)"/.exec(attrs) || [])[1];
          var v = /<v>([\s\S]*?)<\/v>/.exec(body);
          var val = '';
          if(t === 'inlineStr') val = texts(body);
          else if(!v) val = '';
          else if(t === 's') val = sst[+v[1]] !== undefined ? sst[+v[1]] : '';
          else if(t === 'str' || t === 'e') val = unesc(v[1]);
          else if(t === 'b') val = v[1] === '1' ? 'TRUE' : 'FALSE';
          else {
            val = v[1];
            if(sIdx !== undefined && dateStyle[+sIdx]){
              var iso = serialToISO(parseFloat(v[1]));
              if(iso) val = iso;
            } else if(/^-?\d*\.\d{10,}$/.test(val)){
              // Excel stores 99.9 as 99.90000000000001 in the XML; showing
              // that dust in a money column reads as broken. 15 significant
              // digits is what Excel itself displays.
              var n = parseFloat(val);
              if(isFinite(n)) val = String(parseFloat(n.toPrecision(15)));
            }
          }
          while(cells.length < col - 1) cells.push('');
          cells[col - 1] = val;
        }
        rows.push(cells);
        /* A formula cell IS data even with no cached value -- Excel computes
           it on open. Without this, a template like /starter/'s tracker (300
           formula rows, 3 typed samples) scores below its own 13-row prose
           guide sheet, and the "busiest" pick analyzes the instructions. */
        var hasValue = false;
        for(var ci = 0; ci < cells.length; ci++) if(cells[ci] !== ''){ hasValue = true; break; }
        if(hasValue || /<f[ >]/.test(rm[1])) occupied++;
      }
      rows.occupied = occupied;
      return rows;
    }

    return Promise.all(sheets.slice(0, 8).map(function(sh){
      return inflate(entries[sh.target]).then(parseWS).then(function(rows){
        return {name: sh.name, rows: rows, score: rows.occupied};
      }, function(){ return {name: sh.name, rows: [], score: -1}; });
    })).then(function(parsed){
      var best = parsed[0];
      for(var i = 1; i < parsed.length; i++)
        if(parsed[i].score > best.score) best = parsed[i];   // strict >: ties keep workbook order
      if(!best || best.score < 1) throw new Error('no sheet with data');
      var rows = best.rows;
      rows.sheetName = best.name;
      rows.sheetCount = sheets.length;
      return rows;
    });
  });
}
function rowsToCSV(rows){
  return rows.map(function(r){
    return r.map(function(v){
      v = String(v === undefined || v === null ? '' : v);
      return /[",\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
    }).join(',');
  }).join('\n');
}
function readAny(f, done){
  /* One intake for every tool: .xlsx parsed locally, everything else read as
     text. Parse failures alert per-file and never call done() -- a silently
     empty table is the lie these tools exist to end. */
  var reader = new FileReader();
  if(/\.(xlsx|xlsm)$/i.test(f.name)){
    reader.onload = function(){
      xlsxToRows(reader.result).then(function(rows){ done(rowsToCSV(rows)); })
        .catch(function(err){
          alert('Could not read ' + f.name + ' as an Excel workbook (' + err.message +
                '). Save it as CSV and try again.');
        });
    };
    reader.readAsArrayBuffer(f);
  } else {
    reader.onload = function(){ done(String(reader.result)); };
    reader.readAsText(f);
  }
}
"""


def with_xlsx(script_js):
    """Inject the xlsx reader after the 'use strict' prologue. Raises if the
    anchor is missing or the functions don't land -- a builder that silently
    skipped the injection would ship a page whose intake calls readAny into a
    void."""
    if _ANCHOR not in script_js:
        raise SystemExit("with_xlsx: no \"'use strict';\" anchor")
    out = script_js.replace(_ANCHOR, _ANCHOR + XLSX_JS, 1)
    for fn in ('function xlsxToRows', 'function rowsToCSV', 'function readAny'):
        if out.count(fn) != 1:
            raise SystemExit('with_xlsx: %s not injected exactly once' % fn)
    return out

# --- migration -----------------------------------------------------------
# Deliberately narrow: only `esc` and `parseCSV` are swapped. `money`,
# `parseDate` and `normText` are NOT, because several pages define their own
# variants -- money-leak's `parseDate` understands its own column conventions --
# and a blanket injection would silently override a page-specific version with
# a generic one. That is the same class of bug this module exists to prevent,
# so the migration stays as small as the duplication actually is.
_ESC_DEF = re.compile(r'^function esc\(s\)\{.*?\}\n', re.M)
_CSV_DEF = re.compile(r'^function parseCSV\(text\)\{.*?^\}\n', re.M | re.S)
_ANCHOR = "'use strict';\n"


def with_core(script_js):
    """Replace a page's hand-copied esc/parseCSV with the shared ones.

    Raises rather than returning something subtly wrong: a builder that
    silently skipped the swap would keep shipping its own drifting copy while
    appearing migrated, which is exactly the failure this is meant to end.
    """
    out, n_esc = _ESC_DEF.subn('', script_js)
    out, n_csv = _CSV_DEF.subn('', out)
    if n_esc != 1 or n_csv != 1:
        raise SystemExit(
            'with_core: expected exactly one esc and one parseCSV to replace, '
            'found %d and %d -- the definitions moved; fix before shipping' % (n_esc, n_csv))
    if _ANCHOR not in out:
        raise SystemExit("with_core: no \"'use strict';\" anchor to insert after")
    out = out.replace(_ANCHOR, _ANCHOR + ESC_JS + PARSE_CSV_JS, 1)
    for name, count in (('function esc(', out.count('function esc(')),
                        ('function parseCSV(', out.count('function parseCSV('))):
        if count != 1:
            raise SystemExit('with_core: %s appears %d times after merge, want 1' % (name, count))
    return out


__all__ = ['CORE_JS', 'ESC_JS', 'PARSE_CSV_JS', 'MONEY_JS', 'PARSE_DATE_JS',
           'NORM_TEXT_JS', 'with_core']
