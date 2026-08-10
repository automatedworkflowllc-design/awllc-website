#!/usr/bin/env python3
"""Build /shift-coverage-check/ -- the fourth free in-browser tool.

Aimed at businesses that run on a roster rather than a ledger: senior living,
clinics, restaurants, facilities, security. Their expensive mistakes are not
typos, they are STRUCTURAL -- a shift nobody covers, a person quietly at 52
hours, a role only one human on the payroll can do.

Every finding is arithmetic on the roster they already export. Nothing is
predicted or scored, and nothing uploads -- staff schedules are personnel data.

Deliberately NOT a scheduler: it never proposes who should work when. Telling a
manager how to staff their floor from a CSV is the overreach that makes these
tools untrustworthy.
"""
from __future__ import annotations

import pathlib
import re

from toolkit import with_core, with_xlsx, PLAIN_CSS, plain_english, with_plain

PLAIN = plain_english(
    'Reads your staff schedule and points out the four problems that cost money: a shift nobody is covering, someone drifting into overtime, a job only one person can do, and shifts too close together to be safe.',
    'These are normally noticed on Friday &mdash; <b>after</b> the overtime is already owed or the shift already went uncovered. This finds them while you can still move someone.',
    'Your schedule export: who works, what role, which day.',
    'About ten seconds. Nothing about your staff is uploaded anywhere.')


ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'shift-coverage-check'

TITLE = 'Free Shift Coverage Check — Find Gaps In Your Roster'
DESC = ('Drop a schedule export and see the gaps: uncovered shifts, people heading into '
        'overtime, roles only one person can fill. Nothing uploads.')
CANON = 'https://automatedworkflowllc.com/shift-coverage-check/'

