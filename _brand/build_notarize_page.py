#!/usr/bin/env python3
"""Build /proof/notarize/ -- an in-browser notary using Ed25519.

This closes, in public, the limit /proof/ admits to: our CLI receipts are signed
with HMAC, which proves integrity to anyone holding the key and therefore proves
nothing to a stranger. Ed25519 is now native in the Web Crypto API (64-byte
signatures, 32-byte public keys), so a browser can mint a keypair, sign a
receipt, and hand a verifier the PUBLIC half. Nobody has to trust us, or share a
secret, or hold an account, or upload a byte.

What a visitor does here:
  1. Drop a file. The browser hashes it (SHA-256) and signs a receipt.
  2. Drop the same file again later -- or a changed one -- and the page says
     MATCHES or ALTERED, with the two hashes side by side.
  3. Export the receipt chain and the public key. Anyone, anywhere, with no
     account and no contact with us, can verify both.

Receipts use the same shape as our CLI ledger (spec/id/prev/canonical JSON,
chained by sha256 of the previous raw line) because a format only becomes a
standard if the free tool and the paid tool speak it.

HONESTY, stated on the page rather than buried:
  * A keypair proves CONTINUITY, not IDENTITY. Anyone can generate one. It
    proves the same holder signed these things in this order -- to bind it to a
    person you must publish the fingerprint somewhere, which is what our own
    anchors file does.
  * The timestamp comes from the visitor's clock. It is not a trusted time
    source, and the page says so.
  * The private key lives in this browser's localStorage and nowhere else. Clear
    the browser and it is gone. That is stated up front, not discovered later.

Same shell as the other pages so nav/footer/tokens never drift. Nothing uploads:
no fetch, no XHR, no socket -- the architectural promise every tool page makes,
asserted against the built bytes at the bottom of this file.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'spreadsheet-cleanup-service' / 'index.html'
OUT_DIR = ROOT / 'proof' / 'notarize'

TITLE = 'Notarize a File in Your Browser — Signed and Verifiable'
DESC = ('Hash and sign any file in your own browser with Ed25519, then prove later it has not '
        'changed. Anyone can verify with the public key. Nothing is uploaded.')
CANON = 'https://automatedworkflowllc.com/proof/notarize/'

PAGE_CSS = """
/* ---- in-browser notary ---- */
.nz-lede{font-size:1.06rem;max-width:40rem}
.nz-grid{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));margin:1.6rem 0 0}
.nz-card{border:1px solid var(--line);border-radius:.8rem;background:var(--card);padding:1.1rem 1.2rem}
.nz-card h2{margin:0 0 .25rem;font-size:1.05rem}
.nz-card p{margin:0 0 .8rem;color:var(--ink-soft);font-size:.9rem}
.nz-drop{border:1.5px dashed var(--line-strong);border-radius:.6rem;padding:1.2rem;text-align:center;
  color:var(--ink-soft);font-size:.9rem;cursor:pointer;background:var(--bg-soft);transition:.15s}
.nz-drop:hover,.nz-drop.over{border-color:var(--accent);color:var(--ink)}
.nz-drop:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.nz-out{margin:.9rem 0 0;font-family:var(--mono);font-size:.78rem;word-break:break-all;color:var(--ink-soft)}
.nz-verdict{margin:.9rem 0 0;font-family:var(--mono);font-size:.85rem;padding:.6rem .8rem;
  border-radius:.5rem;border:1px solid var(--line);background:var(--bg-soft);color:var(--ink-soft)}
