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