PAGE_CSS = """
/* ---- shift coverage ---- */
.sc-drop{border:2px dashed var(--line-strong);border-radius:16px;background:var(--card);
padding:2.6rem 1.4rem;text-align:center;cursor:pointer}
.sc-drop.is-over{border-color:var(--accent,var(--green,#1E7A47));background:var(--well)}
.sc-drop:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.sc-drop strong{display:block;font-size:1.05rem;margin-bottom:.35rem}
.sc-drop span{color:var(--ink-soft);font-size:.92rem}
.sc-actions{display:flex;gap:.7rem;justify-content:center;flex-wrap:wrap;margin-top:1rem}
.sc-note{margin-top:1rem;font-size:.85rem;color:var(--ink-soft);text-align:center}
.sc-note code{font-family:var(--mono);font-size:.8rem}
#sc-report{margin-top:2rem;display:none}
.sc-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem;margin:0 0 1.4rem}
@media(max-width:700px){.sc-kpis{grid-template-columns:1fr 1fr}}
.sc-kpi{border:1px solid var(--line);border-radius:.7rem;padding:.8rem .9rem;background:var(--card)}
.sc-kpi b{display:block;font-size:1.6rem;font-family:var(--mono);line-height:1.1}
.sc-kpi.k-bad b{color:#B4452C}
.sc-kpi span{font-size:.72rem;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.05em}
.sc-sec{margin:1.5rem 0 .5rem;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-soft)}
.sc-card{background:var(--card);border:1px solid var(--line);border-left:4px solid #B4452C;
border-radius:.6rem;padding:.85rem 1.05rem;margin:0 0 .55rem}
.sc-card.warn{border-left-color:#A8842B}
.sc-card h4{margin:0 0 .2rem;font-size:.96rem}
.sc-card p{margin:0;font-size:.89rem;color:var(--ink-soft)}
.sc-clean{border-left:4px solid var(--accent,var(--green,#1E7A47));background:var(--card);border-radius:.6rem;
padding:1rem 1.2rem;color:var(--ink-soft)}
.sc-cta{margin-top:1.6rem;padding:1.3rem;border:1px solid var(--line);border-radius:12px;background:var(--bg-soft)}
.sc-cta p{margin:.2rem 0 .9rem;color:var(--ink-soft)}
.sc-map{overflow-x:auto;margin:.4rem 0 1.2rem}
.sc-map table{border-collapse:collapse;font-size:.8rem;font-family:var(--mono)}
.sc-map th{padding:.25rem .45rem;color:var(--ink-soft);font-weight:normal;text-align:center;
border-bottom:1px solid var(--line-strong);white-space:nowrap}
.sc-map td{padding:.25rem .45rem;text-align:center;border-bottom:1px solid var(--line-soft)}
.sc-map td.role{text-align:left;color:var(--ink-soft);white-space:nowrap;padding-right:.9rem}
.sc-map .ok{color:var(--accent,var(--green,#1E7A47))}
.sc-map .gap{color:#B4452C;font-weight:bold}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">Shift Coverage Check</h1>
  <p style="color:var(--ink-soft);max-width:41rem">
    For anyone who runs on a roster &mdash; senior living, clinics, restaurants, facilities,
    security. Drop your schedule export and see the four things that cost real money and nobody
    catches until Friday: <strong>a day a role isn't covered</strong>, someone quietly heading
    into <strong>overtime</strong>, a role <strong>only one person can fill</strong>, and
    <strong>turnarounds too short to be safe</strong>.
  </p>
  <p style="max-width:41rem"><strong>Nothing uploads.</strong>
    <span style="color:var(--ink-soft)">Staff schedules are personnel data. The analysis runs
    entirely in your browser &mdash; there is no server to send it to. Check the network tab:
    zero requests after load.</span></p>

  <div class="sc-drop" id="sc-drop" role="button" tabindex="0"
       aria-label="Choose a schedule CSV to analyze locally">
    <strong>Drop your schedule .csv here</strong>
    <span>date, employee, role, start, end &middot; stays on your machine</span>
    <input type="file" id="sc-file" accept=".csv,.tsv,.txt,.xlsx,.xlsm" style="display:none">
  </div>
  <div class="sc-actions">
    <button class="btn" id="sc-sample" type="button">Try the sample roster</button>
  </div>
  <p class="sc-note">Works with most exports &mdash; it finds the date, name, role and time
    columns itself. <strong>Excel .xlsx files work directly</strong> (the busiest sheet is analyzed).</p>

  <section id="sc-report" aria-live="polite">
    <h2 id="sc-title" style="margin-bottom:.9rem"></h2>
    <div class="sc-kpis" id="sc-kpis"></div>
    <div id="sc-body"></div>
    <div class="sc-cta">
      <strong>Want this every Monday, automatically?</strong>
      <p>A recurring version reads next week's roster the moment it's published and flags these
      before they become someone's Saturday problem &mdash; that's
      <a href="/automated-reports/">Report Autopilot</a>. Or start with a
      <a href="/free-demo/?from=shift-coverage">free 1-day demo on your real roster</a>, keep it either way.</p>
      <a class="btn" href="/free-demo/?from=shift-coverage">Run it on your real schedule — free</a>
      <p style="margin:.9rem 0 0;font-size:.85rem">Also free, same rule &mdash; nothing uploads:
      <a href="/spreadsheet-health-check/">Spreadsheet Health Check</a>,
      <a href="/money-leak-finder/">Money Leak Finder</a>,
      <a href="/duplicate-customer-finder/">Duplicate Customer Finder</a>.</p>
    </div>
  </section>
</main>
"""