.nz-verdict.ok{border-color:#1F6E4A;color:#1F6E4A}
.nz-verdict.bad{border-color:#B4452C;color:#B4452C}
.nz-key{margin:1.6rem 0 0;border:1px solid var(--line);border-radius:.8rem;background:var(--bg-soft);
  padding:1rem 1.2rem}
.nz-key code{font-family:var(--mono);font-size:.78rem;word-break:break-all}
.nz-rows{margin:1rem 0 0;display:grid;gap:.5rem}
.nz-row{border:1px solid var(--line);border-radius:.55rem;background:var(--card);padding:.6rem .8rem;
  font-size:.85rem}
.nz-row b{font-family:var(--mono);font-size:.8rem}
.nz-row span{color:var(--ink-soft);font-family:var(--mono);font-size:.72rem;word-break:break-all;
  display:block;margin-top:.15rem}
.nz-btns{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0 0}
.nz-btns button{font:inherit;font-size:.86rem;padding:.5rem .9rem;border-radius:.45rem;cursor:pointer;
  border:1px solid var(--line-strong);background:var(--card);color:var(--ink)}
.nz-btns button:hover{border-color:var(--ink)}
.nz-btns button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.nz-limits{margin:2.2rem 0 0;padding-left:1.15rem;max-width:42rem}
.nz-limits li{margin:.45rem 0;color:var(--ink-soft)}
.nz-limits b{color:var(--ink)}
.nz-unsupported{border:1px solid #B4452C;border-radius:.6rem;padding:.9rem 1.1rem;margin:1.4rem 0 0;
  color:#B4452C;font-size:.9rem}
"""

MAIN = """
<main id="main" class="wrap" style="padding-top:2.2rem;padding-bottom:3rem;max-width:52rem">
  <h1 style="margin-bottom:.4rem">Notarize a file in your own browser.</h1>
  <p class="nz-lede" style="color:var(--ink-soft)">
    Drop in a report, a contract, an export &mdash; anything. Your browser hashes it and signs a
    receipt with a key it generates on this device. Later, you (or your auditor, or your client)
    can prove the file has not changed by a single byte. <b>Nothing is uploaded</b>: there is no
    endpoint here to receive a file, and you can watch the network tab stay empty.
  </p>

  <div id="nz-unsupported" class="nz-unsupported" hidden>
    This browser does not support Ed25519 signing in the Web Crypto API, so the signing half of this
    page cannot run. Hashing and comparison still work. Recent Chrome, Edge, Safari and Firefox all
    support it.
  </div>

  <div class="nz-grid">
    <div class="nz-card">
      <h2>1 &middot; Notarize</h2>
      <p>Hash the file and sign a receipt. The file never leaves this page.</p>
      <div class="nz-drop" id="drop-sign" tabindex="0" role="button"
           aria-label="Choose or drop a file to notarize">Drop a file here, or press to choose</div>
      <input type="file" id="file-sign" hidden>
      <div class="nz-out" id="out-sign"></div>
    </div>

    <div class="nz-card">
      <h2>2 &middot; Check it later</h2>
      <p>Drop the same file &mdash; or a changed one &mdash; and compare against its receipt.</p>
      <div class="nz-drop" id="drop-check" tabindex="0" role="button"
           aria-label="Choose or drop a file to check">Drop a file here, or press to choose</div>
      <input type="file" id="file-check" hidden>
      <div class="nz-verdict" id="out-check">No file checked yet.</div>
    </div>
  </div>

  <div class="nz-key">
    <h2 style="margin:0 0 .3rem;font-size:1.05rem">Your public key</h2>
    <p style="margin:0 0 .5rem;color:var(--ink-soft);font-size:.9rem">Hand this to anyone who needs
    to verify your receipts. It cannot sign anything and it reveals nothing about the files.</p>
    <code id="pubkey">generating&hellip;</code>
    <div class="nz-btns">
      <button id="btn-verify-all">Verify every receipt</button>
      <button id="btn-export">Export receipts + key</button>
      <button id="btn-clear">Clear this device's ledger</button>
    </div>
    <div class="nz-verdict" id="out-verify">Chain not yet verified.</div>
    <div class="nz-rows" id="rows"></div>
  </div>

  <h2 style="margin-top:2.4rem">What this proves, and what it does not</h2>
  <ul class="nz-limits">
    <li><b>It proves continuity, not identity.</b> Anyone can generate a keypair, including someone
      pretending to be you. What a signature proves is that <em>the holder of this key</em> signed
      these files in this order. Binding a key to a person means publishing its fingerprint
      somewhere public &mdash; which is exactly what we do with
      <a href="/proof/">our own chain head</a>.</li>
    <li><b>The timestamp is your computer's clock.</b> It is not a trusted time source. It is
      evidence of ordering, not proof of the hour.</li>
    <li><b>The private key lives in this browser and nowhere else.</b> We never see it &mdash; there
      is nothing here to send it to. Clear your browser storage and it is gone for good, and old
      receipts stay verifiable by their public key but you cannot sign new ones in the same chain.</li>
    <li><b>A receipt proves the bytes, not the truth.</b> It proves a file has not changed since it
      was signed. Whether the file was right in the first place is a different question, and an
      honest tool should not pretend otherwise.</li>
  </ul>

  <div style="margin-top:2rem;padding:1.4rem;border:1px solid var(--line);border-radius:12px;background:var(--card)">
    <h2 style="margin-top:0">This is the same machinery we run on ourselves</h2>
    <p style="color:var(--ink-soft)">Our own scheduled jobs write receipts in this format every
    night, chained the same way, and we publish the chain head publicly so the record binds us too
    &mdash; including the nights our own audit produced nothing.</p>
    <p style="margin-bottom:0"><a class="btn" href="/proof/">See our ledger</a>
    &nbsp; <a href="/free-demo/">Ask about an automation audit &rarr;</a></p>
  </div>
</main>
"""

JS = """
<script>
(function(){
  'use strict';
  var LS_KEY = 'awllc.notary.key', LS_LEDGER = 'awllc.notary.ledger';
  var priv = null, pubB64 = null, ledger = [], canSign = true;

  function b64u(buf){
    var b = '', a = new Uint8Array(buf);
    for (var i = 0; i < a.length; i++) b += String.fromCharCode(a[i]);
    return btoa(b).replace(/\\+/g,'-').replace(/\\//g,'_').replace(/=+$/,'');
  }
  function unb64u(s){
    s = s.replace(/-/g,'+').replace(/_/g,'/');
    while (s.length % 4) s += '=';
    var bin = atob(s), a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return a;
  }
  function hex(buf){
    return Array.prototype.map.call(new Uint8Array(buf), function(x){
      return x.toString(16).padStart(2,'0'); }).join('');
  }
  async function sha256(data){
    return hex(await crypto.subtle.digest('SHA-256',
      typeof data === 'string' ? new TextEncoder().encode(data) : data));
  }
  // Canonical JSON: sorted keys, no whitespace. Same rule as our CLI, so a
  // receipt signed here and a receipt signed there hash identically.
  function canon(o){
    if (Array.isArray(o)) return '[' + o.map(canon).join(',') + ']';
    if (o && typeof o === 'object')
      return '{' + Object.keys(o).sort().map(function(k){
        return JSON.stringify(k) + ':' + canon(o[k]); }).join(',') + '}';
    return JSON.stringify(o);
  }
  function esc(s){ return String(s).replace(/[<>&"]/g, function(c){
    return ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'})[c]; }); }

  async function initKey(){
    try {
      var stored = localStorage.getItem(LS_KEY);
      if (stored){
        var jwk = JSON.parse(stored);
        priv = await crypto.subtle.importKey('jwk', jwk, {name:'Ed25519'}, true, ['sign']);
        var pj = {kty:jwk.kty, crv:jwk.crv, x:jwk.x};
        var pk = await crypto.subtle.importKey('jwk', pj, {name:'Ed25519'}, true, ['verify']);
        pubB64 = b64u(await crypto.subtle.exportKey('raw', pk));
      } else {
        var kp = await crypto.subtle.generateKey({name:'Ed25519'}, true, ['sign','verify']);
        priv = kp.privateKey;
        localStorage.setItem(LS_KEY, JSON.stringify(await crypto.subtle.exportKey('jwk', kp.privateKey)));
        pubB64 = b64u(await crypto.subtle.exportKey('raw', kp.publicKey));
      }
      document.getElementById('pubkey').textContent = 'ed25519:' + pubB64;
    } catch (e){
      canSign = false;
      document.getElementById('nz-unsupported').hidden = false;
      document.getElementById('pubkey').textContent = 'unavailable in this browser';
    }
  }

  function loadLedger(){
    try { ledger = JSON.parse(localStorage.getItem(LS_LEDGER) || '[]'); }
    catch (e){ ledger = []; }
  }
  function saveLedger(){ localStorage.setItem(LS_LEDGER, JSON.stringify(ledger)); }

  async function headHash(){
    return ledger.length ? await sha256(ledger[ledger.length-1]) : 'GENESIS';
  }

  async function notarize(file){
    var out = document.getElementById('out-sign');
    out.textContent = 'hashing ' + file.name + '\\u2026';
    var digest = await sha256(await file.arrayBuffer());
    var body = {
      spec: 'attest/0.1-web', kind: 'notarize',
      name: file.name, bytes: file.size, sha256: digest,
      at: new Date().toISOString().replace(/\\.\\d+Z$/, ''),
      prev: await headHash(), pubkey: canSign ? ('ed25519:' + pubB64) : null
    };
    if (canSign){
      var sig = await crypto.subtle.sign({name:'Ed25519'}, priv, new TextEncoder().encode(canon(body)));
      body.sig = 'ed25519:' + b64u(sig);
    }
    ledger.push(canon(body));
    saveLedger();
    out.innerHTML = '<b>' + esc(file.name) + '</b> &mdash; sha256 ' + digest.slice(0,32) + '&hellip;'
      + (canSign ? '<br>signed, receipt ' + ledger.length + ' in your chain'
                 : '<br>hashed (signing unavailable in this browser)');
    render();
  }

  async function check(file){
    var v = document.getElementById('out-check');
    if (!ledger.length){ v.className = 'nz-verdict'; v.textContent = 'Notarize a file first.'; return; }
    var digest = await sha256(await file.arrayBuffer());
    var hit = null;
    for (var i = 0; i < ledger.length; i++){
      var r = JSON.parse(ledger[i]);
      if (r.sha256 === digest){ hit = {r:r, i:i}; break; }
    }
    if (hit){
      v.className = 'nz-verdict ok';
      v.textContent = 'MATCHES receipt ' + (hit.i+1) + ' \\u2014 ' + hit.r.name + ', notarized '
        + hit.r.at + '. Not one byte has changed.';
      return;
    }
    var same = null;
    for (var j = 0; j < ledger.length; j++){
      var q = JSON.parse(ledger[j]);
      if (q.name === file.name){ same = q; break; }
    }
    v.className = 'nz-verdict bad';
    v.textContent = same
      ? 'ALTERED \\u2014 a file named ' + file.name + ' was notarized with hash '
        + same.sha256.slice(0,24) + '\\u2026 but this one hashes to ' + digest.slice(0,24)
        + '\\u2026 The contents are not the same.'
      : 'NO RECEIPT \\u2014 nothing in this chain matches this file (' + digest.slice(0,24) + '\\u2026).';
  }

  async function verifyAll(){
    var v = document.getElementById('out-verify');
    if (!ledger.length){ v.className = 'nz-verdict'; v.textContent = 'No receipts yet.'; return; }
    var prev = 'GENESIS', linkBad = 0, sigBad = 0, sigChecked = 0;
    for (var i = 0; i < ledger.length; i++){
      var r = JSON.parse(ledger[i]);
      if (r.prev !== prev) linkBad++;
      if (r.sig && r.pubkey){
        var body = {}; Object.keys(r).forEach(function(k){ if (k !== 'sig') body[k] = r[k]; });
        try {
          var pk = await crypto.subtle.importKey('raw', unb64u(r.pubkey.replace(/^ed25519:/,'')),
                     {name:'Ed25519'}, false, ['verify']);
          var ok = await crypto.subtle.verify({name:'Ed25519'}, pk,
                     unb64u(r.sig.replace(/^ed25519:/,'')), new TextEncoder().encode(canon(body)));
          sigChecked++; if (!ok) sigBad++;
        } catch (e){ sigBad++; }
      }
      prev = await sha256(ledger[i]);
    }
    if (!linkBad && !sigBad){
      v.className = 'nz-verdict ok';
      v.textContent = 'VERIFIED \\u2014 ' + ledger.length + ' receipt(s), chain intact, '
        + sigChecked + ' signature(s) valid. Head ' + prev.slice(0,24) + '\\u2026';
    } else {
      v.className = 'nz-verdict bad';
      v.textContent = 'FAILED \\u2014 ' + linkBad + ' broken link(s), ' + sigBad + ' bad signature(s).';
    }
  }

  function render(){
    var host = document.getElementById('rows');
    host.textContent = '';
    ledger.forEach(function(line, i){
      var r = JSON.parse(line);
      var d = document.createElement('div');
      d.className = 'nz-row';
      d.innerHTML = '<b>' + (i+1) + ' &middot; ' + esc(r.name) + '</b> <span>' + esc(r.at)
        + ' &middot; ' + r.bytes + ' bytes &middot; sha256 ' + esc(r.sha256) + '</span>';
      host.appendChild(d);
    });
  }

  function exportAll(){
    var text = '# Automated Workflow notary export\\n'
      + '# public key: ' + (pubB64 ? 'ed25519:' + pubB64 : '(none)') + '\\n'
      + '# Each line is a receipt. Verify: signature over the canonical JSON of the\\n'
      + '# receipt without its "sig" field; chain: prev = sha256 of the previous raw line.\\n'
      + ledger.join('\\n') + '\\n';
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], {type:'text/plain'}));
    a.download = 'notary-receipts.txt';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function wireDrop(dropId, inputId, handler){
    var d = document.getElementById(dropId), inp = document.getElementById(inputId);
    d.addEventListener('click', function(){ inp.click(); });
    d.addEventListener('keydown', function(e){
      if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); inp.click(); } });
    d.addEventListener('dragover', function(e){ e.preventDefault(); d.classList.add('over'); });
    d.addEventListener('dragleave', function(){ d.classList.remove('over'); });
    d.addEventListener('drop', function(e){
      e.preventDefault(); d.classList.remove('over');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) handler(e.dataTransfer.files[0]);
    });
    inp.addEventListener('change', function(){ if (inp.files[0]) handler(inp.files[0]); });
  }

  document.addEventListener('DOMContentLoaded', function(){
    loadLedger(); render();
    initKey();
    wireDrop('drop-sign', 'file-sign', notarize);
    wireDrop('drop-check', 'file-check', check);
    document.getElementById('btn-verify-all').addEventListener('click', verifyAll);
    document.getElementById('btn-export').addEventListener('click', exportAll);
    document.getElementById('btn-clear').addEventListener('click', function(){
      ledger = []; saveLedger(); render();
      var v = document.getElementById('out-verify');
      v.className = 'nz-verdict'; v.textContent = 'Ledger cleared on this device.';
    });
  });
})();
</script>
"""


def main() -> None:
    # The promise every tool page makes must hold in the built bytes, not the intent.
    for bad in ('fetch(', 'XMLHttpRequest', 'WebSocket', 'sendBeacon'):
        if bad in MAIN + JS:
            raise SystemExit(f'refusing to build: {bad} would break the no-upload promise')

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

    page = head + MAIN + JS + footer + '\n</body>\n</html>\n'
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / 'index.html').write_text(page, encoding='utf-8')
    print(f'wrote {OUT_DIR / "index.html"} ({len(page)} bytes)')


if __name__ == '__main__':
    main()