SCRIPT = r"""
<script>
(function(){
'use strict';
/* All local. No fetch, no XHR, no beacon. */

var OT_HOURS = 40;          // weekly hours above which overtime starts
var SHORT_TURNAROUND = 10;  // hours between shifts below which fatigue risk is real
var MAX_STREAK = 6;         // consecutive days worked before a day off is due

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

function parseDate(v){
  v = String(v).trim();
  var m = v.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if(m) return new Date(+m[1], +m[2]-1, +m[3]);
  m = v.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/);
  if(m) return new Date(m[3].length===2 ? 2000 + (+m[3]) : +m[3], +m[1]-1, +m[2]);
  return null;
}
/* minutes past midnight, or null. Handles 7:00, 07:00, 7:00 AM, 7a, 1900. */
function parseTime(v){
  v = String(v).trim().toLowerCase().replace(/\s+/g, '');
  if(!v) return null;
  var m = v.match(/^(\d{1,2}):(\d{2})(a|p|am|pm)?$/);
  if(m){
    var h = +m[1], mi = +m[2];
    if(m[3] && m[3].charAt(0) === 'p' && h < 12) h += 12;
    if(m[3] && m[3].charAt(0) === 'a' && h === 12) h = 0;
    return h*60 + mi;
  }
  m = v.match(/^(\d{1,2})(a|p|am|pm)$/);
  if(m){ var hh = +m[1]; if(m[2].charAt(0)==='p' && hh<12) hh+=12; if(m[2].charAt(0)==='a' && hh===12) hh=0; return hh*60; }
  m = v.match(/^(\d{4})$/);
  if(m) return (+m[1].slice(0,2))*60 + (+m[1].slice(2));
  return null;
}

function distinctCount(list){
  var seen = Object.create(null), n = 0;
  list.forEach(function(v){ if(v && !seen[v]){ seen[v]=1; n++; } });
  return n;
}

var NAMED = {
  date:   /date|day\b|shift.?date|work.?date/i,
  person: /employee|name|staff|person|worker|associate|caregiver|tech|nurse|agent/i,
  role:   /role|position|title|job|dept|department|unit|skill|classification|area/i,
  start:  /start|time.?in|\bin\b|from|begin/i,
  end:    /end|time.?out|\bout\b|\bto\b|finish/i
};

function scoreCol(header, values, kind){
  var present = values.filter(Boolean);
  if(!present.length) return -1;
  var score = NAMED[kind].test(header) ? 3 : 0;
  if(kind === 'date') score += present.filter(function(v){ return parseDate(v); }).length / present.length;
  else if(kind === 'start' || kind === 'end') score += present.filter(function(v){ return parseTime(v) !== null; }).length / present.length;
  else {
    // people and roles repeat across rows; roles repeat harder than people
    var d = distinctCount(present);
    if(d >= present.length) score += 0.1;
    else if(kind === 'role') score += (d <= present.length/3) ? 1 : 0.4;
    else score += 0.7;
  }
  return score;
}

function detect(header, body){
  var picks = {}, taken = {};
  ['date','start','end','person','role'].forEach(function(kind){
    var best = -1, bestScore = 1.0;   // require a real signal, not a coin flip
    header.forEach(function(h, i){
      if(taken[i]) return;
      var vals = body.map(function(r){ return (r[i]===undefined?'':String(r[i])).trim(); });
      var s = scoreCol(h, vals, kind);
      if(s > bestScore){ bestScore = s; best = i; }
    });
    if(best >= 0){ picks[kind] = best; taken[best] = 1; }
  });
  return picks;
}

function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function iso(d){ return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); }
function weekKey(d){ var t = new Date(d.getTime()); t.setDate(t.getDate() - t.getDay()); return iso(t); }
function fmtH(h){ return (Math.round(h*10)/10) + 'h'; }

function analyze(header, body, picks){
  if(picks.date === undefined) return { error: 'No date column found. The file needs one row per shift with a date.' };

  var shifts = [];
  body.forEach(function(r){
    var d = parseDate(r[picks.date]);
    if(!d) return;
    var s = picks.start !== undefined ? parseTime(r[picks.start]) : null;
    var e = picks.end   !== undefined ? parseTime(r[picks.end])   : null;
    var hours = null;
    if(s !== null && e !== null){
      var span = e - s;
      if(span <= 0) span += 24*60;          // overnight shift crosses midnight
      hours = span / 60;
    }
    shifts.push({
      date: d, day: iso(d),
      person: picks.person !== undefined ? String(r[picks.person]||'').trim() : '',
      role:   picks.role   !== undefined ? String(r[picks.role]||'').trim()   : '',
      start: s, end: e, hours: hours
    });
  });
  if(!shifts.length) return { error: 'No dated shift rows found in that file.' };
  shifts.sort(function(a,b){ return a.date - b.date || (a.start||0) - (b.start||0); });

  var out = { shifts: shifts, ot: [], solo: [], turn: [], streak: [], gaps: [], unassigned: [], days: [], roles: [] };

  // ---- overtime: hours per person per ISO week
  if(picks.person !== undefined && shifts.some(function(s){ return s.hours !== null; })){
    var byWeek = Object.create(null);
    shifts.forEach(function(s){
      if(!s.person || s.hours === null) return;
      var k = s.person + '||' + weekKey(s.date);
      byWeek[k] = (byWeek[k] || 0) + s.hours;
    });
    Object.keys(byWeek).forEach(function(k){
      if(byWeek[k] > OT_HOURS){
        var p = k.split('||');
        out.ot.push({ person: p[0], week: p[1], hours: byWeek[k] });
      }
    });
    out.ot.sort(function(a,b){ return b.hours - a.hours; });
  }

  // ---- single point of failure: a role only one person ever covers
  if(picks.role !== undefined && picks.person !== undefined){
    var peopleByRole = Object.create(null), shiftsByRole = Object.create(null);
    shifts.forEach(function(s){
      if(!s.role || !s.person) return;
      (peopleByRole[s.role] = peopleByRole[s.role] || Object.create(null))[s.person] = 1;
      shiftsByRole[s.role] = (shiftsByRole[s.role] || 0) + 1;
    });
    Object.keys(peopleByRole).forEach(function(role){
      var who = Object.keys(peopleByRole[role]);
      if(who.length === 1 && shiftsByRole[role] >= 3){
        out.solo.push({ role: role, person: who[0], shifts: shiftsByRole[role] });
      }
    });
    out.solo.sort(function(a,b){ return b.shifts - a.shifts; });
  }

  // ---- short turnaround + consecutive-day streaks, per person
  if(picks.person !== undefined){
    var byPerson = Object.create(null);
    shifts.forEach(function(s){ if(s.person) (byPerson[s.person] = byPerson[s.person] || []).push(s); });
    Object.keys(byPerson).forEach(function(person){
      var list = byPerson[person];
      for(var i=1;i<list.length;i++){
        var prev = list[i-1], cur = list[i];
        if(prev.end === null || cur.start === null) continue;
        var prevEnd = prev.date.getTime() + prev.end*60000;
        if(prev.end <= (prev.start === null ? 0 : prev.start)) prevEnd += 24*3600*1000; // overnight
        var curStart = cur.date.getTime() + cur.start*60000;
        var gapH = (curStart - prevEnd) / 3600000;
        if(gapH >= 0 && gapH < SHORT_TURNAROUND){
          out.turn.push({ person: person, from: prev.day, to: cur.day, hours: gapH });
        }
      }
      // streaks of consecutive calendar days
      var days = [];
      list.forEach(function(s){ if(days[days.length-1] !== s.day) days.push(s.day); });
      var run = 1, runStart = days[0];
      for(var j=1;j<days.length;j++){
        var a = new Date(days[j-1]), b = new Date(days[j]);
        if((b - a) === 86400000){ run++; }
        else { if(run > MAX_STREAK) out.streak.push({ person: person, days: run, from: runStart, to: days[j-1] }); run = 1; runStart = days[j]; }
      }
      if(run > MAX_STREAK) out.streak.push({ person: person, days: run, from: runStart, to: days[days.length-1] });
    });
    out.turn.sort(function(a,b){ return a.hours - b.hours; });
    out.streak.sort(function(a,b){ return b.days - a.days; });
  }

  // ---- coverage: a role staffed on most days but missing on some
  if(picks.role !== undefined){
    var dayset = Object.create(null), roleset = Object.create(null), filled = Object.create(null);
    /* A row with a role but NOBODY NAMED ON IT is not coverage -- it is the
       most literal possible gap, and it used to count as filled. On a roster
       with three unassigned shifts the tool printed "No gaps found. Every
       normally-staffed role is covered every day", which is a false CLEAN in
       the direction that gets someone's Saturday ruined. Found 2026-08-09 by
       running the tool on a roster built with known holes.
       Only counted when the file HAS a person column: with no such column,
       every row would look unassigned and the tool would cry wolf on a file it
       simply cannot judge. */
    var knowsPeople = picks.person !== undefined;
    shifts.forEach(function(s){
      dayset[s.day] = 1;
      if(!s.role) return;
      roleset[s.role] = 1;
      if(knowsPeople && !s.person){ out.unassigned.push({ role: s.role, day: s.day }); return; }
      filled[s.role + '||' + s.day] = (filled[s.role + '||' + s.day] || 0) + 1;
    });
    var days = Object.keys(dayset).sort(), roles = Object.keys(roleset).sort();
    out.days = days; out.roles = roles; out.filled = filled;
    roles.forEach(function(role){
      var covered = days.filter(function(d){ return filled[role + '||' + d]; }).length;
      // Only call it a gap if the role is normally staffed -- a role that runs
      // 2 days a week is a schedule, not a hole.
      if(covered >= days.length * 0.6 && covered < days.length){
        days.forEach(function(d){
          if(!filled[role + '||' + d]) out.gaps.push({ role: role, day: d });
        });
      }
    });
  }

  return out;
}

function render(name, res, picks, header){
  var rep = document.getElementById('sc-report');
  if(res.error){
    document.getElementById('sc-title').textContent = 'Could not read ' + name;
    document.getElementById('sc-kpis').innerHTML = '';
    document.getElementById('sc-body').innerHTML = '<p style="color:var(--ink-soft)">' + esc(res.error) + '</p>';
    rep.style.display = 'block'; return;
  }
  var mapped = ['date','person','role','start','end']
    .filter(function(k){ return picks[k] !== undefined; })
    .map(function(k){ return k + ' → "' + header[picks[k]] + '"'; }).join(' · ');

  document.getElementById('sc-title').textContent =
    'Coverage report: ' + name + ' — ' + res.shifts.length + ' shifts, ' + res.days.length + ' days';

  document.getElementById('sc-kpis').innerHTML =
    '<div class="sc-kpi' + (res.gaps.length?' k-bad':'') + '"><b>' + res.gaps.length + '</b><span>coverage gaps</span></div>' +
    '<div class="sc-kpi' + (res.ot.length?' k-bad':'') + '"><b>' + res.ot.length + '</b><span>overtime weeks</span></div>' +
    '<div class="sc-kpi' + (res.solo.length?' k-bad':'') + '"><b>' + res.solo.length + '</b><span>one-deep roles</span></div>' +
    '<div class="sc-kpi' + (res.turn.length?' k-bad':'') + '"><b>' + (res.turn.length + res.streak.length) + '</b><span>fatigue flags</span></div>';

  var h = '<p style="font-size:.83rem;color:var(--ink-soft)">Columns read: ' + esc(mapped) + '</p>';
  /* unassigned MUST be in this test -- otherwise a roster whose only problem is
     three empty slots still prints the green "no gaps found" banner. */
  var any = res.gaps.length || res.ot.length || res.solo.length || res.turn.length ||
            res.streak.length || (res.unassigned && res.unassigned.length);

  if(res.roles.length && res.days.length && res.days.length <= 21){
    h += '<div class="sc-sec">Coverage map</div><div class="sc-map"><table><tr><th></th>' +
      res.days.map(function(d){ return '<th>' + d.slice(5) + '</th>'; }).join('') + '</tr>';
    res.roles.forEach(function(role){
      h += '<tr><td class="role">' + esc(role) + '</td>' + res.days.map(function(d){
        var n = res.filled[role + '||' + d];
        return n ? '<td class="ok">' + n + '</td>' : '<td class="gap">·</td>';
      }).join('') + '</tr>';
    });
    h += '</table></div>';
  }

  if(res.gaps.length){
    h += '<div class="sc-sec">Coverage gaps</div>';
    var byRole = Object.create(null);
    res.gaps.forEach(function(g){ (byRole[g.role] = byRole[g.role] || []).push(g.day); });
    Object.keys(byRole).forEach(function(role){
      h += '<div class="sc-card"><h4>' + esc(role) + ' — ' + byRole[role].length + ' day' +
        (byRole[role].length===1?'':'s') + ' with nobody scheduled</h4><p>' +
        esc(byRole[role].join(', ')) + '. This role is staffed on every other day in the file.</p></div>';
    });
  }
  if(res.unassigned && res.unassigned.length){
    /* Reported separately from a coverage gap on purpose: "this role has no
       shift that day" and "this shift exists and nobody is on it" are different
       problems with different fixes, and collapsing them would hide which one
       you have. */
    var byU = Object.create(null);
    res.unassigned.forEach(function(u){ (byU[u.role] = byU[u.role] || []).push(u.day); });
    h += '<div class="sc-sec">Shifts with nobody on them</div>';
    Object.keys(byU).sort().forEach(function(role){
      var ds = byU[role];
      h += '<div class="sc-card"><h4>' + esc(role) + ' — ' + ds.length + ' shift' +
        (ds.length===1?'':'s') + ' with no name against ' + (ds.length===1?'it':'them') + '</h4><p>' +
        esc(ds.join(', ')) + '. The row is on the roster, the slot is empty. This is not the same ' +
        'as the role being unscheduled &mdash; somebody planned the shift and nobody was assigned.</p></div>';
    });
  }
  if(res.ot.length){
    h += '<div class="sc-sec">Overtime</div>';
    res.ot.forEach(function(o){
      h += '<div class="sc-card' + (o.hours >= 48 ? '' : ' warn') + '"><h4>' + esc(o.person) + ' — ' +
        fmtH(o.hours) + ' in the week of ' + o.week + '</h4><p>' + fmtH(o.hours - OT_HOURS) +
        ' over the ' + OT_HOURS + '-hour line, at premium rate.</p></div>';
    });
  }
  if(res.solo.length){
    h += '<div class="sc-sec">One-deep roles</div>';
    res.solo.forEach(function(s){
      h += '<div class="sc-card"><h4>' + esc(s.role) + ' — only ' + esc(s.person) + ' ever covers it</h4>' +
        '<p>' + s.shifts + ' shifts in this file, one person deep. A single call-out has no backup.</p></div>';
    });
  }
  if(res.turn.length || res.streak.length){
    h += '<div class="sc-sec">Fatigue risk</div>';
    res.turn.forEach(function(t){
      h += '<div class="sc-card warn"><h4>' + esc(t.person) + ' — ' + fmtH(t.hours) +
        ' between shifts</h4><p>Off ' + t.from + ', back on ' + t.to + '. Under the ' +
        SHORT_TURNAROUND + '-hour turnaround most rosters treat as the floor.</p></div>';
    });
    res.streak.forEach(function(s){
      h += '<div class="sc-card warn"><h4>' + esc(s.person) + ' — ' + s.days +
        ' days straight</h4><p>' + s.from + ' through ' + s.to + ', no day off.</p></div>';
    });
  }
  if(!any){
    h += '<div class="sc-clean"><strong>No gaps found.</strong> Every normally-staffed role is ' +
      'covered every day, nobody crosses ' + OT_HOURS + ' hours, no role is one person deep, and ' +
      'every turnaround clears ' + SHORT_TURNAROUND + ' hours. That is the result you want &mdash; ' +
      'and it is not the same as not having looked.</div>';
  }
  document.getElementById('sc-body').innerHTML = h;
  rep.style.display = 'block';
  rep.scrollIntoView({behavior:'smooth', block:'start'});
}

/* Invented facility. Names, roles and every hour are made up. */
var SAMPLE = [
'Date,Employee,Role,Start,End',
'2026-08-03,Dana Whitfield,Med Tech,07:00,15:00',
'2026-08-03,Marcus Reyes,Caregiver,07:00,19:00',
'2026-08-03,Priya Nandan,Caregiver,19:00,07:00',
'2026-08-03,Tom Alvarez,Dining,06:00,14:00',
'2026-08-04,Dana Whitfield,Med Tech,07:00,15:00',
'2026-08-04,Marcus Reyes,Caregiver,07:00,19:00',
'2026-08-04,Priya Nandan,Caregiver,19:00,07:00',
'2026-08-04,Tom Alvarez,Dining,06:00,14:00',
'2026-08-05,Dana Whitfield,Med Tech,07:00,15:00',
'2026-08-05,Marcus Reyes,Caregiver,07:00,19:00',
'2026-08-05,Sofia Grant,Caregiver,19:00,07:00',
'2026-08-05,Tom Alvarez,Dining,06:00,14:00',
'2026-08-06,Dana Whitfield,Med Tech,07:00,15:00',
'2026-08-06,Marcus Reyes,Caregiver,07:00,19:00',
'2026-08-06,Priya Nandan,Caregiver,19:00,07:00',
'2026-08-06,Tom Alvarez,Dining,06:00,14:00',
'2026-08-07,Marcus Reyes,Caregiver,07:00,19:00',
'2026-08-07,Priya Nandan,Caregiver,19:00,07:00',
'2026-08-07,Tom Alvarez,Dining,06:00,14:00',
'2026-08-08,Dana Whitfield,Med Tech,07:00,15:00',
'2026-08-08,Marcus Reyes,Caregiver,07:00,19:00',
'2026-08-08,Sofia Grant,Caregiver,19:00,07:00',
'2026-08-08,Tom Alvarez,Dining,06:00,14:00',
'2026-08-09,Dana Whitfield,Med Tech,07:00,15:00',
'2026-08-09,Marcus Reyes,Caregiver,07:00,19:00',
'2026-08-09,Priya Nandan,Caregiver,19:00,07:00',
'2026-08-09,Tom Alvarez,Dining,06:00,14:00'
].join('\n');

var current = null;
function load(name, text){
  var rows = parseCSV(text);
  if(rows.length < 2){ alert('That file has no shift rows.'); return; }
  var header = rows[0].map(function(h,i){ return (h||'').trim() || ('column ' + (i+1)); });
  var body = rows.slice(1).filter(function(r){ return r.join('').trim() !== ''; });
  var picks = detect(header, body);
  render(name, analyze(header, body, picks), picks, header);
}

var drop = document.getElementById('sc-drop');
var input = document.getElementById('sc-file');
function handleFile(f){
  if(!f) return;
  readAny(f, function(text){
    try { load(f.name, text); }
    catch(e){ alert('Could not read that file. Try saving it as CSV.'); }
  });
}
drop.addEventListener('click', function(){ input.click(); });
drop.addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); input.click(); } });
input.addEventListener('change', function(){ handleFile(input.files[0]); });
['dragover','dragenter'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.add('is-over'); }); });
['dragleave','drop'].forEach(function(ev){ drop.addEventListener(ev, function(e){ e.preventDefault(); drop.classList.remove('is-over'); }); });
drop.addEventListener('drop', function(e){ handleFile(e.dataTransfer.files[0]); });
document.getElementById('sc-sample').addEventListener('click', function(){ load('sample-roster.csv', SAMPLE); });
})();
</script>
"""

LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Shift Coverage Check",
  "url": "https://automatedworkflowllc.com/shift-coverage-check/",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Any",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "description": "Free in-browser schedule analyzer for rosters: uncovered days, overtime weeks, roles only one person can fill, short turnarounds. No upload -- runs locally."
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
